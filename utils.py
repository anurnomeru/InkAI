# utils.py
# -*- coding: utf-8 -*-
import os
import json
from typing import Any, Callable, Optional

DEFAULT_ENCODING = "utf-8"


def _normalize_text(s: Any) -> str:
    """
    统一输出为 str，优先保持原字符串；若是 bytes，按 UTF-8 解码（errors='replace'）。
    避免界面意外传入 bytes 导致乱码或异常。
    """
    if isinstance(s, bytes):
        try:
            return s.decode(DEFAULT_ENCODING, errors="replace")
        except Exception:
            return s.decode("utf-8", errors="replace")
    return str(s) if not isinstance(s, str) else s


def read_file(filename: str) -> str:
    """读取文件的全部内容，若文件不存在或异常则返回空字符串。统一使用 UTF-8。"""
    try:
        with open(filename, "r", encoding=DEFAULT_ENCODING) as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"[read_file] 读取文件时发生错误: {e}")
        return ""


def append_text_to_file(text_to_append: str, file_path: str) -> None:
    """在文件末尾追加文本(带换行)。若文本非空且无换行，则自动加换行。UTF-8。"""
    text_to_append = _normalize_text(text_to_append)
    if text_to_append and not text_to_append.startswith("\n"):
        text_to_append = "\n" + text_to_append
    try:
        with open(file_path, "a", encoding=DEFAULT_ENCODING) as file:
            file.write(text_to_append)
    except IOError as e:
        print(f"[append_text_to_file] 发生错误：{e}")


def clear_file_content(filename: str) -> None:
    """清空指定文件内容。UTF-8。"""
    try:
        with open(filename, "w", encoding=DEFAULT_ENCODING):
            pass
    except IOError as e:
        print(f"[clear_file_content] 无法清空文件 '{filename}' 的内容：{e}")


def save_string_to_txt(content: str, filename: str) -> None:
    """将字符串保存为 txt 文件（覆盖写）。UTF-8。"""
    content = _normalize_text(content)
    try:
        with open(filename, "w", encoding=DEFAULT_ENCODING) as file:
            file.write(content)
    except Exception as e:
        print(f"[save_string_to_txt] 保存文件时发生错误: {e}")


def save_data_to_json(data: dict, file_path: str) -> bool:
    """将数据保存到 JSON 文件（UTF-8 且 ensure_ascii=False）。"""
    try:
        with open(file_path, "w", encoding=DEFAULT_ENCODING) as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"[save_data_to_json] 保存数据到JSON文件时出错: {e}")
        return False


def ensure_utf8(s: Any) -> str:
    """
    对外导出的统一编码入口：把任意输入变成 UTF-8 安全的 str（bytes → utf-8 decode replace）。
    供 UI 文本、日志、安全打印等场景调用，彻底杜绝乱码来源。
    """
    return _normalize_text(s)
