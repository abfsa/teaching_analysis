import httpx
from .config import settings
from loguru import logger

async def push_result(result: dict, *, hid: str, objectid: str, fid: str) -> None:
    """
    将分析结果 POST 给回调接口：
    http://xxx.com/fudan/videoai/result/callback?hid={hid}&objectId={objectid}
    注意：如果未来确认 objectId 也需传 hid，请把 objectid 改成 hid 即可。
    """
    url = f"{settings.callback_base_url}?hid={hid}&objectId={objectid}&fid={fid}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # **要求：把 analyze_content() 的返回值放在 body 内**
            resp = await client.post(url, json={"data": result})
            resp.raise_for_status()
            logger.info(f"Callback OK → {url}")
    except Exception as exc:
        logger.error(f"Callback FAILED → {url} • {exc}")
        raise