import requests
import os

from .variables import DEFAULT_OUT_DIR, ImageList, MetadataList
from .utils import save_json, save_txt


class ManifestIIIF:
    """
        Class to manipulate IIIF manifest
    """
    # Class attributes
    id = ''
    json = {}
    images = []

    def __init__(self, url: str, path: str, **kwargs):
        self.out_dir = os.path.join(path, DEFAULT_OUT_DIR)
        self.n = kwargs.get('n')
        self.verbose = kwargs.get('verbose')
        self._load_from_url(url)

    def _load_from_url(self, url: str):
        """Load a IIIF manifest from an url.
        url: str, manifest's url
        """
        if self.verbose: print(' * loading manifest from url', url)
        self.json = requests.get(url).json()
        self.id = self.json.get('@id', '').removeprefix("https://").replace("manifest/", "").replace('/', '_').rstrip(
            '.json')

    def _json_present(self):
        if not self.json:
            print(' ! please use the load_from_url(path_to_manifest) method before calling this method')
            return False
        return True

    def save_manifest(self):
        """Save self.json to disk"""
        if self._json_present():
            out_path = os.path.join(self.out_dir, 'manifests')
            save_json(iiif_json=self.json, file_path=out_path)
        if self.verbose:
            print('Finish to save manifests !')

    def get_images_from_manifest(self) -> ImageList:
        """ Gets a URI, read the manifest

        :param self: URI of a manifest
        :return: List of images link
        """

        return list([
            (canvas['images'][0]['resource']['@id'], canvas['@id'].split("/")[-1] + ".jpeg")
            for canvas in self.json['sequences'][0]['canvases']
        ])



    def _get_metadata(self) -> MetadataList:
        """ Gets a URI, read the manifest

        :return: Dict, list of all metadatas in manifest iiif
        """
        return list([(mtda['label'], mtda['value']) for mtda in self.json['metadata']])

    def save_metadata(self):
        """Save metadata to disk"""
        if self._json_present():
            out_path = os.path.join(self.out_dir, 'metadata')
            mtda = self._get_metadata()
            save_txt(list_mtda=mtda, file_path=out_path)
        if self.verbose:
            print('Finish to save metadata !')
