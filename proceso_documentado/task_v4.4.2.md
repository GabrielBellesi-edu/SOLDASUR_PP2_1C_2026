# Checklist de Tareas v4.4.2 — Ajuste de Prompts y Estilo Rioplatense en Weber

Este archivo hace seguimiento a los cambios y la verificación para la versión **v4.4.2**.

---

## 📋 Tareas de Desarrollo

- [x] **1. Refinar Prompts de Weber (`configs/prompts.json`)**
  - [x] Modificar `configs/prompts.json` para agregar reglas estrictas y ejemplos correctos/incorrectos (*few-shot*) para el agente Weber.
  - [x] Sincronizar el system prompt por defecto `SYSTEM_PROMPT_WEBER_DEFAULT` en `RAG_engine/query/weber_rag_llm.py`.

---

## 🛠️ Plan de Verificación

- [x] **1. Verificación de Respuestas de Chat:**
  - [x] Validar que la respuesta a *"que productos tiene weber?"* no use el modismo "Che" ni "mirá".
  - [x] Validar que no contenga errores de conjugación (como "si tenés consultando").
  - [x] Asegurar que el voseo sea profesional y respetuoso.
