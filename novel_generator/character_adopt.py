# novel_generator/character_adopt.py
# -*- coding: utf-8 -*-
"""角色采纳操作（从 Auto 采纳到 Manual）。
- 仅依赖 character_store；不涉及向量或 UI。
"""
from __future__ import annotations
from typing import Dict, Any, Iterable, Optional
import logging
from .character_store import load_manual, save_manual, load_auto_history


def _union_list(a, b):
    out = []
    seen = set()
    for x in (a or []) + (b or []):
        k = str(x)
        if k not in seen:
            seen.add(k); out.append(x)
    return out


def adopt_auto_entry(
    save_path: str,
    char_id: str,
    chapter_num: Optional[int] = None,
    fields: Optional[Iterable[str]] = None,
) -> bool:
    """将某章（或最近一章）的 Auto 条目合并到 Manual。
    - 标量字段：若 Manual 为空则填充；已有值则保留 Manual。
    - 数组字段：并集去重。
    - relationships：按 target 合并，Manual 优先。
    - timeline：追加（不去重），上层展示时排序。
    返回：是否有改动写入。
    """
    fields_set = set(fields) if fields else None
    # 取目标 auto 条目
    history = load_auto_history(save_path, char_id, up_to_chapter=chapter_num)
    if not history:
        logging.info(f"[角色库] 采纳: 无可用 AUTO 条目 id={char_id} up_to={chapter_num}")
        return False
    target_chap, auto = history[-1]
    if chapter_num is not None and target_chap != int(chapter_num):
        logging.info(f"[角色库] 采纳: 指定章节未找到，使用最近章 auto@{target_chap} id={char_id}")
    manual = load_manual(save_path, char_id) or { 'id': char_id, 'name': char_id }
    before = repr(manual)
    def allowed(field: str) -> bool:
        return (fields_set is None) or (field in fields_set)
    # name/aliases/tags/summary
    if allowed('name') and not manual.get('name') and auto.get('name'):
        manual['name'] = auto['name']
    if allowed('aliases') and auto.get('aliases'):
        manual['aliases'] = _union_list(manual.get('aliases', []), auto.get('aliases'))
    if allowed('tags') and auto.get('tags'):
        manual['tags'] = _union_list(manual.get('tags', []), auto.get('tags'))
    if allowed('summary') and auto.get('summary') and not manual.get('summary'):
        manual['summary'] = auto['summary']
    # attributes
    if allowed('attributes') and auto.get('attributes'):
        manual.setdefault('attributes', {})
        for k, v in (auto['attributes'] or {}).items():
            if isinstance(v, list):
                manual['attributes'][k] = _union_list(manual['attributes'].get(k, []), v)
            elif isinstance(v, str) and not manual['attributes'].get(k):
                manual['attributes'][k] = v
    # relationships
    if allowed('relationships') and auto.get('relationships'):
        manual.setdefault('relationships', {})
        for tgt, desc in (auto['relationships'] or {}).items():
            if tgt not in manual['relationships']:
                manual['relationships'][tgt] = desc
    # timeline
    if allowed('timeline') and auto.get('timeline'):
        manual.setdefault('timeline', [])
        manual['timeline'].extend(auto['timeline'])
    changed = (repr(manual) != before)
    if changed:
        save_manual(save_path, manual)
        logging.info(f"[角色库] 采纳到手动: id={char_id} from=auto@{target_chap} fields={sorted(list(fields_set)) if fields_set else 'ALL'}")
    else:
        logging.info(f"[角色库] 采纳无改动: id={char_id} from=auto@{target_chap}")
    return changed
