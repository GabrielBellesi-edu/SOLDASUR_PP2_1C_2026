# Checklist de Tareas v4.4.1 — Sistema Experto y Enrutamiento Neutro

Este archivo hace seguimiento a los cambios y la verificación para la versión **v4.4.1**.

---

## 📋 Tareas de Desarrollo

- [x] **1. Configuración de Prompts (`configs/prompts.json`)**
  - [x] Agregar la clave `"neutral"` en [prompts.json](../configs/prompts.json).
- [x] **2. Eliminación de Parámetros de Caché (`web_app/index.html`)**
  - [x] Remover el sufijo `?v=...` de la hoja de estilos CSS en [index.html](../web_app/index.html).
  - [x] Remover el sufijo `?v=...` de los scripts en [index.html](../web_app/index.html).
- [x] **3. Desactivación de Caché en el Backend (`app/main.py`)**
  - [x] Implementar middleware HTTP de control de caché en [main.py](main.py) para archivos `.js`, `.css` y `.json`.
- [x] **4. Enrutamiento Semántico y Respuestas Neutras (`app/main.py`)**
  - [x] Importar `IntentClassifier` e `IntentType` de `app.orchestrator` en [main.py](main.py).
  - [x] Instanciar `intent_classifier` en [main.py](main.py).
  - [x] Reemplazar la lógica de `_is_weber_query` en `/api/chat` usando el clasificador semántico.
  - [x] Implementar respuesta neutral llamando a Ollama con la configuración neutral si la consulta no es específica.

---

## 🛠️ Plan de Verificación

- [x] **1. Verificación del Servidor:**
  - [x] Iniciar uvicorn y asegurar que arranque sin errores de importación o sintaxis.
- [x] **2. Verificación de Caché (Network Headers):**
  - [x] Validar que el header `Cache-Control` se envíe con `no-store, no-cache, must-revalidate, max-age=0` para recursos `.js` y `.css`.
- [x] **3. Verificación de Enrutamiento Semántico:**
  - [x] Validar que "hola" retorne respuesta neutra y sin productos.
  - [x] Validar que "pegamento" o "pastina" vaya a Weber.
  - [x] Validar que "caldera" o "radiador" vaya a PEISA.
