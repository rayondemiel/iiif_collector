import asyncio
import aiohttp

async def open_json_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                json_data = await response.json()
                return json_data
            else:
                print(f"Error opening URL: {url}, Status code: {response.status}")
                return None

async def process_urls(urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(open_json_url(url))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results

async def main():
    urls = [
        'https://gallica.bnf.fr/iiif/ark:/12148/bpt6k1330314/manifest.json',
        'https://gallica.bnf.fr/iiif/ark:/12148/bpt6k854660v/manifest.json',
        'https://gallica.bnf.fr/iiif/ark:/12148/bpt6k5727849d/manifest.json'
    ]

    json_data_list = await process_urls(urls)
    for url, json_data in zip(urls, json_data_list):
        if json_data:
            # Process the JSON data for each URL
            print(f"URL: {url}")
            print(json_data)
            print()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())