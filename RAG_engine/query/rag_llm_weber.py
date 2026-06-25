"""
rag_llm_weber.py – Generador RAG / LLM para productos Weber.
"""

import requests
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .rag_query_weber import search_weber, calcular_cantidad, _extract_superficie

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def _load_configured_model() -> str:
    """Carga el modelo configurado en configs/models.json con fallback a llama3.2:3b"""
    models_path = Path(__file__).resolve().parent.parent.parent / "configs" / "models.json"
    if models_path.exists():
        try:
            with open(models_path, "r", encoding="utf-8") as f:
                return json.load(f).get("ollama_model", "llama3.2:3b")
        except Exception:
            pass
    return "llama3.2:3b"

# Estandarizamos el System Prompt por defecto (fallback)
SYSTEM_PROMPT_WEBER_DEFAULT = """Sos Soldy, asesor técnico de SOLDASUR especializado en productos Weber (Saint-Gobain) para construcción y reforma. Tu función es recomendar productos Weber adecuados para la necesidad del cliente, hablando siempre en representación de SOLDASUR.

REGLAS OBLIGATORIAS:
1. RESPONDÉ en español argentino (rioplatense) natural y profesional. Usá el voseo ('vos', 'tenés', 'podés') de forma gramaticalmente correcta.
2. NUNCA uses lunfardo, vocativos informales o modismos callejeros como 'Che', 'mirá', 'chequeá', etc. Tampoco abuses de exclamaciones informales.
3. EVITÁ errores de conjugación (NUNCA digas 'si tenés consultando', 'tenés interesado' o 'tenés acá para ayudar'; decí 'si estás consultando', 'si te interesa' o 'estoy acá para ayudarte').
4. RESPONDÉ directamente a la consulta del usuario. NUNCA vuelvas a saludar (como 'Hola', 'Buen día') ni te presentes como 'Soldy' si la conversación ya se inició. Responde directo al grano técnico/comercial.
5. MENCIONÁ siempre al menos un producto Weber del catálogo por su nombre comercial exacto.
6. RESPUESTAS MUY BREVES: Máximo 2 o 3 oraciones cortas (40-50 palabras en total) y directas al grano, sin rodeos comerciales largos.
7. Si preguntan precio, decí que consulten en el local.
8. EVITÁ ALUCINAR COLORES: Si no se especifican explícitamente los colores en el contexto de productos del catálogo (el array de colores está vacío), NUNCA inventes nombres de colores (como tonos pastel, beige, verde, etc.). En su lugar, respondé que el producto viene en colores estándar listos (como blanco o gris, si corresponde) y una amplia gama de tonos a elección preparados por sistema tintométrico, sugiriendo consultar la carta física de colores de SOLDASUR en el local.
9. ORTOGRAFÍA Y TERMINOLOGÍA: Escribí siempre con ortografía perfecta en español. Usá el término técnico de construcción argentino 'revoque' (o 'revestimiento') en lugar del término español/portugués 'revoco'. Asegurá la correcta acentuación y escritura de palabras clave como 'manual' (NUNCA digas 'manuel').
10. TEXTO PLANO ÚNICAMENTE: NUNCA uses formato Markdown ni ningún tipo de marcado. Está PROHIBIDO usar asteriscos (**negrita**, *cursiva*), almohadillas (# títulos), guiones de lista (- ítem), backticks (`código`) o cualquier otro símbolo de marcado. Escribí siempre en texto plano corrido, como si fuera una conversación hablada.

CUÁNTOS PRODUCTOS RECOMENDAR:
- Por defecto: 1 solo producto (el más adecuado para la consulta).
- Máximo 2 productos: SOLO si el usuario pide explícitamente 'opciones', 'alternativas' o 'qué más hay'.
- NUNCA recomendés 3 o más productos en una consulta específica. Si el contexto trae varios productos, elegí el MÁS RELEVANTE para la consulta y mencioná solo ese.

EJEMPLOS CORRECTOS (CÓMO DEBÉS RESPONDER):
Usuario: "¿qué productos tiene weber para impermeabilizar?"
Soldy: "Para impermeabilizar te recomiendo weber.tec impermeable cerámicos con ceresita, ideal para losas, baños y piletas. Si me decís los metros cuadrados, calculo la cantidad de bolsas."

Usuario: "necesito pegar cerámicos en el baño"
Soldy: "Para el baño te recomiendo weber impermeable cerámicos con ceresita, ya que está formulado para soportar la humedad y evitar filtraciones. Si me indicás los metros cuadrados, calculo la cantidad de bolsas necesarias."

Usuario: "¿en qué colores viene el weberplast llaneado?"
Soldy: "El weberplast llaneado viene en colores estándar listos y en una gran variedad de tonos preparados a elección por sistema tintométrico. Te sugiero pasar por el local de SOLDASUR para ver la carta física de colores."

Usuario: "¿qué opciones tengo para pegar porcellanato?"
Soldy: "Tenés dos opciones: weber flex porcellanato para juntas anchas y movimiento, o weber gris cerámicos para aplicaciones estándar. Ambas se consiguen en SOLDASUR."

EJEMPLOS INCORRECTOS (NUNCA HAGAS ESTO):
- "Hola! Soy Soldy. Contamos con..." (Prohibido volver a saludar o presentarse).
- "Che! Si tenés consultando qué productos tenemos..." (Prohibido empezar con 'Che' y mala conjugación).
- "Mirá, te comento que tenemos..." (Prohibido usar 'mirá').
- "Tenés acá para ayudarte..." (Mala gramática, usar 'estoy acá para ayudarte').
- Listar 3 productos cuando la consulta es específica (NUNCA hagas esto)."""


def _load_prompt_config() -> Dict[str, Any]:
    """Carga la configuración de prompts del archivo configs/prompts.json."""
    config_path = Path(__file__).resolve().parent.parent.parent / "configs" / "prompts.json"
    
    # Valores por defecto de fallback
    default_config = {
        "system_prompt": SYSTEM_PROMPT_WEBER_DEFAULT,
        "temperature": 0.3,
        "max_tokens": 200
    }
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("weber", default_config)
        except Exception as e:
            print(f"[WeberRAG] Error cargando configs/prompts.json ({e}). Usando fallback.")
    return default_config


def answer_weber(
    query: str,
    context_products: List[Dict[str, Any]],
    superficie_m2: Optional[float] = None,
    last_active_product: Optional[str] = None
) -> str:
    """
    Genera una respuesta usando Ollama con los productos Weber como contexto.
    """
    if not context_products:
        return "No encontré productos Weber para tu consulta. Podés consultar el catálogo completo en ar.weber.com."

    # Construir contexto de productos: usar solo los 2 más relevantes para
    # evitar que el LLM mencione un tercero poco relacionado con la consulta.
    context_lines = []
    for p in context_products[:2]:  # Top 2 productos
        desc = p.get("descripcion_larga") or p.get("description") or ""
        linea = f"- {p.get('model','')}: {desc}"
        if p.get("pdf_text_snippet"):
            linea += f" | Detalles técnicos: {p['pdf_text_snippet']}"
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
"""
    if last_active_product:
        prompt += f"\nContexto de conversación: El usuario acaba de recibir una recomendación sobre el producto '{last_active_product}' (o estaba hablando de él). Si la consulta del cliente es una pregunta de seguimiento (como colores, rendimiento, secado, precio, etc.), responde asumiendo que se refiere a este producto."

    prompt += f"\nConsulta del cliente: {query}\n\nRespuesta:"

    # Cargar prompts y configuraciones parametrizadas
    config = _load_prompt_config()
    model = _load_configured_model()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "system": config.get("system_prompt", SYSTEM_PROMPT_WEBER_DEFAULT),
                "stream": False,
                "options": {
                    "num_predict": config.get("max_tokens", 250),
                    "temperature": config.get("temperature", 0.3)
                }
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
        return "Soy Soldy de SOLDASUR. No encontré productos para tu consulta en este momento."

    p = products[0]
    resp = f"Hola, soy Soldy. Para tu consulta sobre Weber, te recomiendo **{p.get('model','')}**: {p.get('description','')}"

    if superficie_m2 and superficie_m2 > 0:
        calculo = calcular_cantidad(p, superficie_m2)
        resp += f"\n{calculo['descripcion_calculo']}"

    return resp


def get_weber_product_by_model(model_name: str) -> Optional[Dict[str, Any]]:
    """Busca y retorna un producto del catálogo de Weber por su nombre de modelo (case-insensitive)."""
    import RAG_engine.query.rag_query_weber as weber_query
    weber_query._load_resources()
    meta = weber_query._metadata
    if meta:
        model_lower = model_name.lower().strip()
        for p in meta:
            if p.get("model", "").lower().strip() == model_lower:
                return p
    return None


# Umbral mínimo de similitud semántica para considerar un producto relevante.
# Los productos con score menor a este valor se descartan para no contaminar
# la respuesta del LLM con productos poco relacionados a la consulta.
SIMILARITY_THRESHOLD = 0.25


def _filter_by_relevance(
    productos: List[Dict[str, Any]],
    min_score: float = SIMILARITY_THRESHOLD,
    keep_at_least: int = 1
) -> List[Dict[str, Any]]:
    """
    Filtra productos por similarity_score.
    Siempre retorna al menos `keep_at_least` producto (el más relevante),
    aunque ninguno supere el umbral.
    """
    filtered = [p for p in productos if p.get("similarity_score", 0) >= min_score]
    if not filtered and productos:
        # Garantía mínima: devolver el más relevante aunque no pase el umbral
        filtered = productos[:keep_at_least]
    return filtered


def search_and_answer(
    query: str,
    last_active_product: Optional[str] = None,
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Función de alto nivel: busca productos y genera respuesta.
    Equivalente al search_filtered() + answer() de PEISA.

    Detecta automáticamente si el usuario mencionó una superficie.
    """
    # Detectar superficie en la consulta
    superficie_m2 = _extract_superficie(query)

    # Buscar productos relevantes (top_k reducido a 3 para mayor precisión)
    productos = search_weber(query, top_k)

    # Filtrar por relevancia semántica antes de enviar al LLM
    productos = _filter_by_relevance(productos)

    # Si se especificó un producto activo y no está en los resultados, lo inyectamos al principio
    # pero solo si el usuario no ha cambiado explícitamente de tema hacia otro producto.
    effective_last_active = None
    if last_active_product:
        is_topic_switch = False
        query_lower = query.lower()
        active_lower = last_active_product.lower().strip()
        
        # Analizar palabras clave de la consulta para detectar desvíos
        keywords_query = set(re.findall(r'\w+', query_lower))
        stop_words = {
            "para", "que", "sirve", "la", "el", "un", "una", "de", "en", "con", "y", "o", "se", "del", 
            "al", "los", "las", "como", "colores", "viene", "color", "weber", "peisa", "tiene", "tienen",
            "sobre", "cuál", "cuales", "como", "cómo", "qué", "admiten", "admite"
        }
        query_important_words = keywords_query - stop_words
        
        if query_important_words and productos:
            # Si el usuario menciona palabras clave que coinciden con algún producto recuperado
            # pero no coinciden con el producto activo, detectamos un cambio de tema (topic switch).
            for p in productos:
                p_model = p.get("model", "").lower().strip()
                if p_model != active_lower:
                    matches_p = any(word in p_model for word in query_important_words)
                    matches_active = any(word in active_lower for word in query_important_words)
                    if matches_p and not matches_active:
                        is_topic_switch = True
                        break

        if not is_topic_switch:
            p_activo = get_weber_product_by_model(last_active_product)
            if p_activo:
                # Remover duplicados si ya estaba en la lista
                productos = [p for p in productos if p.get("model", "").lower().strip() != last_active_product.lower().strip()]
                productos.insert(0, p_activo)
                effective_last_active = last_active_product

    # Generar respuesta
    respuesta = answer_weber(query, productos, superficie_m2, effective_last_active)

    # Devolver al frontend máximo 2 productos (los más relevantes):
    # evita mostrar una tarjeta de producto que el LLM no llegó a mencionar.
    productos_frontend = productos[:2] if productos else []

    return {
        "respuesta": respuesta,
        "productos": productos_frontend,
        "superficie_detectada": superficie_m2,
        "calculo": calcular_cantidad(productos[0], superficie_m2) if productos and superficie_m2 else None,
        "marca": "Weber"
    }

