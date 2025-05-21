import asyncio, tempfile, os
from pathlib import Path
from celery import Celery, shared_task
from .config import settings
from .downloader import download_file
from .analyze import analyze_content
from .callback import push_result
import uuid, shutil, json

celery_app = Celery("tasks")
celery_app.config_from_object("app.config")

TMP_ROOT = Path(tempfile.gettempdir()) / "teaching_analysis"

@shared_task(name="download_task")
def download_task(video_url: str, outline_url: str) -> tuple[str, str]:
    """
    下载视频与教案 → 返回二者本地路径
    """
    workdir = TMP_ROOT / uuid.uuid4().hex
    workdir.mkdir(parents=True, exist_ok=True)

    video_path   = workdir / "audio.mp3"
    outline_path = workdir
    outline_file = download_file(outline_url, outline_path)         # 根据扩展名自动保存
    download_file(video_url,   video_path)

    return str(video_path), str(outline_file)   # 交给下游

@shared_task(name="analyze_task")
def analyze_task(paths: tuple[str, str]) -> dict:
    video_path, outline_path = paths
    result = analyze_content(video_path, outline_path)
    return result

@shared_task(name="callback_task")
def callback_task(result: dict, hid: str, objectid: str, fid: str) -> None:
    # 直接调用异步函数；Celery 允许 sync wait
    import anyio
    anyio.run(push_result, result, hid=hid, objectid=objectid, fid=fid)