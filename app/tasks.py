import asyncio, tempfile, os
from pathlib import Path
from celery import Celery
from app.config import settings, celery_app
from app.downloader import async_download
from app.analyze import analyze_content
from app.callback import send_result

@celery_app.task(bind=True, max_retries=3)
def download_and_analyze(self, url: str, callback_url: str):
    try:
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "video.mp4"
            asyncio.run(async_download(url, dst))
            analysis = analyze_content(dst, output_path)
        send_result.delay(result=analysis, callback_url=callback_url)
        return analysis
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)