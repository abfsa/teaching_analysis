from app.tasks import celery_app
import httpx
from app.config import settings

@celery_app.task(bind=True, max_retries=3)
def send_result(self, result, callback_url: str):
    try:
        resp = httpx.post(callback_url, 
                         json=result,
                         timeout=settings.download_timeout)
        resp.raise_for_status()
        return {"status": "success", "response": resp.text}
    except httpx.RequestError as exc:
        raise self.retry(exc=exc, countdown=60)
    except Exception as e:
        return {"status": "error", "message": str(e)}