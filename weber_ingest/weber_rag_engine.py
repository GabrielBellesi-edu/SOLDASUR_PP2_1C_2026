"""
weber_rag_engine.py  –  Motor RAG para productos Weber (Paso 3)
===============================================================
Módulo equivalente al rag_engine_v2.py de PEISA pero para Weber.
Expone:
  - search_weber(query, top_k)  → lista de productos relevantes
  - calcular_cantidad(producto, superficie_m2) → dict con bolsas y costo estimado
  - answer_weber(query, context) → respuesta generada por Ollama

Integración: importar desde app/modules/chatbot/ igual que rag_engine_v2.py
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

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


# ── Rutas (ajustar según la estructura del proyecto) ──────────────────────────
FAISS_PATH = "embeddings/weber_products.faiss"
META_PATH  = "embeddings/weber_metadata.json"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

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
            _index = faiss.read_index(FAISS_PATH)
            with open(META_PATH, encoding="utf-8") as f:
                _metadata = json.load(f)
            print(f"[WeberRAG] Índice cargado: {_index.ntotal} productos Weber")
        else:
            print(f"[WeberRAG] AVISO: No se encontró {FAISS_PATH}")
            print("           Ejecutar primero: python 02_build_embeddings.py")


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

    Args:
        producto: Dict del producto (debe tener campo 'rendimiento')
        superficie_m2: Superficie a cubrir en m²

    Returns:
        Dict con: bolsas_necesarias, rendimiento_por_bolsa, descripcion_calculo
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


# ── Generación de respuesta con Ollama ───────────────────────────────────────

SYSTEM_PROMPT_WEBER = """Sos un asesor técnico de SOLDASUR especializado en productos Weber (Saint-Gobain) para construcción y reforma.

Tu función es recomendar productos Weber adecuados para la necesidad del cliente.

Reglas:
- Respondé siempre en español rioplatense (Argentina).
- Mencioná siempre al menos un producto Weber por su nombre comercial exacto.
- Sé conciso y técnico pero comprensible para alguien sin experiencia en construcción.
- Si el cliente menciona una superficie, calculá la cantidad de bolsas necesarias.
- Si no sabés el precio, decí que consultén en el local.
- No inventes características que no estén en el contexto provisto.
- Máximo 4 oraciones de respuesta."""


def answer_weber(
    query: str,
    context_products: List[Dict[str, Any]],
    superficie_m2: Optional[float] = None
) -> str:
    """
    Genera una respuesta usando Ollama con los productos Weber como contexto.

    Args:
        query: Pregunta del usuario
        context_products: Lista de productos relevantes del RAG
        superficie_m2: Si el usuario mencionó superficie, para calcular cantidades

    Returns:
        String con la respuesta generada
    """
    if not context_products:
        return "No encontré productos Weber para tu consulta. Podés consultar el catálogo completo en ar.weber.com."

    # Construir contexto de productos
    context_lines = []
    for p in context_products[:3]:  # Top 3 productos
        linea = f"- {p.get('model','')}: {p.get('description','')}"
        if p.get("rendimiento"):
            linea += f" | Rendimiento: {p['rendimiento']}"
        if p.get("presentacion"):
            linea += f" | Presentación: {p['presentacion']}"
        context_lines.append(linea)

    # Agregar cálculo de cantidades si se especificó superficie
    calculo_texto = ""
    if superficie_m2 and superficie_m2 > 0:
        calculo = calcular_cantidad(context_products[0], superficie_m2)
        calculo_texto = f"\nCálculo: {calculo['descripcion_calculo']}"

    prompt = f"""Productos Weber relevantes:
{chr(10).join(context_lines)}
{calculo_texto}

Consulta del cliente: {query}

Respuesta:"""

    if not REQUESTS_OK:
        return _format_fallback_response(context_products, superficie_m2)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "system": SYSTEM_PROMPT_WEBER,
                "stream": False,
                "options": {"num_predict": 200, "temperature": 0.3}
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception as e:
        print(f"[WeberRAG] Error Ollama: {e}")

    return _format_fallback_response(context_products, superficie_m2)


def _format_fallback_response(
    products: List[Dict[str, Any]],
    superficie_m2: Optional[float] = None
) -> str:
    """Respuesta de fallback cuando Ollama no está disponible."""
    if not products:
        return "No encontré productos para tu consulta."

    p = products[0]
    resp = f"Para tu consulta, te recomiendo **{p.get('model','')}**: {p.get('description','')}"

    if superficie_m2 and superficie_m2 > 0:
        calculo = calcular_cantidad(p, superficie_m2)
        resp += f"\n{calculo['descripcion_calculo']}"

    return resp


# ── Función principal de integración ─────────────────────────────────────────

def search_and_answer(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Función de alto nivel: busca productos y genera respuesta.
    Equivalente al search_filtered() + answer() de PEISA.

    Detecta automáticamente si el usuario mencionó una superficie.
    """
    # Detectar superficie en la consulta
    superficie_m2 = _extract_superficie(query)

    # Buscar productos relevantes
    productos = search_weber(query, top_k)

    # Generar respuesta
    respuesta = answer_weber(query, productos, superficie_m2)

    return {
        "respuesta": respuesta,
        "productos": productos[:3],
        "superficie_detectada": superficie_m2,
        "calculo": calcular_cantidad(productos[0], superficie_m2) if productos and superficie_m2 else None,
        "marca": "Weber"
    }


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
