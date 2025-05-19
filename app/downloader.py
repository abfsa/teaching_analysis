import aiohttp
from app.config import settings

async def async_download(url: str) -> str:
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=settings.download_timeout)) as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            raise Exception(f"Download failed: {str(e)}")