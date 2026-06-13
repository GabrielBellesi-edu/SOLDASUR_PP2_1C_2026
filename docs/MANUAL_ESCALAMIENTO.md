# Estándar de Estructura de Datos Scrapeados para SOLDASUR

Este documento define la estructura de directorios, nombres de archivos y esquemas de datos que debe cumplir cualquier scraper de nuevas marcas para que el instalador automático (`install_brand.py`) pueda procesar e integrar los productos, imágenes, documentos y sistemas expertos de forma 100% autónoma.

---

## 1. Estructura de Carpetas en el Repositorio

Los scrapers deben dejar todos los datos obtenidos dentro de la carpeta `scraping/data_raw/<nombre_marca>/` de la raíz del repositorio `SOLDASUR_PP2_1C_2026/`. 

La estructura exacta requerida es la siguiente:

```text
SOLDASUR_PP2_1C_2026/
└── scraping/
    └── data_raw/
        └── <marca_lower>/                    # Identificador de la marca en minúsculas (ej: durlock)
            ├── config.json                   # Configuración, palabras clave y prompts de la marca
            ├── <marca_lower>_catalog.json    # Catálogo estructurado de productos (ej: durlock_catalog.json)
            ├── <marca_lower>-logo.png        # Logotipo de la marca (cualquier imagen con 'logo' en el nombre)
            ├── calculator_kb.json            # (Opcional) Base de conocimiento del sistema experto
            ├── calculator_engine.py          # (Opcional) Lógica/Cálculos del sistema experto
            │
            ├── documentos/                   # Fichas técnicas, manuales y folletos en PDF
            │   └── *.pdf
            │
            ├── img/                          # Imágenes reales de los productos
            │   └── *.png | *.jpg | *.jpeg
            │
            └── logica/                       # (Opcional) Copia de archivos JS/calc de la web original
                └── *.js
```

---

## 2. Especificación de Archivos de Configuración

### A. Archivo `config.json`
Establece los metadatos de la marca, los desencadenadores de conversación y el System Prompt del modelo RAG.

> [!IMPORTANT]
> **Generación Automática Obligatoria:**
> El script de scraping de la marca debe encargarse de autogenerar este archivo `config.json` en la carpeta `scraping/data_raw/<marca_lower>/` al finalizar la ejecución si este no existe. Se debe poblar con valores por defecto representativos (incluyendo palabras clave sugeridas y una plantilla base del prompt del sistema).
> De esta forma, el usuario o desarrollador puede posteriormente abrir dicho archivo para ajustar la personalidad, el tono del chatbot o editar `configs/prompts.json` una vez instalado.

```json
{
  "brand_key": "DURLOCK",
  "display_name": "Durlock",
  "direct_keywords": [
    "durlock",
    "placa",
    "placas",
    "yeso",
    "perfiles"
  ],
  "anchor_text": "placas de yeso placas de cemento siding masillas adhesivos aislantes perfiles construccion en seco revestimientos cielorrasos desmontables",
  "system_prompt": "Sos Soldy, el asesor experto de SOLDASUR especializado en productos Durlock. Ayudas al cliente con informacion tecnica sobre placas, perfiles y consumos. Tus respuestas deben ser breves, profesionales y en español rioplatense (voseo). NUNCA uses markdown ni formateo en tus respuestas.",
  "temperature": 0.2,
  "max_tokens": 250,
  "has_calculator": true,
  "calculator_display": "Calculadora Durlock"
}
```

*   `brand_key`: Identificador único en mayúsculas.
*   `display_name`: Nombre a mostrar en la interfaz de chat.
*   `direct_keywords`: Palabras clave en minúsculas que fuerzan la activación de esta marca en el chat.
*   `anchor_text`: Texto semántico descriptivo utilizado para el enrutamiento inteligente mediante IA.
*   `system_prompt`: Instrucción de comportamiento y personalidad del LLM.
*   `has_calculator`: `true` si la marca tiene un calculador/sistema experto; `false` si no.
*   `calculator_display`: Título del botón del calculador en el frontend.

---

## 3. Esquema del Catálogo de Productos (`<marca_lower>_catalog.json`)

El catálogo debe guardarse en la raíz de la carpeta de la marca bajo el nombre `<marca_lower>_catalog.json` (ej: `durlock_catalog.json`). Consiste en un array JSON de objetos con el siguiente esquema estricto:

```json
[
  {
    "model": "Placa Estándar Durlock®",
    "description": "La Placa Durlock® Estandar es la placa ideal para renovar o construir...",
    "url": "https://durlock.com/productos/placa-estandar-durlock/",
    "imagen_url": "https://durlock.com/files/productos/estandar-2.png",
    "local_imagen_path": "data_raw/durlock/img/estandar-2.png",
    "imagen_local": "data_raw/durlock/img/estandar-2.png",
    "categories": [
      "placas-de-yeso"
    ],
    "categories_processed": [
      "Placas de yeso"
    ],
    "applications": [
      "pared",
      "revestimiento",
      "cielorraso"
    ],
    "specifications": {
      "Placa": "Espesor | ancho | Largo",
      "Estándar de Durlock®": "15mm. | 1,2mts. | 2,6mts."
    },
    "advantages": [
      "Fácil instalación",
      "Excelente terminación"
    ],
    "technical_features": [
      "Espesor nominal: 15mm"
    ],
    "prestaciones": {
      "RESISTENCIA AL FUEGO": "3/5",
      "AISLACIÓN ACÚSTICA": "2.5/5",
      "RESISTENCIA AL IMPACTO": "3/5"
    },
    "documentos": [
      {
        "nombre": "DT - Pared Simple",
        "url": "https://durlock.com/files/biblioteca/archivos/dt--pared-simple-durlock-2.pdf",
        "filename": "dt--pared-simple-durlock-2.pdf",
        "local_path": "data_raw/durlock/documentos/dt--pared-simple-durlock-2.pdf"
      }
    ]
  }
]
```

> [!IMPORTANT]
> **Compatibilidad con `install_brand.py` y Frontend:**
> 1. El campo `"imagen_local"` es **crítico**. Debe contener la ruta de la imagen relativa a la carpeta `scraping/` del repositorio, usando barras diagonales `/` y comenzando con `data_raw/` (ej: `data_raw/durlock/img/estandar-2.png`). El frontend le concatena `/scraping/` al inicio para servir la imagen estática.
> 2. Las categorías en `"categories"` deben guardarse como una lista de slugs en minúsculas (ej: `["placas-de-yeso"]`).
> 3. Se debe incluir un campo `"categories_processed"` con la lista de nombres de categorías estilizados y amigables para el usuario final (ej: `["Placas de yeso"]`). El instalador automático (`install_brand.py`) **priorizará siempre** el uso de `"categories_processed"` para estructurar el menú del chat y los metadatos vectoriales. Si no está disponible, caerá en des-slugificar `"categories"`.
> 4. Las aplicaciones o uso del producto se pueden definir bajo cualquiera de las siguientes claves: `"applications"`, `"aplicacion"`, `"aplicaciones"` o `"aplicar"`. El instalador automático resolverá estas variantes de forma transparente mediante un fallback automático, normalizándolo como `"applications"` (un array de strings) en los metadatos compilados para el motor RAG.
> 5. El campo `"prestaciones"` (opcional) es un diccionario de valores clave de rendimiento y desempeño del producto (ej: escalas, palabras clave o números como `3/5`).
> 6. En `"documentos"`, el subcampo `"local_path"` debe apuntar al PDF en la carpeta `documentos/` de forma relativa a la carpeta `scraping/`, comenzando con `data_raw/` y usando barras `/`.

---

## 4. Archivos del Sistema Experto / Calculador (Opcional)

Si el `config.json` define `"has_calculator": true`, la carpeta de la marca debe incluir obligatoriamente los archivos que estructuran las reglas lógicas:

### A. Archivo `calculator_kb.json`
Contiene la base de conocimiento con el árbol de decisiones en formato JSON. Estructura recomendada:

```json
[
  {
    "id": "pantalla_inicial",
    "pregunta": "Seleccione el tipo de estructura que desea construir:",
    "tipo": "opciones",
    "opciones": [
      {"texto": "Pared Divisoria", "siguiente": "pared_simple"},
      {"texto": "Cielorraso", "siguiente": "cielorraso_estructura"}
    ]
  },
  {
    "id": "pared_simple",
    "tipo": "respuesta",
    "texto": "Para una pared divisoria estándar, te recomendamos usar placas de 12.5mm con perfilería de 70mm."
  }
]
```

### B. Archivo `calculator_engine.py`
Contiene la clase python con la lógica de cálculo y navegación. Debe seguir esta firma exacta:

```python
class ExpertEngine:
    async def process(self, conversation_id: str, expert_state: dict, 
                      option_index: int = None, input_values: dict = None) -> dict:
        """
        Procesa el estado actual y calcula los materiales en base a los m2 ingresados.
        """
        # Lógica de cálculo y transiciones de nodo...
        return {
            "conversation_id": conversation_id,
            "node_id": "resultado_calculo",
            "type": "response",
            "text": "Los materiales requeridos para tu proyecto de 20m2 son...",
            "options": []
        }
```

---

## 5. El Flujo de Instalación

Una vez que la carpeta `scraping/data_raw/<marca_lower>/` está completamente estructurada con todos los archivos listos:

1.  **Ejecutar Instalador:**
    Se corre el comando de instalación en la raíz del repositorio pasando el nombre de la marca (ej: `Durlock` o `durlock`):
    ```bash
    python app/modules/escalamiento/install_brand.py Durlock
    ```
    *(O bien ejecutando el archivo batch `instalar_marca.bat Durlock`)*
2.  **Resultado Automático:**
    `install_brand.py` compilará la base vectorial FAISS en `RAG_engine/database/`, generará los módulos de consulta `rag_query_durlock.py` e inferencia `rag_llm_durlock.py`, copiará el logotipo a `web_app/img/durlock-logo.png`, instalará los archivos del calculador en `app/` y registrará las configuraciones en `configs/brands_registry.json` y `configs/prompts.json`.
