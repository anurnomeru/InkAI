import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import os
import json
from novel_generator.character_store import ensure_structure, save_manual, load_manual, save_auto, build_effective, list_manual, list_auto

def test_manual_only_effective(tmp_path):
    fp = str(tmp_path)
    ensure_structure(fp)
    cid = save_manual(fp, { 'name': '林越', 'summary': '手动设定', 'attributes': {'能力':['刀术']}, 'locked': {}})
    eff = build_effective(fp, cid)
    assert eff['summary'] == '手动设定'
    assert eff['attributes']['能力'] == ['刀术']

def test_auto_fills_when_manual_empty(tmp_path):
    fp = str(tmp_path)
    ensure_structure(fp)
    cid = save_manual(fp, { 'name': '苏锦' })
    save_auto(fp, 1, { cid: { 'summary': '自动摘要', 'attributes': {'性格':['冷静']}} })
    eff = build_effective(fp, cid)
    assert eff['summary'] == '自动摘要'
    assert '冷静' in eff['attributes']['性格']

def test_locked_field_prevents_override(tmp_path):
    fp = str(tmp_path)
    ensure_structure(fp)
    cid = save_manual(fp, { 'name': '阿青', 'summary': '手动摘要', 'locked': {'summary': True} })
    save_auto(fp, 2, { cid: { 'summary': '自动想改手动摘要' } })
    eff = build_effective(fp, cid)
    assert eff['summary'] == '手动摘要'

def test_arrays_union_and_timeline_sort(tmp_path):
    fp = str(tmp_path)
    ensure_structure(fp)
    cid = save_manual(fp, { 'name': '白也', 'attributes': {'能力':['刀术']}})
    save_auto(fp, 3, { cid: { 'attributes': {'能力':['轻功']}, 'timeline': [{'when':'相遇','ref_chapter':3}] } })
    save_auto(fp, 1, { cid: { 'timeline': [{'when':'铺垫','ref_chapter':1}] } })
    eff = build_effective(fp, cid)
    assert eff['attributes']['能力'] == ['刀术','轻功']
    assert [e['ref_chapter'] for e in eff['timeline']] == [1,3]

def test_listing_and_index(tmp_path):
    fp = str(tmp_path)
    ensure_structure(fp)
    a = save_manual(fp, { 'name': '甲' })
    b = save_manual(fp, { 'name': '乙' })
    save_auto(fp, 1, { a: {'summary':'s1'}, b: {'summary':'s2'} })
    assert set(list_manual(fp)) == {a,b}
    la = list_auto(fp)
    assert list(la.keys()) == [1]
    assert set(la[1]) == {a,b}
