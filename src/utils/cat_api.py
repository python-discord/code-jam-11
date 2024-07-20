import aiohttp

CAT_API_URL: str = "https://api.thecatapi.com/v1/images/search"


async def get_cat_image_url() -> str:
    """Get a URL for a random cat image."""
    async with aiohttp.ClientSession() as client, client.get(CAT_API_URL) as response:
        response.raise_for_status()
        data = await response.json()
        return data[0]["url"]
