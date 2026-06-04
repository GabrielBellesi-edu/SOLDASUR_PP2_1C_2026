# Checklist de Tareas v4.4.6 — Homogeneización de Badges de Categoría en Tarjetas de Producto

Este archivo hace seguimiento a los cambios y la verificación para la versión **v4.4.6**.

---

## 📋 Tareas de Desarrollo

- [x] **1. Priorizar Categoría en Badges de Producto (Frontend)**
  - [x] Modificar `web_app/js_modules/core.js` para renderizar el badge priorizando `category` sobre `family` (`product.category || product.family || 'Producto'`).
  - [x] Modificar `web_app/js_modules/chatbot.js` para aplicar el mismo orden de prioridad en el badge de las tarjetas devueltas en la conversación.

- [x] **2. Pruebas de Verificación**
  - [x] Recargar el frontend y realizar una simulación del sistema experto Weber y una consulta RAG libre.
  - [x] Validar que tanto la tarjeta del sistema experto como las tarjetas sugeridas por el chat muestren `"Revestimientos plásticos"` de manera uniforme.

- [x] **3. Documentación**
  - [x] Crear bitácora `proceso_documentado/v4.4.6.md`.
  - [x] Crear task list `proceso_documentado/task_v4.4.6.md` (este archivo).
