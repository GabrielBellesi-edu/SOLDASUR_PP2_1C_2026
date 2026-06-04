# Documentación del Chatbot (RAG + LLM)

Esta guía explica el funcionamiento del chatbot “Soldy” y cómo configurarlo. Incluye detalles para usuarios sin conocimientos previos.

## Componentes

- Front-end: `web_app/js_modules/chatbot.js`
  - Carga `web_app/data/peisa_catalog.json` (y `weber_catalog.json`) en el navegador.
  - Filtra productos relevantes por consulta (`filterRelevantProducts`).
  - Construye un “system prompt” específico por consulta con productos relevantes (no todo el catálogo).
  - Llama a Ollama vía HTTP o a través de la API del Backend (`/api/chat`).
  - Sanitiza y acorta la respuesta (`cleanHtmlFromMessage`, `briefenResponse`).
  - Detecta productos mencionados y renderiza tarjetas (`detectMentionedProducts`, `renderProducts`).
  - Flujo de contacto comercial por ciudad (Río Grande/Ushuaia).

- LLM Wrapper: `RAG_engine/query/peisa_rag_llm.py`
  - Modelo por defecto: `llama3.2:3b` (Ollama local).
  - Prompt de sistema con reglas fuertes:
    - Mencionar al menos 1 producto por nombre.
    - 2–3 oraciones breves (40–60 palabras).
    - Manejo de precios: pedir ciudad (RG/Ushuaia), sanitizar montos.
    - Branding: PEISA (marca) y Soldasur (empresa/sucursales).
  - Post-procesamiento: truncar respuesta, normalizar punto final, evitar precios explícitos.

- Motor RAG (PEISA): `RAG_engine/query/peisa_rag_query.py`
  - Carga catálogo (`web_app/data/peisa_catalog.json`).
  - Embeddings: `SentenceTransformer('distiluse-base-multilingual-cased-v2')`.
  - Índice FAISS en `RAG_engine/database/peisa_products.faiss` y base SQLite en `peisa_products.db`.
  - `search_filtered(question, top_k)`: vectoriza consulta y recupera productos similares aplicando filtros por potencia/caldera.

- Motor RAG (Weber): `RAG_engine/query/weber_rag_query.py` y `weber_rag_llm.py`
  - Carga catálogo (`web_app/data/weber_catalog.json`).
  - Embeddings: `SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')`.
  - Índice FAISS en `RAG_engine/database/weber_products.faiss` y metadatos en `weber_metadata.json`.
  - `search_and_answer(query)`: busca productos, detecta superficies y calcula cantidades.

- Ingesta Unificada: `RAG_engine/scripts/ingest.py`
  - Ejecuta la ingesta modular para PEISA (`peisa_ingest.py`) y Weber (`weber_build_catalog.py` y `weber_build_embeddings.py`).
  - Genera las bases SQLite e índices FAISS en `RAG_engine/database/`.

## Configuración

- Ollama
  - Instalar desde https://ollama.ai y descargar el modelo:
    ```bash
    ollama pull llama3.2:3b
    ```
  - Endpoint por defecto: `http://127.0.0.1:11434`.
  - Para cambiar de modelo (ejemplo): actualizar en `peisa_rag_llm.py` y `weber_rag_llm.py` la variable del modelo.

- CORS y red
  - Si la UI corre en un origen distinto, habilitar CORS en el backend o servir todo desde el mismo host/puerto.

## Flujo de una consulta

1) Usuario: “Necesito calefacción para un ambiente chico, ¿qué me recomendás?”
2) `chatbot.js`: filtra 3–5 productos relevantes del catálogo.
3) Construye `system prompt` con esos productos (modelo, familia, descripción, ventajas, URL) y la pregunta del usuario.
4) Llama a Ollama con historial acotado (10 mensajes), baja temperatura y `num_predict` bajo.
5) Post-procesa el texto, resalta productos mencionados y muestra tarjetas “Ver”/“Consultar”.

## Ejemplo de llamada a Ollama

Payload típico (Ollama /api/chat):
```json
{
  "model": "llama3.2:3b",
  "messages": [
    {"role": "system", "content": "...contexto con productos relevantes..."},
    {"role": "user", "content": "Necesito calefacción para un ambiente chico"}
  ],
  "options": {"temperature": 0.3, "num_predict": 150, "top_p": 0.7, "top_k": 20}
}
```

## Parámetros sugeridos

- `chatbot.js`
  - `MAX_HISTORY_LENGTH = 10` para no saturar contexto.
  - Filtrar 3–5 productos relevantes por consulta.
- `peisa_rag_llm.py` y `weber_rag_llm.py`
  - `temperature=0.2–0.3`, `num_predict=150`, `top_p=0.5–0.7`, `top_k=20` → respuestas cortas y estables.
  - Sanitización de precios mediante regex con exclusión de unidades técnicas.
- `peisa_rag_query.py` y `weber_rag_query.py`
  - `top_k` de recuperación: 3–5.

## Requisitos y ejecución (standalone)

- Abrir la UI:
  - Opción 1 (estático):
    ```bash
    python -m http.server 8000
    # http://localhost:8000/
    ```
  - Opción 2 (backend):
    ```bash
    python -m uvicorn app.main:app --reload
    # http://localhost:8000/
    ```

## Consejos de precisión y performance

- Reducir el set de productos en el `system prompt` mejora foco y latencia.
- Enriquecer `web_app/data/peisa_catalog.json` y `weber_catalog.json` con descripciones y ventajas claras aumenta la calidad.
- Precalentar embeddings o iniciar el RAG Engine al boot para evitar latencia de primer uso.
- Usar GPU para SentenceTransformers si está disponible (opcional).

## Troubleshooting

- “No se puede llamar a Ollama”: verificar `http://127.0.0.1:11434` y que el modelo esté descargado.
- Respuestas largas: bajar `num_predict` o reforzar el post-procesamiento (`_truncate_to_brief`).
- Alucinaciones de productos: reforzar prompt y asegurar que el contexto incluye solo productos válidos.
