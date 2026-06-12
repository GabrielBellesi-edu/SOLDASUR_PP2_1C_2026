# Manual de Escalamiento: Cómo Agregar una Nueva Línea de Productos

Este manual describe el procedimiento estándar, paso a paso, para integrar una nueva marca de producto (por ejemplo, **Tigre**, **Sica**, **IPS**, etc.) al sistema inteligente del Asistente Técnico unificado de **SOLDASUR**.

Gracias a la arquitectura dinámica introducida en la versión 5.0.0, este proceso **no requiere modificar el código principal de FastAPI ni el del Orquestador**.

---

## Estructura de Carpetas de la Marca

Para agregar la marca (llamémosla `NUEVA_MARCA` en este ejemplo), debes crear y ubicar los archivos en las siguientes carpetas dentro del proyecto:

```text
SOLDASUR_PP2_1C_2026/
├── RAG_engine/
│   ├── database/
│   │   ├── nueva_marca_metadata.json         # JSON con el catálogo de productos
│   │   └── nueva_marca_products.faiss        # Índice vectorial compilado de FAISS
│   │
│   ├── query/
│   │   ├── nueva_marca_rag_query.py         # Retrievial (búsqueda vectorial en FAISS)
│   │   └── nueva_marca_rag_llm.py           # Inferencia RAG (Prompt + llamada a Ollama)
│   │
│   └── scripts/
│       ├── nueva_marca_build_catalog.py    # Generador/limpiador del catálogo limpio
│       └── nueva_marca_build_embeddings.py # Generador del índice vectorial .faiss
```

---

## Paso 1: Compilar la Base de Datos Vectorial de la Marca

1. **Crear Catálogo JSON (`nueva_marca_metadata.json`):**
   * Prepara un archivo JSON estructurado con los productos de la marca. 
   * Se recomienda el siguiente formato estándar para compatibilidad con la interfaz de tarjetas del frontend:
     ```json
     [
       {
         "model": "Nombre Exacto del Producto",
         "category": "Categoría de producto",
         "description": "Ficha descriptiva completa para el LLM",
         "presentacion": "Medida/Bolsa/Unidad (ej: 25 kg)",
         "url": "https://url-del-fabricante.com/producto",
         "imagen_local": "/img/nueva_marca/imagen1.jpg",
         "imagen_url": "https://url-fabricante.com/imagen.jpg"
       }
     ]
     ```
   * Puedes usar o automatizar esto copiando y adaptando `RAG_engine/scripts/weber_build_catalog.py`.

2. **Generar el Índice Vectorial (`nueva_marca_products.faiss`):**
   * Copia `RAG_engine/scripts/weber_build_embeddings.py` a `RAG_engine/scripts/nueva_marca_build_embeddings.py`.
   * Cambia las constantes de ruta para apuntar a tus archivos JSON y FAISS de la nueva marca.
   * Ejecuta el script para compilar el índice semántico:
     ```bash
     python RAG_engine/scripts/nueva_marca_build_embeddings.py
     ```

---

## Paso 2: Crear los Scripts de Consulta del RAG

1. **Buscador de Productos (`nueva_marca_rag_query.py`):**
   * Copia `RAG_engine/query/weber_rag_query.py` a `RAG_engine/query/nueva_marca_rag_query.py`.
   * Actualiza las constantes de ruta al inicio del archivo:
     ```python
     FAISS_PATH = SCRIPT_DIR.parent / "database" / "nueva_marca_products.faiss"
     META_PATH  = SCRIPT_DIR.parent / "database" / "nueva_marca_metadata.json"
     ```
   * Renombra la función de búsqueda a `search_nueva_marca()`.
   * Si la marca no requiere calculadora de cantidades por superficie, puedes remover la función `calcular_cantidad()` para simplificar.

2. **Módulo LLM (`nueva_marca_rag_llm.py`):**
   * Copia `RAG_engine/query/weber_rag_llm.py` a `RAG_engine/query/nueva_marca_rag_llm.py`.
   * Modifica los imports al inicio para cargar la búsqueda creada arriba:
     ```python
     from .nueva_marca_rag_query import search_nueva_marca
     ```
   * Define el Prompt de Sistema de fallback (`SYSTEM_PROMPT_NUEVA_MARCA_DEFAULT`) instruyendo al modelo sobre el tono de la marca.
   * Cambia la función `_load_prompt_config()` para leer la sección `"nueva_marca"` en `configs/prompts.json`.
   * Adapta y renombra la función principal:
     ```python
     def search_and_answer(query: str, last_active_product: Optional[str] = None, top_k: int = 3) -> Dict[str, Any]:
         # ... lógica de búsqueda, filtrado por similitud y respuesta de Ollama ...
         return {
             "respuesta": respuesta,
             "productos": productos_frontend,
             "marca": "Nueva Marca"
         }
     ```

---

## Paso 3: Configurar el Prompts y LLM en `configs/prompts.json`

Añade los parámetros e instrucciones de personalidad de tu nueva marca en el archivo central de prompts:

```json
{
  "weber": { ... },
  "peisa": { ... },
  "neutral": { ... },
  "nueva_marca": {
    "system_prompt": "Sos Soldy, el asesor experto de SOLDASUR especializado en productos NUEVA_MARCA. Tus respuestas deben ser breves, profesionales y en español rioplatense...",
    "temperature": 0.2,
    "max_tokens": 250
  }
}
```

---

## Paso 4: Registrar la Marca en `configs/brands_registry.json`

Este es el paso fundamental para que el orquestador y el servidor reconozcan la marca dinámicamente. Añade tu marca en el archivo JSON:

```json
{
  "brands": {
    "WEBER": { ... },
    "PEISA": { ... },
    "NUEVA_MARCA": {
      "key": "NUEVA_MARCA",
      "display_name": "Nueva Marca",
      "intent_type": "nueva_marca_query",
      "direct_keywords": ["palabramarca", "keyword1", "keyword2", "keyword3"],
      "anchor_text": "descripción semántica natural en un párrafo breve de los productos y soluciones que comercializa esta marca",
      "rag_module": "RAG_engine.query.nueva_marca_rag_llm",
      "rag_function": "search_and_answer",
      "response_formatter": "weber"
    }
  }
}
```

### Campos de Configuración del Registro:
*   `intent_type`: Usar `"nueva_marca_query"` o `"free_query"` (para PEISA).
*   `direct_keywords`: Palabras clave únicas e inequívocas de la marca para enrutamiento instantáneo (0ms).
*   `anchor_text`: Texto conceptual que describe los productos. Se codificará vectorialmente para evaluar la similitud contra consultas complejas de los usuarios.
*   `rag_module`: Ruta de importación de Python para la lógica LLM creada en el Paso 2.
*   `rag_function`: Nombre de la función de alto nivel expuesta en dicho archivo.
*   `response_formatter`: 
    *   `weber`: Usa el formateador Weber (búsqueda unificada + renderizado compatible con cálculos de rendimiento).
    *   `peisa`: Usa el formateador PEISA (búsqueda externa + inyección del producto activo).
    *   `generic`: Si tu nueva función RAG retorna directamente una estructura personalizada básica (`{"respuesta": "...", "productos": [...]}`).

---

## Anexo: Cómo Agregar un Nuevo Sistema Experto (Calculadora)

Si la nueva marca que deseas incorporar requiere un **Sistema Experto con flujo de preguntas/respuestas estructurado y cálculos técnicos** (como el dimensionador de calderas de PEISA o la calculadora de bolsas de Weber), el flujo dinámico del RAG no es suficiente por sí solo. 

Debes integrar el nuevo sistema experto siguiendo la arquitectura existente del frontend y backend de **SOLDASUR**. Tienes dos caminos según la complejidad:

### Opción A: Sistema Experto basado en Árbol de Decisión (Recomendado)
Sigue el patrón de **PEISA/Weber** donde las preguntas y opciones se definen en un archivo JSON en el backend, y el motor de FastAPI responde paso a paso:

1. **Crear la Base de Conocimiento JSON:**
   * Crea un archivo (ej: `app/nueva_marca_knowledge_base.json`) con los nodos de tipo `opciones`, `entrada_usuario`, `calculo` y `respuesta`.
   * Ejemplo de estructura:
     ```json
     [
       {
         "id": "inicio_nueva_marca",
         "pregunta": "¿Qué cálculo deseas realizar?",
         "tipo": "opciones",
         "opciones": [
           { "texto": "Calcular Cañerías", "siguiente": "superficie_m2" }
         ]
       },
       {
         "id": "superficie_m2",
         "pregunta": "Ingresá los m² a cubrir:",
         "tipo": "entrada_usuario",
         "variable": "area",
         "siguiente": "procesar_calculo"
       }
     ]
     ```

2. **Crear y registrar los Endpoints en el Servidor (`app/main.py`):**
   * Inicializa la base de conocimiento o motor en `main.py`.
   * Crea dos endpoints dedicados para manejar las solicitudes del chat de este sistema experto:
     ```python
     @app.post("/expert/nueva_marca/start")
     async def start_nueva_marca_expert(request: StartConversationRequest):
         # Retorna el primer nodo del JSON
         
     @app.post("/expert/nueva_marca/reply")
     async def reply_nueva_marca_expert(request: ReplyRequest):
         # Guarda las variables en sesión, evalúa el cálculo matemático y retorna el siguiente nodo o resultado
     ```

3. **Crear el Módulo JS en el Frontend (`web_app/js_modules/`):**
   * Crea `web_app/js_modules/nueva_marca_expert.js`.
   * Implementa las funciones para iniciar el flujo (`iniciarExpertoNuevaMarca()`) y enviar respuestas al endpoint `/expert/nueva_marca/reply`.
   * Registra el script en `web_app/index.html`:
     ```html
     <script src="js_modules/nueva_marca_expert.js"></script>
     ```

4. **Vincular al Menú Principal (`web_app/soldasur.js`):**
   * En `startConversation()`, agrega la opción al menú principal del chat (ej: `"Calculadora Nueva Marca"`).
   * En `handleOptionClick(option)`, agrega la condicional para capturar el click de esa opción y ejecutar `iniciarExpertoNuevaMarca()`.

---

### Opción B: Calculadora 100% Frontend (Para cálculos sencillos)
Si el cálculo es muy simple y no requiere consultar bases de datos en el servidor, puedes resolver todo directamente en JavaScript:

1. Crea `web_app/js_modules/nueva_marca_expert.js`.
2. Utiliza las funciones compartidas de `core.js` (como `appendMessage`, `renderOptions`, `createNumberInput`) para interactuar con el usuario en el chat.
3. Resuelve el cálculo en JS y muestra el resultado usando tarjetas o burbujas directamente.
4. Vincula la opción de inicio en `web_app/soldasur.js`.



