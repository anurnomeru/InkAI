# novel_generator/character_extract.py
# -*- coding: utf-8 -*-
"""角色抽取器（占位 M1）
- 目标：从已定稿章节文本中抽取角色增量条目（不落盘）。
- M1 实现：提供一个简化的正则解析器；后续可替换为 LLM 抽取。
"""
from __future__ import annotations
from typing import Dict, Any
import re

def extract_from_chapter_text(chapter_text: str, chapter_num: int) -> Dict[str, Dict[str, Any]]:
    """从章节文本中抽取角色：
    简化规则：匹配行首“角色：<名字>”或“【角色】<名字>”，
    对同名去重，生成最小字段 {id,name,summary?}
    """
    entries: Dict[str, Dict[str, Any]] = {}
    if not chapter_text:
        return entries
    lines = chapter_text.splitlines()
    for ln in lines:
        ln = ln.strip()
        m = re.match(r'^(?:角色[:：]|【角色】)\s*([^\s，,：:《〈(（]+)', ln)
        if not m:
            continue
        name = m.group(1).strip()
        if not name:
            continue
        cid = name  # id 默认使用原名（允许中文文件名）
        if cid not in entries:
            entries[cid] = {
                'id': cid,
                'name': name,
                'summary': f'来自第{chapter_num}章的抽取',
            }
    return entries
