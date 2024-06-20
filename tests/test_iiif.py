import os
import logging
from rich import print as rich_print
from rich import console
from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open
import tempfile

from iiif_collector.iiif import ConfigIIIF, ImageIIIF


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


class TestImageIIIF(TestCase):

    def setUp(self):
        #init log
        self.temp_dir = tempfile.mkdtemp()
        logfile_path = os.path.join(self.temp_dir, "logfile_test.txt")
        logging.basicConfig(filename=logfile_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        # Example parameters for ImageIIIF instance
        url = "https://gallica.bnf.fr/iiif/ark:/12148/btv1b52505441p/f11/full/full/0/native.jpg"
        path = "/tmp"
        kwargs = {'verbose': True}

        # Initialize ImageIIIF instance
        self.image_iiif = ImageIIIF(url, path, **kwargs)
        self.image_iiif.api_mode(2.0)

    @patch('requests.Session')
    def test_load_image_with_session(self, mock_session):
        # Initialize mock objects
        mock_session_instance = mock_session.return_value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = MagicMock()
        mock_session_instance.get.return_value = mock_response

        # Test loading an image with session
        self.image_iiif.load_image(session=mock_session_instance)

        # Assertions
        mock_session_instance.get.assert_called_once_with(self.image_iiif.url, stream=True, allow_redirects=True)
        self.assertIsInstance(self.image_iiif.img, MagicMock)

    @patch('requests.Session')
    def test_load_image_without_session(self, mock_session):
        # Initialize mock objects
        mock_session_instance = mock_session.return_value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = MagicMock()
        mock_session_instance.get.return_value = mock_response

        # Test loading an image without session
        self.image_iiif.load_image()

        # Assertions
        mock_session_instance.get.assert_not_called()  # Since no session was passed, should not be called
        self.assertIsInstance(self.image_iiif.img, MagicMock)

    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_image(self, _mock_open, mock_makedirs):
        # Set up mock image data and configuration
        mock_response = MagicMock()
        mock_response.raw = MagicMock()
        self.image_iiif.img = mock_response
        self.image_iiif.config = {'format': 'jpg', 'region': 'full', 'size': 'full', 'rotation': '0'}
        self.image_iiif.id_img = 'test_image'

        # Test saving an image
        self.image_iiif.save_image()

        # Assertions
        _mock_open.assert_called_once_with('/tmp/images/test_image.jpg', 'wb')
        self.assertTrue(mock_response.raw.decode_content)

    def test_change_format(self):
        # Test changing image format
        filename = 'image.png'
        self.image_iiif.config = {'format': 'jpg'}
        new_filename = self.image_iiif.change_format(filename)
        self.assertEqual(new_filename, 'image.jpg')

    def test_format_url(self):
        # Test formatting the URL
        self.image_iiif.config = {'format': 'png', 'region': 'full', 'size': ',640', 'rotation': '35',
                                  'quality': 'bitonal'}
        formatted_url = self.image_iiif._format_url(self.image_iiif.url)
        expected_url = "https://gallica.bnf.fr/iiif/ark:/12148/btv1b52505441p/f11/full/,640/35/bitonal.png"
        self.assertEqual(formatted_url, expected_url)

    @patch('rich.print')
    def test_str_method(self, mock_print):
        # Test __str__ method
        self.image_iiif.__str__()
        mock_print.assert_called_once_with("URL api image is : \
        https://gallica.bnf.fr/iiif/ark:/12148/btv1b52505441p/f11/full/full/0/native.jpg")

    def test_log_error(self):
        # Test _log_error method
        url = "http://example.com/iiif-image"
        error = "Error message"
        self.image_iiif._log_error(url, error)

        # Read the log file and assert that the error message is logged
        with open(os.path.join(self.temp_dir, "logfile_test.txt"), 'r') as f:
            logged_content = f.read()
            self.assertIn(f"ERROR - {url} - {error}", logged_content)

