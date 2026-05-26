# MANUAL DE USUARIO - SoldaSur IA Chatbot

## Sistema de Asesoramiento Inteligente para Calefacción PEISA

**Versión**: 2025 - Práctica Profesionalizante II  
**Equipo**: Cussi Nicolás · Biason Franco · Bolaña Silvia · Luna Luciano  
**Empresa**: Soldasur (Tierra del Fuego)  
**Productos**: Catálogo PEISA

---

## Índice

1. [Introducción](#introducción)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Instalación](#instalación)
4. [Configuración Inicial](#configuración-inicial)
5. [Uso del Sistema](#uso-del-sistema)
6. [Funcionalidades Principales](#funcionalidades-principales)
7. [Mantenimiento](#mantenimiento)
8. [Solución de Problemas](#solución-de-problemas)
9. [Glosario](#glosario)
10. [Soporte](#soporte)

---

## Introducción

El **SoldaSur IA Chatbot** es un sistema inteligente de asesoramiento técnico-comercial para productos de calefacción de la marca PEISA. Combina dos tecnologías de inteligencia artificial:

- **Sistema Experto** (IA simbólica): Guía paso a paso con cálculos precisos
- **Chatbot RAG** (Recuperación semántica + LLM): Respuestas en lenguaje natural

### ¿Qué puede hacer el sistema?

**Calcular potencia necesaria** para piso radiante, radiadores y calderas  
**Recomendar productos específicos** del catálogo PEISA  
**Responder consultas** en lenguaje natural sobre calefacción  
**Buscar productos** por categoría y características  
**Conectar con sucursales** de Río Grande y Ushuaia  

### Características destacadas

- **100% Local**: No requiere conexión a internet una vez instalado
- **Actualizable**: Catálogo de productos se actualiza automáticamente
- **Explicable**: Cálculos transparentes y justificados
- **Conversacional**: Interfaz natural e intuitiva

---

## Requisitos del Sistema

### Requisitos Mínimos

| Componente | Especificación |
|------------|----------------|
| **Sistema Operativo** | Windows 10/11, macOS 10.15+, Ubuntu 18.04+ |
| **Procesador** | Intel i5/AMD Ryzen 5 o superior |
| **Memoria RAM** | 8 GB mínimo (16 GB recomendado) |
| **Espacio en disco** | 10 GB libres |
| **Python** | Versión 3.10 o superior |
| **Navegador** | Chrome, Firefox, Safari, Edge (versiones actuales) |

### Software Requerido

1. **Python 3.10+** - [Descargar aquí](https://python.org)
2. **Ollama** - [Descargar aquí](https://ollama.ai)
3. **Git** (opcional) - Para clonar el repositorio

---

## Instalación

### Paso 1: Instalar Ollama

1. Descargar Ollama desde [https://ollama.ai](https://ollama.ai)
2. Ejecutar el instalador según tu sistema operativo
3. Verificar instalación:
   ```bash
   ollama --version
   ```

### Paso 2: Descargar Modelo de IA

```bash
ollama pull llama3.2:3b
```

### Paso 3: Obtener el Proyecto

**Opción A: Desde ZIP**
1. Descargar el archivo ZIP del proyecto
2. Extraer en la carpeta deseada

**Opción B: Con Git**
```bash
git clone https://github.com/fbiason/pp2-soldasur-2c-2025.git
cd pp2-soldasur-2c-2025
```

### Paso 4: Crear Entorno Virtual (Windows)

```cmd
python -m venv venv
venv\Scripts\activate
```

**Para Linux/macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

### Paso 5: Instalar Dependencias

```bash
pip install -r requirements.txt
```

---

##  Configuración Inicial

### 1. Verificar Ollama

Asegurar que Ollama esté ejecutándose:

```bash
ollama serve
```

Debería mostrar: `Ollama is running on http://127.0.0.1:11434`

### 2. Actualizar Catálogo de Productos

```bash
python app/modules/scraping/product_scraper.py
```

### 3. (Opcional) Generar Embeddings Persistentes

```bash
python ingest/ingest.py data/processed/products_mock.csv
```

---

##  Uso del Sistema

### Iniciar el Sistema

**Opción A: Frontend Estático (Recomendado)**
```bash
cd app
python -m http.server 8000
```
Luego abrir: `http://localhost:8000/index.html`

**Opción B: Con API Backend**
```bash
python -m uvicorn app.main:app --reload
```
Luego abrir: `http://localhost:8000/`

### Interfaz Principal

Al abrir el sistema verás tres opciones principales:

1. **"Guíame"** - Sistema Experto
2. **"Tengo una pregunta"** - Chatbot
3. **"Buscar productos"** - Catálogo

---

##  Funcionalidades Principales

### 1. Sistema Experto: "Guíame"

**¿Cuándo usar?**
- Necesitas cálculos precisos de potencia
- Quieres recomendaciones paso a paso
- Buscas una solución específica y detallada

**Flujos disponibles:**

####  Piso Radiante
1. **Superficie**: Ingresa los m² a calefaccionar
2. **Tipo de piso**: Cerámica, madera, alfombra
3. **Zona geográfica**: Centro/Norte o Sur
4. **Resultado**: Potencia necesaria, cantidad de caño, número de circuitos

####  Radiadores
1. **Objetivo**: Ambiente principal o auxiliar
2. **Dimensiones**: Largo × ancho × alto del ambiente
3. **Aislación**: Buena, regular, mala
4. **Instalación**: A pared, embutido, pie
5. **Estilo**: Tradicional, moderno, compacto
6. **Color**: Blanco, negro, gris
7. **Resultado**: Carga térmica y radiadores recomendados

####  Calderas
1. **Agua caliente**: ¿Necesita agua caliente sanitaria?
2. **Superficie**: Área total a calefaccionar
3. **Resultado**: Potencia requerida y calderas recomendadas

### 2. Chatbot: "Tengo una pregunta"

**¿Cuándo usar?**
- Tienes preguntas específicas sobre productos
- Quieres comparar opciones
- Necesitas información rápida
- Buscas asesoramiento personalizado

**Ejemplos de consultas:**
- "Necesito calefaccionar una casa de 80m²"
- "¿Qué radiador me recomendás para un baño?"
- "Diferencias entre calderas murales y de pie"
- "¿Tienen toalleros calefactores?"

**Características del Chatbot:**
-  **Respuestas breves**: 2-3 oraciones
-  **Menciona productos específicos** por nombre
-  **Evita precios directos**: Solicita ciudad para contacto
-  **Memoria de contexto**: Recuerda la conversación

### 3. Búsqueda de Productos: "Buscar productos"

**Categorías disponibles:**
- Calderas hogareñas
- Radiadores
- Piso radiante
- Accesorios
- Termostatos

**Cada producto muestra:**
- Nombre del modelo
- Descripción técnica
- Ventajas principales
- Enlace al sitio de PEISA

### 4. Contacto Comercial

**Cuando necesites precios o asesoramiento personalizado:**

**Río Grande**
- **Dirección**: Dirección de la sucursal
- **Teléfono**: Número de contacto
- **WhatsApp**: Enlace directo

**Ushuaia**  
- **Dirección**: Dirección de la sucursal
- **Teléfono**: Número de contacto
- **WhatsApp**: Enlace directo

---

##  Mantenimiento

### Actualización del Catálogo

**Frecuencia recomendada**: Semanal

```bash
python app/modules/scraping/product_scraper.py
```

Este comando:
- Conecta con peisa.com.ar
- Extrae información actualizada de productos
- Genera nuevo `data/products_catalog.json`

### Verificar Estado del Sistema

```bash
# Verificar Ollama
curl http://127.0.0.1:11434/api/health

# Probar consulta RAG
python query/query.py "¿Tienen calderas de más de 17000 W?"

# Verificar embeddings
python scripts/test_embeddings.py
```

### Monitoreo de Logs

Los logs del sistema aparecen en la consola cuando ejecutas:
- Consultas RAG procesadas
- Productos encontrados
- Errores de conexión con Ollama

### Backup de Datos

**Archivos importantes a respaldar:**
- `data/products_catalog.json` - Catálogo de productos
- `app/peisa_advisor_knowledge_base.json` - Reglas del sistema experto
- `embeddings/products.faiss` - Índice de búsqueda (si se usa)

---

## Solución de Problemas

### Problemas Comunes

#### El Chatbot no responde

**Síntomas:**
- El chatbot se queda "pensando"
- Error de conexión
- Respuestas vacías

**Soluciones:**
1. Verificar que Ollama esté ejecutándose:
   ```bash
   ollama list  # Ver modelos disponibles
   ollama serve  # Iniciar servicio
   ```

2. Verificar el modelo:
   ```bash
   ollama pull llama3.2:3b
   ```

3. Reiniciar el servicio:
   ```bash
   # En Windows
   taskkill /f /im ollama.exe
   ollama serve
   ```

#### No aparecen productos

**Síntomas:**
- Búsquedas devuelven resultados vacíos
- Error "catálogo no encontrado"

**Soluciones:**
1. Actualizar catálogo:
   ```bash
   python app/modules/scraping/product_scraper.py
   ```

2. Verificar archivo:
   ```bash
   # Verificar que existe data/products_catalog.json
   ls -la data/products_catalog.json
   ```

#### Error al calcular en Sistema Experto

**Síntomas:**
- El cálculo se detiene
- Números incorrectos
- Error de expresión

**Soluciones:**
1. Verificar entrada de datos numéricos
2. Usar punto (.) como separador decimal, no coma (,)
3. Revisar que las dimensiones sean realistas

####  Respuestas muy largas del Chatbot

**Soluciones:**
1. El sistema tiene filtros automáticos, pero si persiste:
2. Editar `app/modules/chatbot/llm_wrapper.py`
3. Reducir `num_predict` en el parámetro de Ollama

####  Error de puerto ocupado

**Error:** `Port 8000 is already in use`

**Solución:**
```bash
# Usar otro puerto
python -m http.server 8080

# O encontrar y terminar el proceso
netstat -ano | findstr :8000
taskkill /f /pid NUMERO_PID
```

### Logs y Diagnóstico

**Habilitar modo debug:**
```bash
# Ejecutar con logs detallados
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python app/modules/chatbot/rag_engine_v2.py
```

### Contacto Técnico

Si los problemas persisten:

1. **Recolectar información:**
   - Versión de Python: `python --version`
   - Versión de Ollama: `ollama --version`
   - Sistema operativo
   - Mensaje de error completo

2. **Revisar documentación técnica:**
   - `docs/CHATBOT.md`
   - `docs/SISTEMA_EXPERTO.md`
   - `docs/MANUAL_ESCALAMIENTO.md`

---

##  Glosario

### Términos Técnicos

**IA Simbólica (Sistema Experto)**
: Inteligencia artificial basada en reglas explícitas y árboles de decisión. Es determinística y explicable.

**RAG (Retrieval-Augmented Generation)**
: Patrón que combina recuperación semántica de conocimiento con generación mediante un LLM.

**LLM (Large Language Model)**
: Modelo generativo de lenguaje. En nuestro caso, Ollama con llama3.2:3b.

**Embeddings**
: Representación numérica de textos que permite medir similitud semántica.

**FAISS**
: Librería de búsqueda vectorial eficiente utilizada para encontrar productos similares.

### Términos de Calefacción

**Carga Térmica**
: Cantidad de calor necesaria para mantener una temperatura confortable, medida en Watts (W) o kcal/h.

**ACS (Agua Caliente Sanitaria)**
: Sistema de agua caliente para uso doméstico (ducha, lavamanos, etc.).

**Potencia por m²**
: Regla práctica para calcular calefacción:
- Zona Norte/Centro: 100 W/m²
- Zona Sur: 125 W/m²

**Circuito de Piso Radiante**
: Bucle de caño por donde circula agua caliente. Máximo recomendado: 100 metros por circuito.

### Marcas y Productos

**PEISA**
: Marca argentina de productos de calefacción y agua caliente.

**SOLDASUR**
: Empresa distribuidora de productos PEISA en Tierra del Fuego con sucursales en Río Grande y Ushuaia.

---

##  Soporte

### Documentación Adicional

- **Sistema Experto**: `docs/SISTEMA_EXPERTO.md`
- **Chatbot RAG**: `docs/CHATBOT.md`
- **Scraping**: `docs/SCRAPING.md`
- **Escalamiento**: `docs/MANUAL_ESCALAMIENTO.md`
- **Pruebas**: `docs/TEST_*.md`

### Estructura del Proyecto

```
pp2-soldasur-2c-2025/
│
├── 📄 README.md                          # Documentación principal del proyecto
├── 📄 Manual_Usuario.md                  # Manual para usuarios finales
├── 📄 requirements.txt                   # Dependencias Python
├── 📄 LICENSE                            # Licencia del proyecto
├── 📄 Makefile                           # Comandos automatizados
├── 📄 .env                               # Variables de entorno
│
├── 📁 app/                               # ⭐ APLICACIÓN PRINCIPAL
│   │
│   ├── 🌐 index.html                   # Página web principal
│   ├── 🎨 soldasur.css                  # Estilos CSS
│   ├── ⚙️ soldasur.js                   # Lógica frontend principal
│   │
│   ├── 🔧 main.py                       # API FastAPI (endpoints)
│   ├── 🔧 app.py                        # Configuración de la app
│   ├── 🔧 orchestrator.py               # Orquestador híbrido (EXPERTO/RAG)
│   ├── 🔧 models.py                     # Modelos de datos
│   │
│   ├── 📋 peisa_advisor_knowledge_base.json  # ⭐ BASE DE CONOCIMIENTO (KB)
│   │
│   ├── 📁 modules/                      # ⭐ MÓDULOS DEL SISTEMA
│   │   │
│   │   ├── 📁 chatbot/                  # 🤖 CHATBOT (RAG + LLM)
│   │   │   ├── chatbot.js              # Frontend del chatbot
│   │   │   ├── llm_wrapper.py          # Wrapper de Ollama
│   │   │   └── rag_engine_v2.py        # Motor RAG (FAISS + Embeddings)
│   │   │
│   │   ├── 📁 expertSystem/             # 🧠 SISTEMA EXPERTO
│   │   │   ├── expertSystem.js         # Frontend del experto
│   │   │   ├── expert_engine.py        # Motor de inferencia
│   │   │   ├── product_loader.py       # Cargador de productos
│   │   │   └── models.py               # Modelos de radiadores
│   │   │
│   │   └── 📁 scraping/                 # 🕷️ WEB SCRAPING
│   │       ├── product_scraper.py      # Scraper de PEISA
│   │       └── inspect_peisa.py        # Inspector de HTML
│   │
│   └── 📁 img/                          # Imágenes de la app
│       └── soldy_head.png              # Favicon (Soldy)
│
├── 📁 data/                              # 💾 DATOS
│   └── products_catalog.json           # ⭐ CATÁLOGO DE PRODUCTOS
│
├── 📁 embeddings/                        # 🔢 VECTORES
│   └── products.faiss                   # Índice FAISS (búsqueda semántica)
│
├── 📁 ingest/                            # 📥 INGESTA DE DATOS
│   └── ingest.py                        # Script de ingesta (CSV → FAISS)
│
├── 📁 query/                             # 🔍 CONSULTAS
│   └── query.py                         # Script de consulta RAG
│
├── 📁 scripts/                           # 🛠️ SCRIPTS AUXILIARES
│   └── test_embeddings.py               # Test de embeddings
│
├── 📁 docs/                              # 📚 DOCUMENTACIÓN TÉCNICA
│   ├── GLOSARIO.md                      # Términos técnicos
│   ├── CHATBOT.md                       # Guía del chatbot
│   ├── SISTEMA_EXPERTO.md               # Guía del sistema experto
│   ├── SCRAPING.md                      # Guía de scraping
│   └── MANUAL_ESCALAMIENTO.md           # Manual para escalar
│
├── 📁 images/                            # 🖼️ IMÁGENES GENERALES
│   ├── logo_white.png                   # Logo SOLDASUR
│   ├── welcome.webp                     # Imagen de bienvenida
│   └── soldy_head.png                   # Avatar de Soldy
│
├── 📁 configs/                           # ⚙️ CONFIGURACIONES
│   └── params.yaml                      # Parámetros del sistema
│
└── 📁 tests/                             # 🧪 TESTS
```

#### 🔍 Explicación por Componentes

**🌐 Frontend (Interfaz de Usuario)**
```
app/
├── index.html    → Página web principal
├── soldasur.css         → Estilos visuales
└── soldasur.js          → Lógica de navegación y UI
```
Interfaz web que el usuario ve. Tiene 3 puntos de entrada: Guíame (experto), Pregunta (chat), Buscar productos.

**🤖 Chatbot (RAG + LLM)**
```
app/modules/chatbot/
├── chatbot.js           → Frontend del chat (memoria, filtrado)
├── llm_wrapper.py       → Conexión con Ollama (LLM local)
└── rag_engine_v2.py     → Búsqueda semántica (FAISS + embeddings)
```
Conversación libre en lenguaje natural. Busca productos similares y genera respuestas con Ollama.

**🧠 Sistema Experto (IA Simbólica)**
```
app/modules/expertSystem/
├── expertSystem.js          → Frontend del flujo guiado
├── expert_engine.py         → Motor de inferencia (ejecuta reglas)
├── product_loader.py        → Carga catálogo y funciones auxiliares
└── models.py                → Datos técnicos de radiadores

app/peisa_advisor_knowledge_base.json  → BASE DE CONOCIMIENTO (reglas)
```
Flujo guiado paso a paso con preguntas y cálculos. Dimensiona calefacción según reglas técnicas.

**🔗 Orquestador Híbrido**
```
app/orchestrator.py      → Clasifica intención y enruta (EXPERTO/RAG/HÍBRIDO)
```
Decide qué sistema usar según la consulta del usuario. Unifica ambos enfoques.

**🕷️ Scraping**
```
app/modules/scraping/
├── product_scraper.py   → Extrae productos de peisa.com.ar
└── inspect_peisa.py     → Inspecciona estructura HTML
```
Actualiza automáticamente el catálogo desde la web de PEISA.

**💾 Datos**
```
data/
└── products_catalog.json    → CATÁLOGO UNIFICADO (usado por experto y chatbot)

embeddings/
└── products.faiss           → Índice vectorial para búsqueda semántica
```
Fuente única de verdad para productos. Ambos sistemas lo consumen.

#### 🔄 Flujo de Datos Simplificado

```
┌─────────────┐
│   USUARIO   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  FRONTEND (index.html)          │
│  • Guíame (Experto)             │
│  • Pregunta (Chat)              │
│  • Buscar productos             │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  ORQUESTADOR (orchestrator.py)  │
│  Clasifica intención            │
└──────┬──────────────────────────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
┌─────────────┐ ┌─────────┐ ┌──────────┐
│   EXPERTO   │ │   RAG   │ │ HÍBRIDO  │
│   (Reglas)  │ │  (LLM)  │ │  (Ambos) │
└──────┬──────┘ └────┬────┘ └─────┬────┘
       │             │            │
       └─────────────┴────────────┘
                     │
                     ▼
       ┌─────────────────────────┐
       │  CATÁLOGO DE PRODUCTOS  │
       │  (products_catalog.json)│
       └─────────────────────────┘
```

#### 📊 Archivos Clave

| Archivo | Función | Tipo |
|---------|---------|------|
| `peisa_advisor_knowledge_base.json` | Base de conocimiento (reglas) | KB |
| `expert_engine.py` | Motor de inferencia | Backend |
| `llm_wrapper.py` | Conexión con Ollama | Backend |
| `rag_engine_v2.py` | Búsqueda semántica | Backend |
| `orchestrator.py` | Clasificador de intención | Backend |
| `product_scraper.py` | Scraping de PEISA | Script |
| `products_catalog.json` | Catálogo unificado | Datos |
| `index.html` | Interfaz web | Frontend |
| `chatbot.js` | Lógica del chat | Frontend |
| `expertSystem.js` | Lógica del experto | Frontend |

### Versiones y Actualizaciones

**Versión Actual**: 2025.1  
**Última Actualización**: Noviembre 2025

**Próximas Mejoras Planificadas:**
- Integración con sistema de inventario
- Calculadora de costos de instalación
- Soporte para múltiples idiomas
- App móvil

### Contribuciones

Para mejoras o reportes de errores:

1. **Documentar el problema**
2. **Incluir pasos para reproducir**
3. **Adjuntar logs relevantes**
4. **Sugerir solución si es posible**

### Licencia

Este proyecto se distribuye bajo los términos de la licencia incluida en `LICENSE`.

---

**© 2025 - Equipo PP2 SOLDASUR - Centro Politécnico Malvinas Argentinas**

