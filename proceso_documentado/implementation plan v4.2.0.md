# Plan de Reestructuración y Estandarización de Archivos — SOLDASUR v4.2.0

Este plan detalla los pasos finales para realizar la reestructuración del repositorio, la simetría total de motores RAG, la actualización de importaciones en el backend y frontend, y la adaptación de la documentación.

## User Review Required

> [!IMPORTANT]
> - **Actualización de Importaciones de Weber RAG:** Se reemplazará el import de `app/modules/chatbot/weber_rag_engine` por los nuevos módulos simétricos `RAG_engine.query.weber_rag_llm` y `RAG_engine.query.weber_rag_query` en `app/main.py` y `app/orchestrator.py`.
> - **Catálogo e Imágenes en Frontend:** Ya se ha modificado `web_app/js_modules/core.js` para usar `web_app/data/peisa_catalog.json` e `img/...`.
> - **Actualización de Documentación:** Se adaptarán las rutas relativas en el glosario, manual de escalamiento, manual de usuario y especificaciones de scraping.

## Proposed Changes

### Backend FastAPI (`app/`)

#### [MODIFY] [main.py](../app/main.py)
- Corregir el import de `weber_rag_engine` en el endpoint `/ask_weber` para apuntar a `RAG_engine/query/weber_rag_llm.py` and `RAG_engine/query/weber_rag_query.py`.

#### [MODIFY] [orchestrator.py](../app/orchestrator.py)
- Cambiar la importación de `search_and_answer` de `weber_rag_engine` a `RAG_engine.query.weber_rag_llm`.

---

### Documentación y Manuales (`docs/` y Raíz)

#### [MODIFY] [CHATBOT.md](../docs/CHATBOT.md)
- Actualizar rutas de scripts de frontend (`web_app/js_modules/`), catálogo (`web_app/data/peisa_catalog.json`), e indexación/motores RAG en `RAG_engine/`.

#### [MODIFY] [GLOSARIO.md](../docs/GLOSARIO.md)
- Ajustar nombres de archivos de catálogo, scraper y rutas de ingesta.

#### [MODIFY] [MANUAL_ESCALAMIENTO.md](../docs/MANUAL_ESCALAMIENTO.md)
- Adaptar las rutas y scripts al nuevo estándar (scraping, ingesta y RAG).

#### [MODIFY] [SCRAPING.md](../docs/SCRAPING.md)
- Actualizar nombres y rutas de scripts (`scraping/peisa_product_scraper.py`) y catálogo.

#### [MODIFY] [SISTEMA_EXPERTO.md](../docs/SISTEMA_EXPERTO.md)
- Reflejar que el motor de inferencia server-side de PEISA corre en `app/app.py`, el de Weber en `app/modules/expertSystem/weber_expert_engine.py`, y en cliente se encuentran en `web_app/js_modules/`.

#### [MODIFY] [Manual_Usuario.md](../Manual_Usuario.md)
- Modificar el mapa del sistema y las descripciones del catálogo unificado (`peisa_catalog.json`), la nueva carpeta de imágenes (`img/`), y los scripts de ingesta/RAG reestructurados.

---

## Verification Plan

### Automated Tests & Ingest Verification
1. **Verificación de Ingesta:**
   - Ejecutar: `python RAG_engine/scripts/ingest.py --peisa`
   - Ejecutar: `python RAG_engine/scripts/ingest.py --weber`
   - Validar que recrea las bases y FAISS en `/RAG_engine/database/` sin errores de ruta.

### Manual Verification
1. **Inicio de FastAPI:**
   - Iniciar el servidor: `python -m uvicorn app.main:app --port 8000 --reload`
   - Validar que la carga e inicialización resuelvan sin fallos de importación.
2. **Pruebas de la Interfaz Web:**
   - Acceder a `http://localhost:8000`.
   - Probar que el chat con Soldy responda tanto de PEISA como de Weber.
   - Validar que los asesores expertos offline (PEISA y Weber) carguen correctamente.
