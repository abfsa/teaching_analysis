import aiohttp, asyncio, async_timeout, pathlib
from app.config import settings

async def async_download(url: str, dest: str, timeout=120):
    pathlib.Path(dest).parent.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(timeout):
            async with session.get(url) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    async for chunk in resp.content.iter_chunked(CHUNK):
                        f.write(chunk)