import concurrent.futures
import asyncio
import aiohttp
import threading


class ParallelizeRequest:

    def __init__(self, urls: list, **kwargs):
        self.urls = urls
        self.image = kwargs.get("image", False)
        self.verbose = kwargs.get("verbose", False)

    @staticmethod
    async def process_url(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if 200 <= response.status < 400:
                    return await response.json()

    @staticmethod
    def process_urls(urls):
        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create a task for each URL
        tasks = [loop.create_task(ParallelizeRequest.process_url(url)) for url in urls]

        # Wait for all tasks to complete
        loop.run_until_complete(asyncio.gather(*tasks))

        # Process the results
        for task in tasks:
            result = task.result()

        # Close the event loop
        loop.close()
        return "prout"

    def run_image(self):
        # Use a ThreadPoolExecutor for multithreading
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            executor.submit(self.process_urls, self.urls)
            if self.verbose:
                print(f"Number of threads used : {str(threading.active_count())}")
