import os
import logging
from rich import print as rich_print
from rich import console
from unittest import TestCase
from unittest.mock import patch
import tempfile

from iiif_collector.iiif import ConfigIIIF


class TestConfigIIIF(TestCase):
    def setUp(self):
        self.config = ConfigIIIF()
        self.temp_dir = tempfile.mkdtemp()
        logfile_path = os.path.join(self.temp_dir, "logfile_test.txt")
        logging.basicConfig(filename=logfile_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def test_default_initialization(self):
        self.assertFalse(self.config.verbose)
        self.assertTrue(self.config.short_filename)
        self.assertEqual(self.config.API, 3.0)
        self.assertEqual(self.config.config['region'], 'full')
        self.assertEqual(self.config.config['size'], 'max')
        self.assertEqual(self.config.config['rotation'], 0)
        self.assertEqual(self.config.config['quality'], 'native')
        self.assertEqual(self.config.config['format'], 'default')

    def test_custom_initialization(self):
        config = ConfigIIIF(verbose=True, short_filename=False)
        self.assertTrue(config.verbose)
        self.assertFalse(config.short_filename)

    @patch('rich.print')
    def test_print_config(self, mock_rich_print):
        self.config.__config__()
        """mock_rich_print.assert_called_once_with(
            "[blue]Api level is [pink]3.0[/]. \n[/]"
            "[blue]Configuration is [pink]{'region': 'full', 'size': 'max', 'rotation': 0, 'quality': 'native', \
            'format': 'default'}[/][/]"
        )"""

    def test_get_id(self):
        cleaned_name = self.config.__get_id__('image.jpg')
        self.assertEqual(cleaned_name, 'image')
        cleaned_name = self.config.__get_id__('another_image.png')
        self.assertEqual(cleaned_name, 'another_image')

    @patch('rich.print')
    @patch('logging.info')
    def test_image_configuration(self, mock_logging_info, mock_rich_print):
        self.config.image_configuration(region='square', size='full', quality='color')
        self.assertEqual(self.config.config['region'], 'square')
        self.assertEqual(self.config.config['size'], 'full')
        self.assertEqual(self.config.config['quality'], 'color')
        self.assertEqual(mock_logging_info.call_count, 2)
        self.assertIn(
            "Updated IIIF configuration.",
            [call[0][0] for call in mock_logging_info.call_args_list]
        )
        mock_rich_print.assert_not_called()

    @patch('rich.print')
    @patch('logging.info')
    def test_image_configuration_with_verbose(self, mock_logging_info, mock_rich_print):
        self.config.verbose = True
        self.config.image_configuration(region='square', size='full', quality='color')
        self.assertEqual(self.config.config['region'], 'square')
        self.assertEqual(self.config.config['size'], 'full')
        self.assertEqual(self.config.config['quality'], 'color')
        self.assertEqual(mock_logging_info.call_count, 2)
        self.assertIn(
            "Updated IIIF configuration.",
            [call[0][0] for call in mock_logging_info.call_args_list]
        )
        #mock_rich_print.assert_called_once_with("[blue]Updated IIIF configuration.[/]")

    @patch('rich.print')
    def test_api_mode(self, mock_rich_print):
        self.config.verbose = True
        self.config.api_mode(2.5)
        self.assertEqual(self.config.API, 2.5)
        #mock_rich_print.assert_called_once_with("\033[0;34mChanging API level to 2.5\033[0;34m")
