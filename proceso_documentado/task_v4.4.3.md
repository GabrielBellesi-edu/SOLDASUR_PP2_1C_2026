# Checklist de Tareas v4.4.3 — Remoción de Presentaciones Repetitivas de Soldy

Este archivo hace seguimiento a los cambios y la verificación para la versión **v4.4.3**.

---

## 📋 Tareas de Desarrollo

- [x] **1. Modificar Prompts de Weber (`configs/prompts.json`)**
  - [x] Cambiar la regla de identificación repetida en `configs/prompts.json` (removiendo "IDENTIFICATE siempre como Soldy" y prohibiendo saludos introductorios si ya está iniciada la charla).
  - [x] Sincronizar la variable `SYSTEM_PROMPT_WEBER_DEFAULT` en `RAG_engine/query/weber_rag_llm.py`.

---

## 🛠️ Plan de Verificación

- [x] **1. Verificación de Respuestas de Chat:**
  - [x] Validar que la respuesta no vuelva a presentarse como "Soy Soldy" ni salude de nuevo en consultas técnicas de Weber.
  - [x] Comprobar que responda directo al grano y mantenga el voseo rioplatense profesional.
