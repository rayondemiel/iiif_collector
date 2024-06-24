import logging
import os
import requests
import shutil
import tempfile
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from iiif_collector.iiif import ManifestIIIF, ImageIIIF
from iiif_collector.variables import TEST_IIIF_MANIFEST


class TestManifestIIIF(TestCase):

    @patch('requests.Session')
    def setUp(self, mock_session_class):
        # init log
        self.path = tempfile.mkdtemp()
        logfile_path = os.path.join(self.path, "logfile_test.txt")
        logging.basicConfig(filename=logfile_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # Set up a fake URL and path
        self.fake_url = 'https://example.org/iiif/book1/manifest'

        # Configure mock response to return TEST_IIIF_MANIFEST
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = TEST_IIIF_MANIFEST

        # Mock Session instance
        self.mock_session_instance = MagicMock()
        self.mock_session_instance.get.return_value = self.mock_response

        # Ensure the mock session class returns the mock session instance
        mock_session_class.return_value = self.mock_session_instance

        # Instantiate ManifestIIIF with fake URL
        self.manifest = ManifestIIIF(url=self.fake_url,
                                     path=self.path,
                                     session=self.mock_session_instance,
                                     verbose=True,
                                     n=10,
                                     random=True)

    def tearDown(self):
        shutil.rmtree(self.path)

    def test_init_with_session(self):
        """iiif_collection.iiif.ManifestIIIF"""
        # Assertions based on the expected behavior after initialization
        self.assertEqual(self.manifest.url, self.fake_url)
        self.assertEqual(self.manifest.session, self.mock_session_instance)
        self.assertEqual(self.manifest.n, 10)
        self.assertTrue(self.manifest.random)
        self.assertEqual(self.manifest.json, TEST_IIIF_MANIFEST)
        self.assertTrue(os.path.exists(self.manifest.out_dir))

    def test_clean_id(self):
        """iiif_collection.iiif.ManifestIIIF._clean_id"""
        cleaned_id = self.manifest._clean_id("https://example.org/iiif/book1/manifest")
        self.assertEqual(cleaned_id, "example.org_iiif_book1_manifest")

    def test_get_title_value(self):
        """iiif_collection.iiif.ManifestIIIF._get_title_value"""
        title_value = self.manifest._get_title_value()
        self.assertEqual(title_value, "Sample Book")

    @patch('logging.info')
    def test_json_present(self, mock_logging_info):
        """iiif_collection.iiif.ManifestIIIF._json_present"""
        self.assertTrue(self.manifest._json_present())
        manifest_error = ManifestIIIF(url=self.fake_url,
                                     path=self.path,
                                     session=self.mock_session_instance,
                                     verbose=True,
                                     n=10,
                                     random=True)
        manifest_error.json = {}
        self.assertFalse(manifest_error._json_present())
        self.assertEqual(mock_logging_info.call_count, 1)

    @patch('os.path.join')
    @patch('json.dump')
    @patch('builtins.open')
    @patch('logging.info')
    def test_save_manifest(self, mock_logging_info, mock_open, mock_json_dump, mock_os_path_join):
        """iiif_collection.iiif.ManifestIIIF.save_manifest"""
        mock_os_path_join.side_effect = [
            os.path.join(self.manifest.out_dir, 'manifests', 'manifest_IIIF.json'),
            os.path.join(self.manifest.out_dir, 'manifests'),
            os.path.join(self.manifest.out_dir, 'manifests', 'manifest_IIIF.json')
        ]

        self.manifest.save_manifest()

        self.assertEqual(mock_os_path_join.call_count, 5)
        mock_open.assert_called_once_with(mock_os_path_join.return_value, mode='w')
        mock_json_dump.assert_called_once_with(TEST_IIIF_MANIFEST, mock_open.return_value.__enter__.return_value,
                                               indent=3, ensure_ascii=False)
        mock_logging_info.assert_called_once_with('https://example.org/iiif/book1/manifest : Manifest saved',
                                                  exc_info=True)
        self.assertEqual(mock_logging_info.call_count, 1)

    def test_get_images_from_manifest(self):
        images = self.manifest.get_images_from_manifest()
        self.assertEqual(images, [("https://example.org/iiif/book1/res/page1/full/full/0/default.jpg", "p1")])

    @patch('iiif_collector.iiif.ImageIIIF')
    @patch('iiif_collector.iiif.ManifestIIIF.get_images_from_manifest')
    @patch('logging.info')
    def test_save_images(self, mock_logging_info, mock_get_images, mock_ImageIIIF):
        """iiif_collection.iiif.ManifestIIIF.save_images"""
        mock_get_images.return_value = [('url1', 'filename1'), ('url2', 'filename2')]
        mock_image_instance = MagicMock()
        mock_ImageIIIF.return_value = mock_image_instance
        mock_image_instance.img.headers.get.return_value = '1024'
        mock_image_instance.img.iter_content.return_value = [b'data'] * 128

        self.manifest.short_filename = False
        self.manifest.random = False
        self.manifest.n = None
        self.manifest.save_images()

        mock_get_images.assert_called_once()
        mock_ImageIIIF.assert_has_calls([call('url1', self.manifest.out_dir, short_filename=False),
                                        call('url2', self.manifest.out_dir, short_filename=False)], any_order=True)
        mock_image_instance.load_image.assert_called()
        mock_image_instance.save_image.assert_called()
        self.assertEqual(mock_logging_info.call_count, 1)

    @patch('os.path.join')
    @patch('builtins.open')
    def test_save_list_images(self, mock_open, mock_os_path_join):
        """iiif_collection.iiif.ManifestIIIF.save_list_images"""
        mock_os_path_join.return_value = os.path.join(self.path, "images", "list_images.txt")
        self.manifest.save_list_images()
        mock_open.assert_called_once_with(mock_os_path_join.return_value, 'w')

    def test_get_metadata(self):
        """iiif_collection.iiif.ManifestIIIF._get_metadata"""
        metadata = self.manifest._get_metadata()
        self.assertEqual(metadata, [("Author", "John Doe"), ("Published", "2023")])

    @patch('os.path.join')
    @patch('builtins.open')
    @patch('logging.info')
    def test_save_metadata(self, mock_save_txt, mock_os_path_join):
        """iiif_collection.iiif.ManifestIIIF.save_metadata"""
        mock_os_path_join.return_value = os.path.join(self.path, "metadata")
        self.manifest.save_metadata()
        mock_save_txt.assert_called_once_with(list_mtda=[("Author", "John Doe"), ("Published", "2023")],
                                              file_path=mock_os_path_join.return_value)

    @patch('os.path.join')
    @patch('builtins.open')
    @patch('logging.info')
    def test_save_metadata(self, mock_logging_info, mock_open, mock_os_path_join):
        """iiif_collection.iiif.ManifestIIIF.save_metadata"""
        mock_os_path_join.return_value = lambda *args: os.path.join(*args)
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        self.manifest.save_metadata()

        self.assertEqual(mock_os_path_join.call_count, 2)
        mock_open.assert_called_once_with(os.path.join('/tmp', 'metadata', 'metadata.txt'), 'w')
        mock_file.writelines.assert_called_once()
        generator_content = list(mock_file.writelines.call_args[0][0])
        expected_content = [f"{i[0]} : {i[1]}\n" for i in [('Author', 'John Doe'), ("Published", "2023")]]
        self.assertEqual(generator_content, expected_content)

    @patch('requests.get')
    def test_load_from_url_without_session(self, mock_requests_get):
        """iiif_collection.iiif.ManifestIIIF without session"""

        mock_response = MagicMock()
        mock_response.json.return_value = TEST_IIIF_MANIFEST
        mock_requests_get.return_value = mock_response

        manifest = ManifestIIIF(self.fake_url, self.path)

        mock_requests_get.assert_called_once_with('https://example.org/iiif/book1/manifest')
        self.assertEqual(manifest.json, TEST_IIIF_MANIFEST)
        self.assertEqual(manifest.id, 'example.org_iiif_book1_manifest')