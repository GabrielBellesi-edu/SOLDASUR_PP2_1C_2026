"""
orchestrator_patch.py  –  Parche para integrar Weber al orquestador existente
==============================================================================
Este archivo muestra los cambios que hay que hacer en orchestrator.py
para que detecte consultas sobre Weber y las enrute correctamente.

NO reemplaza orchestrator.py, sino que muestra exactamente qué agregar.

Instrucciones:
  1. Abrir app/orchestrator.py
  2. Aplicar los cambios marcados con # ← AGREGAR
"""

# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 1: En la clase IntentClassifier, agregar WEBER_QUERY a IntentType
# ─────────────────────────────────────────────────────────────────────────────

# En orchestrator.py, dentro de class IntentType(Enum), agregar:
#
#   WEBER_QUERY = "weber_query"   # ← AGREGAR
#
# Quedaría así:
#
# class IntentType(Enum):
#     GUIDED_CALCULATION = "guided_calculation"
#     FREE_QUERY         = "free_query"
#     PRODUCT_SEARCH     = "product_search"
#     HYBRID             = "hybrid"
#     SWITCH_MODE        = "switch_mode"
#     CLARIFICATION      = "clarification"
#     WEBER_QUERY        = "weber_query"   # ← AGREGAR


# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 2: En IntentClassifier.PATTERNS, agregar patrones Weber
# ─────────────────────────────────────────────────────────────────────────────

# Dentro de PATTERNS = { ... }, agregar al final:
#
#   IntentType.WEBER_QUERY: [           # ← AGREGAR este bloque completo
#       r"weber",
#       r"mortero",
#       r"revoque",
#       r"cerámico",
#       r"porcellanato",
#       r"pastina",
#       r"adhesivo",
#       r"impermeabilizante",
#       r"membrana",
#       r"carpeta",
#       r"nivelación",
#       r"pegamento.*piso",
#       r"pegamento.*pared",
#       r"revocar",
#       r"hormigón",
#       r"aislaci[oó]n\s+t[eé]rmica",
#       r"micropiso",
#       r"piso\s+decorativo",
#       r"piso\s+sobre\s+piso",
#   ],


# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 3: En el método classify(), agregar detección de Weber ANTES del
#           bloque de PRODUCT_SEARCH
# ─────────────────────────────────────────────────────────────────────────────

# Agregar estas líneas en classify(), antes de "if self._matches_patterns(...)":
#
#   # Detectar consultas sobre productos Weber        # ← AGREGAR
#   if self._matches_patterns(message_lower, IntentType.WEBER_QUERY):   # ← AGREGAR
#       return Intent(IntentType.WEBER_QUERY, confidence=0.9)           # ← AGREGAR


# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 4: En ConversationOrchestrator.process_message(), agregar manejo Weber
# ─────────────────────────────────────────────────────────────────────────────

# Agregar este bloque en process_message(), después del elif de PRODUCT_SEARCH:
#
#   elif intent.type == IntentType.WEBER_QUERY:    # ← AGREGAR este bloque
#       result = await self._handle_weber_query(conversation_id, message)
#       return result


# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 5: Agregar el método _handle_weber_query() a ConversationOrchestrator
# ─────────────────────────────────────────────────────────────────────────────

# Agregar este método completo dentro de la clase ConversationOrchestrator:

WEBER_HANDLER_CODE = '''
    async def _handle_weber_query(self, conversation_id: str, message: str) -> dict:
        """
        Maneja consultas sobre productos Weber.
        Usa el WeberRAGEngine en lugar del RAG de PEISA.
        """
        try:
            from app.modules.chatbot.weber_rag_engine import search_and_answer
            result = search_and_answer(message)
            return {
                "type": "response",
                "text": result["respuesta"],
                "products": result.get("productos", []),
                "mode": "weber",
                "mode_label": "Asesor Weber",
                "marca": "Weber",
                "calculo": result.get("calculo"),
                "is_final": False,
            }
        except Exception as e:
            print(f"[Orchestrator] Error en Weber RAG: {e}")
            return {
                "type": "response",
                "text": "No pude consultar el catálogo Weber. Intentá de nuevo.",
                "mode": "weber",
                "mode_label": "Asesor Weber",
                "is_final": False,
            }
'''

print("=" * 60)
print("PARCHE PARA ORCHESTRATOR.PY")
print("=" * 60)
print()
print("Cambios a aplicar en app/orchestrator.py:")
print()
print("1. Agregar WEBER_QUERY a IntentType")
print("2. Agregar patrones Weber a PATTERNS")
print("3. Agregar detección Weber en classify()")
print("4. Agregar elif WEBER_QUERY en process_message()")
print("5. Agregar método _handle_weber_query()")
print()
print("Ver comentarios en este archivo para el código exacto.")
print()
print("Código del método _handle_weber_query():")
print(WEBER_HANDLER_CODE)


# ─────────────────────────────────────────────────────────────────────────────
# CAMBIO 6: En main.py, agregar endpoint /ask_weber
# ─────────────────────────────────────────────────────────────────────────────

MAIN_ENDPOINT_CODE = '''
# Agregar en app/main.py, después del endpoint /ask existente:

@app.get("/ask_weber")
def ask_weber(
    question: str = Query(..., min_length=3),
    superficie: float = Query(None, description="Superficie en m² (opcional)")
):
    """
    Endpoint para consultas sobre productos Weber.
    Opcionalmente acepta superficie_m2 para calcular cantidades.
    """
    from app.modules.chatbot.weber_rag_engine import search_and_answer, calcular_cantidad

    result = search_and_answer(question)

    # Si se pasó superficie y no la detectó automáticamente
    if superficie and not result.get("superficie_detectada"):
        if result.get("productos"):
            calculo = calcular_cantidad(result["productos"][0], superficie)
            result["calculo"] = calculo

    return result
'''

print()
print("Endpoint para main.py:")
print(MAIN_ENDPOINT_CODE)
