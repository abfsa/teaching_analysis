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
def download_task(audio_url: str, outline_url: str) -> tuple[str, str]:
    """
    下载视频与教案 → 返回二者本地路径
    """
    workdir = TMP_ROOT / uuid.uuid4().hex
    workdir.mkdir(parents=True, exist_ok=True)

    audio_path   = workdir / "audio.mp3"
    outline_path = workdir 
    if outline_url == "":
        return str(audio_path), None
    outline_file = download_file(outline_url, outline_path)         # 根据扩展名自动保存
    download_file(audio_url,   audio_path)

    return str(audio_path), str(outline_path)   # 交给下游

@shared_task(name="analyze_task")
def analyze_task(paths: tuple[str, str]) -> dict:
    video_path, outline_path = paths
    result = analyze_content(video_path, outline_path)
    return result

@shared_task(name="download_and_analyze")
def download_and_analyze(audio_url: str, outline_url: str) -> dict:
    workdir = TMP_ROOT / uuid.uuid4().hex
    workdir.mkdir(parents=True, exist_ok=True)

    audio_path   = workdir / "audio.mp3"
    if outline_url == "":
        download_file(audio_url, audio_path)
        if not audio_path.exists() or audio_path.stat().st_size == 0:
            raise RuntimeError("audio download failed")
        return analyze_content(str(audio_path), None)
        
    outline_file = download_file(outline_url, workdir)
    download_file(audio_url, audio_path)

    # —— 确保下载成功再分析
    if not audio_path.exists() or audio_path.stat().st_size == 0:
        raise RuntimeError("audio download failed")

    return analyze_content(str(audio_path), str(outline_file))

@shared_task(name="callback_task")
def callback_task(result: dict, fid: str, hid: str, objectid: str) -> None:
    # 直接调用异步函数；Celery 允许 sync wait
    import anyio
    anyio.run(lambda: push_result(result=result, fid=fid, hid=hid, objectid=objectid))

