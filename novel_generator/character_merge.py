# novel_generator/character_merge.py
# -*- coding: utf-8 -*-
"""合并规则（Manual 优先 + Auto 叠加），字段级锁定支持。"""
from __future__ import annotations
from typing import Dict, Any, List
import copy

def _union_list(a: List[Any], b: List[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []
    for x in (a or []) + (b or []):
        key = str(x)
        if key not in seen:
            seen.add(key); out.append(x)
    return out


def merge_character_entries(manual: Dict[str, Any], autos: List[Dict[str, Any]], *, locks: Dict[str, Any] | None = None) -> Dict[str, Any]:
    locks = locks or {}
    eff: Dict[str, Any] = copy.deepcopy(manual) if manual else {}

    def locked(field: str) -> bool:
        v = locks.get(field)
        if isinstance(v, bool):
            return v
        return False

    for auto in autos or []:
        if not isinstance(auto, dict):
            continue
        # name
        if not eff.get('name') and auto.get('name'):
            if not locked('name'):
                eff['name'] = auto.get('name')
        # aliases
        if auto.get('aliases'):
            eff['aliases'] = _union_list(eff.get('aliases', []), list(auto.get('aliases') or []))
        # tags
        if auto.get('tags'):
            eff['tags'] = _union_list(eff.get('tags', []), list(auto.get('tags') or []))
        # summary
        if auto.get('summary') and (not eff.get('summary') or not locked('summary')):
            eff['summary'] = auto.get('summary')
        # attributes (dict of list/str)
        attrs_auto = auto.get('attributes') or {}
        if attrs_auto:
            if 'attributes' not in eff:
                eff['attributes'] = {}
            if not locked('attributes'):
                for k, v in attrs_auto.items():
                    if isinstance(v, list):
                        eff['attributes'][k] = _union_list(list(eff['attributes'].get(k, [])), v)
                    elif isinstance(v, str):
                        if not eff['attributes'].get(k):
                            eff['attributes'][k] = v
        # relationships (map target->desc)
        rel_auto = auto.get('relationships') or {}
        if rel_auto:
            if 'relationships' not in eff:
                eff['relationships'] = {}
            if not locked('relationships'):
                for tgt, desc in rel_auto.items():
                    if tgt not in eff['relationships']:
                        eff['relationships'][tgt] = desc
        # timeline (list of events)
        tl_auto = auto.get('timeline') or []
        if tl_auto:
            if 'timeline' not in eff:
                eff['timeline'] = []
            eff['timeline'].extend(tl_auto)
    # timeline 排序（若有 ref_chapter）
    if isinstance(eff.get('timeline'), list):
        eff['timeline'].sort(key=lambda ev: (ev.get('ref_chapter', 10**9), ev.get('when','')))
    return eff
