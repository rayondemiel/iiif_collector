import asyncio
import aiohttp
import aiofiles
import logging
import os
import shutil
import tempfile
from itertools import cycle, islice
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import call, patch, MagicMock, ANY

from iiif_collector.multiproc import IIIFCollector, ImageIIIFAsync, ParallelizeIIIF
from iiif_collector.variables import DEFAULT_OUT_DIR, TEST_IIIF_MANIFEST


class TestIIIFCollector(IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        logfile_path = os.path.join(self.test_dir, "logfile_test.txt")
        logging.basicConfig(filename=logfile_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        self.collector = IIIFCollector(path=self.test_dir, verbose=False, delay=1, retry=3, short_filename=False)
        self.test_urls = [
            "https://example.org/iiif/image1/full/full/0/default.jpg",
            "https://example.org/iiif/image2/full/full/0/default.jpg",
            "https://example.org/iiif/image3/full/full/0/default.jpg"
        ]

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch.object(ImageIIIFAsync, 'load_image_async')
    async def test_process_urls(self, mock_load_image_async):
        """iiif_collection.multiproc.IIIFCollector.process_urls"""
        await self.collector.process_urls(self.test_urls)
        self.assertEqual(mock_load_image_async.call_count, len(self.test_urls))

    @patch.object(IIIFCollector, 'process_urls')
    async def test_run_async(self, mock_process_urls):
        """iiif_collection.multiproc.IIIFCollector.run_async"""
        await self.collector.run_async(self.test_urls)
        mock_process_urls.assert_called_once_with(self.test_urls)


class TestImageIIIFAsync(IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        logfile_path = os.path.join(self.test_dir, "logfile_test.txt")
        logging.basicConfig(filename=logfile_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        self.image_iiif_async = ImageIIIFAsync(url='https://example.org/iiif/image1/full/full/0/default.jpg',
                                               path=self.test_dir, verbose=False, short_filename=False)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('logging.info')
    async def test_load_image_async(self, mock_logging_info):
        """iiif_collection.multiproc.ImageIIIFAsync.load_image_async"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'fake image data'
        mock_session.get.return_value.__aenter__.return_value = mock_response

        await self.image_iiif_async.load_image_async(mock_session, max_retries=1, retry_delay=1)

        files = os.listdir(self.test_dir)
        self.assertTrue(any(file.endswith('.jpg') for file in files))
        self.assertEqual(mock_logging_info.call_count, 2)

    @patch('asyncio.sleep')
    @patch('logging.info')
    async def test_load_image_async_retry(self, mock_logging_info, mock_sleep):
        """iiif_collection.multiproc.ImageIIIFAsync.load_image_async with retry"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 500
        mock_session.get.return_value.__aenter__.return_value = mock_response

        await self.image_iiif_async.load_image_async(mock_session, max_retries=2, retry_delay=1)
        self.assertEqual(mock_logging_info.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('asyncio.sleep')
    @patch('logging.error')
    async def test_load_image_async_exception(self, mock_logging_error, mock_sleep):
        """iiif_collection.multiproc.IIIFCollector.load_image_async with error"""
        mock_session = MagicMock()
        mock_session.get.side_effect = aiohttp.ClientError

        await self.image_iiif_async.load_image_async(mock_session, max_retries=2, retry_delay=1)

        self.assertEqual(mock_sleep.call_count, 2)
        mock_logging_error.assert_called_once()

class MockEventLoop(asyncio.AbstractEventLoop):
    """Specific mock event for loop"""
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    def is_closed(self):
        return self.closed

    def run_until_complete(self, future):
        pass


class TestParallelizeIIIF(TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        logfile_path = os.path.join(self.path, "logfile_test.txt")
        logging.basicConfig(filename=logfile_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        self.urls = ['http://example.com/manifest1', 'http://example.com/manifest2']
        self.kwargs = {'retry': 3, 'delay': 1, 'verbose': False, 'short_filename': True}

    def test_init(self):
        """iiif_collection.multiproc.ParallelizeIIIF._init() manifest"""
        parallel = ParallelizeIIIF(self.urls, self.path, **self.kwargs)
        self.assertEqual(parallel.urls, self.urls)
        self.assertEqual(parallel.out_dir + '/iiif_output', os.path.join(self.path, DEFAULT_OUT_DIR))
        self.assertEqual(parallel.retry, 3)
        self.assertEqual(parallel.delay, 1)

    def test_init_image(self):
        """iiif_collection.multiproc.ParallelizeIIIF._init() image"""
        parallel = ParallelizeIIIF(self.urls, self.path, image=True, **self.kwargs)
        self.assertTrue(parallel.image)
        self.assertEqual(parallel.out_dir, os.path.join(self.path, DEFAULT_OUT_DIR))

    @patch('multiprocessing.cpu_count')
    def test_get_cpu(self, mock_cpu_count):
        """iiif_collection.multiproc.ParallelizeIIIF.cpu_count"""
        mock_cpu_count.return_value = 8
        parallel = ParallelizeIIIF(self.urls, self.path, **self.kwargs)
        self.assertEqual(parallel._get_cpu(), 4)

    @patch('iiif_collector.multiproc.IIIFCollector')
    @patch('asyncio.new_event_loop')
    @patch('asyncio.set_event_loop')
    @patch('asyncio.run')
    def test_process_chunk_image(self, mock_run, mock_set_event_loop, mock_new_event_loop, mock_IIIFCollector):
        """iiif_collection.multiproc.ParallelizeIIIF._process_chunk_image"""
        parallel = ParallelizeIIIF(self.urls, self.path, image=True, **self.kwargs)
        chunk = [
            "https://example.org/iiif/image1/full/full/0/default.jpg",
            "https://example.org/iiif/image2/full/full/0/default.jpg",
            "https://example.org/iiif/image3/full/full/0/default.jpg"
        ]

        mock_loop = MockEventLoop()
        mock_new_event_loop.return_value = mock_loop

        parallel._process_chunk_image(chunk)

        mock_IIIFCollector.assert_called_once()
        mock_new_event_loop.assert_called_once()
        mock_set_event_loop.assert_called_once_with(mock_loop)
        mock_run.assert_called_once()
        self.assertTrue(mock_loop.is_closed())

    @patch('requests.get')
    def test_process_chunk_manifest(self, mock_requests_get):
        """iiif_collection.multiproc.ParallelizeIIIF._process_chunk_manifest"""
        mock_manifest = MagicMock()
        mock_manifest.out_dir = self.path
        mock_manifest.json.return_value = TEST_IIIF_MANIFEST

        mock_requests_get.return_value = mock_manifest

        parallel = ParallelizeIIIF(self.urls, self.path, image=False, **self.kwargs)
        chunk = ['https://example.org/iiif/book1/manifest']

        with patch.object(parallel, '_process_chunk_image') as mock_process_chunk_image:
            parallel._process_chunk_manifest(chunk)

            mock_process_chunk_image.assert_called_once_with(
                [('https://example.org/iiif/book1/res/page1/full/full/0/default.jpg', 'p1')])

        mock_requests_get.assert_called_once()
        mock_process_chunk_image.assert_called_once()

    @patch('multiprocessing.Process')
    @patch.object(ParallelizeIIIF, '_process_chunk_manifest')
    @patch('psutil.cpu_percent', return_value=40)
    @patch('psutil.virtual_memory')
    def test_run(self, mock_virtual_memory, mock_cpu_percent, mock_process_chunk_manifest, mock_process):
        """iiif_collection.multiproc.ParallelizeIIIF.run()"""
        parallel = ParallelizeIIIF(self.urls, self.path, **self.kwargs)

        mock_process_instance = MagicMock()
        mock_process.return_value = mock_process_instance

        # Simulate processes running and then stopping
        process_alive_sequence = list(islice(cycle([True]), 10)) + [False, False, False]
        mock_process_instance.is_alive.side_effect = process_alive_sequence

        mock_virtual_memory.return_value = MagicMock(total=1024 * 1024 * 1024)

        parallel.run()

        # Check if Process was called for each URL chunk
        expected_calls = [
            call(target=ANY, args=([url],))
            for url in self.urls
        ]
        mock_process.assert_has_calls(expected_calls, any_order=True)

        # Assertions
        self.assertEqual(mock_process.call_count, parallel.num_processes)
        mock_process_instance.start.assert_called()
        mock_process_instance.join.assert_called()
        self.assertGreater(mock_cpu_percent.call_count, 1)
        self.assertGreater(mock_virtual_memory.call_count, 1)