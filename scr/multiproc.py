import asyncio
import aiohttp
import multiprocessing
import time
import psutil

from .iiif import ConfigIIIF, ImageIIIF
from scr.opt.performance import calculate_performance

class IIIFCollector:
    def __init__(self):
        pass

    async def process_url(self, session, url):
        async with session.get(url) as response:
            # Process the response data asynchronously
            response_data = await response.json()
            return response_data  # Return the processed data asynchronously

    async def process_urls(self, session, urls):
        # Create tasks for each URL
        tasks = [self.process_url(session, url) for url in urls]

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)

        # Process the results
        for result in results:
            ok = result

    async def run_async(self, urls):
        # Create an aiohttp.ClientSession within the context of an async with statement
        # This ensures the session is properly closed
        async with aiohttp.ClientSession() as session:
            await self.process_urls(session, urls)


class ParallelizeImage(ConfigIIIF):

    def process_chunk(self, chunk):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        collector = IIIFCollector()
        loop.run_until_complete(collector.run_async(chunk))
        loop.close()

    def __get_cpu__(self):
        return max(2, multiprocessing.cpu_count() // 2)

    @classmethod
    def run_image(cls, urls):
        start_time = time.time()  # Start time
        # Determine the number of processes
        num_processes = cls.__get_cpu__()
        # Determine number chunk validity cpu count
        if len(urls) > num_processes:
            num_processes = len(urls)
        # Split the URLs among processes
        url_chunks = [urls[i::num_processes] for i in range(num_processes)]

        # Create a list to hold the process objects
        processes = []

        for chunk in url_chunks:
            # Create a process for each chunk
            process = multiprocessing.Process(target=cls.process_chunk, args=(chunk,))
            processes.append(process)
            process.start()

        # Measure CPU and memory usage during execution
        cpu_percent = []
        memory_usage = []

        while any(process.is_alive() for process in processes):
            cpu_percent.append(psutil.cpu_percent())
            memory_usage.append(psutil.virtual_memory().percent)

        # Wait for all processes to finish
        for process in processes:
            process.join()

        # Determine resource and time consumption
        end_time = time.time()
        calculate_performance(start_time, end_time, cpu_percent, memory_usage)
