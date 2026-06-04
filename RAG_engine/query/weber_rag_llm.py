"""
weber_rag_llm.py – Generador RAG / LLM para productos Weber.
"""

import requests
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .weber_rag_query import search_weber, calcular_cantidad, _extract_superficie

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

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

EJEMPLOS CORRECTOS (CÓMO DEBÉS RESPONDER):
Usuario: "¿qué productos tiene weber?"
Soldy: "Ofrecemos una amplia variedad de soluciones Weber. Disponemos de Weber Anclaje Químico para fijaciones de alta exigencia, Weber Espuma PU para sellar, y pastinas clásicas para cerámicos. Si necesitás stock o asesoramiento técnico en obra, te sugiero consultar en el local."

Usuario: "necesito pegar cerámicos en el baño"
Soldy: "Para el baño te recomiendo usar Weber Impermeable, ya que está formulado para soportar la humedad y evitar filtraciones. Además vas a necesitar pastina para rellenar las juntas. Si me indicás los metros cuadrados, calculo la cantidad de bolsas necesarias."

Usuario: "¿en qué colores viene el weberplast llaneado?"
Soldy: "El weberplast llaneado viene en colores estándar listos y en una gran variedad de tonos preparados a elección por sistema tintométrico. Te sugiero pasar por el local de SOLDASUR para ver la carta física de colores."

EJEMPLOS INCORRECTOS (NUNCA HAGAS ESTO):
- "Hola! Soy Soldy. Contamos con..." (Prohibido volver a saludar o presentarse).
- "Che! Si tenés consultando qué productos tenemos..." (Prohibido empezar con 'Che' y mala conjugación).
- "Mirá, te comento que tenemos..." (Prohibido usar 'mirá').
- "Tenés acá para ayudarte..." (Mala gramática, usar 'estoy acá para ayudarte')."""


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
"""
    if last_active_product:
        prompt += f"\nContexto de conversación: El usuario acaba de recibir una recomendación sobre el producto '{last_active_product}' (o estaba hablando de él). Si la consulta del cliente es una pregunta de seguimiento (como colores, rendimiento, secado, precio, etc.), responde asumiendo que se refiere a este producto."

    prompt += f"\nConsulta del cliente: {query}\n\nRespuesta:"

    # Cargar prompts y configuraciones parametrizadas
    config = _load_prompt_config()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
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
    import RAG_engine.query.weber_rag_query as weber_query
    weber_query._load_resources()
    meta = weber_query._metadata
    if meta:
        model_lower = model_name.lower().strip()
        for p in meta:
            if p.get("model", "").lower().strip() == model_lower:
                return p
    return None


def search_and_answer(
    query: str,
    last_active_product: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Función de alto nivel: busca productos y genera respuesta.
    Equivalente al search_filtered() + answer() de PEISA.

    Detecta automáticamente si el usuario mencionó una superficie.
    """
    # Detectar superficie en la consulta
    superficie_m2 = _extract_superficie(query)

    # Buscar productos relevantes
    productos = search_weber(query, top_k)

    # Si se especificó un producto activo y no está en los resultados de búsqueda, lo inyectamos al principio
    if last_active_product:
        p_activo = get_weber_product_by_model(last_active_product)
        if p_activo:
            # Remover duplicados si ya estaba en la lista de búsqueda
            productos = [p for p in productos if p.get("model", "").lower().strip() != last_active_product.lower().strip()]
            productos.insert(0, p_activo)

    # Generar respuesta
    respuesta = answer_weber(query, productos, superficie_m2, last_active_product)

    return {
        "respuesta": respuesta,
        "productos": productos[:3] if productos else [],
        "superficie_detectada": superficie_m2,
        "calculo": calcular_cantidad(productos[0], superficie_m2) if productos and superficie_m2 else None,
        "marca": "Weber"
    }

