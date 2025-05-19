from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    task_result_backend: str = "redis://localhost:6379/1"
    model_path: str = "./models/analysis_model"
    download_timeout: int = 300
    
settings = Settings()