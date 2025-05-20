import pytest
from fastapi import status

async def test_health_endpoint(test_client):
    response = test_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}

async def test_submit_endpoint(test_client):
    test_data = {
        "video_url": "http://example.com/video.mp4",
        "callback_url": "http://example.com/callback",
        "extra": {"resolution": "1080p"}
    }
    
    response = test_client.post("/submit", json=test_data)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    
    assert "task_id" in response_data
    assert len(response_data["task_id"]) == 36  # UUID length check
    assert response_data["status"] == "queued"