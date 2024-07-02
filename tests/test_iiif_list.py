import os
from unittest import TestCase
from tempfile import NamedTemporaryFile

from iiif_collector.iiif_list import ListIIIF


class TestListIIIF(TestCase):
    def setUp(self):
        # Setup code for creating test files
        self.csv_content = """filename,manifest_url,notes
file1,http://example.com/iiif/1,This is the first manifest
file2,http://example.com/iiif/2,This is the second manifest
file3,http://example.com/iiif/3,This is the third manifest
"""
        self.txt_content = """http://example.com/iiif/4
http://example.com/iiif/5
http://example.com/iiif/6"""

        with NamedTemporaryFile(delete=False, mode='w', suffix='.csv') as csv_file:
            csv_file.write(self.csv_content)
            self.csv_file = csv_file.name

        with NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as txt_file:
            txt_file.write(self.txt_content)
            self.txt_file = txt_file.name

    def tearDown(self):
        os.remove(self.csv_file)
        os.remove(self.txt_file)

    def test_initialization(self):
        """iiif_collector.iiif_list.ListIIIF"""
        list_iiif = ListIIIF()
        self.assertFalse(list_iiif.verbose)
        self.assertFalse(list_iiif.case)

    def test_length(self):
        """iiif_collector.iiif_list.ListIIIF.__len__"""
        list_iiif = ListIIIF()
        self.assertEqual(len(list_iiif), 0)

    def test_read_csv(self):
        """iiif_collector.iiif_list.ListIIIF.read_csv"""
        list_iiif = ListIIIF()
        list_iiif.read_csv(self.csv_file, 'manifest_url')
        self.assertEqual(len(list_iiif), 3)
        self.assertEqual(list_iiif.url_iiif, [
            'http://example.com/iiif/1',
            'http://example.com/iiif/2',
            'http://example.com/iiif/3'
        ])

    def test_read_txt(self):
        """iiif_collector.iiif_list.ListIIIF.read_txt"""
        list_iiif = ListIIIF()
        list_iiif.read_txt(self.txt_file)
        self.assertEqual(len(list_iiif), 3)
        self.assertEqual(list_iiif.url_iiif, [
            'http://example.com/iiif/4',
            'http://example.com/iiif/5',
            'http://example.com/iiif/6'
        ])

    def test_get_next(self):
        """iiif_collector.iiif_list.ListIIIF.__get_next__"""
        list_iiif = ListIIIF()
        list_iiif.read_txt(self.txt_file)
        self.assertEqual(list_iiif.__get_next__(), 'http://example.com/iiif/4')

    def test_case_insensitive_csv(self):
        """iiif_collector.iiif_list.ListIIIF.case"""
        list_iiif = ListIIIF(case_insensitive=True)
        list_iiif.read_csv(self.csv_file, 'MANIFEST_URL')
        self.assertEqual(len(list_iiif), 3)
        self.assertEqual(list_iiif.url_iiif, [
            'http://example.com/iiif/1',
            'http://example.com/iiif/2',
            'http://example.com/iiif/3'
        ])

    def test_key_error_for_invalid_column(self):
        """iiif_collector.iiif_list.ListIIIF"""
        list_iiif = ListIIIF()
        with self.assertRaises(KeyError):
            list_iiif.read_csv(self.csv_file, 'invalid_column')
