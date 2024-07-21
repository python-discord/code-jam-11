from discord import aiohttp

CAT_API_URL = "https://api.thecatapi.com/v1/images/search"


async def get_cat_image_url(http_session: aiohttp.ClientSession) -> str:
    """Get a URL for a random cat image.

    The produced image can also be a GIF.
    """
    async with http_session.get(CAT_API_URL) as resp:
        resp.raise_for_status()
        data = await resp.json()
        return data[0]["url"]
