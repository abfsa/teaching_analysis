import re
import json
from typing import Union, Dict
import os

def _extract_from_markdown(text: str) -> Dict[str, str]:
    """原来的正则版本，保持不变"""
    pattern_top = r"#### 知识点：(.+?)\n- \*\*覆盖情况\*\*：(.+?)\n"
    pattern_sub = r"- \*\*知识点：(.+?)\*\*\n  - \*\*覆盖情况\*\*：(.+?)\n"
    matches_top = re.findall(pattern_top, text)
    matches_sub = re.findall(pattern_sub, text)
    return {name.strip(): cov.strip() for name, cov in matches_top + matches_sub}

def _extract_from_json(data: dict) -> Dict[str, str]:
    """根据 JSON 样例提取 {知识点: 覆盖情况}"""
    analysis = data.get("分析", [])
    return {item["name"].strip(): item["覆盖情况"].strip()
            for item in analysis if "name" in item and "覆盖情况" in item}

def extract_coverage_map(src: Union[str, dict]) -> Dict[str, str]:
    """
    自动识别输入类型并提取覆盖情况映射。
    - src 可以是 markdown 字符串、json 字符串，或已解析好的 dict
    """
    # ① 已是 dict → 当作 json
    if isinstance(src, dict):
        return _extract_from_json(src)

    # ② str：先尝试当 json 解析
    if isinstance(src, str):
        try:
            return _extract_from_json(json.loads(src))
        except json.JSONDecodeError:
            # 解析失败说明不是 json 字符串，按 markdown 处理
            return _extract_from_markdown(src)

    raise TypeError("src 只能是 str 或 dict")


def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()
    
def read_json_to_data(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data
    
def save_text_to_file(text, output_path):
    """将提取的文本保存到 txt 文件中"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"文本已保存到 {output_path}")


import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

def score(level):
    return {"覆盖": 1, "部分覆盖": 0.5, "未覆盖": 0}.get(level, 0)

# 递归收集所有子节点的“节点”字段
def collect_subtree_nodes(node):
    nodes = [node["节点"]]
    for child in node.get("子节点", []):
        nodes.extend(collect_subtree_nodes(child))
    return nodes


def generate_coverage_radar(filepath):
    """
    根据 filepath 下的 report.json / tree2.json 生成雷达图:
    - report.json 需包含字段 response5 (覆盖评语)
    - tree2.json 为知识树 (可为空 {})
    生成 radar.png 保存在同一目录
    """
    response = read_json_to_data(os.path.join(filepath, 'report.json'))
    response5 = response["response5"]                       # markdown / json 字符串
    coverage_map = extract_coverage_map(response5)          # 兼容 md / json

    json_data = read_json_to_data(os.path.join(filepath, 'tree2.json'))

    if isinstance(json_data, dict) and not json_data:
        labels  = list(coverage_map.keys())
        values  = [score(coverage_map[l]) for l in labels]
        title   = "覆盖情况雷达图（无知识树降级模式）"
    else:                                                   # 正常知识树
        first_level_nodes = json_data                       # tree2.json 顶层就是 list
        labels, values = [], []
        for node in first_level_nodes:
            label = node["节点"]
            subtree_nodes  = collect_subtree_nodes(node)
            subtree_scores = [score(coverage_map.get(n, "未覆盖"))
                              for n in subtree_nodes]
            avg_score = np.mean(subtree_scores) if subtree_scores else 0
            labels.append(label)
            values.append(avg_score)
        title = "一级知识点子树覆盖得分雷达图"

    # ---------- 画雷达 ----------
    if len(labels) < 3:                                     # 少于 3 轴会退化成折线
        print("Warning: 维度不足 3，图形可能不完整。")

    values   += values[:1]                                  # 闭合
    angles    = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles   += angles[:1]

    fig = plt.figure(figsize=(6, 6))
    ax  = plt.subplot(111, polar=True)
    ax.plot(angles, values, 'o-', linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=9)
    ax.set_title(title)
    ax.grid(True)

    os.makedirs(filepath, exist_ok=True)
    out_path = os.path.join(filepath, 'coverage.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)