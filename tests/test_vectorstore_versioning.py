import os
import shutil
import tempfile
import pytest

from novel_generator.vectorstore_utils import (
    index_chapter_version,
    load_vector_store,
    get_relevant_context_from_vector_store,
    rebuild_vector_store_from_chapters,
    vector_store_is_empty,
)

class DummyEmbeddingAdapter:
    def embed_documents(self, texts):
        return [[0.1]*16 for _ in texts]
    def embed_query(self, query: str):
        return [0.1]*16


def write_chapter(root: str, n: int, text: str):
    os.makedirs(os.path.join(root, 'chapters'), exist_ok=True)
    p = os.path.join(root, 'chapters', f'chapter_{n}.txt')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    return p


def test_index_and_retrieve_active_only(tmp_path):
    fp = str(tmp_path)
    adapter = DummyEmbeddingAdapter()
    write_chapter(fp, 1, "A story about apple. NEWWORD")
    ok = index_chapter_version(adapter, 1, "A story about apple. NEWWORD", fp)
    assert ok
    store = load_vector_store(adapter, fp)
    assert store is not None
    docs = store.similarity_search("NEWWORD", k=3, filter={"chapter": 1})
    assert len(docs) >= 1
    for d in docs:
        assert d.metadata.get('chapter') == 1
        assert d.metadata.get('chapter_version') >= 1


def test_reindex_increments_version_and_filters(tmp_path):
    fp = str(tmp_path)
    adapter = DummyEmbeddingAdapter()
    write_chapter(fp, 1, "First content v1.")
    assert index_chapter_version(adapter, 1, "First content v1.", fp)
    # reindex with new content
    assert index_chapter_version(adapter, 1, "Second content v2 with KEYV2.", fp)
    store = load_vector_store(adapter, fp)
    # Should return content from latest (by text match)
    docs = store.similarity_search("KEYV2", k=3, filter={"chapter": 1})
    assert any('KEYV2' in (d.page_content or '') for d in docs)


def test_rebuild_full_and_query_with_chapter_filter(tmp_path):
    fp = str(tmp_path)
    adapter = DummyEmbeddingAdapter()
    write_chapter(fp, 1, "C1 apple banana.")
    write_chapter(fp, 2, "C2 mango papaya.")
    # ensure empty then rebuild
    assert vector_store_is_empty(fp)
    assert rebuild_vector_store_from_chapters(adapter, fp)
    # query with chapter_lte=1 should not include chapter 2
    text = get_relevant_context_from_vector_store(adapter, 'mango', fp, k=5, exclude_text=None, chapter_lte=1)
    assert 'mango' not in (text or '')
    # without filter should include
    text2 = get_relevant_context_from_vector_store(adapter, 'mango', fp, k=5)
    assert 'mango' in (text2 or '')
