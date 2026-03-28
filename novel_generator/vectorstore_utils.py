#novel_generator/vectorstore_utils.py
# -*- coding: utf-8 -*-
# Vector store related operations (init, update, search, clear).
import os
import logging
import traceback
try:
    import nltk
    _HAVE_NLTK = True
except Exception:
    nltk = None
    _HAVE_NLTK = False
import numpy as np
import re
import ssl
import requests
import warnings
from langchain_chroma import Chroma
logging.basicConfig(
    filename='app.log',      # 閺冦儱绻旈弬鍥︽閸?
    filemode='a',            # 鏉╄棄濮炲Ο鈥崇础閿?w' 娴兼俺顩惄鏍电礆
    level=logging.INFO,      # 鐠佹澘缍?INFO 閸欏﹣浜掓稉濠勯獓閸掝偆娈戦弮銉ョ箶
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# 缁備胶鏁ら悧鐟扮暰閻ㄥ嚲orch鐠€锕€鎲?
warnings.filterwarnings('ignore', message='.*Torch was not compiled with flash attention.*')
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # 缁備胶鏁okenizer楠炴儼顢戠拃锕€鎲?

from chromadb.config import Settings
from langchain.docstore.document import Document
from sklearn.metrics.pairwise import cosine_similarity
from .common import call_with_retry

def get_vectorstore_dir(filepath: str) -> str:
    # Get vectorstore path
    return os.path.join(filepath, "vectorstore")

def clear_vector_store(filepath: str) -> bool:
    # Clear vector store
    import shutil
    store_dir = get_vectorstore_dir(filepath)
    if not os.path.exists(store_dir):
        logging.info("No vector store found to clear.")
        return False
    try:
        shutil.rmtree(store_dir)
        logging.info(f"Vector store directory '{store_dir}' removed.")
        return True
    except Exception as e:
        logging.error(f"閺冪姵纭堕崚鐘绘珟閸氭垿鍣烘惔鎾存瀮娴犺泛銇欓敍宀冾嚞閸忔娊妫寸粙瀣碍閸氬孩澧滈崝銊ュ灩闂?{store_dir}閵嗕繐n {str(e)}")
        traceback.print_exc()
        return False

def init_vector_store(embedding_adapter, texts, filepath: str):

    # Create or load a Chroma vector store under filepath and insert texts.
    # Return None on failure (non-blocking).
    # Return None on failure (non-blocking).
    from langchain.embeddings.base import Embeddings as LCEmbeddings

    store_dir = get_vectorstore_dir(filepath)
    os.makedirs(store_dir, exist_ok=True)
    documents = [Document(page_content=str(t)) for t in texts]

    try:
        class LCEmbeddingWrapper(LCEmbeddings):
            def embed_documents(self, texts):
                return call_with_retry(
                    func=embedding_adapter.embed_documents,
                    max_retries=3,
                    fallback_return=[],
                    texts=texts
                )
            def embed_query(self, query: str):
                res = call_with_retry(
                    func=embedding_adapter.embed_query,
                    max_retries=3,
                    fallback_return=[],
                    query=query
                )
                return res

        chroma_embedding = LCEmbeddingWrapper()
        vectorstore = Chroma.from_documents(
            documents,
            embedding=chroma_embedding,
            persist_directory=store_dir,
            client_settings=Settings(anonymized_telemetry=False),
            collection_name="novel_collection"
        )
        return vectorstore
    except Exception as e:
        logging.warning(f"Init vector store failed: {e}")
        traceback.print_exc()
        return None

def load_vector_store(embedding_adapter, filepath: str):

    # Load existing Chroma vector store; return None if missing/failure.

    from langchain.embeddings.base import Embeddings as LCEmbeddings
    store_dir = get_vectorstore_dir(filepath)
    if not os.path.exists(store_dir):
        logging.info("Vector store not found. Will return None.")
        return None

    try:
        class LCEmbeddingWrapper(LCEmbeddings):
            def embed_documents(self, texts):
                return call_with_retry(
                    func=embedding_adapter.embed_documents,
                    max_retries=3,
                    fallback_return=[],
                    texts=texts
                )
            def embed_query(self, query: str):
                res = call_with_retry(
                    func=embedding_adapter.embed_query,
                    max_retries=3,
                    fallback_return=[],
                    query=query
                )
                return res

        chroma_embedding = LCEmbeddingWrapper()
        return Chroma(
            persist_directory=store_dir,
            embedding_function=chroma_embedding,
            client_settings=Settings(anonymized_telemetry=False),
            collection_name="novel_collection"
        )
    except Exception as e:
        logging.warning(f"Failed to load vector store: {e}")
        traceback.print_exc()
        return None

def split_by_length(text: str, max_length: int = 500):
    # Split text by max_length
    segments = []
    start_idx = 0
    while start_idx < len(text):
        end_idx = min(start_idx + max_length, len(text))
        segment = text[start_idx:end_idx]
        segments.append(segment.strip())
        start_idx = end_idx
    return segments


def split_text_for_vectorstore(chapter_text: str, max_length: int = 500, similarity_threshold: float = 0.7):
    # Split chapter text into segments for vector store insertion (NLTK optional).
    if not chapter_text or not str(chapter_text).strip():
        return []
    def _regex_sentences(t: str):
        parts = re.split(r"(?<=[銆傦紒锛?\?锛?锛?])\s+|\n+", t)
        return [p.strip() for p in parts if p and p.strip()]
    sentences = None
    if '_HAVE_NLTK' in globals() and _HAVE_NLTK:
        try:
            sentences = nltk.sent_tokenize(chapter_text)
        except Exception:
            sentences = _regex_sentences(chapter_text)
    else:
        sentences = _regex_sentences(chapter_text)
    if not sentences:
        return []
    final_segments = []
    current_segment = []
    current_length = 0
    for sentence in sentences:
        L = len(sentence)
        if current_length + L > max_length:
            if current_segment:
                final_segments.append(" ".join(current_segment))
            current_segment = [sentence]
            current_length = L
        else:
            current_segment.append(sentence)
            current_length += L
    if current_segment:
        final_segments.append(" ".join(current_segment))
    return final_segments

def update_vector_store(embedding_adapter, new_chapter: str, filepath: str):
    # Insert new chapter segments into the vector store (init if needed).
    # 閼汇儱绨辨稉宥呯摠閸︺劌鍨崚婵嗩潗閸栨牭绱遍懟銉ュ灥婵瀵?閺囧瓨鏌婃径杈Е閿涘苯鍨捄瀹犵箖閵?
    from utils import read_file, clear_file_content, save_string_to_txt
    splitted_texts = split_text_for_vectorstore(new_chapter)
    if not splitted_texts:
        logging.warning("No valid text to insert into vector store. Skipping.")
        return

    store = load_vector_store(embedding_adapter, filepath)
    if not store:
        logging.info("Vector store does not exist or failed to load. Initializing a new one for new chapter...")
        store = init_vector_store(embedding_adapter, splitted_texts, filepath)
        if not store:
            logging.warning("Init vector store failed, skip embedding.")
        else:
            logging.info("New vector store created successfully.")
        return

    try:
        docs = [Document(page_content=str(t)) for t in splitted_texts]
        store.add_documents(docs)
        logging.info("Vector store updated with the new chapter splitted segments.")
    except Exception as e:
        logging.warning(f"Failed to update vector store: {e}")
        traceback.print_exc()

def get_relevant_context_from_vector_store(embedding_adapter, query: str, filepath: str, k: int = 2, exclude_text: str | None = None) -> str:
    # 浠庡悜閲忓簱涓绱笌 query 鏈€鐩稿叧鐨?k 娈垫枃鏈紝鎷兼帴杩斿洖銆?
    # 鍙€?exclude_text锛氳嫢鎻愪緵锛屽垯浼氳繃婊ゆ帀涓庝箣瀹屽叏瀛愪覆鍖归厤鐨勭墖娈碉紙鐢ㄤ簬鎺掗櫎鈥滃綋鍓嶇珷鑺傚簾绋库€濓級銆?
    # 鏈€缁堜粎杩斿洖 <=2000 瀛楃鐨勬嫾鎺ユ枃鏈€?
    store = load_vector_store(embedding_adapter, filepath)
    if not store:
        logging.info("No vector store found or load failed. Returning empty context.")
        return ""

    try:
        docs = store.similarity_search(query, k=k)
        if not docs:
            logging.info(f"No relevant documents found for query '{query}'. Returning empty context.")
            return ""
        # 杩囨护褰撳墠绔犺妭鍙兘鐨勫簾绋匡紙鍚彂寮忥細瀹屽叏瀛愪覆鍖归厤锛?
        if exclude_text:
            try:
                excl = exclude_text
                filtered = []
                for d in docs:
                    pc = getattr(d, 'page_content', '') or ''
                    if pc and pc not in excl:
                        filtered.append(d)
                if filtered:
                    docs = filtered
            except Exception:
                pass
        combined = "\n".join([d.page_content for d in docs])
        if len(combined) > 2000:
            combined = combined[:2000]
        return combined
    except Exception as e:
        logging.warning(f"Similarity search failed: {e}")
        traceback.print_exc()
        return ""
def _get_sentence_transformer(model_name: str = 'paraphrase-MiniLM-L6-v2'):
    # Load sentence transformer model (handles SSL)
    try:
        # 鐠佸墽鐤唗orch閻滎垰顣ㄩ崣姗€鍣?
        os.environ["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "0"
        os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "0"
        
        # 缁備胶鏁SL妤犲矁鐦?
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # ...existing code...
    except Exception as e:
        logging.error(f"Failed to load sentence transformer model: {e}")
        traceback.print_exc()
        return None




def vector_store_is_empty(filepath: str) -> bool:
    store_dir = get_vectorstore_dir(filepath)
    if not os.path.isdir(store_dir):
        return True
    for _, _, files in os.walk(store_dir):
        if files:
            return False
    return True


def rebuild_vector_store_from_chapters(embedding_adapter, filepath: str) -> bool:
    """
    Rebuild the vector store from all existing chapter_*.txt under <filepath>/chapters
    Only runs when the store directory is missing or empty. Returns True on success.
    """
    try:
        store_dir = get_vectorstore_dir(filepath)
        # Only rebuild when empty / missing
        if os.path.isdir(store_dir):
            # if non-empty, do nothing
            for _, _, files in os.walk(store_dir):
                if files:
                    logging.info("Vector store already present; skip full rebuild.")
                    return False
        chapters_dir = os.path.join(filepath, 'chapters')
        if not os.path.isdir(chapters_dir):
            logging.info("Chapters directory not found; nothing to rebuild.")
            return False
        # Collect texts from all chapter_N.txt
        chapter_files = []
        for name in os.listdir(chapters_dir):
            if name.startswith('chapter_') and name.endswith('.txt') and name.count('_') == 1:
                try:
                    num = int(name.split('_')[1].split('.')[0])
                except Exception:
                    continue
                chapter_files.append((num, os.path.join(chapters_dir, name)))
        if not chapter_files:
            logging.info("No chapter files found for rebuild.")
            return False
        chapter_files.sort(key=lambda x: x[0])
        all_segments = []
        for _, full in chapter_files:
            try:
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    txt = f.read().strip()
                segs = split_text_for_vectorstore(txt)
                if segs:
                    all_segments.extend([Document(page_content=str(s)) for s in segs])
            except Exception:
                continue
        if not all_segments:
            logging.info("No valid text segments to embed.")
            return False
        # Initialize vector store once with first batch, then add the rest if needed
        from langchain.embeddings.base import Embeddings as LCEmbeddings
        class LCEmbeddingWrapper(LCEmbeddings):
            def embed_documents(self, texts):
                return call_with_retry(
                    func=embedding_adapter.embed_documents,
                    max_retries=3,
                    fallback_return=[],
                    texts=texts
                )
            def embed_query(self, query: str):
                return call_with_retry(
                    func=embedding_adapter.embed_query,
                    max_retries=3,
                    fallback_return=[],
                    query=query
                )
        chroma_embedding = LCEmbeddingWrapper()
        os.makedirs(store_dir, exist_ok=True)
        # Create store with first chunk to avoid too large single call
        first_chunk = all_segments[:200]
        rest = all_segments[200:]
        vectorstore = Chroma.from_documents(
            first_chunk,
            embedding=chroma_embedding,
            persist_directory=store_dir,
            client_settings=Settings(anonymized_telemetry=False),
            collection_name='novel_collection'
        )
        if rest:
            vectorstore.add_documents(rest)
        logging.info(f"Full vector store rebuilt from {len(chapter_files)} chapters, total segments: {len(all_segments)}")
        return True
    except Exception as e:
        logging.error(f"Full rebuild failed: {e}")
        traceback.print_exc()
        return False