import os
import re
import requests
from rich.console import Group
from rich.live import Live
from rich import print
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn, TransferSpeedColumn, DownloadColumn, \
    TimeElapsedColumn
import shutil
import time

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
        print(f"[blue]Api level is [pink]{str(self.API)}[/]. \n[/]"
              f"[blue]Configuration is [pink]{str(self.config)}[/][/]")

    @staticmethod
    def __get_id__(name):
        """
        Get and clean file name
        :param name: str, filename identifier on API image
        :return: txt cleaned
        """
        extension = re.compile(r"\.\w{3,4}$")
        return re.sub(extension, "", name)

    def image_configuration(self, **kwargs):
        """
        Configuration function to API image
        :param kwargs: config attribute key
        """
        for key, value in kwargs.items():
            self.config[key] = value

        # Adjust configuration based on API level
        if self.API < 3.0 and self.config['size'] == "max":
            self.config['size'] = "full"

        journal_error(level='INFO', object='CONFIG IIIF', message=str(self.config),
                      complement_info="Updated IIIF configuration.")
        if self.verbose:
            print("[blue]Updated IIIF configuration.[/]")

    def api_mode(self, level: float):
        """
        change api level. Ex: 3.0
        :param level: decimal
        :return:
        """
        self.API = level
        if self.verbose and self.API != 3.0:
            print(f"[blue]Changing API level to {str(level)}[/]")


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

    def load_image(self, session=None, filename=None, download_progress=None, task_id=None):
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
                self.img = session.get(url, stream=True, allow_redirects=True)
            # Check status request
            if 200 <= self.img.status_code < 400:
                journal_error(level='INFO', object=url, message=str(self.img.status_code),
                              complement_info=str(f"Succesing request image {str(self.id_img)}"))
                if self.verbose:
                    print(f"[blue]Succesing request image {str(self.id_img)} to {url}[/]")
            else:
                print(f"[red]error request, {url}, {self.img.status_code}[/]")
                self._log_error(url, self.img.status_code)
                pass
        except requests.exceptions.RequestException as err:
            self._log_error(url, err)
            print(err)

    def _format_url(self, url):
        """Format the url to request an image of a reasonable size"""
        # {scheme}://{server}{/prefix}/{identifier}/{region}/{size}/{rotation}/{quality}.{format}
        # scheme, server, prefix, identifier, region, size, rotation, quality = [i for i in url.split('/') if i]
        url_parts = url.split('/')
        url_parts[-4] = str(self.config['region'])
        url_parts[-3] = str(self.config['size'])
        url_parts[-2] = str(self.config['rotation'])
        url_parts[-1] = self.change_format(url_parts[-1])
        if self.verbose:
            print("[blue]Finish configuration parameters API image[/]")
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
                journal_error(level='INFO', object=self.id_img + "." + self.config['format'], message=str('* saving'))
            if self.verbose:
                print(f"[green] * saving : {out_path}[/]")
        except (OSError, Exception) as err:
            self._log_error(os.path.join(out_path, self.id_img + "." + self.config['format']), err)

    def change_format(self, filename: str):
        """
        Change format image and transform last element in list
        :param filename: Get ultimate element in list split url
        :return:
        """
        parts = filename.split(".")
        parts[0] = self.config['quality']
        parts[-1] = self.config['format'] if self.config['format'] != 'default' else parts[-1]
        return '.'.join(parts)

    @staticmethod
    def _log_error(url: str, error: int or str):
        """Log errors encountered during image loading"""
        journal_error(level='ERROR', object=url, message=str(error))


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
        print(f"[blue]URI manifest is : {self.url}[/]")

    def _load_from_url(self, url: str):
        """Load a IIIF manifest from an url.
        url: str, manifest's url
        """
        if self.verbose:
            print(f'[blue]* loading manifest from url {url}[/]')
        try:
            if self.session is not None:
                self.json = self.session.get(url).json()
            else:
                self.json = requests.get(url).json()
            journal_error(level='INFO', object=url, message=str('Request manifest succeed'))
        except Exception as err:
            journal_error(level='ERROR', object=url, message=str(err))
        self.id = self._clean_id(self.json.get('@id', ''))
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
            journal_error(level='WARNING', object=self.url,
                          message=str("Verify link or request. <ManifestIIIF._load_from_url>"))
            print(f"""[red]Verify link or request. [orange]<ManifestIIIF._load_from_url>[/] \n link : {self.url}[/]""")
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
                journal_error(level='INFO', object=self.url, message=str("Manifest saved"))
                print('[green]Finished saving manifests![/]')

    def get_images_from_manifest(self) -> ImageList:
        """ Gets a URI, read the manifest

        :param self: URI of a manifest
        :return: List of images link
        """
        return list([
            (canvas['images'][0]['resource']['@id'], canvas['@id'].split("/")[-1])
            for canvas in self.json['sequences'][0]['canvases']
        ])

    def save_images(self):
        """
        To save images referenced in IIIF manifest. All or partial (self.n).
        We activate the randomizer only on a partial selection of images, otherwise not useful.
        """
        download_progress = Progress(
            TextColumn('[bold yellow]Downloading image {task.fields[filename]}'),
            BarColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        )
        overall_progress = Progress(
            TextColumn('{task.description}'),
            TextColumn('{task.fields[images_per_second]:>5.2f} images/s'),
            TimeElapsedColumn(),
            BarColumn(),
            TextColumn('[pink]{task.percentage:>3.0f}%'),
            TextColumn('[cyan]{task.completed}/{task.total} images'))
        group = Group(
            overall_progress,
            download_progress,
        )

        if self._json_present():
            images = self.get_images_from_manifest()
            if self.random and self.n is not None:
                images = randomized(images, self.n)
            elif self.n is not None:
                images = zip(images, range(min(self.n, len(images) - 1)))

            with Live(group, refresh_per_second=10):
                task1 = overall_progress.add_task("[cyan]Saving images from manifest IIIF",
                                                  total=len(images),
                                                  images_per_second=0.0)
                start_time_total = time.time()
                for url, filename in images:
                    image = ImageIIIF(url, self.out_dir, short_filename=self.short_filename)
                    image.config = self.config
                    start_time = time.time()
                    if self.session is not None:
                        image.load_image(filename=filename, session=self.session)
                    else:
                        image.load_image(filename=filename)

                    total_size = int(image.img.headers.get('Content-Length', 0))
                    task2 = download_progress.add_task(
                        "[cyan]Downloading image",
                        total=total_size,
                        filename=filename
                    )

                    for chunk in image.img.iter_content(chunk_size=8192):
                        if chunk:
                            download_progress.update(task2, advance=len(chunk))

                    image.save_image()
                    overall_progress.update(task1, advance=1)

                    # Calculate download speed in MB/s
                    elapsed_time = time.time() - start_time
                    download_speed = total_size / elapsed_time if elapsed_time > 0 else 0
                    download_speed_mb = download_speed / (1024 * 1024)

                    # Update the second progress bar with download speed
                    download_progress.update(task2, completed=total_size, refresh=True)
                    download_progress.update(task2, description=f"[cyan]Download speed: {download_speed_mb:.2f} MB/s")
                    download_progress.stop_task(task2)
                    download_progress.update(task2, visible=False)

                    # Calculate images per second for the first progress bar
                    elapsed_time_total = time.time() - start_time_total
                    images_per_second = overall_progress.tasks[
                                            0].completed / elapsed_time_total if elapsed_time_total > 0 else 0
                    overall_progress.update(task1, images_per_second=images_per_second)
                    """elapsed_time_total = time.time() - start_time_total
                    images_per_second = overall_progress.tasks[
                                            0].completed / elapsed_time_total if elapsed_time_total > 0 else 0
                    overall_progress.update(task1,
                                    description=f"[cyan]Saving images from manifest IIIF ({images_per_second:.2f} images/s)")"""

            journal_error(level='INFO', object=url, message=str("Image saved"))
            if self.verbose:
                print('[green]Finished saving images![/]')

    def save_list_images(self):
        """Save a list of images to disk."""
        out_path = os.path.join(self.out_dir, 'images', self.list_image_txt)
        with open(out_path, 'w') as f:
            for image in self.get_images_from_manifest():
                f.write(f"{image[0]}\n")
        journal_error(level='INFO', object=self.url, message=str("List of images in manifeste saved"))

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
                print('[green]Finished saving metadata![/]')

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
                journal_error(level='ERROR', object=self.url, message=str("Path manifest IIIF not found"))
                print(f"Error! File {str(self.list_image_txt)} doesn't exists")
        else:
            print("<ManifestIIIF.__print_path> error config folder. Verify it.")
