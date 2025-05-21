import argparse
from openai import OpenAI
import os
import json
import subprocess
import re
from tools.generate_doc_tree import *
from tools.video_transformer import *
from tools.generate_video_tree import *
from tools.generate_report import *
from tools.new_outline import *
from tools.generate_coverage import *

def analyze_content(audio_path, outline_path):
    # 4. 转录字幕
    api = RequestApi(appid=os.getenv("appid"),
                     secret_key=os.getenv("secret_key"),
                     upload_file_path=audio_path
                     )
    result = api.get_result()
    
    # 解析嵌套的 JSON 字符串
    order_result = json.loads(result['content']['orderResult'])
    print("Parsed orderResult:", order_result)
    subtitles = convert_to_srt(order_result)

    print('字幕转录成功...')
    # 5. 生成视频图谱
    video_tree = generate_video_tree(subtitles)
    print('视频图谱生成成功...')

    # 6. 生成教案图谱
    outline_tree = generate_document_tree(outline_path)
    print('教案图谱生成成功...')

    # 8. 生成新教案
    new_outline = generate_outline(subtitles, video_tree)
    print('新教案生成成功...')

    # 7. 生成报告
    report = generate_report(subtitles, video_tree, outline_tree)
    print('分析报告生成成功...')

    print(f"视频处理完成")
    result = {
        'subtitles': subtitles,
        'video_tree': video_tree,
        'outline_tree': outline_tree,
        'analysis': report,
        'new_outline': new_outline
    }
    return result


# # 测试用
# file_name = "序列决策"

# with open(f"video/{file_name}.mp4", 'rb') as f:
#     video_data = f.read()
# outline_data = None
# result = analyze_content(video_data, outline_data)
# with open(f"result/{file_name}.json", 'w', encoding="utf-8") as f:
#     json.dump(result, f, ensure_ascii=False, indent=4)