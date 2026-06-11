# app/main.py
import sys
import os
import importlib
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
from RAG_engine.query.weber_rag_llm import search_and_answer as weber_search_and_answer
from app.modules.expertSystem.weber_expert_engine import WeberExpertEngine #Agregamos esto
import math
from math import ceil
from bisect import bisect_left
from app.models import RADIATOR_MODELS
from RAG_engine.query.peisa_rag_query import search_filtered
from RAG_engine.query.peisa_rag_llm import answer
from app.app import replace_variables, filter_radiators, perform_calculation, format_radiator_recommendations, exec_expression
from app.app import init_knowledge_base, get_node_by_id
from app.orchestrator import IntentClassifier, IntentType
from pathlib import Path
import requests

# Cargar registro de marcas
brands_registry = {}
try:
    with open(os.path.join(BASE_DIR, "configs", "brands_registry.json"), "r", encoding="utf-8") as f:
        brands_registry = json.load(f).get("brands", {})
        print(f"[Main] Registro de marcas cargado: {list(brands_registry.keys())}")
except FileNotFoundError:
    print("Advertencia: No se encontró configs/brands_registry.json")


app = FastAPI(title="SOLDASUR S.A - Asistente Técnico", description="Asistente técnico para calefacción (PEISA) y construcción (Weber)")

@app.middleware("http")
async def disable_cache_for_dev(request, call_next):
    response = await call_next(request)
    if request.url.path.endswith((".js", ".css", ".json")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

weber_expert = WeberExpertEngine() #Agregamos esto
weber_sessions = {} #Agregamos esto

# Modelos Pydantic para request/response
class StartConversationRequest(BaseModel):
    conversation_id: str

class ReplyRequest(BaseModel):
    conversation_id: str
    option_index: Optional[int] = None
    input_values: Optional[Dict[str, Any]] = {}

class ConversationResponse(BaseModel):
    conversation_id: str
    node_id: str
    type: Optional[str] = None
    text: Optional[str] = None
    options: Optional[List[str]] = None
    input_type: Optional[str] = None
    input_label: Optional[str] = None
    inputs: Optional[List[Dict[str, Any]]] = None
    is_final: Optional[bool] = None
    error: Optional[str] = None

# Cargar la base de conocimiento
try:
    with open(os.path.join(BASE_DIR, "app/peisa_advisor_knowledge_base.json"), "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)
        init_knowledge_base(knowledge_base)  # Inicializar la base de conocimiento
except FileNotFoundError:
    print("Advertencia: No se encontró el archivo peisa_advisor_knowledge_base.json")
    knowledge_base = []
    init_knowledge_base(knowledge_base)


# Contexto de la conversación
conversations = {}

# Servir archivos estáticos (CSS, JS, imágenes)
app.mount("/js_modules", StaticFiles(directory=os.path.join(BASE_DIR, "web_app", "js_modules")), name="js_modules")
app.mount("/img", StaticFiles(directory=os.path.join(BASE_DIR, "web_app", "img")), name="img")
app.mount("/data", StaticFiles(directory=os.path.join(BASE_DIR, "web_app", "data")), name="data")
app.mount("/scraping", StaticFiles(directory=os.path.join(BASE_DIR, "scraping")), name="scraping")

@app.get("/soldasur.css", response_class=HTMLResponse)
async def get_css():
    try:
        with open(os.path.join(BASE_DIR, "web_app", "soldasur.css"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), media_type="text/css")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo soldasur.css no encontrado")

@app.get("/soldasur.js", response_class=HTMLResponse)
async def get_js():
    try:
        with open(os.path.join(BASE_DIR, "web_app", "soldasur.js"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo soldasur.js no encontrado")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Sirve la página principal del chat"""
    try:
        with open(os.path.join(BASE_DIR, "web_app", "index.html"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo index.html no encontrado")

@app.post("/start", response_model=ConversationResponse)
async def start_conversation(request: StartConversationRequest):
    """Inicia una nueva conversación"""
    conversation_id = request.conversation_id
    conversations[conversation_id] = {
        'current_node': 'inicio',
        'context': {}
    }
    return await get_next_message(conversation_id)

@app.post("/reply", response_model=ConversationResponse)
async def handle_reply(request: ReplyRequest):
    """Maneja las respuestas del usuario"""
    conversation_id = request.conversation_id
    option_index = request.option_index
    input_values = request.input_values or {}
    
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    conv = conversations[conversation_id]
    node = get_node_by_id(conv['current_node'])
    
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    
    # Procesar la respuesta del usuario
    if node.get('tipo') == 'entrada_usuario':
        try:
            if 'variable' in node:
                value = str(input_values.get('value', '')).replace(',', '.')
                conv['context'][node['variable']] = float(value)
            elif 'variables' in node:
                for var in node['variables']:
                    value = str(input_values.get(var, '')).replace(',', '.')
                    conv['context'][var] = float(value)
            conv['current_node'] = node['siguiente']
        except ValueError:
            return ConversationResponse(
                conversation_id=conversation_id,
                node_id=node['id'],
                error='Por favor ingrese valores numéricos válidos (ej: 4.5, 3.75)',
                type='input_error',
                text=node['pregunta']
            )
    
    elif 'opciones' in node:
        if option_index is not None and 0 <= option_index < len(node['opciones']):
            selected = node['opciones'][option_index]
            # Guardar el valor usando el ID del nodo como clave
            variable_name = node.get('variable', node['id'])
            conv['context'][variable_name] = selected.get('valor', selected['texto'])
            # Guardar también el texto para mostrar
            conv['context'][f"{variable_name}_texto"] = selected['texto']
            conv['current_node'] = selected['siguiente']
    
    # Debug: Mostrar el contexto completo
    print("Contexto completo:", conv['context'])
    
    return await get_next_message(conversation_id)

async def get_next_message(conversation_id: str) -> ConversationResponse:
    """Obtiene el siguiente mensaje de la conversación"""
    conv = conversations[conversation_id]
    node = get_node_by_id(conv['current_node'])
    
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    
    response = ConversationResponse(
        conversation_id=conversation_id,
        node_id=node['id']
    )
    
    # Procesar según el tipo de nodo
    if node.get('tipo') == 'calculo':
        perform_calculation(node, conv['context'])
        conv['current_node'] = node['siguiente']
        return await get_next_message(conversation_id)
    elif 'pregunta' in node:
        response.type = 'question'
        response.text = replace_variables(node['pregunta'], conv['context'])
        
        if 'opciones' in node:
            response.options = [opt['texto'] for opt in node['opciones']]
        elif node.get('tipo') == 'entrada_usuario':
            if 'variable' in node:
                response.input_type = 'number'
                response.input_label = 'Ingrese el valor'
            elif 'variables' in node:
                response.input_type = 'multiple'
                response.inputs = [
                    {'name': var, 'label': f'Ingrese {var} (metros)', 'type': 'number'}
                    for var in node['variables']
                ]
    elif node.get('tipo') == 'respuesta':
        response.type = 'response'
        response.text = replace_variables(node['texto'], conv['context'])
        
        if 'opciones' in node:
            response.options = [opt['texto'] for opt in node['opciones']]
        else:
            response.is_final = True
    elif node.get('tipo') == 'opciones_dinamicas':
        # Manejar opciones dinámicas basadas en modelos recomendados
        if 'modelos_recomendados' in conv['context']:
            models = conv['context']['modelos_recomendados']
            response.type = 'question'
            response.text = node['pregunta']
            response.options = [
                f"{model['name']} (Potencia: {model['potencia']*model['coeficiente']:.0f} kcal/h)"
                for model in models
            ]
    
    return response

# Endpoint adicional para salud del servicio
@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servicio"""
    return {"status": "ok", "service": "SOLDASUR S.A - Asistente Técnico"}

@app.get("/ask")
def ask(question: str = Query(..., min_length=5)):
    top_items = search_filtered(question, top_k=3)
    respuesta = answer(question, top_items)
    return {"respuesta": respuesta, "productos": top_items}


@app.get("/ask_weber")  # Endpoint para consultas sobre productos Weber
def ask_weber(
    question: str = Query(..., min_length=3),
    superficie: float = Query(None, description="Superficie en m² (opcional)")
):
    """
    Endpoint para consultas sobre productos Weber.
    Opcionalmente acepta superficie para calcular cantidades.
    """
    from RAG_engine.query.weber_rag_llm import search_and_answer
    from RAG_engine.query.weber_rag_query import calcular_cantidad

    result = search_and_answer(question)

    # Si se pasó superficie y no la detectó automáticamente
    if superficie and not result.get("superficie_detectada"):
        if result.get("productos"):
            calculo = calcular_cantidad(result["productos"][0], superficie)
            result["calculo"] = calculo

    return result


# ── Palabras clave que indican una consulta Weber (construcción / revestimientos) ──
WEBER_KEYWORDS = [
    "weber",
    "porcelanato", "porcelanatos", "cerámica", "ceramica", "cerámico",
    "adhesivo", "adhesivos",
    "revoque", "revoques", "revestimiento", "revestimientos",
    "mortero", "morteros",
    "nivelador", "autonivelante",
    "contrapiso",
    "impermeabilizante", "impermeabilizacion",
    "junta", "juntas",
    "pastina",
    "fraguado", "fragua",
]


def _is_weber_query(message: str) -> bool:
    """Detecta si el mensaje es sobre productos Weber (construcción/revestimientos)."""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in WEBER_KEYWORDS)


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    last_active_brand: Optional[str] = None
    last_active_product: Optional[str] = None


intent_classifier = IntentClassifier()


def _get_neutral_response(message: str) -> str:
    """Genera una respuesta neutral de bienvenida usando Ollama."""
    config_path = Path(BASE_DIR) / "configs" / "prompts.json"
    
    default_prompt = (
        "Sos Soldy, el asistente inteligente unificado de SOLDASUR. Tu única función es saludar "
        "y dar la bienvenida al cliente de manera muy cordial, breve y neutral. Explícale de forma "
        "amigable (máximo 2 oraciones) que podés ayudarlo a calcular materiales de construcción y revestimientos (Weber) "
        "o a dimensionar su sistema de calefacción (PEISA), e invitalo a realizar su consulta sobre cualquiera de estas marcas. "
        "Hablá siempre en español rioplatense (vos, tenés, podés). NUNCA recomiendes ni nombres ningún producto específico."
    )
    temp = 0.5
    max_tokens = 100
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                neutral_config = data.get("neutral", {})
                system_prompt = neutral_config.get("system_prompt", default_prompt)
                temp = neutral_config.get("temperature", temp)
                max_tokens = neutral_config.get("max_tokens", max_tokens)
        except Exception as e:
            print(f"[NeutralChat] Error cargando prompts.json ({e}). Usando fallback.")
            system_prompt = default_prompt
    else:
        system_prompt = default_prompt

    ollama_url = "http://127.0.0.1:11434/api/generate"
    try:
        response = requests.post(
            ollama_url,
            json={
                "model": "llama3.2:3b",
                "prompt": message,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temp
                }
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception as e:
        print(f"[NeutralChat] Error llamando a Ollama: {e}")
        
    return "¡Hola! Soy **Soldy**, el asistente inteligente de **SOLDASUR**. Puedo ayudarte con productos de calefacción **PEISA** o de construcción **Weber**. ¿Sobre qué te gustaría consultar hoy?"


@app.post("/api/chat")
async def api_chat(request: ChatRequest):
    """
    Endpoint unificado de chat para el frontend.
    Detecta si la consulta es sobre Weber (construcción) o PEISA (calefacción)
    usando enrutamiento semántico y rutea al motor RAG correspondiente de forma dinámica.
    """
    message = request.message.strip()

    context = {
        "last_active_brand": request.last_active_brand,
        "last_active_product": request.last_active_product
    }

    # Clasificar intención usando enrutamiento híbrido/semántico con contexto activo
    intent = intent_classifier.classify(message, context)

    # Determinar la marca correspondiente
    brand_key = intent.metadata.get("brand_key")
    if not brand_key:
        # Buscar por tipo de intención en el registro si no vino directa en la metadata
        for bk, b_config in brands_registry.items():
            if b_config.get("intent_type") == intent.type.value:
                brand_key = bk
                break

    if brand_key and brand_key in brands_registry:
        b_config = brands_registry[brand_key]
        module_name = b_config["rag_module"]
        func_name = b_config["rag_function"]
        
        try:
            # Importar dinámicamente el módulo y obtener la función RAG
            module = importlib.import_module(module_name)
            rag_func = getattr(module, func_name)
            
            # Formateador específico según la marca
            formatter = b_config.get("response_formatter", "generic")
            
            if formatter == "weber":
                # Ruta RAG autogestionada (ej: Weber, que maneja búsqueda y respuesta juntas)
                result = rag_func(message, last_active_product=request.last_active_product)
                response_text = result.get("respuesta", "")
                productos_weber = result.get("productos", [])
                calculo = result.get("calculo")

                # Formatear productos para la UI
                products_formatted = [
                    {
                        "model": p.get("model", ""),
                        "family": p.get("category", "Weber"),
                        "category": p.get("category", ""),
                        "description": p.get("description", ""),
                        "url": p.get("url", ""),
                        "brand": p.get("brand", b_config.get("display_name", "Weber")),
                        "imagen_local": p.get("imagen_local", ""),
                        "imagen_url": p.get("imagen_url", ""),
                    }
                    for p in productos_weber
                ]

                resp = {
                    "mode": brand_key.lower(),
                    "text": response_text,
                    "products": products_formatted,
                }
                if calculo:
                    resp["calculo"] = {
                        "superficie_m2": calculo.get("superficie_m2"),
                        "producto": calculo.get("producto"),
                        "bolsas_necesarias": calculo.get("bolsas_necesarias"),
                        "rendimiento_kg_m2": calculo.get("rendimiento_por_bolsa"),
                    }
                return resp

            elif formatter == "peisa":
                # Ruta RAG separada (ej: PEISA, requiere búsqueda previa + generación de respuesta)
                top_items = search_filtered(message, top_k=3)

                # Inyectar el producto activo al inicio si existe
                if request.last_active_product:
                    from RAG_engine.query.peisa_rag_query import get_peisa_product_by_model
                    p_activo = get_peisa_product_by_model(request.last_active_product)
                    if p_activo:
                        # Remover duplicados si ya estaba en la lista
                        top_items = [p for p in top_items if p.get("model", "").lower().strip() != request.last_active_product.lower().strip()]
                        top_items.insert(0, p_activo)

                respuesta = rag_func(message, top_items, last_active_product=request.last_active_product)
                
                # Asegurar que los productos tengan la marca asociada
                products_formatted = []
                for p in top_items[:3]:
                    p_copy = p.copy()
                    if "brand" not in p_copy:
                        p_copy["brand"] = b_config.get("display_name", "PEISA")
                    products_formatted.append(p_copy)

                return {
                    "mode": brand_key.lower(),
                    "text": respuesta,
                    "products": products_formatted,
                }
            
            else:
                # Formateador genérico fallback para nuevas marcas
                try:
                    result = rag_func(message, last_active_product=request.last_active_product)
                except TypeError:
                    result = rag_func(message)
                
                if isinstance(result, dict):
                    text = result.get("respuesta") or result.get("answer") or result.get("text") or ""
                    products = result.get("productos") or result.get("products") or []
                else:
                    text = str(result)
                    products = []
                    
                return {
                    "mode": brand_key.lower(),
                    "text": text,
                    "products": products
                }
                
        except Exception as e:
            print(f"[api_chat] Error ejecutando RAG dinámico para {brand_key}: {e}")
            # Si hay un error, cae en el fallback neutral de abajo

    # ── Ruta Neutra (Saludos y consultas generales/híbridas) ─────────────────
    respuesta_neutra = _get_neutral_response(message)
    return {
        "mode": "neutral",
        "text": respuesta_neutra,
        "products": []
    }


# ... (Todo el código intermedio de tus endpoints actuales de PEISA y ask_weber)

# 👇 PEGÁ ESTOS DOS ENDPOINTS COMPLETOS ACÁ:

@app.post("/expert/weber/start")
async def start_weber_expert(request: StartConversationRequest):
    node = weber_expert.get_node_by_id("inicio_weber")
    weber_sessions[request.conversation_id] = {"context": {}, "current_node": "inicio_weber"}
    return {
        "conversation_id": request.conversation_id,
        "node_id": node["id"],
        "type": node["tipo"],
        "text": node["pregunta"],
        "options": [opt["texto"] for opt in node.get("opciones", [])]
    }

@app.post("/expert/weber/reply")
async def reply_weber_expert(request: ReplyRequest):
    session = weber_sessions.get(request.conversation_id)
    if not session:
        raise HTTPException(status_code=400, detail="Sesión no encontrada")
        
    current_node = weber_expert.get_node_by_id(session["current_node"])
    
    if "variable" in current_node:
        var_name = current_node["variable"]
        if current_node["tipo"] == "opciones" and request.option_index is not None:
            val = current_node["opciones"][request.option_index].get("valor")
            session["context"][var_name] = val
            siguiente_nodo_id = current_node["opciones"][request.option_index]["siguiente"]
        else:
            val = float(request.input_values.get(var_name, 0))
            session["context"][var_name] = val
            siguiente_nodo_id = current_node["siguiente"]
    else:
        siguiente_nodo_id = current_node["siguiente"]

    next_node = weber_expert.get_node_by_id(siguiente_nodo_id)
    session["current_node"] = siguiente_nodo_id

    if next_node and next_node["tipo"] == "calculo":
        ctx = session["context"]
        calculo_res = weber_expert.resolver_calculo(ctx["soporte_obra"], ctx["metros_cuadrados"])
        session["context"]["resultado"] = calculo_res
        next_node = weber_expert.get_node_by_id(next_node["siguiente"])
        session["current_node"] = next_node["id"]

    if session["current_node"] == "resultado_final_weber":
        res = session["context"]["resultado"]
        texto_salida = (
            f"### 📊 Resultado del Asesoramiento Weber\n\n"
            f"Para cubrir **{session['context']['metros_cuadrados']} m²** sobre el soporte seleccionado, "
            f"te recomendamos utilizar **{res['producto'].upper()}**.\n\n"
            f"• **Cantidad necesaria:** {res['bolsas_necesarias']} bolsas de 25 kg.\n"
            f"• **Rendimiento estimado:** {res['rendimiento_kg_m2']} kg/m² (+10% desperdicio técnico).\n"
            f"• **Masa total del material:** {res['kg_totales']} kg."
        )
        return {
            "conversation_id": request.conversation_id,
            "node_id": "final",
            "type": "respuesta",
            "text": texto_salida,
            "options": [],
            "mode": "weber",
            "calculo": res
        }

    return {
        "conversation_id": request.conversation_id,
        "node_id": next_node["id"],
        "type": next_node["tipo"],
        "text": next_node["pregunta"],
        "options": [opt["texto"] for opt in next_node.get("opciones", [])] if "opciones" in next_node else []
    }


# Montar la raíz del proyecto para servir todos los archivos estáticos del frontend (HTML, JS, CSS, JSON, imágenes, etc.)
app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "web_app"), html=True), name="frontend")


# ── Bloque de cierre que ya tenías (Dejalo tal cual abajo de todo) ──
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)


