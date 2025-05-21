import json
import os
import time
import requests
import base64
import hashlib
import hmac
import time
import requests
import urllib
import subprocess
import io
from .util import *
lfasr_host = 'https://raasr.xfyun.cn/v2/api'

# 请求的接口名

api_upload = '/upload'
api_get_result = '/getResult'

@retry_on_failure(max_retries=2)
def generate_audio(video_input):
    """
    将视频文件转换为音频文件。
    """
    # 构建 FFmpeg 命令
    command = [
        'ffmpeg',
        '-i', 'pipe:0' if not isinstance(video_input, str) else video_input,
        '-vn',
        '-acodec', 'libmp3lame',
        '-ab', "64k",
        '-f', "mp3",
        '-'
    ]

    # 准备输入数据（如果是变量）
    input_data = None
    if isinstance(video_input, (bytes, io.BytesIO)):
        if isinstance(video_input, io.BytesIO):
            video_input = video_input.getvalue()
        input_data = video_input

    try:
        # 执行FFmpeg
        result = subprocess.run(
            command,
            input=input_data,  # 如果是变量则传入
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return result.stdout

    except subprocess.CalledProcessError as e:
        print(f"转换失败，错误：{e.stderr.decode()}")
        return None

def convert_to_srt(data):
    srt_lines = []
    index = 1

    for lattice in data['lattice2']:
        begin = int(lattice['begin'])
        end = int(lattice['end'])
        sentence = []
        start_time = begin
        end_time = end

        for segment in lattice['json_1best']['st']['rt']:
            for word_segment in segment['ws']:
                sentence.append(''.join([word['w'] for word in word_segment['cw']]))

        # Join the sentence and format the time
        full_sentence = ''.join(sentence)
        start_time_srt = f"{start_time // 3600000:02d}:{(start_time % 3600000) // 60000:02d}:{(start_time % 60000) // 1000:02d},{start_time % 1000:03d}"
        end_time_srt = f"{end_time // 3600000:02d}:{(end_time % 3600000) // 60000:02d}:{(end_time % 60000) // 1000:02d},{end_time % 1000:03d}"

        srt_lines.append(f"{index}\n")
        srt_lines.append(f"--> speaker: \n")
        srt_lines.append(f"{start_time_srt} --> {end_time_srt}\n")
        srt_lines.append(f"{full_sentence}\n")
        srt_lines.append(f"\n")
        index += 1
    
    subtitles = []

    for i in range(len(srt_lines)//5):
        j = 5*i
        id = srt_lines[j][:-1]
        speaker = srt_lines[j+1][13:-1]
        time = srt_lines[j+2][:-1]
        content = srt_lines[j+3][:-1]
        start = time[:12]
        end = time[17:]
        subtitles.append({'id':id,'start':start,'end':end,'content':content,'speaker':speaker})
    
    return subtitles


class RequestApi(object):
    def __init__(self, appid, secret_key, audio_path):
        self.appid = appid
        self.secret_key = secret_key
        self.upload_file_path = audio_path
        self.ts = str(int(time.time()))
        self.signa = self.get_signa()

    def get_signa(self):
        appid = self.appid
        secret_key = self.secret_key
        m2 = hashlib.md5()
        m2.update((appid + self.ts).encode('utf-8'))
        md5 = m2.hexdigest()
        md5 = bytes(md5, encoding='utf-8')
        # 以secret_key为key, 上面的md5为msg， 使用hashlib.sha1加密结果为signa
        signa = hmac.new(secret_key.encode('utf-8'), md5, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')
        return signa

    def upload(self):
        upload_file_path = self.upload_file_path
        file_len = os.path.getsize(upload_file_path)
        file_name = os.path.basename(upload_file_path)

        param_dict = {}
        param_dict['appId'] = self.appid
        param_dict['signa'] = self.signa
        param_dict['ts'] = self.ts
        param_dict["fileSize"] = file_len
        param_dict["fileName"] = file_name
        param_dict["duration"] = "200"
        data = open(upload_file_path, 'rb').read(file_len)

        response = requests.post(url=lfasr_host + api_upload + "?" + urllib.parse.urlencode(param_dict),
                                 headers={"Content-type": "application/json"}, data=data)
        result = json.loads(response.text)
        return result

    def get_result(self):
        uploadresp = self.upload()
        orderId = uploadresp['content']['orderId']
        param_dict = {}
        param_dict['appId'] = self.appid
        param_dict['signa'] = self.signa
        param_dict['ts'] = self.ts
        param_dict['orderId'] = orderId
        param_dict['resultType'] = "transfer,predict"
        status = 3
        # 建议使用回调的方式查询结果，查询接口有请求频率限制
        while status == 3:
            response = requests.post(url=lfasr_host + api_get_result + "?" + urllib.parse.urlencode(param_dict),
                                     headers={"Content-type": "application/json"})
            result = json.loads(response.text)
            status = result['content']['orderInfo']['status']
            if status == 4:
                break
            time.sleep(5)
        return result