# Manual para escalar el proyecto (equipo futuro)

Guía práctica para que un nuevo equipo pueda mantener, extender y escalar el sistema.

## 1) Arquitectura (visión)

- Front-end: `index.html`, `soldasur.js`, `soldasur.css` + módulos `app/modules/chatbot` y `app/modules/expertSystem`.
- Sistema experto (IA simbólica): `expert_engine.py` + KB JSON, con funciones auxiliares para cálculos y recomendaciones.
- Chatbot (RAG + LLM): `rag_engine_v2.py` + `llm_wrapper.py` + catálogo JSON y/o embeddings FAISS.
- API (FastAPI): `app/main.py` (endpoints de conversación y demo RAG) y `app/orchestrator.py` (modo híbrido e intenciones, listo para consolidar servidor-side).

## 2) Puesta en marcha

- Requisitos:
  - Python 3.10+
  - `pip install -r requirements.txt`
  - Ollama instalado y corriendo; descargar modelo `ollama pull llama3.2:3b`
- Ejecutar
  - Front-end estático: `python -m http.server 8000` → `http://localhost:8000/`
  - Backend FastAPI: `python -m uvicorn app.main:app --reload` → `http://localhost:8000/`

## 3) Datos y catálogo

- Actualizar catálogo por scraping: `python app/modules/scraping/product_scraper.py`
- Regenerar embeddings (opcional; desde CSV procesado): `python ingest/ingest.py data/processed/products_mock.csv`
- Verificar consultas: `python query/query.py "¿Tienen calderas > 17000 W?"`

## 4) Agregar reglas al sistema experto

1. Editar `app/peisa_advisor_knowledge_base.json` (nodos con `id`, `tipo`, `pregunta`, `opciones`, `acciones`, `siguiente`).
2. En `calculo`, usar sólo funciones auxiliares expuestas (seguras) y variables del contexto.
3. Validar con casos de prueba manuales; si es posible, agregar tests automatizados (pendiente en repo).

## 5) Extender el chatbot/RAG

- Enriquecer `data/products_catalog.json` (descripciones y ventajas claras).
- Ajustar top_k y modelos de embeddings en `rag_engine_v2.py`.
- Afinar `llm_wrapper.py` (prompt, temperatura, longitud, sanitización de precios).

## 6) Estándares de desarrollo

- Ramas: `main` estable, features en `feat/*`, fixes en `fix/*`.
- Code style Python: `black`/`isort`/`flake8` (agregar si aún no están en CI).
- Commits: mensajes claros, en imperativo, referencia a issue cuando aplique.
- PRs: pequeños, con checklist (lint, pruebas manuales, screenshots cuando hay UI).

## 7) Observabilidad y métricas (sugerido)

- Logs: centralizar impresiones clave (inicio RAG, latencias, fallos de scraping, conteo de productos cargados).
- Métricas: número de consultas, tiempo de respuesta, hits sin producto, ratio de recomendaciones con clic.
- Error tracking: Sentry/Elastic APM (opcional).

## 8) Performance

- Inicialización perezosa de modelos o precarga al inicio (RAG embeddings y modelo LLM).
- Reducir tamaño de contexto: limitar historial a 10 mensajes.
- Recorte del catálogo por relevancia antes del prompt del LLM.

## 9) Seguridad y datos

- No exponer APIs externas; Ollama local recomendado.
- Restringir `eval` del experto (ya sin `__builtins__`).
- Revisar políticas de scraping si se despliega públicamente.

## 10) Despliegue (ideas)

- Backend FastAPI + Nginx, static para `app/`.
- Docker con servicios: `web`, `api`, `ollama`, y volumen para `embeddings/`.
- Habilitar CORS para que la UI acceda a Ollama/Backend según dominio.

## 11) Roadmap sugerido

- Integrar `app/orchestrator.py` en endpoints productivos (modo híbrido real con contexto de usuario).
- Tests unitarios para: parser de nodos, cálculo de cargas, filtrado RAG, sanitización de precios.
- Telemetría/analytics de clics en productos (para ranking/aprendizaje futuro).
- Cache de productos y warm-up de embeddings en arranque.

## 12) Propuestas de escalabilidad

Sugerencias prácticas para crecer en funcionalidades, usuarios y equipos:

- Separación de responsabilidades
  - Dividir en servicios: `frontend`, `api`, `ollama`, `scraper`, `embeddings`.
  - Aislar scraping e ingesta en procesos batch con colas (Celery/RQ) y reintentos.

- Persistencia y catálogo
  - Sustituir JSON plano por base de datos (PostgreSQL) para catálogo y metadatos.
  - Versionado de productos y de prompts del LLM (historial de cambios y auditoría).

- Vector store
  - Migrar de FAISS en archivo a un servicio vectorial: Qdrant, Milvus o PGVector.
  - Indexación incremental y filtros estructurados (familia, potencia mínima, disponibilidad).

- Rendimiento
  - Precalentamiento de modelos y caché de resultados frecuentes.
  - Paralelizar scraping y uso de GPU para embeddings.

- Calidad y seguridad
  - Evaluación automática del LLM (tests de regresión de prompts y RAG).
  - Guardrails: listas blancas de productos, verificación de claims contra catálogo.
  - Límite de tasa (rate limiting) y protección básica en endpoints públicos.

- CI/CD e infraestructura
  - Contenerizar servicios con Docker y orquestar con Docker Compose/Kubernetes.
  - Pipelines de CI: lint, pruebas, build de imágenes, despliegue.
  - Infra as Code (Terraform/Ansible) y entornos por rama (staging/producción).

- Observabilidad
  - Logs estructurados, métricas (Prometheus/Grafana) y trazas (OpenTelemetry).
  - Alarmas por latencia alta, fallos de scraping y errores de API.

- Experiencia de usuario
  - A/B testing de prompts y UI.
  - Internacionalización (i18n) y accesibilidad básica.

- Datos y gobierno
  - Políticas de retención de conversaciones y consentimiento del usuario.
  - Catálogo de datos y documentación viva (MkDocs/Docusaurus) para el equipo.
