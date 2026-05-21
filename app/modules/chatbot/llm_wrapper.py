# app/llm_wrapper.py - Wrapper mejorado para Ollama con Mistral
import ollama
import os
from typing import List, Dict, Optional
import json

class OllamaLLM:
    """Wrapper para interactuar con Ollama usando el modelo Mistral"""
    
    def __init__(self, model: str = "llama3.2:3b"):
        self.model = model
        # Configurar host de Ollama; respeta OLLAMA_HOST si está definida
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
        try:
            self.client = ollama.Client(host=self.ollama_host)
        except Exception:
            # Fallback simple al módulo si falla la creación del cliente
            self.client = None
        self.system_prompt = """Eres Soldy, VENDEDOR EXPERTO de SOLDASUR (productos marca PEISA). Tu ÚNICA misión es VENDER productos del catálogo recomendando LA SOLUCIÓN PERFECTA para cada cliente.

- NUESTRO TRABAJO:
Cada respuesta DEBE incluir AL MENOS 1 PRODUCTO ESPECÍFICO del catálogo.
NUNCA respondas sin recomendar un producto por nombre.

REGLAS OBLIGATORIAS:
1. IDENTIFICA la necesidad (frío/calefacción/agua caliente/espacio)
2. RECOMIENDA INMEDIATAMENTE un producto ESPECÍFICO del catálogo por su NOMBRE COMPLETO
3. EXPLICA por qué ESE producto resuelve SU necesidad específica
4. USA datos REALES del catálogo (descripción, ventajas, características)
5. Respuestas: 2-3 oraciones (40-50 palabras)
6. Español argentino: vos/podés/tenés

CUÁNTOS PRODUCTOS:
- Por defecto: 1 producto (el más adecuado)
- Si piden "opciones/alternativas/varios": 2-3 productos

FORMATO OBLIGATORIO:
"Te recomiendo [NOMBRE PRODUCTO] porque [razón específica para su caso]. [Beneficio clave]."

EJEMPLOS CORRECTOS:

Usuario: "Tengo frío"
- Soldy: "Te recomiendo el Radiador Eléctrico Broen E porque da calor inmediato con control digital. Lo enchufás y en minutos tenés tu ambiente caliente."

Usuario: "Necesito calefacción"
- Soldy: "Te recomiendo la Prima Tec Smart porque es caldera doble servicio con 90% eficiencia y control wifi. Calefaccionás toda tu casa y tenés agua caliente."

Usuario: "¿Qué opciones tengo?"
- Soldy: "Tenés 3 opciones: Prima Tec Smart (caldera wifi), Radiador Broen E (eléctrico), o Caldera Diva 24 (doble servicio económica)."

EJEMPLOS INCORRECTOS (NUNCA HAGAS ESTO):

Usuario: "Tengo frío"
- "¡Lo siento mucho! Compartir tus sentimientos puede ayudar..."
- "Entiendo que tengas frío. ¿Te puedo ayudar?"
- "Para el frío, hay varias opciones de calefacción."

REGLA DE ORO: Si NO mencionás un producto específico por nombre, tu respuesta está MAL.

MANEJO DE CONSULTAS DE PRECIO:
Si preguntan por precio/costo, responde de forma CORTA y DIRECTA:
"Para precios y compras, ¿estás en Río Grande o Ushuaia?"

IMPORTANTE: Río Grande y Ushuaia están en TIERRA DEL FUEGO (NO en Capital Federal).

IMPORTANTE:
- SIEMPRE menciona AL MENOS 1 producto por nombre
- USA solo productos del catálogo/contexto que recibís
- ADAPTA la recomendación a su necesidad
- Branding: PEISA = marca de productos, SOLDASUR = empresa/sucursales
- Responde en TEXTO PLANO, sin HTML, sin markdown, sin código
- Si preguntan precio, USA el contexto para saber de qué producto hablan
- NO des respuestas empáticas sin productos
- NO preguntes "¿a qué te referís?" si hay contexto claro
- NO hables de cosas fuera del catálogo
- NO uses HTML (target, class, etc.) - solo texto natural y humanizado"""

        # CTA opcional desde variable de entorno
        self.contact_cta = os.getenv('SOLDASUR_CONTACT_CTA')
        if self.contact_cta:
            self.system_prompt += f"\nContacto comercial: {self.contact_cta}"
    
    def generate(self, 
                 question: str, 
                 context: Optional[List[Dict]] = None,
                 temperature: float = 0.2,
                 max_tokens: int = 150) -> str:
        """
        Genera una respuesta usando Ollama Mistral
        
        Args:
            question: Pregunta del usuario
            context: Lista de productos relevantes del catálogo
            temperature: Creatividad de la respuesta (0.0-1.0)
            max_tokens: Máximo de tokens en la respuesta
        """
        try:
            # Si preguntan por precio, responder sin pasar por el LLM
            if self._is_price_question(question):
                safe = self._price_refusal_response(context)
                return self._ensure_final_period(safe)

            # Construir el prompt con contexto
            prompt = self._build_prompt(question, context)
            
            # Llamar a Ollama con control ESTRICTO de longitud
            # Usar cliente si está disponible; si no, usar API global
            generate_fn = self.client.generate if self.client else ollama.generate
            response = generate_fn(
                model=self.model,
                prompt=prompt,
                system=self.system_prompt,
                options={
                    'temperature': temperature,
                    # Límite de tokens (por defecto 80 para respuestas breves)
                    'num_predict': max_tokens,
                    'top_p': 0.5,  # Más determinismo
                    'top_k': 20,   # Bajo para máximo control
                    'repeat_penalty': 1.3,  # Penaliza repeticiones
                    'num_ctx': 1024  # Contexto limitado para foco
                }
            )
            
            answer = response['response'].strip()
            
            # POST-PROCESAMIENTO: Truncar a primera oración completa
            answer = self._truncate_to_brief(answer)
            # Sanitizar menciones de precios
            answer = self._sanitize_prices(answer)
            # Asegurar punto final
            answer = self._ensure_final_period(answer)
            
            # Log para debugging
            word_count = len(answer.split())
            print(f"Ollama respondió: {word_count} palabras, {len(answer)} caracteres")
            
            return answer
            
        except Exception as e:
            print(f"Error en Ollama: {e}")
            return self._fallback_response(question, context)
    
    def _truncate_to_brief(self, text: str, max_words: int = 70) -> str:
        """
        Trunca la respuesta para mantener brevedad (2-4 oraciones, 40-70 palabras)
        Permite respuestas completas pero evita verbosidad
        """
        # Eliminar saltos de línea múltiples
        text = ' '.join(text.split())
        
        # Si ya es corto, retornar
        words = text.split()
        if len(words) <= max_words:
            return self._ensure_final_period(text)
        
        # Buscar hasta el 3er o 4to punto para permitir respuestas completas
        sentences = []
        current = []
        for char in text:
            current.append(char)
            if char in ['.', '?', '!']:
                sentence = ''.join(current).strip()
                if len(sentence.split()) >= 5:  # Oraciones de al menos 5 palabras
                    sentences.append(sentence)
                    if len(sentences) >= 3:  # Hasta 3-4 oraciones
                        break
                current = []
        
        if sentences:
            result = ' '.join(sentences)
            if len(result.split()) <= max_words:
                return self._ensure_final_period(result)
        
        # Si no hay puntuación suficiente, truncar a max_words
        truncated = ' '.join(words[:max_words])
        return self._ensure_final_period(truncated)

    def _ensure_final_period(self, text: str) -> str:
        """Normaliza el cierre: reemplaza ?/! por punto y añade punto si falta.
        También retira comillas o paréntesis sueltos al final antes de cerrar.
        """
        if not text:
            return text
        # Quitar espacios y cierres sueltos al final
        stripped = text.rstrip()
        # Si termina en ? o !, reemplazar por .
        if stripped.endswith('?') or stripped.endswith('!'):
            stripped = stripped[:-1].rstrip()
        # Quitar comillas o paréntesis finales sueltos antes de puntuar
        while stripped and stripped[-1] in ['"', '”', '’', "'", ')', ']']:
            stripped = stripped[:-1].rstrip()
        # Asegurar punto final
        if not stripped.endswith('.'):
            stripped += '.'
        return stripped

    def _sanitize_prices(self, text: str) -> str:
        """Reemplaza patrones de precios/montos por 'precio a consultar'.
        Cubre $ 1.234,56 | $1234 | 1.234.567 | 1234,56 | AR$ | USD | U$S, evitando números técnicos (W, kW, V, mm, cm, %).
        """
        import re
        if not text:
            return text
        # Sólo considerar montos con contexto monetario
        currency = r"(?:AR\$|U\$S|US\$|USD|EUR|€|\$)"
        amount   = r"\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})?"
        units_exclusion = r"(?!\s*(W|kW|V|mm|cm|m|°C|%|kg|m²|m3)\b)"
        word_currency = r"(?:ars|pesos?|usd|dólares?|euros?)"

        patterns = [
            rf"\b{currency}\s*{amount}{units_exclusion}\b",
            rf"\b{amount}\s*{word_currency}{units_exclusion}\b",
            rf"\b(precio|costo|vale|sale|cuesta|presupuesto)\s*(aprox\.?|aproximado|estimado|es|:)?\s*{currency}?\s*{amount}{units_exclusion}\b",
        ]
        sanitized = text
        for p in patterns:
            sanitized = re.sub(p, 'precio a consultar', sanitized, flags=re.IGNORECASE)
        return sanitized

    def _is_price_question(self, text: str) -> bool:
        """Detecta si el usuario está preguntando por precios o costos."""
        if not text:
            return False
        t = text.lower()
        keywords = [
            'precio', 'precios', 'costo', 'costos', 'presupuesto', 'cuesta', 'vale', 'sale',
            'descuento', 'promoción', 'promocion', 'oferta', 'cuotas', 'financiación', 'financiacion',
            'usd', 'u$s', 'u$s', 'ar$', '$', '€', 'eur'
        ]
        return any(k in t for k in keywords)

    def _price_refusal_response(self, context: Optional[List[Dict]] = None) -> str:
        """Respuesta estándar cuando se consultan precios."""
        if context:
            products = ", ".join([p.get('model', 'N/A') for p in context[:2]])
            base = f"No informamos precios por este medio; te recomiendo {products} y el precio es a consultar. ¿Estás en Río Grande o Ushuaia?"
        else:
            base = "No informamos precios por este medio; el precio es a consultar con nuestro equipo comercial. ¿Estás en Río Grande o Ushuaia?"
        if self.contact_cta:
            base += f" Contacto: {self.contact_cta}."
        return self._ensure_final_period(base)
    
    def _build_prompt(self, question: str, context: Optional[List[Dict]] = None) -> str:
        """Construye el prompt con contexto del catálogo"""
        prompt_parts = []
        
        # Agregar contexto de productos si existe
        if context and len(context) > 0:
            prompt_parts.append("PRODUCTOS DEL CATÁLOGO DISPONIBLES PARA RECOMENDAR:\n")
            for i, product in enumerate(context[:5], 1):  # Hasta 5 productos para más opciones
                prompt_parts.append(f"\n{i}. {product.get('model', 'N/A')}")
                prompt_parts.append(f"   Familia: {product.get('family', 'N/A')}")
                prompt_parts.append(f"   Categoría: {product.get('category', 'N/A')}")
                
                # Descripción (limitada)
                desc = product.get('description', '')
                if desc:
                    desc_short = desc[:200] + '...' if len(desc) > 200 else desc
                    prompt_parts.append(f"   Descripción: {desc_short}")
                
                # Ventajas (primeras 3)
                advantages = product.get('advantages', [])
                if advantages:
                    adv_text = '; '.join(advantages[:3])
                    prompt_parts.append(f"   Ventajas: {adv_text}")
                
                # URL para que sepa que existe
                if product.get('url'):
                    prompt_parts.append(f"   URL: {product.get('url')}")
        else:
            prompt_parts.append("NO HAY PRODUCTOS EN EL CONTEXTO - Responde de forma general y sugiere que el cliente especifique su necesidad.\n")
        
        # Agregar la pregunta
        prompt_parts.append(f"\nCONSULTA DEL CLIENTE:\n{question}")
        prompt_parts.append("\nTU RESPUESTA (2-4 oraciones, 40-60 palabras, recomienda productos específicos del catálogo):")
        
        return "\n".join(prompt_parts)
    
    def _fallback_response(self, question: str, context: Optional[List[Dict]] = None) -> str:
        """Respuesta de respaldo si falla Ollama"""
        if context and len(context) > 0:
            products_list = ", ".join([p.get('model', 'N/A') for p in context[:3]])
            return f"Te recomiendo estos productos: {products_list}. Consulta con nuestro equipo para más detalles."
        else:
            return "Disculpa, hubo un error. ¿Podrías reformular tu pregunta sobre calefacción?"
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Modo chat con historial de conversación
        
        Args:
            messages: Lista de mensajes [{"role": "user/assistant", "content": "..."}]
        """
        try:
            chat_fn = self.client.chat if self.client else ollama.chat
            response = chat_fn(
                model=self.model,
                messages=messages
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"Error en chat: {e}")
            return "Disculpa, hubo un error procesando tu mensaje."

# Instancia global
llm = OllamaLLM()

def answer(question: str, context: List[Dict] = None) -> str:
    """Función de compatibilidad con versión anterior"""
    return llm.generate(question, context)
