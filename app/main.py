from fastapi import FastAPI, HTTPException
from celery import chain
from pydantic import BaseModel, HttpUrl
from app.config import settings
from app.tasks import download_and_analyze
import uuid

app = FastAPI(title="Teaching Video Analysis Service")

class SubmitReq(BaseModel):
    video_url: HttpUrl
    callback_url: HttpUrl
    extra: dict | None = None

class SubmitResp(BaseModel):
    task_id: str
    status: str = "queued"

@app.post("/submit", response_model=SubmitResp)
async def submit(req: SubmitReq):
    task_id = str(uuid.uuid4())
    task_chain = chain(
        download_and_analyze.s(
            str(req.video_url), 
            str(req.callback_url),
            req.extra
        )
    )
    result = task_chain.apply_async(
        broker=settings.redis_url,
        backend=settings.task_result_backend
    )
    return SubmitResp(task_id=task_id)

@app.get("/health")
def health():
    return {"status": "ok"}