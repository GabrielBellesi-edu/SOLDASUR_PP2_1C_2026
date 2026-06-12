# Manual de Escalamiento: Cómo Agregar una Nueva Línea de Productos (v5.0.2)

Este manual describe el procedimiento estándar para integrar una nueva marca de producto al sistema inteligente del Asistente Técnico unificado de **SOLDASUR**.

Gracias a la arquitectura dinámica e instalador automático actualizados en la versión 5.0.2, **todo el proceso está completamente automatizado**. No se requiere compilación manual de vectores, codificación de RAG, ni modificaciones manuales de configuración en FastAPI o en el Orquestador.

---

## Estructura de Origen de la Nueva Marca

Para agregar una nueva marca (por ejemplo, `NUEVA_MARCA`), debes preparar una carpeta con su nombre dentro del directorio `nueva_marca/` en la raíz del proyecto:

```text
SOLDASUR_PP2_1C_2026/
└── nueva_marca/
    └── nueva_marca/                     # Nombre de la carpeta de la marca
        ├── config.json                  # Parámetros y prompts de la marca
        ├── catalog.json                 # Catálogo de productos en formato JSON
        ├── nueva_marca-logo.png         # Logotipo de la marca (cualquier archivo con 'logo' en el nombre)
        ├── calculator_kb.json           # (Opcional) Base de conocimiento del sistema experto
        └── calculator_engine.py         # (Opcional) Motor/cálculos del sistema experto
```

### 1. Archivo `config.json`
Contiene la configuración semántica, palabras clave, e instrucciones de personalidad para la marca. Ejemplo:

```json
{
  "brand_key": "NUEVA_MARCA",
  "display_name": "Nueva Marca",
  "direct_keywords": ["palabramarca", "keyword1", "keyword2"],
  "anchor_text": "descripción semántica de los productos y soluciones que comercializa esta marca para enrutamiento inteligente",
  "system_prompt": "Sos Soldy, el asesor experto de SOLDASUR especializado en productos Nueva Marca. Tus respuestas deben ser breves, cordiales y en español rioplatense...",
  "temperature": 0.2,
  "max_tokens": 250,
  "has_calculator": true,
  "calculator_display": "Calculadora Nueva Marca (Dimensionamiento)"
}
```

*Nota: Los campos `has_calculator` y `calculator_display` son opcionales y solo deben definirse si la marca incluye un sistema experto/calculadora.*

### 2. Catálogo JSON (`catalog.json` o `nueva_marca_catalog.json`)
Listado de productos estructurado en JSON. Formato recomendado para compatibilidad con la interfaz de tarjetas del frontend:

```json
[
  {
    "model": "Nombre Exacto del Producto",
    "category": "Categoría de producto",
    "description": "Ficha descriptiva completa para el LLM",
    "presentacion": "Medida/Bolsa/Unidad (ej: 25 kg)",
    "url": "https://url-del-fabricante.com/producto",
    "imagen_local": "/img/nueva_marca/imagen1.jpg",
    "imagen_url": "https://url-fabricante.com/imagen.jpg"
  }
]
```

---

## Proceso de Instalación en 1 Solo Paso

Una vez que tengas lista la carpeta en `nueva_marca/nueva_marca/`, abre una terminal en la raíz del proyecto y ejecuta el instalador automático proporcionando el nombre de la carpeta:

```bash
python app/modules/escalamiento/install_brand.py nueva_marca
```

### ¿Qué hace el instalador automático internamente?

1.  **Verificación de Dependencias:** Comprueba que estén instaladas las librerías necesarias (`sentence-transformers`, `faiss-cpu`, `numpy`).
2.  **Carga y Validación:** Valida la estructura del `config.json` y del catálogo.
3.  **Compilación Vectorial RAG:** 
    *   Genera los embeddings vectoriales del catálogo usando el modelo multilingual de SentenceTransformers.
    *   Genera el índice de búsqueda en `RAG_engine/database/products_nueva_marca.faiss`.
    *   Formatea el catálogo final en `RAG_engine/database/metadata_nueva_marca.json`.
4.  Generación de Scripts RAG: Genera automáticamente los scripts `rag_query_nueva_marca.py` y `rag_llm_nueva_marca.py` en `RAG_engine/query/`.
5.  **Copia de Logotipo:** Busca cualquier archivo que contenga `logo` en su nombre dentro de la carpeta origen y lo copia como `web_app/img/nueva_marca-logo.png`.
6.  **Copia del Sistema Experto (Si aplica):** Si `has_calculator` es `true`, copia:
    *   `calculator_kb.json` $\rightarrow$ `app/advisor_knowledge_base_nueva_marca.json`
    *   `calculator_engine.py` $\rightarrow$ `app/modules/expertSystem/expert_engine_nueva_marca.py`
7.  **Registro de Configuraciones:** Registra de forma dinámica la marca, intenciones, configuración RAG y estado de la calculadora en `configs/brands_registry.json` y el prompt en `configs/prompts.json`.

---

## Integración y Funcionamiento Automático del Sistema Experto

A partir de la versión 5.0.2, el backend de FastAPI detecta e inicializa dinámicamente el sistema experto de cualquier marca registrada con `"has_calculator": true`.

### Estructura Técnica del Motor Experto (`expert_engine_nueva_marca.py`)

Para que el motor sea cargado y ejecutado correctamente por el enrutador dinámico de `app/main.py`, debe cumplir con el siguiente diseño estándar (idéntico al de PEISA):

1.  Debe definir una clase que termine en `ExpertEngine` (ej: `NuevaMarcaExpertEngine` o `ExpertEngine`).
2.  La clase debe exponer un método asíncrono `process` con la siguiente firma:
    ```python
    async def process(self, conversation_id: str, expert_state: dict, 
                      option_index: int = None, input_values: dict = None) -> dict:
        # Lógica de transición de nodos y cálculos
        return {
            "conversation_id": conversation_id,
            "node_id": "siguiente_nodo",
            "type": "question|response",
            "text": "Texto descriptivo o pregunta",
            "options": ["Opción 1", "Opción 2"] # (Si aplica)
        }
    ```

### Fallback Genérico
Si la marca tiene calculadora pero no se incluye un motor personalizado (`expert_engine_nueva_marca.py`), el servidor instanciará automáticamente el motor genérico `ExpertEngine` heredado de PEISA, el cual procesará la navegación del árbol de decisiones basándose únicamente en el contenido dinámico de su base de conocimiento JSON (`advisor_knowledge_base_nueva_marca.json`).
