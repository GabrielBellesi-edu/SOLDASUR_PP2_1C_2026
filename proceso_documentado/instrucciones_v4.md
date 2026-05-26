# Instrucciones de Puesta en Marcha y Uso: SOLDASUR v4

Este documento detalla los pasos técnicos necesarios para clonar, configurar e iniciar el proyecto **SOLDASUR v4** en un entorno local, así como una breve descripción de sus funcionalidades clave.

---

## 1. Preparación (Antes de arrancar)

Asegúrate de contar con los siguientes requisitos previos instalados en tu sistema:

*   **Python 3.12:** Descarga e instala la versión correspondiente para tu sistema operativo desde el [sitio oficial de Python](https://www.python.org/downloads/). *(Asegúrate de marcar la opción "Add Python to PATH" durante la instalación).*
*   **Ollama:** Necesario para ejecutar el motor de inteligencia artificial local del chatbot. Descárgalo desde el [sitio oficial de Ollama](https://ollama.com/download).
    *   Una vez instalado, abre una consola (Terminal o CMD) y ejecuta el siguiente comando para descargar el modelo de lenguaje de IA:
        ```bash
        ollama pull llama3.2:3b
        ```
*   **Git:** Clona la rama de desarrollo (`develop`) del repositorio del proyecto en tu computadora ejecutando:
    ```bash
    git clone -b develop https://github.com/GabrielBellesi-edu/SOLDASUR_PP2_1C_2026.git
    ```

---

## 2. Guía Paso a Paso para Iniciar el Sistema

Una vez clonado el repositorio, abre una consola dentro de la carpeta raíz del proyecto (`SOLDASUR_PP2_1C_2026/`) y realiza las siguientes acciones:

### Paso 1: Configurar el Entorno Virtual (venv)
Crea un entorno virtual limpio para el proyecto.
*   Si solo tienes una versión de Python instalada:
    ```bash
    python -m venv venv
    ```
*   Si tienes múltiples versiones instaladas y necesitas especificar Python 3.12:
    ```bash
    py -3.12 -m venv venv
    ```

### Paso 2: Activar el Entorno Virtual
Activa el entorno virtual para que la consola use los paquetes aislados del proyecto:
```bash
venv\Scripts\activate
```
*(En macOS/Linux el comando es `source venv/bin/activate`)*.

### Paso 3: Instalar Dependencias
Instala todas las librerías necesarias especificadas en [requirements.txt](../requirements.txt):
```bash
pip install -r requirements.txt
```

### Paso 4: Levantar el Servidor de IA (Ollama)
Asegúrate de tener corriendo Ollama de fondo. Puedes abrir la aplicación de escritorio de Ollama o levantar el servicio desde otra ventana de la consola usando:
```bash
ollama serve
```

### Paso 5: Ejecutar la Aplicación (FastAPI/Uvicorn)
Inicia el servidor local de desarrollo de FastAPI unificado desde la terminal donde activaste tu entorno virtual:
```bash
python -m uvicorn app.main:app --port 8000 --reload
```
*(El archivo de inicialización del servidor es [main.py](../app/main.py))*.

### Paso 6: Abrir en el Navegador
Con el servidor corriendo, abre tu navegador de internet e ingresa a la siguiente dirección:
```text
http://localhost:8000/
```

---

## 3. Guía de Uso del Sistema

La interfaz principal integra tres áreas clave de trabajo:

### A. Calculadora de Calefacción PEISA (100% Offline)
*   **Acceso:** Menú principal → Opción Calefacción PEISA.
*   **Funcionamiento:** Cuestionario interactivo local en JavaScript gestionado por [peisa_expert.js](../app/modules/peisa/peisa_expert.js). Realiza cálculos de carga térmica y dimensionamiento de radiadores en el cliente sin realizar consultas de red externas.
*   **Resultado:** Muestra tarjetas visuales con calderas, radiadores y toalleros PEISA adecuados para el espacio calculado.

### B. Calculadora de Materiales Weber (100% Offline)
*   **Acceso:** Menú principal → Opción Materiales Weber.
*   **Funcionamiento:** Cuestionario dinámico de tipo de soporte y entrada de metros cuadrados procesado enteramente por [weber_expert.js](../app/modules/weber/weber_expert.js).
*   **Resultado:** Indica en pantalla la cantidad de bolsas de adhesivo y pastina Weber recomendadas contemplando los rendimientos específicos y un 10% de desperdicio técnico.

### C. Chatbot Asistente con Inteligencia Artificial (RAG Semántico)
*   **Acceso:** Ícono de chat flotante en la esquina inferior derecha.
*   **Funcionamiento:** Gestionado por el script [chatbot.js](../app/modules/chatbot/chatbot.js) que conecta con el backend de FastAPI en `/api/chat`. Realiza una consulta semántica vectorial en la base de datos local y le provee al modelo local de Ollama (`llama3.2:3b`) el contexto necesario.
*   **Tolerancia a fallos:** Al usar embeddings semánticos, el asistente comprende sinónimos y maneja errores de ortografía de forma nativa.
*   *Nota: Si Ollama no está activo, el sistema mostrará un aviso de error de conexión en la ventana del chat, pero las calculadoras de PEISA y Weber seguirán funcionando normalmente en el navegador.*
