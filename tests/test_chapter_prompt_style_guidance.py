import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from novel_generator import chapter


def _default_blueprint_info(number):
    return {
        "chapter_title": f"第{number}章标题",
        "chapter_role": "推进章节",
        "chapter_purpose": "推动剧情",
        "suspense_level": "中等",
        "foreshadowing": "无",
        "plot_twist_level": "★☆☆☆☆",
        "chapter_summary": f"第{number}章摘要",
    }


def test_build_chapter_prompt_prepends_style_guidance_for_first_chapter(monkeypatch, tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    def fake_read_file(filename):
        name = os.path.basename(filename)
        mapping = {
            "Novel_architecture.txt": "小说设定",
            "Novel_directory.txt": "章节蓝图",
            "global_summary.txt": "全局摘要",
            "character_state.txt": "角色状态",
            "文风说明.txt": "用冷峻、克制、留白的笔调写作。",
        }
        return mapping.get(name, "")

    monkeypatch.setattr(chapter, "read_file", fake_read_file)
    monkeypatch.setattr(chapter, "get_chapter_info_from_blueprint", lambda blueprint, num: _default_blueprint_info(num))

    prompt = chapter.build_chapter_prompt(
        api_key="k",
        base_url="u",
        model_name="m",
        filepath=str(project_dir),
        novel_number=1,
        word_number=3000,
        temperature=0.7,
        user_guidance="遵循剧情主线",
        characters_involved="甲,乙",
        key_items="剑",
        scene_location="山谷",
        time_constraint="夜晚",
        embedding_api_key="ek",
        embedding_url="eu",
        embedding_interface_format="OpenAI",
        embedding_model_name="em",
    )

    assert prompt.startswith("【文风说明】\n用冷峻、克制、留白的笔调写作。\n\n")


def test_build_chapter_prompt_returns_original_prompt_when_style_guidance_missing(monkeypatch, tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    def fake_read_file(filename):
        name = os.path.basename(filename)
        mapping = {
            "Novel_architecture.txt": "小说设定",
            "Novel_directory.txt": "章节蓝图",
            "global_summary.txt": "全局摘要",
            "character_state.txt": "角色状态",
            "文风说明.txt": "   ",
        }
        return mapping.get(name, "")

    monkeypatch.setattr(chapter, "read_file", fake_read_file)
    monkeypatch.setattr(chapter, "get_chapter_info_from_blueprint", lambda blueprint, num: _default_blueprint_info(num))

    prompt = chapter.build_chapter_prompt(
        api_key="k",
        base_url="u",
        model_name="m",
        filepath=str(project_dir),
        novel_number=1,
        word_number=3000,
        temperature=0.7,
        user_guidance="遵循剧情主线",
        characters_involved="甲,乙",
        key_items="剑",
        scene_location="山谷",
        time_constraint="夜晚",
        embedding_api_key="ek",
        embedding_url="eu",
        embedding_interface_format="OpenAI",
        embedding_model_name="em",
    )

    assert not prompt.startswith("【文风说明】")
