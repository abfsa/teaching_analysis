from .util import *
# 生成教学视频图谱

@retry_on_failure(max_retries=2)
def video_tree(subtitles):
    # 打开文件并按行读取内容
    sample = """
你是一名经验丰富的教育专家，以下是一段教学视频内音频转录得到的文字，请根据其中的教学内容提取重要概念、定义、模型、算法、例子等作为知识点，以及各个知识点讲述的时间顺序以及包含关系，归纳出一段详尽的JSON格式的四的树状知识图谱。
要求生成的知识图谱尽可能详细，每十分钟的讲解需要生成10~15个知识节点
对于每个节点（node），要求生成以下属性：
id: 对每个节点生成唯一性编号。
name: 每个知识点的具体名称。
type: 知识点的类型，按知识概念的粒度由粗到细分为"知识模块"，"知识单元"，"知识点"，"子知识点"。
level: 评价知识点的难度，范围为1~10。
time: 根据字幕分析得到的知识点讲述的时间范围，如"00:03:28,170 --> 00:08:48,910"
content: 知识点的简单概括。
child: 节点的子节点，为一个以JSON对象为元素的列表。其中的JSON对象也应具有节点的各个属性。若该节点没有子节点，则该属性值为空列表。

范例如下：
```json
{
    "id": ""
    "name": ""
    "type": ""
    "level": ""
    "time": ""
    "content": ""
    "child": [
        {
            "id": ""
            "name":""
            "type": ""
            "level": ""
            "time": ""
            "content": ""
            "child": []
        }
        {
            "id": ""
            "name":""
            "type": ""
            "level": ""
            "time": ""
            "content": ""
            "child": []
        }
    ]
}
```

注意：请严格按照给出的json格式进行生成，确保每个节点都有"id","name","type","level","time","content","child"七个属性。
"""
    # 构建prompt
    prompt = [
        sample,
      "\n教学内容如下：\n",
      str(subtitles)
    ]
    prompt = "".join(prompt)
    response = get_response(prompt)
    response = extract_json_from_string(response)
    return response

def validate_video_tree(tree):
    required_keys = {"id", "name", "type", "level", "time", "content", "child"}
    if tree is None:
        return False
    if set(tree.keys()) != required_keys:
        return False
    return True
    
def generate_video_tree(subtitles, max_retries=5):
    for attempt in range(max_retries):
        try:
            result = video_tree(subtitles)
            if result is None:
                print(f"Attempt {attempt + 1} failed. Result is None. Retrying...")
                continue
            if validate_video_tree(result):
                return result
            else:
                print(f"Attempt {attempt + 1} failed. Result does not meet the requirements. Retrying...")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with an error: {e}. Retrying...")
    print(f"Failed to generate a valid video tree after {max_retries} retries.")
    return {}
