import json
import os
from openai import OpenAI
import re
import time
from functools import wraps
from dotenv import load_dotenv

load_dotenv()  # 加载.env文件
api_key = os.getenv("api_key")  # 安全获取密钥
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

os.environ["OPENAI_API_KEY"]  =  api_key


client = OpenAI(
  api_key= api_key,
  base_url= base_url
)

def get_response(prompt):
  response = client.chat.completions.create(
    messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
    ],
    model="qwen-plus",
)
  return response.choices[0].message.content
  
def extract_json_from_string(input_string):
    # 使用正则表达式匹配JSON部分
    json_pattern = r"```json\n(.*?)```"
    match = re.search(json_pattern, input_string, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
        # 转换为JSON对象
        json_data = json.loads(json_str)
        return json_data
    else:
        return None
    
def time2seconds(time_str):
    # 分割小时、分钟、秒和毫秒
    time_parts = time_str.split(":")
    hours = int(time_parts[0])
    minutes = int(time_parts[1])
    seconds_milliseconds = time_parts[2].split(",")  # 分割秒和毫秒
    seconds = int(seconds_milliseconds[0])
    milliseconds = int(seconds_milliseconds[1])

    # 计算总秒数
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    return total_seconds

def retry_on_failure(max_retries=3, delay=1):
    """装饰器：自动重试失败函数"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"函数 {func.__name__} 最终失败: {str(e)}")
                        return None
                    print(f"函数 {func.__name__} 第{attempt+1}次重试...")
                    time.sleep(delay)
        return wrapper
    return decorator