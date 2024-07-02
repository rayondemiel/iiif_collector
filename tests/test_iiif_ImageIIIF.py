import os
import logging
from rich import console
import shutil
from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open
import tempfile

from iiif_collector.iiif import ImageIIIF

class TestImageIIIF(TestCase):

    def setUp(self):
        #init log
        self.temp_dir = tempfile.mkdtemp()
        logfile_path = os.path.join(self.temp_dir, "logfile_test.txt")
        logging.basicConfig(filename=logfile_path, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        # Example parameters for ImageIIIF instance
        url = "https://gallica.bnf.fr/iiif/ark:/12148/btv1b52505441p/f11/full/full/0/native.jpg"
        self.url_expected = 'https://gallica.bnf.fr/iiif/ark:/12148/btv1b52505441p/f11/square/full/90/bitonal.jpg'
        path = self.temp_dir
        kwargs = {'verbose': True}

        # Initialize ImageIIIF instance
        self.image_iiif = ImageIIIF(url, path, **kwargs)
        self.image_iiif.api_mode(2.0)
        self.image_iiif.image_configuration(region='square',
                                            size='full',
                                            rotation=90,
                                            quality='bitonal',
                                            format='jpg')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('requests.Session')
    def test_load_image_with_session(self, mock_session):
        """iiif_collector.iiif.ImageIIIF.load_image with session"""

        mock_session_instance = mock_session.return_value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = MagicMock()
        mock_session_instance.get.return_value = mock_response

        self.image_iiif.load_image(session=mock_session_instance)

        mock_session_instance.get.assert_called_once_with(self.url_expected, stream=True, allow_redirects=True)
        self.assertIsInstance(self.image_iiif.img, MagicMock)
        mock_response.reset_mock()

    @patch('requests.get')
    def test_load_image_without_session(self, mock_get):
        """iiif_collector.iiif.ImageIIIF.load_image without session"""

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = MagicMock()
        mock_get.return_value = mock_response

        self.image_iiif.load_image()

        mock_get.assert_called_once_with(self.url_expected, stream=True, allow_redirects=True)
        self.assertIsInstance(self.image_iiif.img, MagicMock)
        mock_response.reset_mock()

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    @patch('shutil.copyfileobj')
    def test_save_image(self, mock_copyfileobj, mock_makedirs, _mock_open):
        """iiif_collector.iiif.ImageIIIF.save_image"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raw = MagicMock()
        self.image_iiif.img = mock_response
        self.image_iiif.id_img = 'test_image'

        self.image_iiif.save_image()

        _mock_open.assert_called_once_with(os.path.join(self.temp_dir, 'images', 'test_image.jpg'), 'wb')
        mock_copyfileobj.assert_called_once_with(mock_response.raw, _mock_open())
        self.assertTrue(mock_response.raw.decode_content)
        mock_makedirs.assert_called_once_with(os.path.join(self.temp_dir, 'images'), exist_ok=True)

    def test_change_format(self):
        """iiif_collector.iiif.ImageIIIF.change_format"""
        filename = 'native.png'
        self.image_iiif.config['format'] = 'tif'
        new_filename = self.image_iiif.change_format(filename)  # get previous config quality
        self.assertEqual(new_filename, 'bitonal.tif')

    def test_format_url(self):
        """iiif_collector.iiif.ImageIIIF.change_format"""
        self.image_iiif.config = {'format': 'png', 'region': 'full', 'size': ',640', 'rotation': '35',
                                  'quality': 'bitonal'}
        formatted_url = self.image_iiif._format_url(self.image_iiif.url)
        expected_url = "https://gallica.bnf.fr/iiif/ark:/12148/btv1b52505441p/f11/full/,640/35/bitonal.png"
        self.assertEqual(formatted_url, expected_url)

    @patch('rich.print')
    def test_str_method(self, mock_print):
        """iiif_collector.iiif.ImageIIIF.str_method"""""
        self.image_iiif.__str__()
        """mock_print.assert_called_once_with("URL api image is : \
        https://gallica.bnf.fr/iiif/ark:/12148/btv1b52505441p/f11/full/full/0/native.jpg")"""