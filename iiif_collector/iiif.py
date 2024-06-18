import shutil
import requests
import os
import tqdm
import re

from .variables import DEFAULT_OUT_DIR, ImageList, MetadataList, CONFIG_FOLDER, OUTPUT_LIST_TXT
from iiif_collector.opt.utils import save_json, save_txt, randomized, journal_error, suppress_char, url2filename


class ConfigIIIF(object):
    verbose = False
    config = {
        'region': 'full',
        'size': 'max',
        'rotation': 0,
        'quality': 'native',
        'format': 'default'}
    API = 3.0

    def __init__(self, **kwargs):
        self.verbose = kwargs.get('verbose', False)
        if 'short_filename' in kwargs:
            self.short_filename = kwargs['short_filename']
        else:
            self.short_filename = True

    def __config__(self):
        print(f"Api level is {str(self.API)}. \n"
              f"Configuration is {str(self.config)}")

    @staticmethod
    def __get_id__(name):
        """
        Get and clean file name
        :param name: str, filename identifier on API image
        :return: txt cleaned
        """
        extension = re.compile(r"\.\w{3,4}$")
        return re.sub(extension, "", name)

    @classmethod
    def image_configuration(cls, **kwargs):
        """
        Configuration function to API image
        :param kwargs: config attribute key
        """
        for key, value in kwargs.items():
            cls.config[key] = value

        # Adjust configuration based on API level
        if cls.API < 3.0 and cls.config['size'] == "max":
            cls.config['size'] = "full"

        if cls.verbose:
            print("Updated IIIF configuration.")

    @classmethod
    def api_mode(cls, level: float):
        """
        change api level. Ex: 3.0
        :param level: decimal
        :return:
        """
        cls.API = level
        if cls.verbose and cls.API != 3.0:
            print(f"Changing API level to {str(level)}")


class ImageIIIF(ConfigIIIF):
    id_img = ''
    img = None

    def __init__(self, url, path, **kwargs):
        """
        Class treating an image API IIIF with parameters.

        :param url: str, URI link's of image
        :param path: directory to save datas and metadatas
        :param kwargs: verbose
        """
        super().__init__(**kwargs)
        self.url = url
        self.out_dir = path

    def __str__(self):
        print(f"URL api image is : {self.url}")

    def load_image(self, session=None, filename=None):
        """Load a IIIF image from a url"""
        url = self._format_url(self.url)
        if self.verbose:
            print(url)
        # get filename
        if filename is not None and self.short_filename is True:
            self.id_img = filename
        else:
            self.id_img = url2filename(url)
        try:
            #Check session
            if session is None:
                self.img = requests.get(url, stream=True, allow_redirects=True)
            else:
                assert isinstance(session, requests.Session), "Session need to be instanced"
                self.img = session.get(url, stream=True, allow_redirects=True)
            # Check status request
            if 200 <= self.img.status_code < 400:
                if self.verbose:
                    print(f"Succesing request image {str(self.id_img)} to {url}")
            else:
                print(f"error request, {url}, {self.img.status_code}")
                self._log_error(url, self.img.status_code)
                pass
        except requests.exceptions.RequestException as err:
            print(err)

    def _format_url(self, url):
        """Format the url to request an image of a reasonable size"""
        # {scheme}://{server}{/prefix}/{identifier}/{region}/{size}/{rotation}/{quality}.{format}
        # scheme, server, prefix, identifier, region, size, rotation, quality = [i for i in url.split('/') if i]
        url_parts = url.split('/')
        if self.verbose:
            print("configuration parameters API image")
        url_parts[-4] = str(self.config['region'])
        url_parts[-3] = str(self.config['size'])
        url_parts[-2] = str(self.config['rotation'])
        url_parts[-1] = self.change_format(url_parts[-1])
        if self.verbose:
            print("Finish configuration parameters API image")
        return '/'.join(url_parts)

    def save_image(self):
        """
        save image to disk
        """
        out_path = os.path.join(self.out_dir, 'images')
        os.makedirs(out_path, exist_ok=True)
        try:
            if 200 <= self.img.status_code < 400:
                with open(os.path.join(out_path, self.id_img + "." + self.config['format']), 'wb') as f:
                    self.img.raw.decode_content = True
                    shutil.copyfileobj(self.img.raw, f)
            if self.verbose:
                print(' * saving', out_path)
        except (OSError, Exception) as err:
            self._log_error(os.path.join(out_path, self.id_img + "." + self.config['format']), err)

    def change_format(self, filename: str):
        """
        Change format image and transform last element in list
        :param filename: Get ultimate element in list split url
        :return:
        """
        parts = filename.split(".")
        parts[-1] = self.config['format'] if self.config['format'] != 'default' else parts[-1]
        return '.'.join(parts)

    def _log_error(self, url: str, error: int or str):
        """Log errors encountered during image loading"""
        journal_error(self.out_dir, url=url, error=error)


class ManifestIIIF(ConfigIIIF):
    """
        Class to manipulate IIIF manifest
    """
    # Class attributes
    id = ''
    json = {}
    images = []
    list_image_txt = OUTPUT_LIST_TXT

    def __init__(self, url: str, path: str, session=None, **kwargs):
        """
        Class treating a manifest IIIF

        :param url: str, URI of a manifest
        :param path: directory to save datas and metadatas
        :param session: Session class in requests lib for build pool connection.
        :param kwargs: verbose : bool
                        n : int, Desired number of images to download
                        random: bool, to randomize image. Best to prepare htr corpus. Default in False
        """
        super().__init__(**kwargs)
        self.url = url
        self.session = session
        self.n = kwargs.get('n')
        self.random = kwargs.get('random', False)
        self._load_from_url(url)
        self.default_title_value = self._get_title_value()
        self.out_dir = os.path.join(path, DEFAULT_OUT_DIR, self.default_title_value)
        os.makedirs(self.out_dir, exist_ok=True)

    def __str__(self):
        print(f"URI manifest is : {self.url}")

    def _load_from_url(self, url: str):
        """Load a IIIF manifest from an url.
        url: str, manifest's url
        """
        if self.verbose:
            print(' * loading manifest from url', url)
        if self.session is not None:
            assert isinstance(self.session, requests.Session), "Session need to be instanced"
            self.json = self.session.get(url).json()
        else:
            self.json = requests.get(url).json()
        self.id = self._clean_id(self.json.get('@id', ''))  # CHANGED: Moved ID cleaning to a separate method
        self.title = self._get_title()

    def _clean_id(self, id_value: str) -> str:
        """Clean the ID value from the manifest."""
        return id_value.removeprefix("https://").replace("manifest/", "").replace('/', '_').rstrip('.json')

    def _get_title_value(self) -> str:
        """Extract and clean the title value from the manifest."""
        title = self.json.get('label', '')
        if isinstance(title, dict):
            title_value = title.get('en', next(iter(title.values())))
        else:
            title_value = title
        return title_value[0] if isinstance(title_value, list) else title_value

    def _json_present(self) -> bool:
        """
        To verify which the script get the manifest and save it (self.json)
        :return: Bool, true if manifest in self.json
        """
        if len(self.json) < 1:
            print(f"""Verify link or request. <ManifestIIIF._load_from_url> \n link : {self.url}""")
            return False
        return True

    def _get_title(self) -> str:
        """
        Get the title of manifest
        :return: str, title of manifest
        """
        return suppress_char(self.json['label'])

    def save_manifest(self):
        """Save self.json to disk"""
        if self._json_present():
            out_path = os.path.join(self.out_dir, 'manifests')
            save_json(iiif_json=self.json, file_path=out_path)
            if self.verbose:
                print('Finished saving manifests!')

    def get_images_from_manifest(self) -> ImageList:
        """ Gets a URI, read the manifest

        :param self: URI of a manifest
        :return: List of images link
        """
        return list([
            (canvas['images'][0]['resource']['@id'], canvas['@id'].split("/")[-1])
            for canvas in self.json['sequences'][0]['canvases']
        ])

    def save_image(self):
        """
        To save images referenced in IIIF manifest. All or partial (self.n).
        We activate the randomizer only on a partial selection of images, otherwise not useful.
        """

        if self._json_present():
            images = self.get_images_from_manifest()
            if self.random and self.n is not None:
                images = randomized(images, self.n)
            elif self.n is not None:
                images = zip(images, range(min(self.n, len(images) - 1)))

            with tqdm.tqdm(total=len(list(images)), desc='Saving images', unit='images') as pbar:
                for url, filename in images:
                    image = ImageIIIF(url, self.out_dir, short_filename=self.short_filename)
                    image.config = self.config
                    if self.session is not None:
                        image.load_image(filename=filename, session=self.session)
                    else:
                        image.load_image(filename=filename)
                    image.save_image()
                    pbar.update(1)

            if self.verbose:
                print('Finished saving images!')

    def save_list_images(self):
        """Save a list of images to disk."""
        out_path = os.path.join(self.out_dir, 'images', self.list_image_txt)
        with open(out_path, 'w') as f:
            for image in self.get_images_from_manifest():
                f.write(f"{image[0]}\n")

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
                print('Finished saving metadata!')

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
