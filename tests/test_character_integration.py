import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from novel_generator.character_integration import process_chapter_for_characters
from novel_generator.character_store import list_auto, build_effective

def test_process_chapter_for_characters(tmp_path):
    fp = str(tmp_path)
    text = "角色：林越\n【角色】苏锦\n其他内容……"
    n = process_chapter_for_characters(text, 5, fp)
    assert n == 2
    la = list_auto(fp)
    assert 5 in la and set(la[5]) == {"林越","苏锦"}
    eff = build_effective(fp, "林越")
    assert eff.get('name') == '林越'
