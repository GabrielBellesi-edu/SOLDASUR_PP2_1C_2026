# Checklist de Tareas v4.4.8 — Homogeneización de Botones, Corrección de Contexto, Rediseño de Tamaño y Miniaturas de Tarjetas de Producto

Este archivo hace seguimiento a los cambios y la verificación para la versión **v4.4.8**.

---

## 📋 Tareas de Desarrollo

- [x] **1. Homogeneizar Frontend: Tarjetas de Producto sugeridas en Asesor Experto (`core.js`)**
  - [x] Cambiar layout horizontal de dos columnas a un layout de una columna (botones abajo).
  - [x] Formatear el botón "Ver en [Marca]" con fondo azul (`#3b82f6`) y texto blanco.
  - [x] Formatear el botón "Consultar" con fondo verde (`#10b981`) y texto blanco.
  - [x] Agregar `event.stopPropagation()` al hacer click en el link "Ver en [Marca]" para no duplicar el evento click de la tarjeta.

- [x] **2. Homogeneizar Frontend: Tarjetas de Producto sugeridas en Chatbot RAG (`chatbot.js`)**
  - [x] Aplicar el mismo rediseño de layout vertical de una columna.
  - [x] Sincronizar clases, estilos de color y layout de los botones azul y verde.

- [x] **3. Corregir Fuga de Contexto en Asesor Experto PEISA (`peisa_expert.js`)**
  - [x] Seteo de `lastActiveBrand = 'PEISA'` y `lastActiveProduct` en todos los flujos de recomendación (piso, radiadores, calderas, toalleros) para actualizar el frontend al finalizar el cálculo.

- [x] **4. Integrar Contexto Activo en RAG libre de PEISA (Backend)**
  - [x] Implementar `get_peisa_product_by_model(model_name)` en `peisa_rag_query.py`.
  - [x] Modificar la firma de `OllamaLLM.generate()`, `_build_prompt()` y la función `answer()` en `peisa_rag_llm.py` para aceptar y utilizar `last_active_product` en el prompt.
  - [x] Actualizar el endpoint `/api/chat` en `main.py` para buscar, inyectar el producto activo en los resultados del RAG y pasarlo a `answer()`.
  - [x] Crear un script de test local `scratch/test_peisa_context.py` y verificar la respuesta a consultas ambiguas de seguimiento.

- [x] **5. Agrandar Contenedor de Chat en Versión Escritorio (`soldasur.css`)**
  - [x] Agrandar el ancho del chat base a `480px`.
  - [x] Agrandar el alto del chat base a `750px`.
  - [x] Configurar `max-height: 80vh` para dejar el 20% superior libre si la pantalla es de menor resolución.
  - [x] Resguardar la versión mobile con `max-height: none` en el media query para no heredar limitaciones.

- [x] **6. Integrar Imágenes de Catálogo y Miniaturas en Tarjetas (Frontend & Backend)**
  - [x] Actualizar `weber_build_catalog.py` para compilar los campos `imagen_url` e `imagen_local` en `weber_catalog.json`.
  - [x] Montar `/scraping` como directorio estático en `main.py` de FastAPI.
  - [x] Modificar la maquetación HTML de tarjetas en `core.js` y `chatbot.js` para añadir la columna derecha con la miniatura de `64px x 64px`.
  - [x] Implementar fallback de logos para productos de Weber (`weber-logo.png`) y PEISA (`peisa-logo.png`) si no cuentan con miniatura de producto.
  - [x] Añadir control de error `onerror` en el elemento `<img>` para que recaiga en el logo en fallas de carga HTTP.
  - [x] Ejecutar la compilación del catálogo de Weber mediante el script `weber_build_catalog.py`.

- [x] **7. Documentación**
  - [x] Crear/actualizar bitácora `proceso_documentado/v4.4.8.md`.
  - [x] Crear/actualizar task list `proceso_documentado/task_v4.4.8.md` (este archivo).
