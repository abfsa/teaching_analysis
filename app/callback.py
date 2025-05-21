import httpx
from .config import settings
from loguru import logger
import hashlib
from datetime import datetime

def generate_enc(fid: str, hid: str, key: str = "fxjg~/@-4]Pv") -> str:
    """
    生成MD5校验值
    
    :param fid: 业务ID
    :param hid: 请求ID
    :param key: 加密密钥（默认使用给定的key）
    :return: 32位小写MD5值
    """
    # 获取当前日期（yyyy-MM-dd格式）
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 拼接原始字符串
    raw_str = f"{fid}-{hid}-{date_str}-{key}"
    
    # 计算MD5
    md5_hash = hashlib.md5(raw_str.encode('utf-8')).hexdigest()
    
    return md5_hash

async def push_result(result: dict, *, hid: str, objectid: str, fid: str) -> None:
    """
    将分析结果 POST 给回调接口：
    http://xxx.com/fudan/videoai/result/callback?hid={hid}&objectId={objectid}
    注意：如果未来确认 objectId 也需传 hid，请把 objectid 改成 hid 即可。
    """
    enc = generate_enc(fid, hid)
    url = f"{settings.callback_base_url}?fid={fid}&hid={hid}&objectId={objectid}&enc={enc}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # **要求：把 analyze_content() 的返回值放在 body 内**
            resp = await client.post(url, json={"data": result})
            resp.raise_for_status()
            logger.info(f"Callback OK → {url}")
    except Exception as exc:
        logger.error(f"Callback FAILED → {url} • {exc}")
        raise