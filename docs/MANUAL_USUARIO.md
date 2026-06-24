# MANUAL DE USUARIO - SoldaSur IA Chatbot (Versión 2026)

## Sistema de Asesoramiento Técnico y Comercial Multimarca Inteligente

**Versión del Sistema**: v5.0.2 (Edición 2026)  
**Institución**: Centro Politécnico Malvinas Argentinas (CPMA) - Práctica Profesionalizante II  
**Empresa**: Soldasur S.A. (Tierra del Fuego)  

---

## Índice

1. [Introducción](#introducción)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Instalación y Puesta en Marcha](#instalación-y-puesta-en-marcha)
4. [Ejecución de la Aplicación](#ejecución-de-la-aplicación)
5. [Estructura y Uso del Chatbot](#estructura-y-uso-del-chatbot)
6. [Mantenimiento y Scraping](#mantenimiento-y-scraping)
7. [Escalamiento: Agregar una Nueva Marca](#escalamiento-agregar-una-nueva-marca)
8. [Estructura del Repositorio](#estructura-del-repositorio)
9. [Solución de Problemas](#solución-de-problemas)
10. [Glosario](#glosario)

---

## Introducción

El **SoldaSur IA Chatbot** es una plataforma inteligente de asistencia técnica y comercial para sucursales de Soldasur en Tierra del Fuego. Integra IA Simbólica y Generativa en una única interfaz web para asesorar a los clientes sobre múltiples marcas (como calefacción PEISA, construcción Weber y sistemas modulares).

El sistema consta de dos tecnologías de IA principales que trabajan juntas de forma transparente:
* **Sistemas Expertos**: Árboles de decisión interactivos basados en reglas técnicas y geográficas para realizar dimensionamiento y cómputo de materiales (como calcular la cantidad de caños de piso radiante o bolsas de adhesivos necesarias según los metros cuadrados).
* **Motores RAG (Generación Aumentada por Recuperación)**: Búsqueda semántica sobre índices vectoriales de catálogos combinados con un modelo de lenguaje (LLM) que responde consultas comerciales, técnicas y de aplicación en lenguaje natural rioplatense.

---

## Requisitos del Sistema

### Requisitos Mínimos de Hardware
| Componente | Especificación Mínima | Especificación Recomendada |
|------------|-----------------------|----------------------------|
| **Procesador** | Intel Core i5 / AMD Ryzen 5 | Intel Core i7 / AMD Ryzen 7 |
| **Memoria RAM** | 8 GB | 16 GB (o superior para Ollama local) |
| **Almacenamiento** | 10 GB libres | SSD con 15 GB libres |

### Software Base Requerido
1. **Python 3.10 o superior** (asegurarse de marcar "Add Python to PATH" durante la instalación).
2. **Ollama** (para la ejecución local y privada del modelo de lenguaje).
3. **Navegador Web** (Google Chrome, Mozilla Firefox, Microsoft Edge o Safari).

---

## Instalación y Puesta en Marcha

### Paso 1: Instalar y Configurar Ollama
1. Descarga el instalador de Ollama desde su sitio web oficial: [https://ollama.com](https://ollama.com).
2. Ejecuta el archivo descargado e instala la aplicación.
3. Inicia el servidor de Ollama. Si no se ejecuta automáticamente en la bandeja del sistema, abre una terminal y arráncalo con:
   ```bash
   ollama serve
   ```
4. Abre otra terminal de tu sistema (CMD o PowerShell en Windows) y descarga el modelo de lenguaje ejecutando:
   ```bash
   ollama pull llama3.2:3b
   ```
   *(Nota: Puedes cambiar el modelo en `configs/prompts.json` si prefieres utilizar otro como `mistral` o `llama3:8b` si tu hardware lo permite)*.


### Paso 2: Crear el Entorno Virtual de Python
Abre la consola en la raíz de la carpeta del proyecto (`SOLDASUR_PP2_1C_2026/`) y ejecuta:

**En Windows (Símbolo del Sistema / CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**En Windows (PowerShell):**
```powershell
python -m venv venv
# Si obtienes un error de permisos la primera vez, ejecuta en PowerShell:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\Activate.ps1
```

**En Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

### Paso 3: Instalar Dependencias de Python
Con el entorno virtual activado (verás el prefijo `(venv)` en tu terminal), instala todas las librerías necesarias especificadas en el archivo de requerimientos:
```bash
pip install -r requirements.txt
```

*(Opcional: Si los scrapers interactivos requieren automatización de navegador con Playwright, ejecuta `playwright install chromium` para descargar su binario)*.

---

## Ejecución de la Aplicación

Para iniciar el servidor del chatbot y poder interactuar con él desde tu navegador web:

1. Asegúrate de iniciar el servidor de Ollama en una terminal si no se encuentra corriendo:
   ```bash
   ollama serve
   ```
2. Abre otra terminal, activa el entorno virtual (`venv` según tu consola) y levanta la API del backend ejecutando:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
3. El servidor iniciará y estará disponible en: `http://localhost:8000`.
4. Abre tu navegador web y entra a `http://localhost:8000` para abrir la interfaz del chat.

---

## Estructura y Uso del Chatbot

Al iniciar la conversación, **Soldy** (el asistente inteligente) te saludará y te presentará el menú interactivo con las siguientes opciones:

### 1. Calculadoras (Sistemas Expertos)
Ideal cuando necesitas calcular cantidades exactas de productos o dimensionar un proyecto:
* **Calefacción PEISA**: Permite calcular la cantidad de caños de piso radiante y circuitos por metros cuadrados y zona geográfica; dimensionar la cantidad de elementos de radiadores según dimensiones y aislamiento térmico del ambiente; o recomendar la caldera adecuada según el tipo de servicio requerido.
* **Construcción Weber**: Realiza cálculos exactos de la cantidad de bolsas o tachos de adhesivos, pastinas, autonivelantes, revoques o revestimientos plásticos en función del soporte de la obra y los m² a cubrir, sumando un 10% por desperdicio de obra.

### 2. Buscar Productos (Búsqueda Libre RAG)
Puedes escribir libremente cualquier consulta técnica o comercial en la caja de texto, por ejemplo:
* *¿Qué tipo de adhesivo necesito para colocar porcelanato sobre un piso viejo sin picar?*
* *Recomendame un toallero eléctrico para baño mediano.*
* *¿En qué colores viene el revestimiento weberplast llaneado?*

El orquestador del chatbot detectará automáticamente a qué marca te refieres, buscará en la base de datos vectorial de FAISS los productos correspondientes, y el LLM te responderá con texto amigable en español rioplatense junto a tarjetas visuales con fotos, ventajas técnicas y enlaces al catálogo.

### 3. Configuración del Modelo de Lenguaje (Ollama)
Si deseas utilizar un modelo de lenguaje local diferente al predeterminado (`llama3.2:3b`) —como por ejemplo `llama3.1:8b` para mayor capacidad—, puedes configurarlo de forma centralizada:
1. Abre el archivo de configuración [configs/models.json](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/configs/models.json) (si no existe, se puede crear en esa ubicación).
2. Modifica la propiedad `"ollama_model"` con el identificador exacto de tu modelo. Por ejemplo:
   ```json
   {
     "ollama_model": "llama3.1:8b"
   }
   ```
3. Antes de iniciar la aplicación, descarga el modelo correspondiente en tu terminal ejecutando:
   ```bash
   ollama pull llama3.1:8b
   ```

---

## Mantenimiento y Scraping

El sistema permite actualizar la información de sus productos de forma autónoma haciendo scraping web de los sitios oficiales de las marcas.

### Actualizar el Catálogo de Productos
Para actualizar los datos comerciales, imágenes y fichas de productos, ejecuta los scripts de scraping correspondientes:

* **Para PEISA:**
  ```bash
  python scraping/peisa_product_scraper.py
  ```
* **Para Weber:**
  ```bash
  python scraping/weber_product_scraper.py
  ```

Los scrapers descargarán la información más reciente y dejarán un archivo JSON unificado con los productos en la ruta correspondiente (por ejemplo, `web_app/data/peisa_catalog.json` y `weber_catalog.json`).

### Generación de Embeddings Vectoriales (Marcas Clásicas)
Si actualizaste la información de los catálogos y quieres que el chatbot empiece a usar estos nuevos datos en sus búsquedas semánticas libres:
```bash
python RAG_engine/scripts/ingest.py --all
```
*(Puedes especificar `--peisa` o `--weber` para actualizar una única marca)*.

---

## Escalamiento: Agregar una Nueva Marca

Una de las ventajas clave de la arquitectura **v5.0.2** es la capacidad de incorporar nuevas marcas al catálogo y a las calculadoras de manera dinámica sin alterar el código central del backend.

Para agregar una nueva marca al sistema (por ejemplo: `Durlock` u otra):

### Paso 1: Generar la Carpeta Origen
Ejecuta el scraper de la nueva marca o crea manualmente una carpeta temporal que recopile sus archivos. Dicha carpeta debe llamarse exactamente igual al nombre de la marca en minúsculas y estar ubicada dentro de `scraping/data_raw/`.

Estructura de archivos requerida dentro de `scraping/data_raw/<marca_lower>/`:
```text
scraping/data_raw/<marca_lower>/
├── config.json                     # Palabras clave de clasificación y prompt del LLM
├── <marca_lower>_catalog.json      # Catálogo JSON con los productos estructurados
├── <marca_lower>-logo.png          # Imagen del logo comercial de la marca
├── calculator_kb.json              # (Opcional) Árbol de decisiones si tiene calculadora
└── calculator_engine.py            # (Opcional) Expresiones matemáticas si tiene calculadora
```

*Nota: La propiedad `"categories_processed"` en tu catálogo de productos permite especificar nombres estilizados para las categorías comerciales de los productos de forma que se rendericen correctamente en el menú del chatbot.*

### Paso 2: Ejecutar el Instalador Automático
Abre la terminal en la raíz del proyecto y ejecuta el instalador indicando el nombre de la carpeta de la marca:
```bash
python app/modules/escalamiento/install_brand.py NombreMarca
```
Por ejemplo, para instalar Durlock: `python app/modules/escalamiento/install_brand.py Durlock`

El script realizará las siguientes acciones de forma automática:
1. **Validación**: Verifica que las dependencias estén presentes.
2. **Base de Datos Vectorial**: Calcula los embeddings de los productos y compila el índice FAISS (`products_<marca>.faiss`) y el archivo de metadatos (`metadata_<marca>.json`) en `RAG_engine/database/`.
3. **Generación de Módulos RAG**: Autogenera los archivos de consultas y respuestas semánticas (`rag_query_<marca>.py` y `rag_llm_<marca>.py`) en `RAG_engine/query/`.
4. **Copia de Assets**: Copia el logotipo de la marca al frontend.
5. **Registro Dinámico**: Da de alta a la marca en `configs/brands_registry.json` y configura su prompt en `configs/prompts.json`.

Si la marca tiene calculadora, copia manualmente los archivos `calculator_kb.json` y `calculator_engine.py` en sus correspondientes rutas en el backend (`app/` y `app/modules/expertSystem/`) para habilitarla al instante.

---

## Estructura del Repositorio

A continuación se detalla la ubicación de los componentes del sistema para tareas de soporte técnico o auditorías:

```text
SOLDASUR_PP2_1C_2026/
│
├── 📄 requirements.txt                   # Librerías de Python requeridas
├── 📄 README.md                          # Documentación
│
├── 📂 app/                               # BACKEND DE LA APLICACIÓN
│   ├── 📄 main.py                        # Servidor FastAPI y endpoints web
│   ├── 📄 app.py                         # Funciones auxiliares y motor experto PEISA
│   ├── 📄 orchestrator.py                # Clasificador de intenciones e híbrido de chats
│   │
│   └── 📂 modules/                       # SUBMÓDULOS DE APLICACIÓN
│       ├── 📂 escalamiento/
│       │   └── 📄 install_brand.py       # Script de instalación automática de marcas
│       └── 📂 expertSystem/
│           ├── 📄 expert_engine_peisa.py # Motor del sistema experto de PEISA
│           ├── 📄 expert_engine_weber.py # Motor de cálculos de materiales Weber
│           └── 📄 product_loader.py      # Cargador de productos desde Excel/SQLite
│
├── 📂 configs/                           # ARCHIVOS DE CONFIGURACIÓN DINÁMICA
│   ├── 📄 brands_registry.json           # Registro de marcas y sus palabras clave
│   └── 📄 prompts.json                   # System prompts y parámetros de Ollama
│
├── 📂 docs/                              # DOCUMENTACIÓN TÉCNICA Y DE USUARIO
│   ├── 📄 MANUAL_ESCALAMIENTO.md         # Guía de escalabilidad para nuevas marcas
│   ├── 📄 MANUAL_SISTEMA_EXPERTO_RAG.md  # Funcionamiento interno de motores expertos y RAG
│   ├── 📄 MANUAL_TECNICO_ORQUESTADOR.md  # Flujo del orquestador e intenciones
│   ├── 📄 MANUAL_TECNICO_SISTEMA_EXPERTO_WEBBER.md # Lógica y rendimiento de Weber
│   └── 📄 MANUAL_USUARIO.md              # Este manual de usuario
│
├── 📂 RAG_engine/                        # MOTOR RAG (BÚSQUEDA VECTORIAL)
│   ├── 📂 database/                      # Índices FAISS y metadatos compilados
│   │   ├── 📄 peisa_products.db          # BD SQLite de metadatos de PEISA
│   │   ├── 📄 peisa_products.faiss       # Índice vectorial de PEISA
│   │   └── 📄 weber_products.faiss       # Índice vectorial de Weber
│   │
│   ├── 📂 query/                         # Código RAG de inferencia de cada marca
│   │   ├── 📄 rag_query_peisa.py
│   │   ├── 📄 rag_llm_peisa.py
│   │   ├── 📄 rag_query_weber.py
│   │   └── 📄 rag_llm_weber.py
│   │
│   └── 📂 scripts/                       # Ingestas de datos tradicionales
│       ├── 📄 ingest.py                  # Orquestador central (--peisa, --weber, --all)
│       └── 📄 peisa_ingest.py            # Ingesta PEISA
│
├── 📂 scraping/                          # MÓDULOS DE EXTRACCIÓN (SCRAPERS)
│   ├── 📂 data_raw/                      # Carpeta de entrada con productos extraídos
│   ├── 📄 peisa_product_scraper.py       # Scraper de productos PEISA (BeautifulSoup)
│   └── 📄 weber_product_scraper.py       # Scraper de productos Weber (Playwright)
│
└── 📂 web_app/                           # INTERFAZ FRONTEND (HTML/CSS/JS Estático)
    ├── 📄 index.html                     # Archivo visual principal de acceso
    ├── 📄 soldasur.css                   # Estilos visuales del chat Soldy y tarjetas
    ├── 📄 soldasur.js                    # Orquestador JS del chatbot en el navegador
    │
    ├── 📂 data/                          # Catálogos comerciales consumidos por el navegador
    │   ├── 📄 peisa_catalog.json
    │   └── 📄 weber_catalog.json
    │
    └── 📂 js_modules/                    # Scripts del comportamiento del chat
        ├── 📄 core.js                    # Estado de navegación y listado de productos
        ├── 📄 chatbot.js                 # Handler para llamadas al LLM
        ├── 📄 peisa_expert.js            # Flujo interactivo de la calculadora PEISA
        └── 📄 weber_expert.js            # Flujo interactivo de la calculadora Weber
```

---

## Solución de Problemas

### 1. El import de la librería `faiss` se muestra en rojo en mi editor
* **Causa**: Falso positivo común. Ocurre si tu editor de código (como VS Code) no tiene seleccionado el entorno virtual de Python (`venv`) donde está instalada la dependencia, o si el analizador de código estático no puede resolver extensiones de C++.
* **Solución**: En tu IDE, selecciona el intérprete de Python correcto apuntando a `.\venv\Scripts\python.exe`. A nivel de ejecución de código, esto no te impedirá correr la aplicación.

### 2. El chatbot se queda "pensando" indefinidamente
* **Causa**: El servicio local de Ollama está apagado o el modelo no está descargado.
* **Solución**: Abre una terminal de tu sistema y corre `ollama serve` para inicializar el servicio. Verifica si el modelo está presente con `ollama list` y, de ser necesario, descárgalo con `ollama pull llama3.2:3b`.

### 3. Error: "Address already in use" (Puerto 8000 ocupado)
* **Causa**: Ya tienes otra instancia del backend corriendo o hay otro servicio escuchando en el puerto 8000.
* **Solución**: Cierra cualquier otra consola del backend activa. Si persiste, detén el proceso ocupante ejecutando en Windows:
  ```cmd
  netstat -ano | findstr :8000
  taskkill /f /pid <NUMERO_PID>
  ```

### 4. Las imágenes de los productos en las tarjetas del chat no cargan
* **Causa**: Las rutas a los archivos de imágenes en el catálogo no son correctas o no empiezan con el prefijo estático `data_raw/<marca>/img/` que lee el frontend.
* **Solución**: Revisa el catálogo JSON de origen para verificar que la propiedad `"imagen_local"` esté apuntando a una ruta válida y accesible dentro del directorio de scraping.

---

## Glosario

* **RAG (Generación Aumentada por Recuperación)**: Técnica de IA que busca en una base de conocimientos específica (catálogos de Soldasur) antes de enviar la pregunta al modelo de lenguaje (LLM), evitando que el chatbot invente respuestas.
* **Sistema Experto**: IA basada en reglas explícitas lógicas y matemáticas. Útil para cálculos deterministicos como el dimensionamiento de calefacción o adhesivos.
* **FAISS (Facebook AI Similarity Search)**: Librería optimizada de búsqueda de similitud que permite buscar textos afines comparando números llamados "embeddings".
* **LLM (Modelo de Lenguaje Grande)**: Algoritmo generativo capaz de entender y formular textos amigables. En este proyecto se utiliza Ollama local con Llama 3.2.
* **Escalamiento**: La capacidad de un sistema de incorporar nuevas funciones, marcas o volúmenes de datos con el menor esfuerzo de programación posible.

---

**© 2026 - Proyecto de Escalamiento Chatbot Soldasur - Centro Politécnico Malvinas Argentinas**
