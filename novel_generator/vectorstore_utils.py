#novel_generator/vectorstore_utils.py
# -*- coding: utf-8 -*-
"""
鍚戦噺搴撶浉鍏虫搷浣滐紙鍒濆鍖栥€佹洿鏂般€佹绱€佹竻绌恒€佹枃鏈垏鍒嗙瓑锛?
"""
import os
import logging
import traceback
import nltk
import numpy as np
import re
import ssl
import requests
import warnings
from langchain_chroma import Chroma
logging.basicConfig(
    filename='app.log',      # 鏃ュ織鏂囦欢鍚?
    filemode='a',            # 杩藉姞妯″紡锛?w' 浼氳鐩栵級
    level=logging.INFO,      # 璁板綍 INFO 鍙婁互涓婄骇鍒殑鏃ュ織
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# 绂佺敤鐗瑰畾鐨凾orch璀﹀憡
warnings.filterwarnings('ignore', message='.*Torch was not compiled with flash attention.*')
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # 绂佺敤tokenizer骞惰璀﹀憡

from chromadb.config import Settings
from langchain.docstore.document import Document
from sklearn.metrics.pairwise import cosine_similarity
from .common import call_with_retry

def get_vectorstore_dir(filepath: str) -> str:
    """鑾峰彇 vectorstore 璺緞"""
    return os.path.join(filepath, "vectorstore")

def clear_vector_store(filepath: str) -> bool:
    """娓呯┖ 娓呯┖鍚戦噺搴?""
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
        logging.error(f"鏃犳硶鍒犻櫎鍚戦噺搴撴枃浠跺す锛岃鍏抽棴绋嬪簭鍚庢墜鍔ㄥ垹闄?{store_dir}銆俓n {str(e)}")
        traceback.print_exc()
        return False

def init_vector_store(embedding_adapter, texts, filepath: str):
    """
    鍦?filepath 涓嬪垱寤?鍔犺浇涓€涓?Chroma 鍚戦噺搴撳苟鎻掑叆 texts銆?
    濡傛灉Embedding澶辫触锛屽垯杩斿洖 None锛屼笉涓柇浠诲姟銆?
    """
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
    """
    璇诲彇宸插瓨鍦ㄧ殑 Chroma 鍚戦噺搴撱€傝嫢涓嶅瓨鍦ㄥ垯杩斿洖 None銆?
    濡傛灉鍔犺浇澶辫触锛坋mbedding 鎴朓O闂锛夛紝鍒欒繑鍥?None銆?
    """
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
    """鎸夌収 max_length 鍒囧垎鏂囨湰"""
    segments = []
    start_idx = 0
    while start_idx < len(text):
        end_idx = min(start_idx + max_length, len(text))
        segment = text[start_idx:end_idx]
        segments.append(segment.strip())
        start_idx = end_idx
    return segments

def split_text_for_vectorstore(chapter_text: str, max_length: int = 500, similarity_threshold: float = 0.7):
    """
    瀵规柊鐨勭珷鑺傛枃鏈繘琛屽垎娈靛悗,鍐嶇敤浜庡瓨鍏ュ悜閲忓簱銆?
    浣跨敤 embedding 杩涜鏂囨湰鐩镐技搴﹁绠椼€?
    """
    if not chapter_text.strip():
        return []
    
    # nltk.download('punkt', quiet=True)
    # nltk.download('punkt_tab', quiet=True)
    sentences = nltk.sent_tokenize(chapter_text)
    if not sentences:
        return []
    
    # 鐩存帴鎸夐暱搴﹀垎娈?涓嶅仛鐩镐技搴﹀悎骞?
    final_segments = []
    current_segment = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > max_length:
            if current_segment:
                final_segments.append(" ".join(current_segment))
            current_segment = [sentence]
            current_length = sentence_length
        else:
            current_segment.append(sentence)
            current_length += sentence_length
    
    if current_segment:
        final_segments.append(" ".join(current_segment))
    
    return final_segments

def update_vector_store(embedding_adapter, new_chapter: str, filepath: str):
    """
    灏嗘渶鏂扮珷鑺傛枃鏈彃鍏ュ埌鍚戦噺搴撲腑銆?
    鑻ュ簱涓嶅瓨鍦ㄥ垯鍒濆鍖栵紱鑻ュ垵濮嬪寲/鏇存柊澶辫触锛屽垯璺宠繃銆?
    """
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
    """
    从向量库中检索与 query 最相关的 k 段文本，拼接返回。
    可选 exclude_text：若提供，则会过滤掉与之完全子串匹配的片段（用于排除“当前章节废稿”）。
    最终仅返回 <=2000 字符的拼接文本。
    """
    store = load_vector_store(embedding_adapter, filepath)
    if not store:
        logging.info("No vector store found or load failed. Returning empty context.")
        return ""

    try:
        docs = store.similarity_search(query, k=k)
        if not docs:
            logging.info(f"No relevant documents found for query '{query}'. Returning empty context.")
            return ""
        # 过滤当前章节可能的废稿（启发式：完全子串匹配）
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
    """鑾峰彇sentence transformer妯″瀷锛屽鐞哠SL闂"""
    try:
        # 璁剧疆torch鐜鍙橀噺
        os.environ["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "0"
        os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "0"
        
        # 绂佺敤SSL楠岃瘉
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # ...existing code...
    except Exception as e:
        logging.error(f"Failed to load sentence transformer model: {e}")
        traceback.print_exc()
        return None

