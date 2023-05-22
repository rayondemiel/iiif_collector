import concurrent.futures
import asyncio
import aiohttp
import threading

from .iiif import ConfigIIIF, ImageIIIF

class AsyncIIIF(ImageIIIF):

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *err):
        await self._session.close()
        self._session = None

    @classmethod
    async def fetch(cls, url, filename=None):
        url = cls._format_url(url)
        if cls.verbose:
            print(url)
        # get filename
        if filename is None:
            cls.id_img = cls.__get_id__(url.split('/')[-5])
        else:
            cls.id_img = filename
        try:
            async with cls._session.get(url) as resp:
                if 200 <= resp.status < 400:
                    return await resp.json()
        except Exception as err:
            print(err)

class ParallelizeImage(ConfigIIIF):

    def process_urls(self, urls, path):
        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create a task for each URL
        tasks = [loop.create_task(AsyncIIIF.fetch(url)) for url in urls]
        tasks_save = [loop.create_task(AsyncIIIF.fetch(url)) for url in urls]

        # Wait for all tasks to complete
        loop.run_until_complete(asyncio.gather(*tasks))

        # Process the results
        for task in tasks:
            result = task.result()

        # Close the event loop
        loop.close()
    
    def __get_cpu__():
        return min(8, multiprocessing.cpu_count() // 2)

    @classmethod
    def run_image(cls, urls, path):
        # Use a ThreadPoolExecutor for multithreading
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.__get_cpu__()) as executor:
            executor.submit(cls.process_urls, urls, path)
            if cls.verbose:
                print(f"Number of threads used : {str(threading.active_count())}")
