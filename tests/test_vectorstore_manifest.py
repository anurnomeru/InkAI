import os
import json
from novel_generator.vectorstore_utils import index_chapter_version, load_manifest, rebuild_vector_store_from_chapters

class DummyEmbeddingAdapter:
    def embed_documents(self, texts):
        return [[0.1]*8 for _ in texts]
    def embed_query(self, query: str):
        return [0.1]*8


def write_chapter(root: str, n: int, text: str):
    os.makedirs(os.path.join(root, 'chapters'), exist_ok=True)
    p = os.path.join(root, 'chapters', f'chapter_{n}.txt')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    return p


def test_manifest_increments_on_reindex(tmp_path):
    fp = str(tmp_path)
    adapter = DummyEmbeddingAdapter()
    write_chapter(fp, 3, 'v1 text for c3')
    assert index_chapter_version(adapter, 3, 'v1 text for c3', fp)
    m1 = load_manifest(fp)
    assert m1['chapters'].get('3', {}).get('current_version') == 1
    assert index_chapter_version(adapter, 3, 'v2 text for c3 KEY', fp)
    m2 = load_manifest(fp)
    assert m2['chapters'].get('3', {}).get('current_version') == 2


def test_manifest_written_on_rebuild(tmp_path):
    fp = str(tmp_path)
    adapter = DummyEmbeddingAdapter()
    write_chapter(fp, 1, 'Aaa')
    write_chapter(fp, 2, 'Bbb')
    assert rebuild_vector_store_from_chapters(adapter, fp)
    m = load_manifest(fp)
    assert m['chapters'].get('1', {}).get('current_version') == 1
    assert m['chapters'].get('2', {}).get('current_version') == 1
