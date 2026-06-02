# Registro de Tareas v4 — Weber Frontend + Módulos Separados y Unificación

Este documento registra el progreso de tareas completadas durante el desarrollo de la versión **v4.0** del sistema **SOLDASUR**, estructurado con enlaces relativos para facilitar la navegación en el repositorio.

## Checklist de Tareas

- [x] Confirmar y validar estructura propuesta para la v4.
- [x] Crear e implementar el módulo común [core.js](../app/modules/core/core.js) (estado global compartido, renderizado de UI, catálogo de productos y consulta de sucursales).
- [x] Crear e implementar el módulo de sistema experto de calefacción [peisa_expert.js](../app/modules/peisa/peisa_expert.js) (cuestionario interactivo y cálculos matemáticos en frontend).
- [x] Crear e implementar el módulo de sistema experto de construcción [weber_expert.js](../app/modules/weber/weber_expert.js) portando el árbol de decisión y lógica de rendimiento 100% al frontend (sin peticiones HTTP).
- [x] Simplificar el archivo orquestador [soldasur.js](../soldasur.js) eliminando código repetido y dejándolo como un inicializador delgado.
- [x] Parchear el controlador del chatbot interactivo [chatbot.js](../app/modules/chatbot/chatbot.js) eliminando variables y utilitarios duplicados para evitar colisiones en el ámbito global del navegador.
- [x] Modificar el archivo principal [index.html](../index.html) para corregir el orden de importación de los scripts JavaScript de manera modular y secuencial.
- [x] Integrar el servidor estático montándolo en la raíz `/` de FastAPI dentro del backend en [main.py](../app/main.py) para unificar la aplicación en un solo puerto.
- [x] Reconstruir y poblar la base de datos de productos en SQLite [products.db](../embeddings/products.db) a partir del catálogo para solucionar el fallo `sqlite3.OperationalError` de tabla inexistente.
- [x] Resolver crasheos de codificación `UnicodeEncodeError` en Windows cp1252 reemplazando los emojis por texto seguro ASCII en los prints de consola de [weber_expert_engine.py](../app/modules/expertSystem/weber_expert_engine.py).
- [x] Corregir dependencias del proyecto en [requirements.txt](../requirements.txt) eliminando `matplotlib` (compilación C++) y flexibilizando la versión de `faiss-cpu`.
- [x] Crear el documento histórico de cambios de la v4 [v4.0.md](v4.0.md) con enlaces relativos.
- [x] Crear el análisis de arquitectura del RAG sintáctico y semántico [v4.0.1.md](v4.0.1.md) para unificación de criterios en el chat.
- [x] Crear la documentación de unificación de servidores en FastAPI [v4.0.2.md](v4.0.2.md).
- [x] Crear la bitácora de cierre y verificación [walkthrough.md](walkthrough.md) detallando las pruebas de funcionamiento.
- [x] Exportar el registro de tareas actual [task.md](task.md) con enlaces relativos a la carpeta de proceso documentado.
- [x] Neutralizar la marca corporativa unificando PEISA y Weber: actualizar el slogan en [index.html](../index.html), corregir a 4 sucursales, agregar 3 tarjetas de productos Weber, unificar metadatos en [main.py](../app/main.py), adaptar [chatbot.js](../app/modules/chatbot/chatbot.js) a `productCatalog` y crear la bitácora de cambios en [v4.1.1.md](v4.1.1.md).
- [x] Portar el scraper de Weber [weber_rag_scraper.py](../weber_ingest/weber_rag_scraper.py) a la carpeta de ingestión de la v4 para que sea autocontenido.
- [x] Actualizar dependencias de scraping (`playwright`, `tqdm`) en [requirements.txt](../requirements.txt) y configurar exclusiones en [.gitignore](../.gitignore).
- [x] Actualizar el documento de [instrucciones_v4.md](instrucciones_v4.md) detallando el flujo paso a paso de Scraping e Ingesta RAG.
- [x] Crear el nuevo scraper robusto [Gscraper.py](../weber_ingest/Gscraper.py) para extraer directamente del catálogo paginado de Weber y actualizar las instrucciones de puesta en marcha.


## Tareas Pendientes

- [ ] Correr la ingesta completa RAG de Weber con el nuevo catálogo (Ejecutar `Gscraper.py` completo con descarga de PDFs, luego `01_build_catalog.py` y `02_build_embeddings.py` para regenerar la base de datos vectorial de 100 productos).
- [ ] Investigar y agregar la extracción de metadatos adicionales de los productos Weber (tales como "área" de aplicación [ej: fachada], "actividad" [ej: pisos], "colores" [ej: blanco], "ancho de juntas" [ej: 5mm], etc.) a nivel de scraping y mapeo en el catálogo RAG.
- [ ] Ampliar el módulo del sistema experto [weber_expert.js](../app/modules/weber/weber_expert.js) para integrar el cálculo de otros productos faltantes del catálogo (ej. Weber Microcolor/Microbase, pastinas, morteros de nivelación, revoques finos y otros impermeabilizantes).
- [x] Agregar soporte para revestimientos plásticos/decorativos de paredes, selladores, fijaciones y mezclas de asiento en el scraper ([weber_rag_scraper.py](../weber_ingest/weber_rag_scraper.py)) y en el catalogador ([01_build_catalog.py](../weber_ingest/01_build_catalog.py)) agregando las nuevas palabras clave y mapeos de categorías.
- [ ] Implementar el **Enrutamiento Semántico (Opción 1 - Comparación de Similitud por Embeddings)** en el endpoint `/api/chat` de [main.py](../app/main.py#L272-L322) para clasificar dinámicamente si el mensaje del usuario es de Weber (construcción) o PEISA (calefacción), superando las limitaciones de la lista estática `WEBER_KEYWORDS` (línea 246):
  * **Archivos a modificar:** [main.py](../app/main.py) (reemplazar la lógica de `_is_weber_query` y actualizar `api_chat`).
  * **Detalle técnico:** Utilizar el modelo de SentenceTransformers ya instanciado en el RAG de Weber (`"sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"`) en [weber_rag_engine.py](../app/modules/chatbot/weber_rag_engine.py) para codificar la consulta del usuario y calcular su similitud del coseno contra dos vectores ancla estáticos precalculados:
    * *Ancla Weber (Construcción):* "colocación de revestimientos cerámicas porcelanatos baldosas impermeabilización de losas piscinas pastina revoque fino mezcla adhesivo cemento"
    * *Ancla PEISA (Calefacción):* "calefacción caldera radiador toallero calefón termotanque agua caliente sanitaria climatización"
  * **Objetivo de usabilidad:** Permitir enrutar correctamente consultas complejas o con errores de ortografía y sinónimos (ej: "vaño pared umedad", "baldosas para el piso") en menos de 50ms y sin depender de llamadas adicionales al LLM (evitando latencia y problemas de cold start).
- [ ] Reestructurar el repositorio (Versión v4.2.0) para separar responsabilidades y modularizar el código:
  * **Estructura de carpetas propuesta:**
    ```text
    Repo/
    ├── scraping/                  # 1. TODO LO RELACIONADO A SCRAPPING
    │   ├── peisa_scraper.py
    │   ├── weber_scraper.py
    │   └── data_raw/              # Descargas crudas (CSVs, HTMLs, PDFs)
    │
    ├── RAG_engine/                # 2. EL MOTOR DE BÚSQUEDA Y BASE DE DATOS
    │   ├── database/              # Archivos SQLite (.db) y FAISS (.faiss)
    │   ├── scripts/               # Scripts de ingesta (ingest.py, etc.)
    │   └── query/                 # Motores de búsqueda RAG (query.py, weber_rag_engine.py)
    │
    ├── web_app/                   # 3. LA APLICACIÓN QUE CORRE EN EL SERVIDOR/WEB
    │   ├── backend/               # Servidor FastAPI (main.py, routers, configs)
    │   └── frontend/              # Archivos estáticos de la web
    │       ├── index.html
    │       ├── soldasur.css
    │       ├── soldasur.js
    │       ├── img/
    │       └── js_modules/        # Scripts que se ejecutan en el navegador
    │           ├── core.js
    │           ├── peisa_expert.js
    │           └── weber_expert.js
    ```




