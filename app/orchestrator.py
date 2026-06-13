import json
from pathlib import Path

# ... (keep existing imports or redefine here)
from typing import Dict, Any, Optional, List
from enum import Enum
import re


class IntentType(Enum):
    """Tipos de intención del usuario"""
    GUIDED_CALCULATION = "guided_calculation"  # Flujo guiado paso a paso
    FREE_QUERY = "free_query"                  # Pregunta abierta
    PRODUCT_SEARCH = "product_search"          # Búsqueda de productos
    HYBRID = "hybrid"                          # Combinación de ambos
    SWITCH_MODE = "switch_mode"                # Cambio de modo
    CLARIFICATION = "clarification"            # Pregunta tangencial durante flujo
    WEBER_QUERY        = "weber_query"         # Consultas sobre productos Weber


class ConversationMode(Enum):
    """Modos de conversación"""
    EXPERT = "expert"      # Modo experto guiado
    RAG = "rag"           # Modo chat libre
    HYBRID = "hybrid"     # Modo híbrido automático


class Intent:
    """Representa la intención clasificada del usuario"""
    def __init__(self, intent_type: IntentType, confidence: float = 1.0, 
                 metadata: Optional[Dict[str, Any]] = None):
        self.type = intent_type
        self.confidence = confidence
        self.metadata = metadata or {}


class IntentClassifier:
    """
    Clasifica la intención del usuario para enrutar correctamente
    entre el sistema experto y las distintas marcas configuradas dinámicamente.
    """
    
    # Patrones para clasificación basada en reglas
    PATTERNS = {
        IntentType.GUIDED_CALCULATION: [
            r"quiero calcular",
            r"necesito dimensionar",
            r"cuántos radiadores",
            r"piso radiante",
            r"ayúdame a calcular",
            r"guíame",
            r"paso a paso",
        ],
        IntentType.FREE_QUERY: [
            r"qué es",
            r"cómo funciona",
            r"diferencia entre",
            r"explica",
            r"cuál es mejor",
            r"ventajas",
            r"desventajas",
        ],
        IntentType.PRODUCT_SEARCH: [
            r"precio",
            r"modelo",
            r"disponibilidad",
            r"características",
            r"catálogo",
            r"tienen.*\?",
            r"busco",
        ],
        IntentType.SWITCH_MODE: [
            r"prefiero que me guíes",
            r"quiero preguntar libremente",
            r"modo experto",
            r"modo chat",
            r"cambiar modo",
        ],
        IntentType.CLARIFICATION: [
            r"qué significa",
            r"no entiendo",
            r"explícame",
            r"qué quiere decir",
        ],
        IntentType.WEBER_QUERY: [
            r"weber",
            r"mortero",
            r"revoque",
            r"cerámico",
            r"porcellanato",
            r"pastina",
            r"adhesivo",
            r"impermeabilizante",
            r"membrana",
            r"carpeta",
            r"nivelación",
            r"pegamento.*piso",
            r"pegamento.*pared",
            r"revocar",
            r"hormigón",
            r"aislaci[oó]n\s+t[eé]rmica",
            r"micropiso",
            r"piso\s+decorativo",
            r"piso\s+sobre\s+piso",
        ]
    }
    
    def __init__(self):
        self.brands_registry = {}
        self.anchor_vectors = {}  # { brand_key: vector }
        self._load_brands_registry()

    def _load_brands_registry(self):
        """Carga el registro centralizado de marcas desde configs/brands_registry.json."""
        try:
            config_path = Path(__file__).resolve().parent.parent / "configs" / "brands_registry.json"
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.brands_registry = data.get("brands", {})
                    print(f"[IntentClassifier] Registro de marcas cargado. Marcas detectadas: {list(self.brands_registry.keys())}")
            else:
                print(f"[IntentClassifier] AVISO: No se encontró el registro de marcas en {config_path}")
        except Exception as e:
            print(f"[IntentClassifier] Error cargando registro de marcas: {e}")

    def _lazy_init_anchors(self):
        """Inicializa de forma diferida (lazy loading) los embeddings de los textos ancla del registro."""
        if not self.anchor_vectors and self.brands_registry:
            try:
                import numpy as np
                import RAG_engine.query.rag_query_weber as weber_query
                weber_query._load_resources()
                model = weber_query._model
                if model is not None:
                    brand_keys = list(self.brands_registry.keys())
                    anchor_texts = [self.brands_registry[bk]["anchor_text"] for bk in brand_keys]
                    
                    # Generar embeddings de las anclas
                    vecs = model.encode(anchor_texts, convert_to_numpy=True)
                    for i, bk in enumerate(brand_keys):
                        norm = np.linalg.norm(vecs[i])
                        self.anchor_vectors[bk] = vecs[i] / norm if norm > 0 else vecs[i]
                    print(f"[IntentClassifier] Similitud vectorial inicializada con éxito para: {', '.join(brand_keys)}")
            except Exception as e:
                print(f"[IntentClassifier] AVISO: No se pudo cargar el modelo para similitud semántica ({e}). Se usará enrutamiento heurístico por Regex.")

    def classify(self, message: str, context: Dict[str, Any]) -> Intent:
        """
        Clasifica la intención del usuario basándose en el mensaje, contexto y similitud vectorial dinámica.
        
        Args:
            message: Mensaje del usuario
            context: Contexto de la conversación
            
        Returns:
            Intent: Intención clasificada con confianza
        """
        message_lower = message.lower().strip()
        
        # 1. Si está en medio de un flujo guiado y hace una pregunta tangencial
        if context.get('mode') == ConversationMode.EXPERT.value:
            if self._matches_patterns(message_lower, IntentType.CLARIFICATION):
                return Intent(IntentType.CLARIFICATION, confidence=0.9)
            if message_lower.isdigit() or self._is_numeric_input(message):
                return Intent(IntentType.GUIDED_CALCULATION, confidence=1.0)
        
        # 2. Detectar cambio de modo explícito
        if self._matches_patterns(message_lower, IntentType.SWITCH_MODE):
            target_mode = self._extract_target_mode(message_lower)
            return Intent(IntentType.SWITCH_MODE, confidence=0.95, 
                          metadata={'target_mode': target_mode})

        # Evaluar palabras clave directas por marca registrada
        brand_kw_matches = {}
        for bk, brand_info in self.brands_registry.items():
            kws = brand_info.get("direct_keywords", [])
            brand_kw_matches[bk] = any(re.search(pat, message_lower) for pat in kws)

        # Enrutamiento Contextual por Marca Activa (si la pregunta es de seguimiento y no cambia de marca explícitamente)
        last_brand = (context.get("last_active_brand") or "").upper()
        
        saludos = [r"^\s*hola\s*$", r"^\s*buenas\s*$", r"^\s*buen\s+d[ií]a\s*$", r"^\s*buen\s*tarde\s*$", r"^\s*gracias\s*$", r"^\s*chau\s*$", r"^\s*adi[oó]s\s*$"]
        is_simple_greeting = any(re.search(pat, message_lower) for pat in saludos)

        if last_brand and not is_simple_greeting and last_brand in self.brands_registry:
            # Si estábamos hablando de esta marca, y no hay palabras clave de NINGUNA OTRA marca registrada
            has_other_brand_kw = any(match for bk, match in brand_kw_matches.items() if bk != last_brand)
            if not has_other_brand_kw:
                brand_info = self.brands_registry[last_brand]
                intent_type_str = brand_info.get("intent_type", "hybrid")
                resolved_type = IntentType.HYBRID
                for item in IntentType:
                    if item.value == intent_type_str:
                        resolved_type = item
                        break
                return Intent(resolved_type, confidence=0.95, metadata={"brand_key": last_brand})

        # 3. Enrutamiento Rápido en Cascada (Heurística directa - 0ms)
        for bk, brand_info in self.brands_registry.items():
            if brand_kw_matches[bk]:
                intent_type_str = brand_info.get("intent_type", "hybrid")
                resolved_type = IntentType.HYBRID
                for item in IntentType:
                    if item.value == intent_type_str:
                        resolved_type = item
                        break
                return Intent(resolved_type, confidence=1.0, metadata={"brand_key": bk})

        # 4. Enrutamiento Semántico Vectorial (SentenceTransformers - fallback robusto)
        self._lazy_init_anchors()
        if self.anchor_vectors:
            try:
                import numpy as np
                import RAG_engine.query.rag_query_weber as weber_query
                model = weber_query._model
                if model is not None:
                    query_vec = model.encode([message_lower], convert_to_numpy=True)[0]
                    query_norm = np.linalg.norm(query_vec)
                    if query_norm > 0:
                        query_vec = query_vec / query_norm
                        
                        # Calcular similitudes para cada marca
                        sims = {}
                        for bk, anchor_vec in self.anchor_vectors.items():
                            sims[bk] = float(np.dot(query_vec, anchor_vec))
                        
                        # Imprimir similitudes
                        sims_str = ", ".join([f"{bk}: {val:.3f}" for bk, val in sims.items()])
                        print(f"[IntentClassifier] Similitudes semánticas -> {sims_str}")
                        
                        # Encontrar la marca con mayor similitud
                        best_brand = max(sims, key=sims.get)
                        best_sim = sims[best_brand]
                        
                        UMBRAL_SIMILITUD = 0.35
                        if best_sim >= UMBRAL_SIMILITUD:
                            brand_info = self.brands_registry[best_brand]
                            intent_type_str = brand_info.get("intent_type", "hybrid")
                            resolved_type = IntentType.HYBRID
                            for item in IntentType:
                                if item.value == intent_type_str:
                                    resolved_type = item
                                    break
                            return Intent(resolved_type, confidence=best_sim, metadata={"brand_key": best_brand})
            except Exception as e:
                print(f"[IntentClassifier] Error durante la clasificación semántica: {e}")

        # 5. Caída en Regex tradicional (para Weber si falló la carga del modelo)
        if self._matches_patterns(message_lower, IntentType.WEBER_QUERY):   
            return Intent(IntentType.WEBER_QUERY, confidence=0.8, metadata={"brand_key": "WEBER"})           
        
        # 6. Resto de intenciones
        if self._matches_patterns(message_lower, IntentType.PRODUCT_SEARCH):
            return Intent(IntentType.PRODUCT_SEARCH, confidence=0.85)
        
        if self._matches_patterns(message_lower, IntentType.GUIDED_CALCULATION):
            return Intent(IntentType.GUIDED_CALCULATION, confidence=0.9)
        
        if self._matches_patterns(message_lower, IntentType.FREE_QUERY):
            return Intent(IntentType.FREE_QUERY, confidence=0.85)
        
        if self._has_specific_data(message_lower):
            return Intent(IntentType.HYBRID, confidence=0.75)
        
        return Intent(IntentType.HYBRID, confidence=0.5)
    
    def _matches_patterns(self, message: str, intent_type: IntentType) -> bool:
        """Verifica si el mensaje coincide con algún patrón del tipo de intención"""
        patterns = self.PATTERNS.get(intent_type, [])
        return any(re.search(pattern, message) for pattern in patterns)
    
    def _is_numeric_input(self, message: str) -> bool:
        """Verifica si el mensaje es una entrada numérica"""
        try:
            float(message.replace(',', '.'))
            return True
        except ValueError:
            return False
    
    def _extract_target_mode(self, message: str) -> str:
        """Extrae el modo objetivo de un mensaje de cambio de modo"""
        if any(word in message for word in ['guíes', 'experto', 'paso a paso']):
            return ConversationMode.EXPERT.value
        elif any(word in message for word in ['libremente', 'chat', 'preguntar']):
            return ConversationMode.RAG.value
        return ConversationMode.HYBRID.value
    
    def _has_specific_data(self, message: str) -> bool:
        """Detecta si el mensaje contiene datos específicos (números, ubicaciones, etc.)"""
        # Buscar números (ej: "50m²", "100 watts")
        has_numbers = bool(re.search(r'\d+', message))
        # Buscar ubicaciones conocidas
        locations = ['ushuaia', 'buenos aires', 'córdoba', 'mendoza', 'norte', 'sur']
        has_location = any(loc in message for loc in locations)
        return has_numbers or has_location


class UnifiedContext:
    """
    Contexto unificado que mantiene el estado de la conversación
    a través de ambos sistemas (experto y RAG).
    """
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.mode = ConversationMode.HYBRID.value
        self.expert_state = {
            'current_node': 'inicio',
            'variables': {},
            'history': []
        }
        self.rag_history = []
        self.user_preferences = {}
        self.session_metadata = {
            'started_at': None,
            'last_interaction': None,
            'interaction_count': 0
        }
        self.paused_expert_node = None  # Para pausar y reanudar flujo experto
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el contexto a diccionario"""
        return {
            'conversation_id': self.conversation_id,
            'mode': self.mode,
            'expert_state': self.expert_state,
            'rag_history': self.rag_history,
            'user_preferences': self.user_preferences,
            'session_metadata': self.session_metadata,
            'paused_expert_node': self.paused_expert_node
        }
    
    def update_expert_state(self, node_id: str, variables: Dict[str, Any]):
        """Actualiza el estado del sistema experto"""
        self.expert_state['current_node'] = node_id
        self.expert_state['variables'].update(variables)
        self.expert_state['history'].append({
            'node': node_id,
            'variables': variables.copy()
        })
    
    def add_rag_interaction(self, query: str, response: str):
        """Registra una interacción con el sistema RAG"""
        self.rag_history.append({
            'query': query,
            'response': response
        })


class ConversationOrchestrator:
    """
    Orquesta la interacción entre el sistema experto y el RAG,
    proporcionando una experiencia unificada.
    """
    
    def __init__(self, expert_engine, rag_engine):
        """
        Args:
            expert_engine: Instancia del motor experto
            rag_engine: Instancia del motor RAG
        """
        self.expert_engine = expert_engine
        self.rag_engine = rag_engine
        self.intent_classifier = IntentClassifier()
        self.contexts: Dict[str, UnifiedContext] = {}
    
    def get_or_create_context(self, conversation_id: str) -> UnifiedContext:
        """Obtiene o crea un contexto unificado para la conversación"""
        if conversation_id not in self.contexts:
            self.contexts[conversation_id] = UnifiedContext(conversation_id)
        return self.contexts[conversation_id]
    
    async def process_message(self, conversation_id: str, message: str, 
                             option_index: Optional[int] = None,
                             input_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario y decide qué motor usar.
        
        Args:
            conversation_id: ID de la conversación
            message: Mensaje del usuario
            option_index: Índice de opción seleccionada (para flujo experto)
            input_values: Valores de entrada (para flujo experto)
            
        Returns:
            Dict con la respuesta y metadatos
        """
        context = self.get_or_create_context(conversation_id)
        context.session_metadata['interaction_count'] += 1
        
        # Clasificar intención
        intent = self.intent_classifier.classify(message, context.to_dict())
        
        # Enrutar según intención
        if intent.type == IntentType.GUIDED_CALCULATION:
            # Usuario quiere un flujo guiado
            result = await self._handle_expert_flow(
                conversation_id, message, option_index, input_values
            )
            context.mode = ConversationMode.EXPERT.value
            return result
        
        elif intent.type == IntentType.FREE_QUERY:
            # Usuario hace una pregunta abierta
            result = await self._handle_rag_query(conversation_id, message)
            context.mode = ConversationMode.RAG.value
            return result
        
        elif intent.type == IntentType.PRODUCT_SEARCH:
            # Búsqueda de productos
            result = await self._handle_product_search(conversation_id, message)
            return result
        
        elif intent.type == IntentType.WEBER_QUERY:
            result = await self._handle_weber_query(conversation_id, message)
            return result
        
        elif intent.type == IntentType.CLARIFICATION:
            # Pregunta tangencial durante flujo guiado
            result = await self._handle_clarification(conversation_id, message)
            return result
        
        elif intent.type == IntentType.SWITCH_MODE:
            # Cambio de modo
            target_mode = intent.metadata.get('target_mode', ConversationMode.HYBRID.value)
            result = await self._handle_mode_switch(conversation_id, target_mode)
            return result
        
        elif intent.type == IntentType.HYBRID:
            # Modo híbrido: combinar ambos sistemas
            result = await self._handle_hybrid_mode(conversation_id, message)
            context.mode = ConversationMode.HYBRID.value
            return result
        
        # Fallback
        return await self._handle_hybrid_mode(conversation_id, message)
    
    async def _handle_expert_flow(self, conversation_id: str, message: str,
                                  option_index: Optional[int] = None,
                                  input_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Maneja el flujo del sistema experto"""
        context = self.get_or_create_context(conversation_id)
        
        # Procesar con el motor experto
        result = await self.expert_engine.process(
            conversation_id, 
            context.expert_state,
            option_index,
            input_values
        )
        
        # Actualizar contexto
        if 'node_id' in result:
            context.update_expert_state(result['node_id'], result.get('variables', {}))
        
        # Agregar metadatos de modo
        result['mode'] = ConversationMode.EXPERT.value
        result['mode_label'] = 'Modo Experto'
        
        return result
    
    async def _handle_rag_query(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Maneja una consulta al sistema RAG"""
        context = self.get_or_create_context(conversation_id)
        
        # Obtener contexto del experto si existe
        expert_context = context.expert_state.get('variables', {})
        
        # Consultar al RAG con contexto
        result = await self.rag_engine.query(message, expert_context)
        
        # Registrar interacción
        context.add_rag_interaction(message, result.get('answer', ''))
        
        # Agregar sugerencia de flujo guiado si es relevante
        if self._should_suggest_guided_flow(message):
            result['suggestion'] = {
                'type': 'switch_to_expert',
                'message': '¿Querés que te guíe en un cálculo preciso paso a paso?'
            }
        
        # Agregar metadatos de modo
        result['mode'] = ConversationMode.RAG.value
        result['mode_label'] = 'Modo Chat'
        
        return result
    
    async def _handle_product_search(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Maneja búsqueda de productos"""
        # Usar el RAG para búsqueda de productos
        result = await self.rag_engine.search_products(message)
        result['mode'] = ConversationMode.RAG.value
        result['mode_label'] = 'Búsqueda de Productos'
        return result
    
    async def _handle_clarification(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Maneja pregunta tangencial durante flujo guiado"""
        context = self.get_or_create_context(conversation_id)
        
        # Pausar el flujo experto
        context.paused_expert_node = context.expert_state['current_node']
        
        # Responder con RAG
        result = await self.rag_engine.query(message, context.expert_state.get('variables', {}))
        
        # Agregar opción para continuar
        result['clarification_mode'] = True
        result['continue_option'] = {
            'text': 'Continuar con el cálculo',
            'action': 'resume_expert'
        }
        result['mode'] = ConversationMode.HYBRID.value
        result['mode_label'] = 'Aclaración'
        
        return result
    
    async def _handle_mode_switch(self, conversation_id: str, target_mode: str) -> Dict[str, Any]:
        """Maneja cambio de modo"""
        context = self.get_or_create_context(conversation_id)
        context.mode = target_mode
        
        if target_mode == ConversationMode.EXPERT.value:
            # Iniciar o reanudar flujo experto
            if context.paused_expert_node:
                context.expert_state['current_node'] = context.paused_expert_node
                context.paused_expert_node = None
            return await self._handle_expert_flow(conversation_id, "", None, None)
        
        elif target_mode == ConversationMode.RAG.value:
            return {
                'type': 'mode_switch',
                'mode': ConversationMode.RAG.value,
                'mode_label': 'Modo Chat',
                'text': 'Perfecto, ahora puedes hacerme cualquier pregunta sobre calefacción.',
                'is_final': False
            }
        
        return {
            'type': 'mode_switch',
            'mode': ConversationMode.HYBRID.value,
            'mode_label': 'Modo Híbrido',
            'text': 'Modo híbrido activado. Puedo guiarte o responder preguntas libremente.',
            'is_final': False
        }
    
    async def _handle_hybrid_mode(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Maneja modo híbrido combinando experto y RAG"""
        context = self.get_or_create_context(conversation_id)
        
        # Obtener información del RAG
        rag_result = await self.rag_engine.query(message, context.expert_state.get('variables', {}))
        
        # Obtener sugerencia del experto
        expert_suggestion = await self.expert_engine.suggest_next_step(
            context.expert_state.get('variables', {})
        )
        
        # Fusionar respuestas
        merged_result = self._merge_responses(rag_result, expert_suggestion)
        merged_result['mode'] = ConversationMode.HYBRID.value
        merged_result['mode_label'] = 'Modo Híbrido'
        
        return merged_result
    
    def _merge_responses(self, rag_result: Dict[str, Any], 
                        expert_suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """Fusiona respuestas del RAG y el experto"""
        merged = {
            'type': 'hybrid',
            'rag_answer': rag_result.get('answer', ''),
            'expert_suggestion': expert_suggestion.get('suggestion', ''),
            'options': []
        }
        
        # Agregar opciones del experto si existen
        if expert_suggestion.get('options'):
            merged['options'].extend(expert_suggestion['options'])
        
        # Agregar opción para búsqueda de productos si el RAG lo sugiere
        if rag_result.get('products'):
            merged['products'] = rag_result['products']
        
        return merged
    
    def _should_suggest_guided_flow(self, message: str) -> bool:
        """Determina si se debe sugerir un flujo guiado"""
        calculation_keywords = ['calcular', 'dimensionar', 'cuántos', 'necesito']
        return any(keyword in message.lower() for keyword in calculation_keywords)

    async def _handle_weber_query(self, conversation_id: str, message: str) -> dict:
        """
        Maneja consultas sobre productos Weber.
        Usa el WeberRAGEngine en lugar del RAG de PEISA.
        """
        try:
            from RAG_engine.query.rag_llm_weber import search_and_answer
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