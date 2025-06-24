from pydantic_settings import BaseSettings
from celery import Celery

class Settings(BaseSettings):
    model_path: str = "./models/analysis_model" # 现在没有用到
    download_timeout: int = 600
    callback_base_url: str = "http://140.210.94.165/fudanvideoai/result/zstp/callback"
    user_agent_default: str = "fudanai-teaching-0527"  # 8 字符，占位符，后续向超星确认

    redis_url: str = "redis://localhost:6379/0"
    task_result_backend: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"

# 单例
settings = Settings()

# ---------- 🌟 Celery 会自动读取的配置变量 ----------
# 这些变量名字必须是 Celery 认识的
broker_url = settings.redis_url
result_backend = settings.task_result_backend
accept_content = ["json"]
task_serializer = "json"
result_serializer = "json"
task_track_started = True
task_time_limit = 600