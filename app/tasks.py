from celery import Celery
from app.config import settings
from app.downloader import async_download
from app.analyze import analyze_content
from app.callback import send_result
import httpx

celery_app = Celery('tasks', 
                    broker=settings.redis_url,
                    backend=settings.task_result_backend)

@celery_app.task(bind=True, max_retries=3)
def download_and_analyze(self, url):
    try:
        # 异步下载任务
        content = async_download(url)
        
        # 调用分析模块
        analysis_result = analyze_content(content)
        
        # 触发回调任务
        send_result.delay(analysis_result)
        
        return analysis_result
    except httpx.RequestError as exc:
        raise self.retry(exc=exc, countdown=60)
    except Exception as e:
        return {'error': str(e)}