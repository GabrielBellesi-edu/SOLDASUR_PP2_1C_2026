# SoldaSur IA Chatbot 🤖

### Sistema de Asesoramiento Técnico y Comercial Multimarca Inteligente

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=for-the-badge)](https://ollama.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20DB-blue?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![Playwright](https://img.shields.io/badge/Playwright-Web%20Scraping-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/)

---

## 📋 Descripción del Proyecto

El **SoldaSur IA Chatbot** es una solución de asistencia inteligente diseñada para las sucursales de **Soldasur S.A.** en Tierra del Fuego, desarrollada en el marco de la **Práctica Profesionalizante II** del **Centro Politécnico Malvinas Argentinas (CPMA)**.

El sistema fusiona dos enfoques complementarios de Inteligencia Artificial para ofrecer una experiencia interactiva completa:
1. **Sistemas Expertos (IA Simbólica):** Motores basados en reglas explícitas para realizar cómputo de materiales y dimensionamientos complejos en obra (por ejemplo, cálculo de metros de caño para piso radiante PEISA o cantidad de adhesivos Weber según metros cuadrados).
2. **Motores RAG (Generación Aumentada por Recuperación):** Búsqueda semántica sobre los catálogos técnicos de las marcas integradas y generación de respuestas contextualizadas en español rioplatense a través de un modelo de lenguaje local y privado.

Una característica clave de la ultima versión es su **arquitectura escalable**, que permite registrar e incorporar de manera dinámica nuevas marcas y catálogos (por ejemplo, Durlock) sin necesidad de modificar el código fuente central del backend.

---

## 👥 Integrantes del Grupo

* **Elias Albornoz**  
  [![GitHub](https://img.shields.io/badge/GitHub-AlbornozElias-181717?style=flat&logo=github)](https://github.com/AlbornozElias) [![LinkedIn](https://img.shields.io/badge/LinkedIn-Elias%20Albornoz-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/elias-albornoz)
* **Gabriel Bellesi**  
  [![GitHub](https://img.shields.io/badge/GitHub-GabrielBellesi--edu-181717?style=flat&logo=github)](https://github.com/GabrielBellesi-edu) [![LinkedIn](https://img.shields.io/badge/LinkedIn-Gabriel%20Bellesi-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/gabriel-undefined-edu)
* **Miriam Velazque**  
  [![GitHub](https://img.shields.io/badge/GitHub-miriamvelazque-181717?style=flat&logo=github)](https://github.com/miriamvelazque) [![LinkedIn](https://img.shields.io/badge/LinkedIn-Miriam%20Velazque-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/miriam-alicia-velazque)

---

## 🛠️ Tecnologías Utilizadas

### Backend y Servidor API
* [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/) — Lenguaje principal de desarrollo.
* [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) — Framework para la creación de endpoints de API veloces.
* [![Uvicorn](https://img.shields.io/badge/Uvicorn-0.34+-499848?style=flat&logo=uvicorn&logoColor=white)](https://www.uvicorn.org/) — Servidor ASGI para producción y desarrollo.
* [![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/) — Validación de datos y esquemas de configuración.

### Inteligencia Artificial y Motores de Búsqueda
* [![Ollama](https://img.shields.io/badge/Ollama-Llama%203.2%20(3b)-black?style=flat)](https://ollama.com/) — Orquestación local y offline de modelos de lenguaje (LLM).
* [![FAISS](https://img.shields.io/badge/FAISS-Vector%20DB-blue?style=flat)](https://github.com/facebookresearch/faiss) — Base de datos vectorial optimizada para búsqueda semántica.
* [![PyTorch](https://img.shields.io/badge/PyTorch-2.7+-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/) — Plataforma base para modelos de embeddings.
* [![HuggingFace](https://img.shields.io/badge/Sentence--Transformers-3.0+-yellow?style=flat&logo=huggingface&logoColor=black)](https://sbert.net/) — Generación de embeddings densos de texto.

### Extracción de Datos (Scraping)
* [![BeautifulSoup4](https://img.shields.io/badge/BeautifulSoup4-Parsing-green?style=flat)](https://www.crummy.com/software/BeautifulSoup/bs4/) — Extracción rápida de catálogos estáticos.
* [![Playwright](https://img.shields.io/badge/Playwright-Automation-2EAD33?style=flat&logo=playwright&logoColor=white)](https://playwright.dev/) — Extracción interactiva en sitios con SPA o carga diferida.

### Frontend
* [![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)](https://developer.mozilla.org/es/docs/Web/HTML) — Estructura semántica de la interfaz de chat.
* [![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)](https://developer.mozilla.org/es/docs/Web/CSS) — Diseño visual personalizado con efectos y responsive.
* [![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=flat&logo=javascript&logoColor=black)](https://developer.mozilla.org/es/docs/Web/JavaScript) — Módulos dinámicos para el flujo de chat y calculadoras.

---

## ⚡ Guía de Inicio Rápido

Sigue estos pasos para poner en marcha el proyecto localmente.

### Prerrequisitos
* Tener **Python 3.10 o superior** instalado.
* Tener **Ollama** instalado y ejecutándose en segundo plano.

### 1. Descarga del Modelo de Lenguaje
Asegúrate de contar con el modelo base descargado en tu servidor de Ollama:
```bash
ollama pull llama3.2:3b
```

### 2. Configuración del Entorno de Python
Clona el repositorio, navega hasta la raíz e inicializa tu entorno virtual:

**En Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**En Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Instala todas las dependencias requeridas:
```bash
pip install -r requirements.txt
```

### 3. Ejecución del Servidor Backend
Levanta la aplicación mediante Uvicorn:
```bash
python -m uvicorn app.main:app --reload
```
El servidor iniciará y estará escuchando peticiones en `http://localhost:8000`.

### 4. Acceder al Chatbot
Abre tu navegador de preferencia e ingresa a:
👉 [http://localhost:8000](http://localhost:8000)

---

## 📂 Estructura Principal del Proyecto

* **`/app`**: Contiene la lógica del backend, el orquestador principal de intenciones (`orchestrator.py`), y los módulos de los sistemas expertos.
* **`/configs`**: Configuración centralizada de prompts del LLM (`prompts.json`) e índices de marcas registradas (`brands_registry.json`).
* **`/docs`**: Documentación técnica detallada y guías de mantenimiento.
* **`/RAG_engine`**: Base de datos vectorial de FAISS, metadatos y scripts de ingesta semántica (`ingest.py`).
* **`/scraping`**: Scripts de actualización autónoma de catálogos mediante web scraping para PEISA y Weber.
* **`/web_app`**: Recursos del frontend estático (HTML, CSS, JavaScript y catálogos locales).

---

## 📖 Documentación Detallada

Para más información sobre el mantenimiento, desarrollo y escalado de la aplicación, puedes consultar los siguientes documentos técnicos ubicados en la carpeta `/docs`:

* 📘 **[Manual de Usuario](./docs/MANUAL_USUARIO.md):** Manual detallado de instalación, configuración del LLM y uso de calculadoras.
* 🛠️ **[Manual de Escalamiento](./docs/MANUAL_ESCALAMIENTO.md):** Guía paso a paso sobre cómo registrar e instalar una nueva marca y catálogo de productos.
* 🧠 **[Manual Técnico del Orquestador](./docs/MANUAL_TECNICO_ORQUESTADOR.md):** Explicación del funcionamiento de la lógica de decisiones e intenciones híbridas.
* 📐 **[Manual Técnico del Sistema Experto Weber](./docs/MANUAL_TECNICO_SISTEMA_EXPERTO_WEBBER.md):** Detalle de fórmulas y lógica de cómputo de materiales de construcción.

---
**Soldasur S.A. IA Chatbot © 2026** - Proyecto Desarrollado para la Práctica Profesionalizante II del Centro Politécnico Malvinas Argentinas.
