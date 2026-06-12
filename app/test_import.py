import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modules.expertSystem.expert_engine_peisa import RADIATOR_MODELS
from app.app import replace_variables
from RAG_engine.query.rag_query_weber import search_weber
from RAG_engine.query.rag_llm_weber import answer_weber
from RAG_engine.query.rag_query_peisa import search_filtered
from RAG_engine.query.rag_llm_peisa import answer
print("SUCCESS")
