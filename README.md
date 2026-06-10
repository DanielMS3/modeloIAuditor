
---

# 🎧 Dashboard de Auditoría QA Inteligente

> Sistema automatizado de auditoría de llamadas con análisis de sentimientos por IA, visualización de dinámicas emocionales y generación de reportes ejecutivos.

---

## 📋 Descripción General

Este sistema automatiza la auditoría de archivos de audio mediante procesamiento de lenguaje natural y análisis de sentimientos. El Dashboard permite:

* **Visualizar métricas** de desempeño de agentes.
* **Analizar dinámicas emocionales** entre agentes y clientes a lo largo de cada llamada.
* **Obtener conclusiones automatizadas** por IA sobre la calidad del servicio.
* **Exportar reportes** dinámicos en PDF y Excel.

---

## 🐍 Configuración del Entorno Virtual

Para mantener las librerías del proyecto organizadas y aisladas, utiliza un entorno virtual:

1. **Crear el entorno virtual:**
```bash
python -m venv venv

```


2. **Configurar permisos de ejecución (si es necesario):**
Si recibes un error al intentar activar el entorno, ejecuta este comando para permitir la ejecución de scripts en la terminal actual:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

```


3. **Activar el entorno virtual:**
```bash
.\venv\Scripts\activate

```



---

### ¿Cómo se integrarlo el README?

1. Clonar el repositorio.
2. Crear y activar el entorno virtual (lo que acabamos de agregar).
3. Instalar las dependencias (`pip install...`).
5. Procesar los audios.


## 🛠️ Instalación y Requisitos

### 1. Dependencias de Python

Asegúrate de tener instalado [Python](https://www.python.org/) y luego instala las librerías necesarias ejecutando:

```bash
pip install openai openai-whisper pandas matplotlib python-dotenv

```

### 2. Prerrequisitos de Audio (FFmpeg)

Este sistema utiliza `whisper` para procesar archivos de audio. Para que esto funcione, necesitas tener **FFmpeg** instalado en tu sistema.

**Instalación rápida:**

* **Windows (Winget):** `winget install ffmpeg`
* **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install ffmpeg`
* **macOS (Homebrew):** `brew install ffmpeg`

---

## 🗂️ Estructura del Proyecto

```text
/
├── analisis_grafica/           # Análisis cualitativo de IA sobre gráficas
├── audios/                     # (Carpeta ignorada) Archivos de entrada
├── dashboard_graficas/         # Gráficas visuales (.png)
├── metricas_silencio/          # Estadísticas de pausas y silencios
├── reportes_qa/                # Reportes finales de auditoría
├── transcripciones/            # Datos diarizados y sentimiento por segmento
├── venv/                       # (Carpeta ignorada) Entorno virtual
├── .env                        # (Secreto) Variables de entorno
├── .gitignore                  # Reglas de exclusión de archivos
├── dashboard.html              # Interfaz principal
├── datos_reportes.json         # Base de datos maestra
├── indicadores.json            # Configuración de criterios de calidad
├── main.py                     # Motor principal del pipeline
└── transcripcion.html          # Vista de detalle

```

---
Aquí tienes la sección de **"Configuración del Entorno Virtual"** actualizada para que la incluyas en tu `README.md`. He organizado los comandos para que cualquier usuario sepa exactamente qué hacer en Windows:

---

## 🚀 Guía de Operación

### 1. Preparación

Crea un archivo `.env` en la raíz con tu clave API:

```text
OPENAI_API_KEY=tu_clave_aqui

```

### 2. Procesamiento

Coloca tus audios (`.wav`, `.mp3`, `.m4a`) en la carpeta `/audios/` y ejecuta:

```bash
python main.py

```

### 3. Visualización

Levanta un servidor local:

```bash
python -m http.server 8000

```

Abre en tu navegador: `http://localhost:8000/dashboard.html`

---

## 🧠 Lógica de Auditoría con IA

El sistema sigue un pipeline automatizado para transformar audio crudo en conocimiento accionable:

1. **Diarización:** Identificación de roles (Cliente vs. Agente).
2. **Análisis Emocional:** Asignación de valores de sentimiento (-1.0 a +1.0) por segmento.
3. **Auditoría IA:** Evaluación basada en criterios de negocio (`indicadores.json`).
4. **Conclusión:** Determinación de efectividad, raíz del éxito/fracaso y probabilidad de cierre.

---

## 📌 Notas de Seguridad y Mantenimiento

* **Seguridad:** El archivo `.env` y el ejecutable `ffmpeg.exe` **no deben subirse nunca** al repositorio. Utiliza el archivo `.gitignore` para excluirlos.
* **Actualización:** El sistema es modular. Para cambiar los criterios de auditoría, simplemente edita `indicadores.json`.
* **Escalabilidad:** Al basarse en archivos JSON, puedes procesar miles de llamadas sin necesidad de bases de datos complejas.

---

*Desarrollado para la optimización de procesos de calidad en BPO.*
