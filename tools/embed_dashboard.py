# tools/embed_dashboard.py
# -*- coding: utf-8 -*-
"""
Streamlit 向量工作台（检索入口 + 可视化 + 维护）
启动：
  streamlit run tools/embed_dashboard.py
依赖：streamlit, plotly；可选：umap-learn（无则回退到 TSNE）
"""
from __future__ import annotations
import os, json, time
import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Any, Dict, List
from sklearn.manifold import TSNE
try:
    import umap.umap_ as umap  # type: ignore
except Exception:
    umap = None

# 项目内部依赖
from config_manager import load_config
from embedding_adapters import create_embedding_adapter
from novel_generator.vectorstore_utils import (
    load_vector_store,
    clear_vector_store,
    rebuild_vector_store_from_chapters,
    vector_store_is_empty,
    get_vectorstore_dir,
    load_manifest,
)

st.set_page_config(page_title='Embedding 工作台', page_icon='📊', layout='wide')

# ------------------------------ 工具函数 ------------------------------

def _load_default_filepath() -> str:
    try:
        cfg = load_config('config.json')
        return (cfg.get('other_params', {}) or {}).get('filepath', '').strip()
    except Exception:
        return ''

def _load_default_embedding_cfg() -> Dict[str, Any]:
    cfg = load_config('config.json') or {}
    last_if = cfg.get('last_embedding_interface_format')
    embs = cfg.get('embedding_configs', {}) or {}
    if last_if and last_if in embs:
        return { 'name': last_if, **embs[last_if] }
    # fallback: 第一个
    if embs:
        name, item = next(iter(embs.items()))
        return { 'name': name, **item }
    # safe default
    return { 'name': 'OpenAI', 'api_key': '', 'base_url': 'https://api.openai.com/v1', 'model_name': 'text-embedding-3-small', 'retrieval_k': 4, 'interface_format': 'OpenAI' }

@st.cache_resource(show_spinner=False)
def _make_adapter(interface_format: str, api_key: str, base_url: str, model_name: str):
    return create_embedding_adapter(interface_format.strip(), api_key.strip(), base_url.strip(), model_name.strip())

@st.cache_resource(show_spinner=False)
def _open_store(adapter, filepath: str):
    return load_vector_store(adapter, filepath)

def _progress_logger() -> Any:
    ph = st.empty()
    buf: List[str] = []
    def log(msg: str):
        buf.append(str(msg))
        ph.code('\n'.join(buf[-200:]), language='text')
    return log

def _collection_stats(store) -> Dict[str, Any]:
    try:
        size = store._collection.count()  # type: ignore
        return { 'size': size, 'ok': True }
    except Exception as e:
        return { 'size': 0, 'ok': False, 'err': str(e) }

# ------------------------------ 侧边栏 ------------------------------
with st.sidebar:
    st.header('配置')
    default_fp = _load_default_filepath()
    project_path = st.text_input('保存路径（项目根）', value=default_fp, placeholder='例如：F:/AI_NovelGenerator_workspace')
    emb_cfg = _load_default_embedding_cfg()
    col_if, col_model = st.columns([1,1])
    with col_if:
        interface_format = st.text_input('接口类型', value=str(emb_cfg.get('interface_format','')))
    with col_model:
        model_name = st.text_input('模型名称', value=str(emb_cfg.get('model_name','')))
    base_url = st.text_input('Base URL', value=str(emb_cfg.get('base_url','')))
    api_key = st.text_input('API Key', value=str(emb_cfg.get('api_key','')), type='password')
    retrieval_k = st.number_input('Top-K（默认检索条数）', min_value=1, max_value=50, value=int(emb_cfg.get('retrieval_k',4)))
    st.divider()
    st.caption('维护操作（作用于上方“保存路径”）')
    do_clear = st.button('🧹 清空向量库', use_container_width=True)
    do_rebuild = st.button('🧱 全量重建向量库', use_container_width=True)

# 连接向量库
st.title('📊 Embedding 工作台')
if not project_path:
    st.warning('请先在左侧设置“保存路径（项目根）”。')
    st.stop()

adapter = _make_adapter(interface_format, api_key, base_url, model_name)
store = _open_store(adapter, project_path)
store_dir = get_vectorstore_dir(project_path)

# 维护区
if do_clear:
    st.subheader('清空向量库')
    log = _progress_logger()
    with st.spinner('正在清空向量库...'):
        ok = clear_vector_store(project_path, progress_cb=log)
    if ok:
        st.success('已清空。按钮将回到主应用中刷新为“重建向量库”。')
    else:
        st.info('目录不存在或已为空。')

if do_rebuild:
    st.subheader('全量重建向量库')
    log = _progress_logger()
    with st.spinner('正在重建（请稍候）...'):
        ok = rebuild_vector_store_from_chapters(adapter, project_path, progress_cb=log)
    if ok:
        st.success('重建完成。')
    else:
        st.info('未执行（可能向量库非空或未找到章节）。')

# 概览
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric('向量目录', store_dir)
with col_b:
    st.metric('是否为空', '是' if vector_store_is_empty(project_path) else '否')
with col_c:
    stats = _collection_stats(store) if store else {'size':0,'ok':False}
    st.metric('向量条目数', stats.get('size',0))

# ------------------------------ 检索入口 ------------------------------
st.subheader('🔎 相似检索')
q = st.text_input('Query（支持中文/英文）', value='')
col1, col2, col3 = st.columns([1,1,1])
with col1:
    topk = st.slider('Top-K', min_value=1, max_value=20, value=retrieval_k)
with col2:
    max_chap = st.number_input('章节上限（≤）', min_value=0, value=0, help='0=不限；用于避免命中“未来章节”的内容')
with col3:
    include_inactive = st.checkbox('包含未标注 active 的片段（知识导入等）', value=False)

if st.button('执行检索', disabled=(not q)):
    if not store:
        st.error('未能加载向量库，请检查保存路径或先重建。')
    else:
        flt: Dict[str, Any] = { 'active': True } if not include_inactive else {}
        if max_chap and isinstance(max_chap, int) and max_chap > 0:
            flt['chapter'] = { '$lte': int(max_chap) }
        try:
            pairs = store.similarity_search_with_score(q, k=topk, filter=flt)  # type: ignore
            rows = []
            for doc, score in pairs:
                md = getattr(doc, 'metadata', {}) or {}
                rows.append({
                    'score': float(score),
                    'chapter': md.get('chapter'),
                    'version': md.get('chapter_version'),
                    'segment_idx': md.get('segment_idx'),
                    'active': md.get('active'),
                    'text': getattr(doc, 'page_content','')[:400].replace('\n',' ')
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=280)
        except Exception as e:
            st.exception(e)

# ------------------------------ 可视化 ------------------------------
st.subheader('🗺️ 向量分布可视化（降维）')
if not store:
    st.info('未找到向量库，无法可视化。')
else:
    colf1, colf2, colf3 = st.columns([1,1,1])
    with colf1:
        method = st.selectbox('降维方法', options=['UMAP(优先)','TSNE(备用)'])
    with colf2:
        color_by = st.selectbox('着色字段', options=['chapter','chapter_version','active'])
    with colf3:
        max_points = st.slider('采样上限', min_value=200, max_value=10000, value=3000, step=200)
    colr1, colr2 = st.columns(2)
    with colr1:
        min_ch = st.number_input('章节起', min_value=0, value=0)
    with colr2:
        max_ch = st.number_input('章节止(0=不限)', min_value=0, value=0)
    where: Dict[str, Any] = {}
    if not include_inactive:
        where['active'] = True
    if min_ch and (max_ch and max_ch>=min_ch):
        where['chapter'] = { '$gte': int(min_ch), '$lte': int(max_ch) }
    elif min_ch and not max_ch:
        where['chapter'] = { '$gte': int(min_ch) }
    elif (not min_ch) and max_ch:
        where['chapter'] = { '$lte': int(max_ch) }

    btn = st.button('生成分布图')
    if btn:
        with st.spinner('读取向量并降维绘图...'):
            try:
                coll = store._collection  # type: ignore
                total = coll.count()
                limit = int(min(max_points, total))
                # 直接用 where 过滤；若 total 很大，可进一步分页
                out = coll.get(include=['embeddings','metadatas'], where=(where or None), limit=limit)
                embs = out.get('embeddings') or []
                metas = out.get('metadatas') or []
                if not embs:
                    st.warning('没有可用的向量数据。')
                else:
                    import numpy as np
                    X = np.asarray(embs, dtype='float32')
                    if method.startswith('UMAP') and umap is not None:
                        reducer = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, metric='cosine', random_state=42)
                        Z = reducer.fit_transform(X)
                    else:
                        Z = TSNE(n_components=2, perplexity=30, learning_rate='auto', init='random', metric='cosine', random_state=42).fit_transform(X)
                    df = pd.DataFrame({
                        'x': Z[:,0],
                        'y': Z[:,1],
                        color_by: [ (m or {}).get(color_by) for m in metas ],
                        'chapter': [ (m or {}).get('chapter') for m in metas ],
                        'version': [ (m or {}).get('chapter_version') for m in metas ],
                        'active': [ (m or {}).get('active') for m in metas ],
                    })
                    fig = px.scatter(df, x='x', y='y', color=color_by, hover_data=['chapter','version','active'], render_mode='webgl', title='向量降维散点图')
                    st.plotly_chart(fig, use_container_width=True, theme='streamlit')
            except Exception as e:
                st.exception(e)

# ------------------------------ 导出 ------------------------------
st.subheader('⬇️ 导出/检查')
left, right = st.columns(2)
with left:
    if st.button('导出 manifest.json'):
        try:
            data = load_manifest(project_path)
            st.download_button('下载 manifest.json', data=json.dumps(data, ensure_ascii=False, indent=2), file_name='manifest.json', mime='application/json')
        except Exception as e:
            st.exception(e)
with right:
    if st.button('导出 Embeddings（TSV）'):
        try:
            coll = store._collection  # type: ignore
            out = coll.get(include=['embeddings','metadatas','documents'])
            import io
            buf = io.StringIO()
            buf.write('chapter\tversion\tsegment_idx\tactive\ttext\tembedding\n')
            for emb, md, doc in zip(out.get('embeddings') or [], out.get('metadatas') or [], out.get('documents') or []):
                md = md or {}
                line = f"{md.get('chapter','')}\t{md.get('chapter_version','')}\t{md.get('segment_idx','')}\t{md.get('active','')}\t{(doc or '').replace('\t',' ').replace('\n',' ')}\t{','.join(map(str,emb))}\n"
                buf.write(line)
            st.download_button('下载 embeddings.tsv', data=buf.getvalue(), file_name='embeddings.tsv', mime='text/tab-separated-values')
        except Exception as e:
            st.exception(e)

st.caption('提示：工作台直接读取/操作当前保存路径下的 vectorstore，与主程序保持一致；不会改变章节文本。')
