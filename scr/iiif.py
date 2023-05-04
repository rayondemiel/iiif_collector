import shutil
import requests
import os
import tqdm

from .variables import DEFAULT_OUT_DIR, ImageList, MetadataList, CONFIG_FOLDER
from .utils import save_json, save_txt, randomized


class ImageIIIF(object):
    id_img = ''
    img = None
    config = {
        'region': 'full',
        'size': 'max',
        'rotation': 0,
        'quality': 'native',
        'format': 'jpg'}
    verbose = False
    API = 3.0

    def __init__(self, url, path, **kwargs):
        self.url = url
        self.out_dir = os.path.join(path, DEFAULT_OUT_DIR)
        self.verbose = kwargs.get('verbose')
        if kwargs['api']:
            self.API = kwargs['api']
        self.load_image()

    def load_image(self):
        """Load a IIIF image from a url"""
        url = self._format_url(self.url)
        if self.verbose:
            print(' * loading image from url', url)
        self.id_img = url.split('/')[-5]
        self.img = requests.get(url, stream=True, allow_redirects=True)

    def _format_url(self, url):
        """Format the url to request an image of a reasonable size"""
        # {scheme}://{server}{/prefix}/{identifier}/{region}/{size}/{rotation}/{quality}.{format}
        # scheme, server, prefix, identifier, region, size, rotation, quality = [i for i in url.split('/') if i]
        split = url.split('/')
        split[-3] = self.config['size']
        if self.config['size'] != 'full':
            split[-3] += ','
        return '/'.join(split)

    @staticmethod
    def image_configuration(**kwargs):
        """
        Configuration function to API image
        :param kwargs: config attribute key
        """
        for arg in kwargs:
            ImageIIIF.config[arg] = kwargs[arg]

        # Condition API
        if ImageIIIF.API < 3.0:
            if kwargs['size'] == "full":
                ImageIIIF.config['size'] = kwargs['size']

        if ImageIIIF.verbose:
            print("Add configuration IIIF")

    def save_image(self, filename):
        """
        save image to disk
        """
        out_path = os.path.join(self.out_dir, 'images')
        if 200 <= self.img.status_code < 400:
            with open(os.path.join(out_path, filename), 'wb') as f:
                self.img.raw.decode_content = True
                shutil.copyfileobj(self.img.raw, f)
        if self.verbose:
            print(' * saving', out_path)


class ManifestIIIF(object):
    """
        Class to manipulate IIIF manifest
    """
    # Class attributes
    id = ''
    json = {}
    images = []
    list_image_txt = 'list_image.txt'

    def __init__(self, url: str, path: str, **kwargs):
        self.url = url
        self.out_dir = os.path.join(path, DEFAULT_OUT_DIR)
        self.verbose = kwargs.get('verbose')
        self.n = kwargs.get('n')
        self.random = kwargs.get('random', False)
        self._load_from_url(url)

    def _load_from_url(self, url: str):
        """Load a IIIF manifest from an url.
        url: str, manifest's url
        """
        if self.verbose:
            print(' * loading manifest from url', url)
        self.json = requests.get(url).json()
        self.id = self.json.get('@id', '').removeprefix("https://").replace("manifest/", "").replace('/', '_').rstrip(
            '.json')
        self.title = self.get_title()

    def _json_present(self) -> bool:
        """
        To verify which the script get the manifest and save it (self.json)
        :return: Bool, true if manifest in self.json
        """
        if len(self.json) < 1:
            print(f"""Verify link or request. <ManifestIIIF._load_from_url> \n link : {self.url}""")
            return False
        return True

    def get_title(self) -> str:
        """
        Get the title of manifest
        :return: str, title of manifest
        """
        return self.json['label']

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

    def save_image(self):
        """
        To save images referenced in IIIF manifest. All or partial (self.n).
        We activate the randomizer only on a partial selection of images, otherwise not useful.
        """

        if self._json_present():
            images = self.get_images_from_manifest()
            out_path = os.path.join(self.out_dir, 'images')
            if self.random is True and self.n is not None:
                images = randomized(images, self.n)
            elif self.random is False and self.n is not None:
                images = images[:min(self.n, len(images) - 1)]
            for url, filename in tqdm.tqdm(images):
                image = ImageIIIF(url, out_path)
                image.image_configuration()
                image.save_image(filename)

    def save_list_images(self):
        """

        :return:
        """

        out_path = os.path.join(self.out_dir, 'images', self.list_image_txt)

        if os.path.isfile(out_path):
            os.remove(out_path)

        for image in self.get_images_from_manifest():
            with open(os.path.join(out_path), 'a+') as f:
                f.writelines(f"{image[0]}\n")

    def _get_metadata(self) -> MetadataList:
        """ Gets a URI, read the manifest

        :return: Dict, list of all metadata in manifest iiif
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

    def __print_path__(self, idx: str) -> str:
        """
        Print complete path of file.
        :idx: str, name of directory. Need to be configurate in CONFIG_FOLDER.
        :return: str, file path's
        """
        if idx in CONFIG_FOLDER:
            path = os.path.join(self.out_dir, idx, self.list_image_txt)
            if os.path.isfile(path):
                return path
            else:
                print(f"Error! File {str(self.list_image_txt)} doesn't exists")
        else:
            print("<ManifestIIIF.__print_path> error config folder. Verify it.")
