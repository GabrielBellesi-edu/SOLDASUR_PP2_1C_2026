# SoldaSur IA Chatbot

Asistente para asesoramiento en calefacción (PEISA) que combina un sistema experto (IA simbólica por reglas) y un chatbot con RAG + LLM local (Ollama).

## Contexto del proyecto

Trabajo realizado con la empresa Soldasur en el marco de la materia Practica Profesionalizante II (PP2), 2º cuatrimestre 2025. El dominio es el asesoramiento técnico-comercial de calefacción con catálogo de productos PEISA, priorizando una solución local (sin dependencias de nubes públicas) y con documentación profesional.

## Objetivo

- Escalar y profesionalizar un prototipo existente, unificando el sistema experto (reglas) con el chatbot (RAG + LLM) bajo una misma experiencia.
- Mejorar mantenibilidad, modularidad y calidad de datos (scraping/ingesta), con deployment local.
- Entregar documentación técnica y operativa para continuidad del proyecto.

## Alcance y entregables

- Sistema experto: flujo guiado con cálculos y reglas para piso radiante, radiadores y calderas.
- Chatbot con RAG: recuperación semántica de productos y generación con LLM (Ollama) con respuestas breves y enfocadas.
- Orquestación opcional: clasificación de intención y modos EXPERTO/RAG/HÍBRIDO listos para consolidar en backend.
- Scraping e ingesta: actualización de catálogo desde peisa.com.ar y pipeline de embeddings/consulta opcional.
- Documentación modular: glosario, guías del chatbot y del experto, scraping y manual de escalamiento.
- Puesta en marcha local y troubleshooting.

## Equipo

Equipo 2 – PP2 SOLDASUR 2C 2025

- Integrantes: Cussi Nicolás · Biason Franco · Bolaña Silvia · Luna Luciano
- Metodología: Ágil (Scrum) con sprints; gestión en Trello y GitHub.

## Características

- Modo Chat (RAG + LLM): recomendaciones en lenguaje natural de productos PEISA, mencionando al menos un producto por nombre.
- Modo Experto (reglas): cálculo guiado de potencia para piso radiante, radiadores y calderas con resultados explicables.
- Catálogo actualizable por scraping del sitio de PEISA.
- 100% local (Ollama); sin dependencias de APIs externas.

## Inicio rápido

Requisitos
- Python 3.10+
- Ollama instalado y corriendo: https://ollama.ai
- Modelo LLM local:
   ```bash
   ollama pull llama3.2:3b
   ```

Instalación
```bash
# Crear y activar entorno (Windows)
python -m venv venv
venv\Scripts\activate

# Dependencias
pip install -r requirements.txt
```

Ejecución
- Opción A (frontend estático):
   ```bash
   python -m http.server 8000
   # Abrir http://localhost:8000/
   ```
- Opción B (backend FastAPI):
   ```bash
   python -m uvicorn app.main:app --reload
   # Abrir http://localhost:8000/
   ```

## Arquitectura (resumen)

- Front-end: `index.html`, `soldasur.js`, `soldasur.css`
   - UI del widget con 3 entradas: Guíame (experto), Tengo una pregunta (chat), Buscar productos.
- Sistema Experto: `app/modules/expertSystem/expert_engine.py` + `app/peisa_advisor_knowledge_base.json`
   - Nodos de preguntas/cálculos/respuestas; funciones auxiliares de recomendación.
- Chatbot RAG: `app/modules/chatbot/llm_wrapper.py`, `app/modules/chatbot/rag_engine_v2.py`
   - Recuperación con FAISS + embeddings y generación con Ollama.
- Scraping: `app/modules/scraping/product_scraper.py`
   - Actualiza `data/products_catalog.json` (descripciones, ventajas, URL).
- API/Orquestación: `app/main.py`, `app/orchestrator.py`
   - Endpoints de conversación y clasificador de intención (híbrido listo para consolidar).

## Documentación

- Glosario: `docs/GLOSARIO.md`
- Chatbot: `docs/CHATBOT.md`
- Sistema Experto: `docs/SISTEMA_EXPERTO.md`
- Scraping: `docs/SCRAPING.md`
- Manual para escalar: `docs/MANUAL_ESCALAMIENTO.md`

## Estructura del proyecto (completa)

```
pp2-soldasur-2c-2025/
├── LICENSE
├── Makefile
├── README.md
├── requirements.txt
├── index.html
├── soldasur.css
├── soldasur.js
├── __pycache__/
├── images/
├── app/
│   ├── app.py
│   ├── ESTRUCTURA.txt
│   ├── main.py
│   ├── models.py
│   ├── orchestrator.py
│   ├── peisa_advisor_knowledge_base.json
│   ├── soldasur.js.backup
│   ├── __pycache__/
│   ├── img/
│   └── modules/
│       ├── chatbot/
│       │   ├── chatbot.js
│       │   ├── llm_wrapper.py
│       │   ├── rag_engine_v2.py
│       │   └── __pycache__/
│       ├── expertSystem/
│       │   ├── expert_engine.py
│       │   ├── expertSystem.js
│       │   ├── models.py
│       │   ├── product_loader.py
│       │   ├── README.md
│       │   └── __pycache__/
│       └── scraping/
│           ├── inspect_peisa.py
│           └── product_scraper.py
├── configs/
│   └── params.yaml
├── data/
│   └── products_catalog.json
├── embeddings/
│   └── products.faiss
├── images/
├── ingest/
│   └── ingest.py
├── models/
├── query/
│   ├── query.py
│   └── __pycache__/
├── scripts/
│   └── test_embeddings.py
└── docs/
    ├── GLOSARIO.md
    ├── CHATBOT.md
    ├── SISTEMA_EXPERTO.md
    ├── SCRAPING.md
    └── MANUAL_ESCALAMIENTO.md
```

## Tareas comunes

- Actualizar catálogo por scraping:
   ```bash
   python app/modules/scraping/product_scraper.py
   ```
- Regenerar embeddings (opcional):
   ```bash
   python ingest/ingest.py data/processed/products_mock.csv
   ```
- Probar consulta RAG filtrada:
   ```bash
   python query/query.py "¿Tienen calderas de más de 17000 W?"
   ```

## Funcionamiento

- Sistema Experto (reglas)
   - Flujo de preguntas y cálculos definido en `app/peisa_advisor_knowledge_base.json`.
   - El motor `expert_engine.py` interpreta cada nodo y ejecuta expresiones controladas (sin `__builtins__`).
   - Funciones auxiliares seguras para recomendar calderas, radiadores y formatear resultados.

- Chatbot (RAG + LLM)
   - Recuperación semántica de productos (FAISS + SentenceTransformers) y respuesta generada por Ollama.
   - Wrapper `llm_wrapper.py` aplica un prompt de sistema estricto (brevedad, mención de producto, manejo de precios).
   - El front-end `chatbot.js` reduce el contexto a 3–5 productos relevantes para mejorar precisión.

- Catálogo y scraping
   - `product_scraper.py` extrae productos de peisa.com.ar (modelo, ventajas, características, URL) y los guarda en `data/products_catalog.json`.
   - El mismo catálogo alimenta el experto (decisiones) y el RAG (recuperación).

## Endpoints (FastAPI)

- GET `/` → sirve `index.html`.
- POST `/start` → inicia una conversación del experto (estado por `conversation_id`).
- POST `/reply` → procesa una opción/entrada y devuelve el siguiente mensaje.
- GET `/ask?question=...` → ejemplo simple de RAG.
- GET `/health` → verificación de estado.

## Configuración

- Ollama: por defecto en `http://127.0.0.1:11434`. Modelo sugerido `llama3.2:3b`.
- Para cambiar el modelo/URL:
   - Back-end: editar `app/modules/chatbot/llm_wrapper.py`.
   - Front-end: revisar `OLLAMA_URL` en `app/modules/chatbot/chatbot.js` si aplica.

## Datos y embeddings

- Catálogo: `data/products_catalog.json` (generado/actualizado por el scraper).
- Embeddings persistentes (opcional):
   - `ingest/ingest.py` crea `embeddings/products.faiss` y una base SQLite (si está configurada).
   - `query/query.py` ejecuta búsquedas con filtros (tipo y potencia mínima aproximada).

## Limitaciones conocidas

- Cambios en el HTML del sitio de PEISA pueden romper el scraping (ajustar selectores).
- Primer uso del modelo de embeddings puede ser más lento por carga inicial.
- El índice FAISS en memoria se reconstruye al arrancar si no se usa el pipeline de ingestión persistente.

## Contribuir

- Mantener PRs pequeños y descriptivos.
- Ejecutar el scraper y validar `data/products_catalog.json` antes de cambios que dependan del catálogo.
- Documentar nuevas reglas del experto en `docs/SISTEMA_EXPERTO.md` y nuevos parámetros del chatbot en `docs/CHATBOT.md`.

## Troubleshooting

- “No responde el chatbot”: verificar que Ollama esté activo en `http://127.0.0.1:11434` y el modelo descargado.
- “Sin productos”: correr el scraper o validar `data/products_catalog.json`.
- Respuestas largas: bajar `num_predict` o reforzar post-procesado en `llm_wrapper.py`.

## Licencia

Este proyecto se distribuye bajo los términos de la licencia incluida en `LICENSE`.