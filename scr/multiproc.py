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
from scr.opt.utils import journal_error, randomized, make_out_dirs
from scr.opt.decorators import time_counter, performance


class IIIFCollector(object):

    def __init__(self, path, **kwargs):
        self.path = path
        self.session = None
        self.verbose = kwargs.get('verbose', False)

    async def process_urls(self, urls: list):
        """
        async process urls to make task to download list of images
        """
        # Create tasks for each URL
        # if base is manifest
        if isinstance(urls[0], tuple):
            tasks = [ImageIIIFAsync(url, path=os.path.join(self.path, 'images')).load_image_async(self.session, filename=filename) for
                     url, filename in urls]
        # if directely image
        else:
            tasks = [ImageIIIFAsync(url, path=os.path.join(self.path, 'image_IIIF')).load_image_async(self.session) for url in urls]
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
    def __init__(self, url, path, verbose=False):
        super().__init__(url=url, path=path, verbose=verbose)

    async def load_image_async(self, session, filename=None):
        """
        Function to load and download images with IIIF API parameters
        :session:
        :filename: None or str, name of image file
        """
        url = self._format_url(self.url)
        if self.verbose:
            print(url)
        # get filename
        if filename is None:
            self.id_img = self.__get_id__(url.split('/')[-5])
        else:
            self.id_img = filename
        async with session.get(url) as response:
            try:
                self.img = response
                # Process the response data asynchronously
                if 200 <= self.img.status < 400:
                    if ImageIIIF.verbose:
                        print(f"Succesing request image {str(self.id_img)} to {url}")
                    # Download image
                    async with aiofiles.open(os.path.join(self.out_dir, self.id_img + "." + self.config['format']), mode='wb') as f:
                        await f.write(await response.read())
                    if self.verbose:
                        print(' * saving', self.out_dir)
                else:
                    print(f"error request, {url}, {self.img.status_code}")
                    journal_error(self.out_dir, url=url, error=self.img.status_code)
                    pass
            except Exception as err:
                print(err)


class ParallelizeIIIF(ConfigIIIF):
    processes = []

    def __init__(self, urls, path, image=False, **kwargs):
        super().__init__(**kwargs)
        self.num_processes = self._get_cpu()
        self.urls = urls
        self.image = image
        self.out_dir = os.path.join(path, DEFAULT_OUT_DIR)
        if image is False:
            self.out_dir = path
            self.n = kwargs.get('n')
            self.random = kwargs.get('random', False)

    def _process_chunk_image(self, chunk):
        """
        Async process list of image urls
        :chunck: list, chunk of all urls (manifest or image)
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        collector = IIIFCollector(path=self.out_dir, verbose=self.verbose)
        asyncio.run(collector.run_async(chunk))
        loop.close()

    def _process_chunk_manifest(self, chunk):
        """
        Multiprocessing manifest IIIF and then async process for images
        :chunk: chunk of urls manifest (API REST JSON)
        """
        for url in chunk:
            manifest = ManifestIIIF(str(url), path=self.out_dir, n=self.n, verbose=self.verbose, random=self.random)
            self.out_dir = manifest.out_dir
            make_out_dirs(self.out_dir)
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

    def _get_cpu(self):
        """Determine the number of processes"""
        return max(2, multiprocessing.cpu_count() // 2)

    @time_counter
    @performance
    def run(self):
        # Variable for cpu and memory
        cpu_percent = []
        memory_usage = []

        # Determine number chunk validity cpu count
        if len(self.urls) > self.num_processes:
            self.num_processes = len(self.urls)
        # Split the URLs among processes
        url_chunks = [self.urls[i::self.num_processes] for i in range(self.num_processes)]
        with tqdm(total=len(url_chunks), desc="Downloading Images", unit="%",
                  ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            for chunk in url_chunks:
                # Create a process for each chunk
                if self.image:
                    process = multiprocessing.Process(target=self._process_chunk_image, args=(chunk,))
                else:
                    process = multiprocessing.Process(target=self._process_chunk_manifest, args=(chunk,))
                self.processes.append(process)
                process.start()

                # Measure CPU and memory usage during execution
                while any(process.is_alive() for process in self.processes):
                    cpu_percent.append(psutil.cpu_percent())
                    memory_usage.append(psutil.virtual_memory().percent)

            # Wait for all processes to finish
            for process in self.processes:
                process.join()
                pbar.update(1)
                sys.stdout.flush()

        # Return the collected performance data as a tuple
        return cpu_percent, memory_usage
