import aiohttp, async_timeout, pathlib, mimetypes
CHUNK = 1 << 15   # 32 KB

async def async_download(
    url: str,
    dest: str | pathlib.Path,
    timeout: int = 120,
    user_agent: str = "fudanai-teaching-0527"   # 8-字符 UA；默认
) -> pathlib.Path:
    dest = pathlib.Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    headers = {"User-Agent": user_agent}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with async_timeout.timeout(timeout):
            async with session.get(url) as resp:
                resp.raise_for_status()
                # 若目标是目录而非文件 → 跟随 Content-Type 推断扩展名
                if dest.is_dir():
                    ctype = resp.headers.get("content-type", "")
                    ext = mimetypes.guess_extension(ctype.split(";")[0]) or ""
                    dest = dest / f"outline{ext}"
                with open(dest, "wb") as f:
                    async for chunk in resp.content.iter_chunked(CHUNK):
                        f.write(chunk)
    return dest

def download_file(url: str, dest: str | pathlib.Path, timeout: int = 120,
                  user_agent: str = "fudanai-teaching-0527",) -> pathlib.Path:
    """
    同步包装，便于 Celery 调用。
    """
    import anyio
    return anyio.run(async_download, url, dest, timeout, user_agent)
