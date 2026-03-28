#novel_generator/finalization.py
# -*- coding: utf-8 -*-
"""
瀹氱绔犺妭鍜屾墿鍐欑珷鑺傦紙finalize_chapter銆乪nrich_chapter_text锛?
"""
import os
import logging
from llm_adapters import create_llm_adapter
from embedding_adapters import create_embedding_adapter
from prompt_definitions import summary_prompt, update_character_state_prompt
from novel_generator.common import invoke_with_cleaning
from utils import read_file, clear_file_content, save_string_to_txt
from novel_generator.vectorstore_utils import index_chapter_version
logging.basicConfig(
    filename='app.log',      # 鏃ュ織鏂囦欢鍚?
    filemode='a',            # 杩藉姞妯″紡锛?w' 浼氳鐩栵級
    level=logging.INFO,      # 璁板綍 INFO 鍙婁互涓婄骇鍒殑鏃ュ織
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
def finalize_chapter(
    novel_number: int,
    word_number: int,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    filepath: str,
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    interface_format: str,
    max_tokens: int,
    timeout: int = 600
):
    """
    瀵规寚瀹氱珷鑺傚仛鏈€缁堝鐞嗭細鏇存柊鍓嶆枃鎽樿銆佹洿鏂拌鑹茬姸鎬併€佹彃鍏ュ悜閲忓簱绛夈€?
    榛樿鏃犻渶鍐嶅仛鎵╁啓鎿嶄綔锛岃嫢鏈夐渶瑕佸彲鍦ㄥ閮ㄨ皟鐢?enrich_chapter_text 澶勭悊鍚庡啀瀹氱銆?
    """
    chapters_dir = os.path.join(filepath, "chapters")
    chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number}.txt")
    chapter_text = read_file(chapter_file).strip()
    if not chapter_text:
        logging.warning(f"Chapter {novel_number} is empty, cannot finalize.")
        return

    global_summary_file = os.path.join(filepath, "global_summary.txt")
    old_global_summary = read_file(global_summary_file)
    character_state_file = os.path.join(filepath, "character_state.txt")
    old_character_state = read_file(character_state_file)

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )

    prompt_summary = summary_prompt.format(
        chapter_text=chapter_text,
        global_summary=old_global_summary
    )
    new_global_summary = invoke_with_cleaning(llm_adapter, prompt_summary)
    if not new_global_summary.strip():
        new_global_summary = old_global_summary

    prompt_char_state = update_character_state_prompt.format(
        chapter_text=chapter_text,
        old_state=old_character_state
    )
    new_char_state = invoke_with_cleaning(llm_adapter, prompt_char_state)
    if not new_char_state.strip():
        new_char_state = old_character_state

    clear_file_content(global_summary_file)
    save_string_to_txt(new_global_summary, global_summary_file)
    clear_file_content(character_state_file)
    save_string_to_txt(new_char_state, character_state_file)

    index_chapter_version(
        embedding_adapter=create_embedding_adapter(
            embedding_interface_format,
            embedding_api_key,
            embedding_url,
            embedding_model_name
        ),
        chapter_number=novel_number,
        chapter_text=chapter_text,
        filepath=filepath
    )

    logging.info(f"Chapter {novel_number} has been finalized.")

    try:
        from novel_generator.character_integration import process_chapter_for_characters
        logging.info(f"[角色库] Finalize Hook: 开始从第{novel_number}章抽取角色…")
        cnt = process_chapter_for_characters(chapter_text, novel_number, filepath)
        logging.info(f"[角色库] Finalize Hook: 已写入 {cnt} 个角色增量")
    except Exception as e:
        logging.warning(f"[角色库] Finalize Hook 失败: err={e}")
def enrich_chapter_text(
    chapter_text: str,
    word_number: int,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    interface_format: str,
    max_tokens: int,
    timeout: int=600
) -> str:
    """
    瀵圭珷鑺傛枃鏈繘琛屾墿鍐欙紝浣垮叾鏇存帴杩?word_number 瀛楁暟锛屼繚鎸佸墽鎯呰繛璐€?
    """
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout
    )
    prompt = f"""\
浠ヤ笅鏄渶瑕佹墿鍐欑殑绔犺妭姝ｆ枃锛岃鍦ㄤ繚鎸侀鏍间笌杩炶疮鎬х殑鍓嶆彁涓嬬粏鍖栧唴瀹癸紝浣垮叾鏇村姞瀹屾暣锛岀洰鏍囨帴杩?{word_number} 瀛椼€傜洿鎺ヨ繑鍥炴墿鍐欏悗鐨勬鏂囷細
鍘熸枃锛?
{chapter_text}
"""
    enriched_text = invoke_with_cleaning(llm_adapter, prompt)
    return enriched_text if enriched_text else chapter_text
