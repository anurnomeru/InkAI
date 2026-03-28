#novel_generator/__init__.py
from .architecture import Novel_architecture_generate
from .blueprint import Chapter_blueprint_generate
from .chapter import (
    get_last_n_chapters_text,
    summarize_recent_chapters,
    get_filtered_knowledge_context,
    build_chapter_prompt,
    generate_chapter_draft
)
from .finalization import finalize_chapter, enrich_chapter_text
from .knowledge import import_knowledge_file
from .vectorstore_utils import clear_vector_store
from .character_store import (
    ensure_structure,
    save_manual, load_manual, list_manual,
    save_auto, list_auto,
    build_effective, build_effective_all,
)




