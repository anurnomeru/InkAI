# novel_generator/character_integration.py
# -*- coding: utf-8 -*-
"""
角色库集成钩子（不依赖 UI）：
- process_chapter_for_characters: 从章节文本抽取角色条目并保存到 auto 层，带详细日志。
"""
from __future__ import annotations
import logging
from typing import Dict, Any
from .character_extract import extract_from_chapter_text
from .character_store import save_auto

def process_chapter_for_characters(chapter_text: str, chapter_num: int, save_path: str) -> int:
    """抽取并保存角色条目；返回保存的角色数量。
    日志：开始/参数/抽取数量/保存完成。
    """
    try:
        logging.info(f"[角色库] 抽取开始: chapter={chapter_num} path={save_path}")
        entries: Dict[str, Dict[str, Any]] = extract_from_chapter_text(chapter_text or '', int(chapter_num))
        n = len(entries or {})
        logging.info(f"[角色库] 抽取完成: chapter={chapter_num} count={n}")
        if n > 0:
            save_auto(save_path, int(chapter_num), entries)
            logging.info(f"[角色库] 已写入自动层: chapter={chapter_num} count={n}")
        else:
            logging.info(f"[角色库] 本章未发现可抽取角色: chapter={chapter_num}")
        return n
    except Exception as e:
        logging.error(f"[角色库] 抽取/保存失败: chapter={chapter_num} err={e}")
        return 0
