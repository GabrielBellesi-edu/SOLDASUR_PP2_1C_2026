# Glosario de conceptos (con ejemplos)

Este glosario explica los conceptos clave del proyecto y cómo se usan en SoldaSur. Incluye ejemplos simples para usuarios sin experiencia previa.

## Conceptos

- IA simbólica (sistema experto)
  - Paradigma basado en reglas explícitas y árboles de decisión. Es determinístico y explicable.
  - En este proyecto: el motor interpreta nodos (preguntas, cálculos, respuestas) definidos en `app/peisa_advisor_knowledge_base.json`.

- Árbol de decisión / Base de conocimiento (KB)
  - Conjunto de nodos enlazados que guían la interacción. Cada nodo puede pedir datos, calcular o responder.
  - Tipos: `pregunta`, `calculo`, `respuesta`, `opciones_dinamicas`.

- Nodo de cálculo (acciones)
  - Evalúa expresiones matemáticas y lógicas declaradas (p. ej. `carga_termica = volumen * 40`).
  - Usa funciones auxiliares seguras (recomendación de calderas/radiadores, `ceil`, etc.).

- Jinja2 / Interpolación
  - Motor de plantillas para insertar valores del contexto en textos: `{{variable}}` o expresiones como `{{ valor|round(0) }}`.

- RAG (Retrieval-Augmented Generation)
  - Patrón que combina recuperación semántica de conocimiento con generación mediante un LLM.
  - Aquí: FAISS + SentenceTransformers recuperan productos; el LLM (Ollama) redacta la respuesta final.

- Embeddings (vectores semánticos)
  - Representación numérica densa de textos; permite medir similitud semántica vía coseno/producto interno.
  - Ejemplo: “radiador toallero” y “toallero calefactor” quedan cercanos en el espacio vectorial aunque usen palabras distintas.

- FAISS
  - Librería de búsqueda vectorial eficiente. Se usa `IndexFlatIP` con vectores L2-normalizados (coseno ≈ producto interno).

- LLM (Large Language Model)
  - Modelo generativo de lenguaje. Usamos Ollama local con `llama3.2:3b`.

- Prompt engineering
  - Diseño del “system prompt” para guiar al LLM: tono, formato, y reglas (siempre recomendar un producto por nombre, respuestas breves, manejo de precios).

- Catálogo de productos
  - Fuente JSON (`data/products_catalog.json`) con descripciones, ventajas y URL. Puede actualizarse por scraping (`app/modules/scraping/product_scraper.py`).

- Ingesta de embeddings
  - Pipeline `ingest/ingest.py`: genera `embeddings/products.faiss` y `embeddings/products.db` a partir de un CSV procesado.

- ACS (Agua Caliente Sanitaria)
  - En cálculo de calderas, puede sumar carga térmica adicional o implicar “caldera mixta”.

## Conexión entre componentes (resumen práctico)

1) El usuario inicia el flujo experto (reglas) o hace una pregunta libre (chat).
2) El catálogo de productos (`data/products_catalog.json`) alimenta tanto el experto (para decidir) como el RAG (para recuperar).
3) El RAG usa embeddings + FAISS para traer productos relevantes y el LLM construye una respuesta breve.

## Unidades y conversiones útiles

- Potencia por superficie para piso radiante (regla simple): 100–125 W/m² según zona y aislación.
- Conversión entre W y kcal/h: `kcal/h ≈ W * 0.859845`.
- Ejemplo: 10000 W ≈ 8598 kcal/h.

## Ejemplo práctico (flujo híbrido)

Caso: “Quiero calefaccionar 60 m² en zona sur con piso radiante y además un radiador para un ambiente chico.”

1) Sistema experto
   - Pide superficie y zona; calcula `carga_termica = superficie * potencia_m2[zona]`.
   - Para radiadores, pide dimensiones (largo×ancho×alto) y nivel de aislación; calcula `carga_termica` en kcal/h.
   - Llama a funciones auxiliares para recomendar un modelo del catálogo.

2) RAG + LLM
   - Convierte la consulta en vector, busca productos similares en FAISS y pasa 2–5 al LLM.
   - El LLM responde en 2–3 oraciones, mencionando un producto específico y la razón, sin precios explícitos.

3) Resultado
   - El usuario recibe: a) un cálculo determinístico (experto) y b) recomendaciones en lenguaje natural (RAG) con enlaces a productos.
