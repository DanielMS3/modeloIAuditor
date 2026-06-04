<<<<<<< HEAD
# 🎧 Dashboard de Auditoría QA Inteligente

> Sistema automatizado de auditoría de llamadas con análisis de sentimientos por IA, visualización de dinámicas emocionales y generación de reportes ejecutivos.

---

## 📋 Descripción General

Este sistema automatiza la auditoría de archivos de audio mediante procesamiento de lenguaje natural y análisis de sentimientos. El Dashboard permite:

- Visualizar **métricas de desempeño** de agentes.
- Analizar **dinámicas emocionales** entre agentes y clientes a lo largo de cada llamada.
- Obtener **conclusiones automatizadas por IA** sobre la calidad del servicio.
- Exportar reportes en **PDF** y **Excel**.

---

## 🗂️ Estructura del Proyecto

```
/
├── analisis_grafica/            # Gráficas generadas del análisis de sentimiento
├── audios/                      # Archivos de audio fuente para procesar
├── dashboard_graficas/          # Imágenes de dinámicas emocionales para el dashboard
├── metricas_silencio/           # Datos y análisis de métricas de silencio por llamada
├── reportes_qa/                 # Reportes de auditoría generados
├── transcripciones/             # JSONs individuales por llamada (transcripción + sentimiento)
├── venv/                        # Entorno virtual de Python
├── .env                         # Variables de entorno (API keys, configuración)
├── dashboard.html               # Interfaz principal del dashboard
├── datos_reportes.json          # Base de datos maestra de auditorías procesadas
├── ffmpeg.exe                   # Binario de FFmpeg para procesamiento de audio
├── indicadores.json             # Configuración de indicadores y métricas de evaluación
├── main.py                      # Script principal de procesamiento y análisis
└── transcripcion.html           # Vista de detalle de transcripción individual
```

| Archivo / Carpeta | Descripción |
|---|---|
| `main.py` | Procesa los audios, realiza el análisis de sentimiento y genera los JSON y gráficas. |
| `dashboard.html` | Frontend principal para la visualización e interacción con los resultados. |
| `transcripcion.html` | Vista de detalle para explorar la transcripción y sentimiento de una llamada individual. |
| `datos_reportes.json` | Resumen consolidado de todas las auditorías. Actualizado automáticamente por `main.py`. |
| `indicadores.json` | Define los indicadores y criterios de calidad usados en la evaluación. |
| `audios/` | Carpeta de entrada con los archivos de audio a procesar. |
| `transcripciones/` | Un JSON por llamada con la transcripción detallada y los datos de sentimiento segmento a segmento. |
| `analisis_grafica/` | Gráficas generadas durante el análisis de sentimiento. |
| `dashboard_graficas/` | Imágenes de dinámicas emocionales utilizadas por el dashboard. |
| `metricas_silencio/` | Archivos con el análisis de silencios detectados en cada llamada. |
| `reportes_qa/` | Reportes de auditoría exportados. |
| `ffmpeg.exe` | Binario de FFmpeg requerido para el procesamiento y conversión de audio. |
| `.env` | Variables de entorno sensibles (API keys, rutas). **No incluir en control de versiones.** |
| `venv/` | Entorno virtual de Python. **No incluir en control de versiones.** |

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python** — Orquestación del pipeline de procesamiento.
- **Pandas** — Manipulación y estructuración de datos.
- **Matplotlib** — Generación de gráficas de dinámicas emocionales.
- **OpenAI API (`gpt-4o-mini`)** — Análisis de sentimientos e interpretación de calidad.

### Frontend
- **HTML5 / CSS3 / JavaScript**
- **Chart.js** — Gráficos interactivos en el dashboard.
- **jQuery + DataTables** — Tablas dinámicas y filtros.
- **jsPDF** — Exportación de reportes en PDF.
- **xlsx** — Exportación de datos a Excel.

---

## 🚀 Guía de Operación

### 1. Procesamiento de nuevas llamadas

Asegúrate de que los archivos de audio estén en la ruta definida en `main.py`, luego ejecuta:

```bash
python main.py
```

El script generará automáticamente:
- Los archivos JSON individuales en `/transcripciones/`.
- Las imágenes de gráficas en `/graficas/`.
- Actualizará el archivo `datos_reportes.json`.

### 2. Visualización del Dashboard

Levanta un servidor local desde la carpeta raíz del proyecto:

```bash
python -m http.server 8000
```

Luego abre en tu navegador:

```
http://localhost:8000/dashboard.html
```

---

## 🧠 Lógica de Auditoría con IA

El sistema utiliza **GPT-4o-mini** para el análisis de calidad. El pipeline sigue estos pasos:

```
Audio
  │
  ▼
1. Diarización ──────────► Separación por interlocutor (Cliente / Agente)
  │
  ▼
2. Análisis de Sentimiento ► Polaridad emocional por segmento (-1.0 a +1.0)
  │
  ▼
3. Interpretación por IA ──► Trayectoria emocional, efectividad del agente,
                              probabilidad de éxito del objetivo
```

La IA evalúa específicamente:

- **Caídas críticas** en el sentimiento del cliente.
- **Efectividad del agente** para estabilizar o reencausar la llamada.
- **Probabilidad de cierre** o cumplimiento del objetivo de la llamada.

---

## 📤 Exportación de Reportes

| Formato | Contenido |
|---|---|
| **PDF** | Reporte ejecutivo con gráficas de sentimiento y observaciones del caso seleccionado. |
| **Excel** | Tabla global con todos los archivos auditados, lista para filtrado y análisis externo. |

---

## 📌 Notas

- El dashboard consume los datos directamente desde `datos_reportes.json` y los archivos en `/transcripciones/`, por lo que **no requiere base de datos externa**.
- Para agregar nuevas llamadas basta con correr `main.py`; no es necesario modificar el frontend.
- Se recomienda un `.gitignore` que excluya `venv/`, `.env`, `audios/` y `ffmpeg.exe`.
=======
# nombre-repo
>>>>>>> 8b0f6953796ec4fab9d0b9d821405f9f23e6171c
