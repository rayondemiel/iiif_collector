import requests
import os

from .variables import DEFAULT_VERBOSE, DEFAULT_OUT_DIR
from .utils import save_json


class ManifestIIIF:
    """
        Class to manipulate IIIF manifest
    """
    out_dir = DEFAULT_OUT_DIR

    def __init__(self, url, **kwargs):
        self.id = ''
        self.json = {}
        self.images = []
        self.verbose = kwargs.get('verbose', DEFAULT_VERBOSE)
        self.load_from_url(url)

    def load_from_url(self, url: str):
        """Load a IIIF manifest from an url.
        url: str,
        """
        if self.verbose: print(' * loading manifest from url', url)
        self.json = requests.get(url).json()
        self.id = self.json.get('@id', '').replace('/', '||').rstrip('.json')

    def json_present(self):
        if not self.json:
            print(' ! please use the load_from_url(path_to_manifest) method before calling this method')
            return False
        return True

    def save_manifest(self):
        """Save self.json to disk"""
        if self.json_present():
            out_path = os.path.join(self.out_dir, 'manifests', self.id)
            save_json(out_path, self.json, verbose=self.verbose)
