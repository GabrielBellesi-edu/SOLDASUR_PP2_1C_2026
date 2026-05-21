# app/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import math
from math import ceil
from bisect import bisect_left
from app.models import RADIATOR_MODELS
from query.query import search_filtered
from app.modules.chatbot.llm_wrapper import answer
from app.app import replace_variables, filter_radiators, perform_calculation, format_radiator_recommendations, exec_expression
from app.app import init_knowledge_base, get_node_by_id  # modificar import

app = FastAPI(title="PEISA - SOLDASUR S.A", description="Asistente para cálculos de calefacción")

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
    with open("app/peisa_advisor_knowledge_base.json", "r", encoding="utf-8") as f:
        knowledge_base = json.load(f)
        init_knowledge_base(knowledge_base)  # Inicializar la base de conocimiento
except FileNotFoundError:
    print("Advertencia: No se encontró el archivo peisa_advisor_knowledge_base.json")
    knowledge_base = []
    init_knowledge_base(knowledge_base)


# Contexto de la conversación
conversations = {}

# Servir archivos estáticos (CSS, JS, imágenes)
# app.mount("/app/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Sirve la página principal del chat"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
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
    return {"status": "ok", "service": "PEISA - SOLDASUR S.A"}

@app.get("/ask")
def ask(question: str = Query(..., min_length=5)):
    top_items = search_filtered(question, top_k=3)
    respuesta = answer(question, top_items)
    return {"respuesta": respuesta, "productos": top_items}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)