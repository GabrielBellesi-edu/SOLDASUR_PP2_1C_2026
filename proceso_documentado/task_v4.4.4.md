# Checklist de Tareas v4.4.4 — Consolidación de Saludo y Persistencia de Contexto de Conversación

Este archivo hace seguimiento a los cambios y la verificación para la versión **v4.4.4**.

---

## 📋 Tareas de Desarrollo

- [x] **1. Frontend: Consolidación de Saludo y Estado de Contexto**
  - [x] Agregar variables de contexto global en `web_app/js_modules/core.js` (`lastActiveBrand`, `lastActiveProduct`).
  - [x] Consolidar el saludo inicial de Weber en `web_app/js_modules/weber_expert.js` (`iniciarExpertoWeber` y `renderWeberNode` con flag `skipQuestionPrint`).
  - [x] Guardar la marca y el producto recomendados en `weber_expert.js` al finalizar el cálculo (`lastActiveBrand`, `lastActiveProduct`).
  - [x] Enviar estas variables en el bodyPayload de `callOllama` en `web_app/js_modules/chatbot.js`.

- [x] **2. Backend: Enrutador y Motor RAG con Contexto Activo**
  - [x] Modificar `ChatRequest` en `app/main.py` para recibir `last_active_brand` y `last_active_product`.
  - [x] Pasar el contexto completo de marca y producto al clasificador semántico.
  - [x] En el clasificador de intenciones (`app/orchestrator.py`), implementar el enrutamiento contextual basado en `last_active_brand` si no hay cambio de marca explícito.
  - [x] Implementar la función `get_weber_product_by_model` en `RAG_engine/query/weber_rag_llm.py`.
  - [x] Modificar `search_and_answer` e `answer_weber` en `weber_rag_llm.py` para recibir e inyectar `last_active_product` en el RAG y en el prompt del LLM.

---

## 🛠️ Plan de Verificación

- [x] **1. Verificación de Consolidación de Saludos:**
  - [x] El saludo inicial de Weber y la primera pregunta aparecen ahora en un solo mensaje de sistema.

- [x] **2. Verificación de Preguntas de Seguimiento (Contexto RAG):**
  - [x] Al simular una consulta de seguimiento genérica (*"en que colores esta disponible?"*) posterior a una recomendación de Weber, el enrutador deriva correctamente la consulta a Weber en lugar de un saludo neutral.
  - [x] La respuesta de Ollama se enfoca y responde en función de la información del producto recomendado (*weberplast llaneado*).
