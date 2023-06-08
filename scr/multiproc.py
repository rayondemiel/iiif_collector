import concurrent.futures
import asyncio
import aiohttp
import threading
import multiprocessing

from .iiif import ConfigIIIF, ImageIIIF


class AsyncIIIF(ImageIIIF):


    async def __aenter__(self):
        self._session = aiohttp.ClientSession()

    async def __aexit__(self, *err):
        await self._session.close()
        self._session = None

    async def fetch(self, filename=None):

        url = self._format_url(self.url)
        if self.verbose:
            print(url)
        # get filename
        if filename is None:
            self.id_img = self.__get_id__(url.split('/')[-5])
        else:
            self.id_img = filename
        try:
            async with self._session.get(url) as resp:
                if 200 <= resp.status < 400:
                    return await resp.json()
        except Exception as err:
            #print(err)
            pass


class ParallelizeImage(ConfigIIIF):

    @staticmethod
    def process_urls(urls: list, path='./'):
        # Create an event loop
        print('test')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create a task for each URL
        tasks = [loop.create_task(AsyncIIIF(url, path).fetch()) for url in urls]
        tasks_save = [loop.create_task(AsyncIIIF(url, path).fetch()) for url in urls]

        # Wait for all tasks to complete
        loop.run_until_complete(asyncio.gather(*tasks))
        # Process the results
        for task in tasks:
            result = task.result()
            print(result)

        # Close the event loop
        loop.close()

    def __get_cpu__(self):
        return max(2, multiprocessing.cpu_count() // 2)

    @classmethod
    def run_image(cls, urls, path, manifest=False):
        # Use a ThreadPoolExecutor for multithreading
        with concurrent.futures.ThreadPoolExecutor(max_workers=cls().__get_cpu__()) as executor:
            if manifest:
                pass
            else:
                # regarder la derniere rep : https://chat.openai.com/c/cf85e960-6efc-4b7e-9dc0-3013d1ebf30a

                #executor.submit(cls.process_urls, urls, path)
                if cls.verbose:
                    print(f"Number of threads used : {str(threading.active_count())}")
