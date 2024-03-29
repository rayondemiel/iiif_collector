import asyncio
import aiohttp
import aiofiles
import multiprocessing
import psutil
import os
import sys
from tqdm import tqdm

from .iiif import ImageIIIF, ManifestIIIF, ConfigIIIF
from .variables import DEFAULT_OUT_DIR
from scr.opt.utils import journal_error, randomized, make_out_dirs, url2filename
from scr.opt.decorators import time_counter, performance


class IIIFCollector(object):
    def __init__(self, path: str, **kwargs):
        """
        Class to manage async process of list of image with aiohttp

        :path: str, path of folder
        :session: to instantiate the ClientSession class
        :verbose: bool, verbose
        :delay: int, Delay parameters to transfert in ImageIIIFAsync
        :retry: int, Retry parameters to transfert in ImageIIIFAsync
        """
        self.path = path
        self.session = None
        self.verbose = kwargs.get('verbose')
        self.delay = kwargs['delay']
        self.retry = kwargs['retry']
        self.short_filename = kwargs['short_filename']

    async def process_urls(self, urls: list):
        """
        async process urls to make task to download list of images
        :urls: list, chunk of urls
        """
        # Create tasks for each URL
        # if base is manifest
        if isinstance(urls[0], tuple):
            tasks = [ImageIIIFAsync(url,
                                    path=os.path.join(self.path, 'images'),
                                    verbose=self.verbose,
                                    short_filename=self.short_filename).load_image_async(self.session,
                                                                           filename=filename,
                                                                           max_retries=self.retry,
                                                                           retry_delay=self.delay)
                     for url, filename in urls]
        # if directely image
        else:
            tasks = [ImageIIIFAsync(url,
                                    path=os.path.join(self.path, 'image_IIIF'),
                                    verbose=self.verbose,
                                    short_filename=self.short_filename).load_image_async(
                                                                            self.session,
                                                                            max_retries=self.retry,
                                                                            retry_delay=self.delay)
                for url in urls]
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

    async def run_async(self, urls):
        """
        run aoihttp session to async request
        """
        # Create an aiohttp.ClientSession within the context of an async with statement
        # This ensures the session is properly closed
        async with aiohttp.ClientSession() as session:
            self.session = session
            await self.process_urls(urls)


class ImageIIIFAsync(ImageIIIF):
    def __init__(self, url, path, verbose=False, short_filename=False):
        super().__init__(url=url, path=path, verbose=verbose, short_filename=short_filename)

    async def load_image_async(self, session, max_retries: int, retry_delay: int, filename=None):
        """
        Function to load and download images with IIIF API parameters
        :session: Session aiohttp
        :filename: None or str, name of image file
        :delay: int, Delay between request to load image of a same image
        :retry: int, Number of retry request's to load image before error
        """
        url = self._format_url(self.url)
        if self.verbose:
            print(url)
        # get filename
        if filename is not None and self.short_filename is True:
            self.id_img = filename
        else:
            self.id_img = url2filename(url)
        for retry_count in range(max_retries + 1):
            try:
                async with session.get(url) as response:
                    if 200 <= response.status < 400:
                        # Process the response data
                        if self.verbose:
                            print(f"Processing image {self.id_img} from {url}")
                        async with aiofiles.open(
                                os.path.join(self.out_dir, self.id_img + "." + self.config['format']),
                                mode='wb') as f:
                            await f.write(await response.read())
                        if self.verbose:
                            print(' * saving', self.out_dir)
                        break  # Successful response, exit the retry loop
                    else:
                        print(f"Error processing URL: {url}. Status code: {response.status}")
                        if retry_count < max_retries:
                            print(f"Retrying after a delay...")
                            await asyncio.sleep(retry_delay)
                        else:
                            journal_error(self.out_dir, url=url, error=response.status)
            except aiohttp.ClientError:
                if self.verbose:
                    print(f"Error processing URL: {url}. Retrying after a delay...")
                if retry_count < max_retries:
                    await asyncio.sleep(retry_delay)
                else:
                    journal_error(self.out_dir, url=url, error="ClientError")
            except Exception as err:
                print(f"Error processing URL: {url}. Exception: {err}")
                journal_error(self.out_dir, url=url, error=str(err))


class ParallelizeIIIF(ConfigIIIF):
    processes = []

    def __init__(self, urls, path, image=False, **kwargs):
        super().__init__(**kwargs)
        self.num_processes = self._get_cpu()
        self.urls = urls
        self.image = image
        self.out_dir = os.path.join(path, DEFAULT_OUT_DIR)
        self.retry = kwargs['retry']
        self.delay = kwargs['delay']
        if image is False:
            self.out_dir = path
            self.n = kwargs.get('n')
            self.random = kwargs.get('random')

    def _process_chunk_image(self, chunk):
        """
        Async process list of image urls
        :chunck: list, chunk of all urls (manifest or image)
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        collector = IIIFCollector(path=self.out_dir,
                                  verbose=self.verbose,
                                  delay= self.delay,
                                  retry= self.retry,
                                  short_filename=self.short_filename)
        asyncio.run(collector.run_async(chunk))
        loop.close()

    def _process_chunk_manifest(self, chunk):
        """
        Multiprocessing manifest IIIF and then async process for images
        :chunk: chunk of urls manifest (API REST JSON)
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
            if self.verbose:
                print("Creating directory to IIIF files")
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
