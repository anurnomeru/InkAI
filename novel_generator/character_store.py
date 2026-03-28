# novel_generator/character_store.py
# -*- coding: utf-8 -*-
"""
角色库存储层（M1）
- 目录：<save_path>/characters/{manual,auto}/ 以及 index.json
- 提供：读写 Manual/Auto、构建 Effective 视图（不依赖向量/检索/GUI）
- 参见 docs/todo/character.txt（前置约定：不在此处耦合向量）
"""
from __future__ import annotations
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from .character_merge import merge_character_entries

ISO_FMT = "%Y-%m-%dT%H:%M:%S%z"

# ----------------------- 路径与结构 -----------------------

def _root(save_path: str) -> str:
    return os.path.join(save_path, 'characters')

def manual_dir(save_path: str) -> str:
    return os.path.join(_root(save_path), 'manual')

def auto_dir(save_path: str) -> str:
    return os.path.join(_root(save_path), 'auto')

def index_path(save_path: str) -> str:
    return os.path.join(_root(save_path), 'index.json')


def ensure_structure(save_path: str) -> None:
    os.makedirs(manual_dir(save_path), exist_ok=True)
    os.makedirs(auto_dir(save_path), exist_ok=True)
    ip = index_path(save_path)
    if not os.path.exists(ip):
        with open(ip, 'w', encoding='utf-8') as f:
            json.dump({'characters': [], 'tags': [], 'stats': {}}, f, ensure_ascii=False, indent=2)

# ----------------------- 工具 -----------------------

def slugify(text: str) -> str:
    """生成相对稳定的 id；允许中文与字母数字，用下划线替换其他字符。"""
    text = (text or '').strip()
    # 保留中文、字母、数字，其他替换为下划线
    out = re.sub(r'[^\w\u4e00-\u9fff]+', '_', text, flags=re.UNICODE)
    out = re.sub(r'_+', '_', out).strip('_')
    return out or 'character'


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.path.exists(path):
        os.remove(path)
    os.replace(tmp, path)


def _now_iso() -> str:
    # 简化：不含时区偏移，便于测试
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

# ----------------------- 索引 -----------------------

def load_index(save_path: str) -> Dict[str, Any]:
    ensure_structure(save_path)
    return _read_json(index_path(save_path)) or {'characters': [], 'tags': [], 'stats': {}}


def save_index(save_path: str, data: Dict[str, Any]) -> None:
    _write_json(index_path(save_path), data)


def _upsert_index(save_path: str, char_id: str, name: str, latest_source: str) -> None:
    idx = load_index(save_path)
    found = None
    for it in idx.get('characters', []):
        if it.get('id') == char_id:
            found = it
            break
    if not found:
        found = {'id': char_id, 'name': name, 'aliases': [], 'tags': [], 'updated_at': _now_iso(), 'latest_source': latest_source}
        idx['characters'].append(found)
    else:
        found['name'] = name or found.get('name')
        found['updated_at'] = _now_iso()
        found['latest_source'] = latest_source
    save_index(save_path, idx)

# ----------------------- Manual 层 -----------------------

def manual_path(save_path: str, char_id: str) -> str:
    return os.path.join(manual_dir(save_path), f'{char_id}.json')


def load_manual(save_path: str, char_id: str) -> Dict[str, Any]:
    return _read_json(manual_path(save_path, char_id))


def save_manual(save_path: str, entry: Dict[str, Any]) -> str:
    ensure_structure(save_path)
    name = (entry.get('name') or '').strip()
    char_id = entry.get('id') or slugify(name)
    if not name:
        # 允许仅 id；但建议提供 name
        name = char_id
        entry['name'] = name
    entry['id'] = char_id
    entry.setdefault('source', 'manual')
    entry.setdefault('updated_at', _now_iso())
    _write_json(manual_path(save_path, char_id), entry)
    _upsert_index(save_path, char_id, name, 'manual')
    return char_id


def list_manual(save_path: str) -> List[str]:
    d = manual_dir(save_path)
    if not os.path.isdir(d):
        return []
    return sorted([os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith('.json')])

# ----------------------- Auto 层 -----------------------

def auto_path(save_path: str, chapter_num: int, char_id: str) -> str:
    return os.path.join(auto_dir(save_path), str(int(chapter_num)), f'{char_id}.json')


def save_auto(save_path: str, chapter_num: int, entries: Dict[str, Dict[str, Any]]) -> None:
    """批量保存自动抽取的增量条目（按章）。entries: {char_id: partial_fields}。"""
    ensure_structure(save_path)
    chapter_dir = os.path.dirname(auto_path(save_path, chapter_num, 'x'))
    os.makedirs(chapter_dir, exist_ok=True)
    for cid, data in (entries or {}).items():
        data = dict(data or {})
        data['id'] = cid
        data['source'] = 'auto'
        data.setdefault('updated_at', _now_iso())
        _write_json(os.path.join(chapter_dir, f'{cid}.json'), data)
        # 索引：仅更新时间与来源
        name = data.get('name') or cid
        _upsert_index(save_path, cid, name, f'auto@{int(chapter_num)}')


def list_auto(save_path: str, chapter_num: Optional[int] = None) -> Dict[int, List[str]]:
    base = auto_dir(save_path)
    if not os.path.isdir(base):
        return {}
    out: Dict[int, List[str]] = {}
    for sub in os.listdir(base):
        if not sub.isdigit():
            continue
        if chapter_num is not None and int(sub) != int(chapter_num):
            continue
        chap_dir = os.path.join(base, sub)
        ids = [os.path.splitext(f)[0] for f in os.listdir(chap_dir) if f.endswith('.json')]
        out[int(sub)] = sorted(ids)
    return dict(sorted(out.items(), key=lambda kv: kv[0]))


def load_auto_history(save_path: str, char_id: str, up_to_chapter: Optional[int] = None) -> List[Tuple[int, Dict[str, Any]]]:
    base = auto_dir(save_path)
    if not os.path.isdir(base):
        return []
    items: List[Tuple[int, Dict[str, Any]]] = []
    for sub in os.listdir(base):
        if not sub.isdigit():
            continue
        chap = int(sub)
        if up_to_chapter is not None and chap > int(up_to_chapter):
            continue
        p = os.path.join(base, sub, f'{char_id}.json')
        if os.path.exists(p):
            items.append((chap, _read_json(p)))
    items.sort(key=lambda x: x[0])
    return items

# ----------------------- Effective 合成 -----------------------

def build_effective(save_path: str, char_id: str, up_to_chapter: Optional[int] = None) -> Dict[str, Any]:
    manual = load_manual(save_path, char_id)
    auto_list = [data for _, data in load_auto_history(save_path, char_id, up_to_chapter)]
    locks = manual.get('locked', {}) if manual else {}
    effective = merge_character_entries(manual or {}, auto_list, locks=locks)
    # 元信息
    effective['id'] = char_id
    if 'name' not in effective:
        effective['name'] = manual.get('name') if manual else char_id
    effective['source'] = 'effective'
    return effective


def build_effective_all(save_path: str, up_to_chapter: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
    ids = set(list_manual(save_path))
    # 扫描 auto 补足 id
    for chap, id_list in list_auto(save_path).items():
        if up_to_chapter is not None and chap > int(up_to_chapter):
            continue
        ids.update(id_list)
    out: Dict[str, Dict[str, Any]] = {}
    for cid in sorted(ids):
        out[cid] = build_effective(save_path, cid, up_to_chapter)
    return out

