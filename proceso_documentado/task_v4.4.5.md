# Checklist de Tareas v4.4.5 — Prevención de Alucinación de Colores y Restricción de Brevedad en Weber

Este archivo hace seguimiento a los cambios y la verificación para la versión **v4.4.5**.

---

## 📋 Tareas de Desarrollo

- [x] **1. Refinar Prompts de Weber**
  - [x] Modificar `configs/prompts.json` para acortar las respuestas (máximo 2-3 oraciones) y agregar la regla de no alucinación de colores, con un ejemplo específico de few-shot.
  - [x] Sincronizar el system prompt por defecto `SYSTEM_PROMPT_WEBER_DEFAULT` en `RAG_engine/query/weber_rag_llm.py`.

- [x] **2. Pruebas de Verificación**
  - [x] Validar que la respuesta a *"en que colores viene?"* posterior a una recomendación de Weber no alucine colores inexistentes (como verde pastel) y sea breve (2-3 oraciones).

- [x] **3. Documentación**
  - [x] Crear bitácora `proceso_documentado/v4.4.5.md`.
  - [x] Crear task list `proceso_documentado/task_v4.4.5.md` (este archivo).
