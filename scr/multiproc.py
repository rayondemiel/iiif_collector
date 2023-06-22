import asyncio
import aiohttp
import multiprocessing
import time
import psutil

from .iiif import ImageIIIF, ManifestIIIF
from scr.opt.performance import calculate_performance
from scr.opt.utils import journal_error

class IIIFCollector:
    def __init__(self):
        self.session = None

    async def process_manifest(self, session, url):
        async with session.get(url) as response:
            # Process the response data asynchronously
            response_data = await response.json()
            return response_data  # Return the processed data asynchronously

    async def process_urls(self, session, path, urls, image=False, **kwargs):    ## HERE
        # Create tasks for each URL
        if image is False:
            tasks = [self.process_manifest(session, url) for url in urls]
        else:
            tasks = [ImageIIIFAsync(url, path, verbose=kwargs['verbose']).load_image_async(session, filename=) for url in urls]

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)

        # Process the results
        for result in results:
            if image:
                pass
            else:
                ok = result

    async def run_async(self, urls):
        # Create an aiohttp.ClientSession within the context of an async with statement
        # This ensures the session is properly closed
        async with aiohttp.ClientSession() as session:
            await self.process_urls(session, urls)


class ImageIIIFAsync(ImageIIIF, IIIFCollector):

    async def load_image_async(self, session, filename):    ## HERE
        url = self._format_url(self.url)
        if self.verbose:
            print(url)
        # get filename
        if filename is None:
            self.id_img = self.__get_id__(url.split('/')[-5])
        async with session.get(url) as response:
            try:
                self.img = await response
                # Process the response data asynchronously
                if 200 <= self.img.status_code < 400:
                    if ImageIIIF.verbose:
                        print(f"Succesing request image {str(self.id_img)} to {url}")
                else:
                    print(f"error request, {url}, {self.img.status_code}")
                    journal_error(self.out_dir, url=url, error=self.img.status_code)
                    pass
            except Exception as err:
                print(err)

class ParallelizeIIIF:
    processes = []
    def __init__(self):
        self.num_processes = self._get_cpu()

    def _process_chunk(self, chunk):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        collector = IIIFCollector()
        loop.run_until_complete(collector.run_async(chunk))
        loop.close()

    def _get_cpu(self):
        """Determine the number of processes"""
        return max(2, multiprocessing.cpu_count() // 2)

    def run_image(self, urls, **kwargs):
        start_time = time.time()  # Start time
        # Determine number chunk validity cpu count
        if len(urls) > self.num_processes:
            num_processes = len(urls)
        # Split the URLs among processes
        url_chunks = [urls[i::self.num_processes] for i in range(self.num_processes)]


        for chunk in url_chunks:
            # Create a process for each chunk
            process = multiprocessing.Process(target=self._process_chunk, args=(chunk,))
            self.processes.append(process)
            process.start()

        # Measure CPU and memory usage during execution
        cpu_percent = []
        memory_usage = []

        while any(process.is_alive() for process in self.processes):
            cpu_percent.append(psutil.cpu_percent())
            memory_usage.append(psutil.virtual_memory().percent)

        # Wait for all processes to finish
        for process in self.processes:
            process.join()

        # Determine resource and time consumption
        end_time = time.time()
        calculate_performance(start_time, end_time, cpu_percent, memory_usage)
