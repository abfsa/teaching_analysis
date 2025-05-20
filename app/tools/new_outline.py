from .util import *

def chat(prompt, conversation_history):
    conversation_history.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        messages=conversation_history,
        model="qwen-plus",
    )
    
    assistant_reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": assistant_reply})
    
    return assistant_reply, conversation_history

def generate_prompt(srt, tree1):
    prompt1 = f"""
    你是一名教育专家，以下是通过教学视频提取出来的字幕以及知识图谱。其中根节点代表课程名称，第二层节点表示章节名称，第三层节点表示知识点。
    图谱：{tree1}
    字幕：{srt}
    """
    prompt2 =  """
    请根据知识图谱的结构，提取字幕中讲述的内容，将字幕中口语化的描述转换为书面语，注意去除字幕中出现的第一人称等口语化用词。
    按照以上任务，返回一个json格式的课程总结，格式如下：
    ```json
    {
        "课程名称": "",
        "章节": [
            {
                "章节名":"",
                "知识点":[
                    {"名称":"", "内容":""},
                    {"名称":"", "内容":""}
                ]
            },
            {
                "章节名":"",
                "知识点":[
                    {"名称":"", "内容":""},
                    {"名称":"", "内容":""}
                ]
            }
        ]
    }
    ```
    注意，你需要将字幕中的对应内容全部转化为书面语，而不是根据字幕内容仅生成一个简短的摘要。
    知识点一等替换成具体的知识点名称。
    确保不改变知识图谱中的知识点名称和数量,并且生成的内容与原字幕的文本量差距不太大，尽可能生成更多的内容。
    """
    return prompt1 + prompt2

@retry_on_failure(max_retries=2)
def generate_outline(srt, tree1):
    conversation_history = [
        {"role": "system", "content": "你是一个教育专家"}
    ]
    prompt3 = f"""
    生成的内容并没有完全覆盖字幕中讲述的所有细节。请按照字幕内容和你对课程的理解进行扩展，要求覆盖字幕的所有教学细节，重新返回一个json格式的分析结果。
    """
    response1, conversation_history = chat(generate_prompt(srt, tree1), conversation_history)
    response2,_ = chat(prompt3, conversation_history)
    response = extract_json_from_string(response2)
    return response