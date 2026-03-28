import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from novel_generator.character_store import ensure_structure, save_manual, save_auto, build_effective, load_manual
from novel_generator.character_adopt import adopt_auto_entry

def test_adopt_specific_fields(tmp_path):
    fp = str(tmp_path)
    ensure_structure(fp)
    cid = save_manual(fp, { 'name': '林越', 'summary': '手动', 'attributes': {'能力':['刀术']} })
    save_auto(fp, 10, { cid: {'summary': '自动', 'attributes': {'能力':['轻功']}, 'relationships': {'苏锦':'同门'}} })
    ok = adopt_auto_entry(fp, cid, chapter_num=10, fields=['relationships'])
    assert ok
    m = load_manual(fp, cid)
    assert m['summary'] == '手动'
    assert set(m['attributes']['能力']) == {'刀术'}
    eff = build_effective(fp, cid)
    assert eff['relationships'].get('苏锦') == '同门'
