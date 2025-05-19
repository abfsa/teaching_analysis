from celery import shared_task
import httpx
from app.config import settings

@shared_task(bind=True, max_retries=3)
def send_result(self, result):
    try:
        # 实际回调地址应由调用方提供，此处为示例
        resp = httpx.post("https://callback.example.com/api/results", 
                         json=result,
                         timeout=settings.download_timeout)
        resp.raise_for_status()
        return {"status": "success", "response": resp.text}
    except httpx.RequestError as exc:
        raise self.retry(exc=exc, countdown=60)
    except Exception as e:
        return {"status": "error", "message": str(e)}