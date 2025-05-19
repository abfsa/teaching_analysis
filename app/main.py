from fastapi import FastAPI, HTTPException
from celery import chain
from app.config import settings
from app.tasks import download_and_analyze

app = FastAPI()

@app.post("/submit")
async def submit_task(url: str):
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    task_chain = chain(
        download_and_analyze.s(url)
    )
    result = task_chain.apply_async(
        broker=settings.redis_url,
        backend=settings.task_result_backend
    )
    return {"task_id": result.id}