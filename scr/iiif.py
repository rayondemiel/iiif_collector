import requests



class Manifest:
    """
    Class to manipulate IIIF manifest
    """

    def __init__(self, url, **kwargs):
        self.id = ''
        self.json = {}
        self.images = []
        self.verbose = kwargs.get('verbose', default_verbose)
        if kwargs.get('url', False):
            self.load_from_url(kwargs.get('url'))

    def load_from_url(self, url):
        """Load a IIIF manifest from a url"""
        if self.verbose: print(' * loading manifest from url', url)
        self.json = requests.get(url).json()
        self.id = self.json.get('@id', '').replace('/', '||').rstrip('.json')
