from fastapi import FastAPI, HTTPException
from celery import chain
from pydantic import BaseModel, HttpUrl, Field
import uuid
from .tasks import download_and_analyze, callback_task
from typing import Union

app = FastAPI(title="Teaching Video Analysis Service",
              description="接收视频/教案，下载，分析，回调",)

class DataUrls(BaseModel):
    video: HttpUrl = Field(..., description="视频下载地址")
    audio: HttpUrl = Field(..., description="视频下载地址")
    outline: Union[HttpUrl, str] = Field("", description="教案/大纲下载地址（可选）")


class SubmitReq(BaseModel):
    fid: str = Field(..., description="用户或课程唯一标识 FID")
    hid: str = Field(..., description="用户或课程唯一标识 HID")
    objectid: str = Field(..., description="对象 ID")
    data: DataUrls


class SubmitResp(BaseModel):
    task_id: str

@app.post("/submit", response_model=SubmitResp)
async def submit(req: SubmitReq):
    fid, hid, obj_id = req.fid, req.hid, req.objectid
    video_url = str(req.data.video)
    audio_url = str(req.data.audio)
    outline_url = str(req.data.outline)

    try:
        job = chain(
                    download_and_analyze.s(video_url, outline_url),
                    callback_task.s(hid=hid, objectid=obj_id, fid=fid)
                ).apply_async()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return SubmitResp(task_id=job.id)

@app.get("/health")
def health():
    return {"status": "ok"}