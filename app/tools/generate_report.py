from .util import *
from openai import OpenAI
import os
import json
import re
import numpy as np
from typing import Union, Dict

prompt1 = """
你是一名教育专家，以下是一段教学视频提取出来的字幕以及知识图谱，其中包含了教师讲述的知识点之间的从属关系、知识点的名称和具体内容、知识点的难度（level）以及知识点讲解的时间范围。
请根据你对该门课程的教学经验，分析知识点教学时长分布的合理性，并对每个知识点生成一段评价和建议，指标如下：
1. 知识点的讲解时长是否与知识点的内容量以及难度相匹配？
2. 知识点的整体难度分布是否比较合理？
3. 知识点的讲解时间与分布是否有利于学生理解？
4. 是否存在高难度知识点过于集中或知识点整体难度过低等问题？
5. 其他合理的评价

例如：
- 马尔可夫决策过程：讲述该知识模块的时间共占用课程的38分钟，讲述时间较长，有利于学生理解这一核心知识点知识点，但这也导致后半部分的知识密度较高。这种安排可能对初学者造成一定压力，尤其是当他们需要快速适应复杂的数学模型时。

请对每个知识点进行以上评价，并生成一段总结，返回一份完整的markdown格式的分析报告，具体格式如下：

### 知识点难度分布
#### 评价
知识点的分布总体上呈现由浅入深、逐步递进的趋势...

- 知识点1：
- 知识点2：
...

#### 建议
将生成的内容保存为json格式的文本，且json对象的每个属性为符合markdown语法的字符串。例如：
```json
{
    "评价":"",
    "建议":"",
    "知识点":[
        {"name":"", "评价":"", "建议":""},
        {"name":"", "评价":"", "建议":""}
    ]
}
```

注意：该分析结果用于教师自评和改善教学效果，请使用委婉的语气，尽量避免对教师的授课内容进行直接的点评，而是生成具有普适性的建议，
避免使用教师实际讲述的内容举例。
"""

prompt2 = """
你是一名教育专家，以下是一段教学视频提取出来的字幕以及知识图谱，其中包含了教师讲述的知识点之间的从属关系、知识点的名称和具体内容、知识点的难度（level）以及知识点讲解的时间范围。
请根据你对该门课程的教学经验，分析其中知识点的逻辑关系。给出以下逻辑关系选项：
1. 层级关系：其中一个知识点是另一个知识点的子集或扩展
2. 序列关系：知识点按时间或逻辑顺序排列，通常表示一个过程或步骤的先后顺序
3. 并列关系：知识点没有直接的层级或顺序关系，但属于同一主题或类别
4. 因果关系: 一个知识点是另一个知识点的原因或结果
5. 支持关系: 一个案例(exmaple)对另一个知识点的讲解起到解释和启发作用

请生成一个json格式的关系列表，里面包含该知识图谱中所有的节点以及所有节点之间的所有关系，其中节点属性包含id，name(与原图保持一致)，type。
type的可选范围为(knowledge, example)，knoeledge指的是知识点，对应原图谱中的知识点，而example通常指的是偏应用的知识或实际问题等案例，根据课程教学内容提取。你需要分析节点内容并推理出节点的type。
格式如下：
```json
{
    "node":[
        {
            "id":"",
            "name":"",
            "type":"",
            "level":""
        },
        {
            "id":"",
            "name":"",
            "type":"",
            "level":""
        }
    ],
    "example":[
        {
            "id":"",
            "name":"",
            "type":"",
        },
    ]
    "edge":[
        {
            "from":""
            "to":""
            "relation":""
        },
        {
            "from":""
            "to":""
            "relation":""
        }
    ]
}
```
注意，from和to属性保存节点的id。对于exmaple类型的节点，不需要level属性。请严格按照给出的json格式生成结果。
请将example类型的节点放在example属性下的列表中
注意：该分析结果用于教师自评和改善教学效果，请使用委婉的语气，尽量避免对教师的授课内容进行直接的点评，而是生成具有普适性的建议，
避免使用教师实际讲述的内容举例。
"""

prompt3 = """
你是一位教育专家，以下是根据一段教学视频提取的知识图谱以及知识点关系。
请根据你的教学经验，对该门课程视频的每个知识点的讲解逻辑生成一段评价和建议。评价内容可以参考以下指标指标如下：

请对知识点之间的逻辑性做出评价，并整理成一段详细的评价和建议，分别列举出结构性和逻辑性较好的部分，以及逻辑性较差的部分，
并生成一段总结，返回一份完整的markdown格式的分析报告，具体格式如下：

1. 知识点的讲解顺序与知识点的关系是否相对应？
2. 每个知识点的前置知识点，也即依赖知识点是否已经讲解到位？
3. 在讲解知识点的同时是否通过相关案例加深学生理解？
4. 在讲解知识点时有没有周期性复习以前的知识点？

### 知识点逻辑分布
#### 评价
#### 建议

请按照以上要求生成一个json格式的报告，格式如下：
```json
{
    "评价":"",
    "建议":["", ""]
}
```

注意：该分析结果用于教师自评和改善教学效果，请使用委婉的语气，尽量避免对教师的授课内容进行直接的点评，而是生成具有普适性的建议，
避免使用教师实际讲述的内容举例。
"""

prompt5 = """
   任务描述：
              你将获得两个输入：
              1. 结构化知识信息：这是从教案中提取出的知识点及其相互关系，格式为层级化的 JSON 或树状结构，包含关键概念、定义、例子等。
              2. 视频转录文字：这是视频内容转录后的文字记录。

                你的任务：
              1. 结构化知识信息：这是从教案中提取出的知识点及其相互关系，格式为层级化的 JSON 或树状结构，包含关键概念、定义、例子等。
              2. 视频转录文字：这是视频内容转录后的文字记录。

              我们提供了完整的课程知识点结构，并希望你逐个知识点地判断讲授内容是否涵盖，评价标准如下：
              覆盖：该知识点在讲授中完整提及并讲解
              部分覆盖：知识点被提及，但未完全讲清或有术语遗漏
              未覆盖：知识点在讲授中完全未出现

              【任务要求】：
            遍历并列出知识图谱中每个知识点（包括子节点）,对每个知识点，输出以下标准格式：
            知识点：<名称>
            覆盖情况：<覆盖 | 部分覆盖 | 未覆盖>
            解释：<简要说明是否出现，是否讲清，举例说明>
            严格使用“覆盖情况”字段，值仅限上述三类

    注意：若未输入从教案中提取的结构化知识信息，则将视频内容与该课程的主流教学方案进行对比，并返回一个简短的评价。
    按照以上要求，返回json格式的分析结果，json对象的每个属性应该为满足markdown格式的字符串。
    参考格式如下：
    ```json
    {
        "覆盖情况总结":"",
        "分析":[
            {
                "name":"",
                "覆盖情况":"",
                "解释":""
            }
        ],
        "覆盖评分":"",
        "改进建议':""
    }
    ```

    注意：该分析结果用于教师自评和改善教学效果，请使用委婉的语气，尽量避免对教师的授课内容进行直接的点评，而是生成具有普适性的建议，
    避免使用教师实际讲述的内容举例。
    """
class model:
    def __init__(self):
        self.conversation_history =  [{"role": "system", "content": "你是一个教育专家"}]
        self.prompt = "你生成的结果格式有错，请严格按照给出的示例格式生成结果。"
        self.result = None

    def chat(self, sample=None):
        if sample == None:
            prompt = self.prompt
        else:
            prompt = sample
        self.conversation_history.append({"role": "user", "content": prompt})
    
        response = client.chat.completions.create(
            messages=self.conversation_history,
            model="qwen-plus",
        )
    
        assistant_reply = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": assistant_reply})
    
        self.result = assistant_reply

def traverse(node, num_node, indent, Beginner, Intermediate, Advanced, depth):
    # 如果有子节点，递归遍历子节点
    if indent + 1 > depth:
        depth = indent+1
    num_node += 1
    if int(node['level']) <= 3:
        Beginner += 1
    elif int(node['level']) <= 6:
        Intermediate += 1
    else:
        Advanced += 1
    if 'child' in node and node['child']:
        depth += 1
        for child in node['child']:
            num_node, Beginner, Intermediate, Advanced, depth = traverse(child, num_node, indent + 1, Beginner, Intermediate, Advanced, depth)
    return num_node, Beginner, Intermediate, Advanced, depth

# 提取视频图谱的基本信息
def extract_baseinf(tree1):
    total_time = tree1['time'][17:]
    title = tree1['name']
    num_node, Beginner, Intermediate, Advanced, depth = traverse(tree1, 0, 0, 0, 0, 0, 0)
    response0 = f"本课程主要讲解{title}，视频时长{total_time}，共包含{num_node}个知识点，其中包含初级知识点（难度在1~3之间）{Beginner}个，中级知识点（难度在4~6之间）{Intermediate}个，高级知识点（难度在7~10之间）{Advanced}个。"
    return response0

def analysis(srt, tree1, sample):
    # 构建prompt
    prompt = [
            sample,
      "\n教学内容如下：\n",
      str(srt),
      "\n图谱内容如下：\n",
      str(tree1)
    ] 
    prompt = "\n".join(prompt)
    chat_model = model()
    print("第一轮对话")
    chat_model.chat(prompt)
    while True:
        try:
            response = extract_json_from_string(chat_model.result)
            if response:
                return response
            print("未找到目标格式，再次进行一轮对话")
            chat_model.chat()
        except:
            print("json对象提取异常，再次进行一轮对话")
            chat_model.chat()

def comparison_for_graph(srt, tree2, sample):
    # 构建prompt
    prompt = [
            sample,
      "\n结构化知识信息如下：\n",
      str(tree2),
      "\n视频转录文字内容如下：\n",
      str(srt)
    ]
    prompt = "\n".join(prompt)
    chat_model = model()
    chat_model.chat(prompt)
    while True:
        try:
            response = extract_json_from_string(chat_model.result)
            if response:
                return response
            print("未找到目标格式，再次进行一轮对话")
            chat_model.chat()
        except:
            print("json对象提取异常，再次进行一轮对话")
            chat_model.chat()

@retry_on_failure(max_retries=2)
def generate_report(srt, tree1, tree2):
    response0 = extract_baseinf(tree1)
    response1 = analysis(srt, tree1, prompt1)

    response2 = analysis(srt, tree1, prompt2)

    response3 = analysis(srt, tree1, prompt3 + "知识点关系列表如下：\n" + str(response2))

    response5 = comparison_for_graph(srt, tree2, prompt5)

    response = {
        'response0':response0,
        'response1':response1,
        'response2':response2,
        'response3':response3,
        'response5':response5
    }
    return response