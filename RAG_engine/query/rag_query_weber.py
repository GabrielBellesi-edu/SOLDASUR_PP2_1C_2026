"""
weber_rag_query.py – Buscador vectorial (Retriever) para productos Weber.
"""

import json
import re
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import faiss
    FAISS_OK = True
except ImportError:
    FAISS_OK = False

try:
    from sentence_transformers import SentenceTransformer
    ST_OK = True
except ImportError:
    ST_OK = False


# ── Rutas ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
FAISS_PATH = SCRIPT_DIR.parent / "database" / "products_weber.faiss"
META_PATH  = SCRIPT_DIR.parent / "database" / "metadata_weber.json"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ── Singleton del modelo (carga una sola vez) ─────────────────────────────────
_model = None
_index = None
_metadata = None


def _load_resources():
    """Carga el modelo y el índice FAISS (lazy loading)."""
    global _model, _index, _metadata

    if _model is None and ST_OK:
        print("[WeberRAG] Cargando modelo de embeddings...")
        _model = SentenceTransformer(MODEL_NAME)

    if _index is None and FAISS_OK:
        if Path(FAISS_PATH).exists():
            _index = faiss.read_index(str(FAISS_PATH))
            with open(META_PATH, encoding="utf-8") as f:
                _metadata = json.load(f)
            print(f"[WeberRAG] Índice cargado: {_index.ntotal} productos Weber")
        else:
            print(f"[WeberRAG] AVISO: No se encontró {FAISS_PATH}")


def search_weber(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Busca productos Weber relevantes para la consulta.
    Retorna lista de dicts con información del producto y score de similitud.
    """
    _load_resources()

    if _model is None or _index is None:
        return _fallback_search(query, top_k)

    # Generar embedding de la consulta
    query_vec = _model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_vec)

    # Buscar en el índice
    scores, indices = _index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        product = _metadata[idx].copy()
        product["similarity_score"] = float(score)
        results.append(product)

    return results


def _fallback_search(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Búsqueda por texto simple si FAISS no está disponible."""
    if _metadata is None:
        try:
            with open(META_PATH, encoding="utf-8") as f:
                meta = json.load(f)
        except FileNotFoundError:
            return []
    else:
        meta = _metadata

    query_lower = query.lower()
    scored = []
    for product in meta:
        text = f"{product.get('model','')} {product.get('description','')} {product.get('category','')}".lower()
        score = sum(1 for word in query_lower.split() if word in text)
        if score > 0:
            p = product.copy()
            p["similarity_score"] = score
            scored.append(p)

    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:top_k]


# ── Calculadora de cantidades ─────────────────────────────────────────────────

def calcular_cantidad(producto: Dict[str, Any], superficie_m2: float) -> Dict[str, Any]:
    """
    Calcula la cantidad de bolsas necesarias para cubrir una superficie.
    """
    rendimiento_raw = producto.get("rendimiento", "")
    presentacion = producto.get("presentacion", "25 kg")

    # Intentar extraer m² por bolsa del campo rendimiento
    m2_por_bolsa = _parse_rendimiento(rendimiento_raw)

    if m2_por_bolsa and m2_por_bolsa > 0:
        bolsas = superficie_m2 / m2_por_bolsa
        bolsas_redondeadas = int(bolsas) + (1 if bolsas % 1 > 0 else 0)
        return {
            "producto": producto.get("model", ""),
            "superficie_m2": superficie_m2,
            "rendimiento_por_bolsa": f"{m2_por_bolsa} m² por bolsa",
            "bolsas_necesarias": bolsas_redondeadas,
            "presentacion": presentacion,
            "descripcion_calculo": (
                f"Para {superficie_m2} m² de {producto.get('model','')}, "
                f"con un rendimiento de {m2_por_bolsa} m² por bolsa de {presentacion}, "
                f"necesitás {bolsas_redondeadas} bolsa{'s' if bolsas_redondeadas > 1 else ''}."
            ),
            "calculo_exitoso": True,
        }

    # Si no pudo parsear el rendimiento
    return {
        "producto": producto.get("model", ""),
        "superficie_m2": superficie_m2,
        "rendimiento_por_bolsa": rendimiento_raw or "no especificado",
        "bolsas_necesarias": None,
        "presentacion": presentacion,
        "descripcion_calculo": (
            f"Para calcular la cantidad exacta de {producto.get('model','')}, "
            f"consultá el rendimiento en la ficha técnica del producto. "
            f"La presentación es de {presentacion}."
        ),
        "calculo_exitoso": False,
    }


def _parse_rendimiento(texto: str) -> Optional[float]:
    """Extrae el valor numérico de m² por bolsa de un texto de rendimiento."""
    if not texto:
        return None

    patrones = [
        r'(\d+[\.,]?\d*)\s*m[²2]\s*(?:aprox\.?\s*)?(?:por|x)\s*bolsa',
        r'(\d+[\.,]?\d*)\s*m[²2]',
        r'(\d+)\s*m2',
    ]
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                continue
    return None


def calcular_multiples_productos(
    productos: List[Dict[str, Any]],
    superficie_m2: float
) -> List[Dict[str, Any]]:
    """Calcula cantidades para una lista de productos."""
    return [calcular_cantidad(p, superficie_m2) for p in productos]


def _extract_superficie(query: str) -> Optional[float]:
    """Extrae la superficie mencionada en la consulta del usuario."""
    patrones = [
        r'(\d+[\.,]?\d*)\s*m[²2]',
        r'(\d+[\.,]?\d*)\s*metros?\s*cuadrados?',
        r'(\d+[\.,]?\d*)\s*m2',
    ]
    for patron in patrones:
        match = re.search(patron, query, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                continue
    return None
