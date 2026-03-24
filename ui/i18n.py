# ui/i18n.py
# -*- coding: utf-8 -*-
import json
import os
from typing import Dict

_LOCALE = 'zh_CN'
_CACHE: Dict[str, Dict[str, str]] = {}
_BASE_DIR = os.path.dirname(__file__)
_LOCALES_DIR = os.path.join(_BASE_DIR, 'locales')


def set_locale(code: str) -> None:
    global _LOCALE
    _LOCALE = code


def _load(locale_code: str) -> Dict[str, str]:
    if locale_code in _CACHE:
        return _CACHE[locale_code]
    path = os.path.join(_LOCALES_DIR, f'{locale_code}.json')
    data: Dict[str, str] = {}
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    except Exception:
        data = {}
    _CACHE[locale_code] = data
    return data


def t(s: str) -> str:
    if not isinstance(s, str):
        return s
    table = _load(_LOCALE)
    return table.get(s, s)

# Alias
tr = t



