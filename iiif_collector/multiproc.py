import asyncio
import aiohttp
import aiofiles
import multiprocessing
import psutil
import os
from rich import print
import sys
from tqdm import tqdm

from .iiif import ImageIIIF, ManifestIIIF, ConfigIIIF
from .variables import DEFAULT_OUT_DIR
from iiif_collector.opt.utils import journal_error, randomized, make_out_dirs, url2filename
from iiif_collector.opt.decorators import time_counter, performance


class IIIFCollector(object):
    def __init__(self, path: str, **kwargs):
        """
        Class to manage asynchronous processing of a list of images using aiohttp.

        :param path: str, path of the folder where images will be saved.
        :param session: aiohttp.ClientSession, optional session to use for HTTP requests.
        :param verbose: bool, if True, enables verbose logging.
        :param delay: int, delay in seconds between retries.
        :param retry: int, number of retry attempts for failed downloads.
        :param short_filename: bool, if True, uses shortened filenames.
        """
        self.path = path
        self.session = None
        self.verbose = kwargs.get('verbose')
        self.delay = kwargs['delay']
        self.retry = kwargs['retry']
        self.short_filename = kwargs['short_filename']

    async def process_urls(self, urls: list):
        """
        Asynchronously processes a list of URLs to download images.
        :urls: list, chunk of URLs or tuples (URL, filename) to download.
        """
        # Create tasks for each URL
        # if base is manifest
        tasks = []
        for url in urls:
            if isinstance(url, tuple):
                url, filename = url
                task = ImageIIIFAsync(url,
                                      path=os.path.join(self.path, 'images'),
                                      verbose=self.verbose,
                                      short_filename=self.short_filename).load_image_async(self.session,
                                                                                           filename=filename,
                                                                                           max_retries=self.retry,
                                                                                           retry_delay=self.delay)
            else:
                task = ImageIIIFAsync(url,
                                      path=os.path.join(self.path, 'image_IIIF'),
                                      verbose=self.verbose,
                                      short_filename=self.short_filename).load_image_async(self.session,
                                                                                           max_retries=self.retry,
                                                                                           retry_delay=self.delay)
            tasks.append(task)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

    async def run_async(self, urls: list):
        """
        Runs an aiohttp session to asynchronously request and download images.
        :param urls: list, a list of URLs or tuples (URL, filename) to download.
        """
        # Create an aiohttp.ClientSession within the context of an async with statement
        # This ensures the session is properly closed
        async with aiohttp.ClientSession() as session:
            self.session = session
            await self.process_urls(urls)


class ImageIIIFAsync(ImageIIIF):
    def __init__(self, url, path, verbose=False, short_filename=False):
        super().__init__(url=url, path=path, verbose=verbose, short_filename=short_filename)

    async def load_image_async(self, session: aiohttp.ClientSession, max_retries: int, retry_delay: int, filename=None):
        """
        Function to load and download images with IIIF API parameters asynchronously.

        :param session: aiohttp.ClientSession, the session to use for the HTTP requests.
        :param filename: str, optional, the name of the image file.
        :param max_retries: int, the maximum number of retries for loading the image.
        :param retry_delay: int, the delay in seconds between retries.
        """
        try:
            url = self._format_url(self.url)
        except IndexError:
            url = self.url
            journal_error(level='ERROR', object=self.url, message="Impossible to split URL parameters IIIF with _format_url()")
        if self.verbose:
            print(f"[plum2 italic]{url}[/]")

        # Get filename
        if filename is not None and self.short_filename is True:
            self.id_img = filename
        else:
            self.id_img = url2filename(url)

        for retry_count in range(max_retries + 1):
            try:
                async with session.get(url) as response:
                    if 200 <= response.status < 400:
                        # Process the response data
                        journal_error(level="INFO", object=self.id_img, message=f"Processing image from {url}")
                        if self.verbose:
                            print(f"[blue]Processing image {self.id_img} from {url}[/]")
                        async with aiofiles.open(
                                os.path.join(self.out_dir, self.id_img + "." + self.config['format']),
                                mode='wb') as f:
                            await f.write(await response.read())
                        journal_error(level="INFO", object=self.id_img, message=f"* saving")
                        if self.verbose:
                            print(f'[cyan] * saving {self.out_dir}[/]')
                        break  # Successful response, exit the retry loop
                    else:
                        if self.verbose:
                            print(f"[orange1]Error processing URL: {url}. Status code: {response.status}[/]")
                        if retry_count < max_retries:
                            journal_error(level="WARNING", object=self.url,
                                          message=f"Retrying after a delay... code error: {response.status}")
                            if self.verbose:
                                print(f"[orange1]Retrying after a delay...[/]")
                            await asyncio.sleep(retry_delay)
                        else:
                            journal_error(level="ERROR", object=url, message=response.status,
                                          complement_info="Impossible to get image")
                            if self.verbose:
                                print(f"[red]Error processing URL: {url}. Status code: {response.status}. END[/]")
            except aiohttp.ClientError:
                journal_error(level="WARNING", object=self.url,
                              message=f"Retrying after a delay...")
                if self.verbose:
                    print(f"[red]Error processing URL: {url}. Retrying after a delay...[/]")
                if retry_count < max_retries:
                    await asyncio.sleep(retry_delay)
                else:
                    journal_error(level="ERROR", object=url, error="ClientError")
            except Exception as err:
                if self.verbose:
                    print(f"[red]Error processing URL: {url}. Exception: {err}")
                journal_error(level="ERROR", object=self.url, error=str(err))


class ParallelizeIIIF(ConfigIIIF):
    processes = []

    def __init__(self, urls: list, path: str, image: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.num_processes = self._get_cpu()
        self.urls = urls
        self.image = image
        self.out_dir = os.path.join(path, DEFAULT_OUT_DIR)
        self.retry = kwargs['retry']
        self.delay = kwargs['delay']
        if not image:
            self.out_dir = path
            self.n = kwargs.get('n')
            self.random = kwargs.get('random')

    def _process_chunk_image(self, chunk):
        """
        Asynchronously process a list of image URLs.
        :param chunk: list, chunk of all URLs (manifest or image)
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        collector = IIIFCollector(path=self.out_dir,
                                  verbose=self.verbose,
                                  delay=self.delay,
                                  retry=self.retry,
                                  short_filename=self.short_filename)
        asyncio.run(collector.run_async(chunk))
        loop.close()

    def _process_chunk_manifest(self, chunk: list):
        """
        Multiprocessing manifest IIIF and then asynchronously process for images.
        :param chunk: list, chunk of URLs manifest (API REST JSON)
        """
        for url in chunk:
            manifest = ManifestIIIF(str(url),
                                    path=self.out_dir,
                                    n=self.n,
                                    verbose=self.verbose,
                                    random=self.random,
                                    short_filename=self.short_filename)
            # make dir
            self.out_dir = manifest.out_dir
            make_out_dirs(self.out_dir)
            # config api image
            manifest.config = self.config
            journal_error(level="INFO", object=manifest.out_dir,
                          message=f"Creating directory to IIIF files succeed")
            if self.verbose:
                print("[blue]Creating directory to IIIF files[/]")
            # Get manifest, metadata and images
            manifest.save_manifest()
            manifest.save_metadata()
            urls = manifest.get_images_from_manifest()
            if self.random is True and self.n is not None:
                urls = randomized(urls, self.n)
            elif self.random is False and self.n is not None:
                urls = urls[:min(self.n, len(urls) - 1)]
            self._process_chunk_image(urls)

    @staticmethod
    def _get_cpu():
        """Determine the number of processes"""
        return max(2, multiprocessing.cpu_count() // 2)

    @time_counter
    @performance
    def run(self):
        # Variable for cpu and memory
        cpu_percent = []
        memory_usage = []

        # Determine number chunk validity cpu count
        if len(self.urls) < self.num_processes:
            self.num_processes = len(self.urls)
        # Split the URLs among processes
        url_chunks = [self.urls[i::self.num_processes] for i in range(self.num_processes)]

        # Shared counter for tracking processed URLs
        manager = multiprocessing.Manager()
        counter = manager.Value('i', 0)

        # Function to process a chunk
        def process_chunk(chunk):
            if self.image:
                self._process_chunk_image(chunk)
            else:
                self._process_chunk_manifest(chunk)
            # Update the shared counter after processing the chunk
            counter.value += len(chunk)

        with tqdm(total=len(self.urls), desc="Downloading Images", unit="%",
                  ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}\n') as pbar:
            processes = []
            for chunk in url_chunks:
                # Create a process for each chunk
                process = multiprocessing.Process(target=process_chunk, args=(chunk,))
                processes.append(process)
                process.start()

            # Measure CPU and memory usage during execution
            while any(process.is_alive() for process in processes):
                cpu_percent.append(psutil.cpu_percent())
                memory_usage.append(psutil.virtual_memory().percent)

            # Update the progress bar with the current value of the shared counter
            pbar.update(counter.value - pbar.n)
            # Flush the output to display the updated progress bar immediately
            sys.stdout.flush()

            # Wait for all processes to finish
            for process in processes:
                process.join()

        # Return the collected performance data as a tuple
        return cpu_percent, memory_usage
