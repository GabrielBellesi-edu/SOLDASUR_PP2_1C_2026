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
