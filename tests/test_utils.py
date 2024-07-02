import json
import logging
import os
import shutil
import tempfile
from unittest import TestCase
from unittest.mock import patch, mock_open, call

from iiif_collector.variables import ImageList, MetadataList, CONFIG_FOLDER, TEST_IIIF_MANIFEST
from iiif_collector.opt.utils import *


class TestUtils(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        logfile_path = os.path.join(self.temp_dir, "logfile_test.txt")
        logging.basicConfig(filename=logfile_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    @patch('logging.error')
    def test_suppress_char(self, mock_logging_error):
        """iiif_collector.opt.utils.suppress_char"""
        self.assertEqual(suppress_char("hello! world;"), "hello_world_")
        self.assertEqual(suppress_char({"key!": "value;"}), {"key_": "value_"})
        self.assertEqual(suppress_char({"key!": ["value1;", "value2!"]}), {"key_": ["value1_", "value2_"]})
        # logging error
        invalid_input = 12345
        with self.assertRaises(TypeError):
            suppress_char(invalid_input)
        self.assertEqual(mock_logging_error.call_count, 1)

    def test_url2filename(self):
        """iiif_collector.opt.utils.url2filename"""
        self.assertEqual(url2filename("https://gallica.bnf.fr/iiif/ark:/12148/btv1b52505441p/f11/full/full/0/native.jpg"),
                               "iiif%2Fark%3A%2F12148%2Fbtv1b52505441p%2Ff11")

    def test_filename2path_url(self):
        """iiif_collector.opt.utils.filename2path_url"""
        self.assertEqual(filename2path_url("ark%3A%2F12148%2Fbtv1b52505441p%2Ff11"), "ark:/12148/btv1b52505441p/f11")

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    def test_save_json(self, mock_join, mock_open_file):
        """iiif_collector.opt.utils.save_json"""
        join_path = os.path.join('/dummy/path', 'manifest_IIIF.json')
        mock_join.return_value = join_path
        save_json(TEST_IIIF_MANIFEST, '/dummy/path')
        mock_open_file.assert_called_once_with(join_path, mode="w")
        mock_open_file.reset_mock()

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    def test_save_txt(self, mock_join, mock_open_file):
        """iiif_collector.opt.utils.save_txt"""
        join_path = os.path.join('/dummy/path', 'metadata.txt')
        mock_join.return_value = join_path
        save_txt(TEST_IIIF_MANIFEST['metadata'], '/dummy/path')
        mock_open_file.assert_called_with(os.path.join('/dummy/path', 'metadata.txt'), 'w')
        mock_open_file.reset_mock()

    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_make_out_dirs(self, mock_exists, mock_makedirs):
        """iiif_collector.opt.utils.make_out_dirs"""
        # api = True
        mock_exists.return_value = False
        make_out_dirs('/dummy/path', api=True)
        mock_makedirs.assert_called_once_with('/dummy/path/image_IIIF')
        mock_makedirs.reset_mock()

        # api = False
        mock_exists.return_value = False
        make_out_dirs('/dummy/path', api=False)
        expected_calls = [
            call('/dummy/path/manifests'),
            call('/dummy/path/images'),
            call('/dummy/path/metadata')
        ]
        self.assertEqual(mock_makedirs.call_count, len(expected_calls))
        mock_makedirs.assert_has_calls(expected_calls, any_order=True)

        # Existing dirs
        mock_makedirs.reset_mock()
        mock_exists.side_effect = lambda path: path in ['/dummy/path/manifests', '/dummy/path/images']
        make_out_dirs('/dummy/path', api=False)
        expected_calls = [call('/dummy/path/metadata')]
        self.assertEqual(mock_makedirs.call_count, len(expected_calls))
        mock_makedirs.assert_has_calls(expected_calls, any_order=True)

    def test_randomized(self):
        """iiif_collector.opt.utils.randomized"""
        image_list = [("uri1", "file1"), ("uri2", "file2"), ("uri3", "file3"), ("uri4", "file4"), ("uri5", "file5")]
        with patch('random.shuffle') as mock_shuffle:
            mock_shuffle.side_effect = lambda x: x.reverse()
            result = randomized(image_list, 3)
            self.assertEqual(len(result), 3)
            self.assertEqual(result, [("uri5", "file5"), ("uri4", "file4"), ("uri3", "file3")])

    @patch('logging.error')
    @patch('logging.warning')
    @patch('logging.info')
    def test_journal_error(self, mock_logging_info, mock_logging_warning, mock_logging_error):
        """iiif_collector.opt.utils.journal_error"""
        # ERROR
        journal_error('ERROR', object="test_object", message="test_message")
        mock_logging_error.assert_called_once_with("An error has occurred - test_object : test_message", exc_info=True)

        # WARNING
        journal_error('WARNING', object="test_object", message="test_message")
        mock_logging_warning.assert_called_once_with("test_object : test_message", exc_info=True)

        # INFO
        journal_error('INFO', object="test_object", message="test_message")
        mock_logging_info.assert_called_once_with("test_object : test_message", exc_info=True)

        # With complement_info
        journal_error('INFO', object="test_object", message="test_message", complement_info="additional_info")
        calls = [
            call("test_object : test_message", exc_info=True),
            call("additional_info", exc_info=True)
        ]
        mock_logging_info.assert_has_calls(calls)
        mock_logging_error.assert_called_once()
        mock_logging_warning.assert_called_once()
