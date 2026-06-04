import os
import json
import whisper
import glob
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
from dotenv import load_dotenv

# --- 1. CONFIGURACIÓN ---
# Carga variables de entorno (API Key) y configura el cliente de OpenAI y el modelo de transcripción
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
whisper_model = whisper.load_model("small")
os.environ["PATH"] += os.pathsep + os.path.dirname(os.path.abspath(__file__))

# --- 2. RUTAS ---
# Definición de directorios para organizar los archivos generados durante el proceso
RUTA_TRANS = "transcripciones"
RUTA_TRANS = "transcripciones"
RUTA_REPORTES = "reportes_qa"
RUTA_SILENCIOS = "metricas_silencio"
RUTA_DASHBOARD = "dashboard_graficas"
RUTA_ANALISIS_GRAFICA = "analisis_grafica"
for r in [RUTA_TRANS, RUTA_REPORTES, RUTA_SILENCIOS, RUTA_DASHBOARD,RUTA_ANALISIS_GRAFICA]:
    os.makedirs(r, exist_ok=True)

# --- 3. CARGA Y NORMALIZACIÓN DE INDICADORES ---
# Lee los criterios de evaluación desde un archivo JSON externo
with open("indicadores.json", "r", encoding="utf-8") as f:
    datos_raw = json.load(f)

# Convierte los pesos/scores a formato numérico para cálculos matemáticos posteriores
matriz_normalizada = []
for i in datos_raw:
    score_str = str(i.get("score", "0")).replace("%", "").strip()
    val = float(score_str)
    matriz_normalizada.append({
        "atributo": i["atributo"], 
        "peso_atributo": val * 100 if val < 1 else val
    })

# --- 4. FUNCIONES ---

def calcular_metricas_silencio(segmentos, duracion_total):
    # Identifica pausas mayores a 1.5 segundos entre bloques de voz
    silencios = [ {"inicio": round(s1['end'], 2), "fin": round(s2['start'], 2), "duracion": round(s2['start'] - s1['end'], 2)} 
                 for s1, s2 in zip(segmentos, segmentos[1:]) if (s2['start'] - s1['end']) > 1.5 ]
    total = sum(s['duracion'] for s in silencios)
    # Retorna un resumen estadístico de los silencios detectados
    return {
        "duracion_total_audio": round(duracion_total, 2),
        "total_silencio_segundos": round(total, 2),
        "porcentaje_silencio": round((total / duracion_total) * 100, 2) if duracion_total > 0 else 0,
        "cantidad_pausas_largas": len(silencios)
    }

def generar_grafica_comparativa_y_analisis(archivo, segmentos):
    # Retorna un resumen estadístico de los silencios detectados.
    df = pd.DataFrame(segmentos)
    df_pivot = df.pivot_table(index="tiempo", columns="rol", values="sentimiento").ffill().fillna(0)
    # Manejo de errores: si un rol no tiene datos, crea serie de ceros para evitar errores al graficar
    cliente_data = df_pivot["CLIENTE"] if "CLIENTE" in df_pivot.columns else pd.Series(0, index=df_pivot.index)
    agente_data = df_pivot["AGENTE"] if "AGENTE" in df_pivot.columns else pd.Series(0, index=df_pivot.index)
    
    # 2. Genera y guarda una gráfica de línea de la dinámica emocional
    plt.figure(figsize=(12, 6))
    plt.plot(df_pivot.index, cliente_data, label='Cliente', marker='o', color='teal')
    plt.plot(df_pivot.index, agente_data, label='Agente', marker='x', color='orange', linestyle='--')
    
    plt.axhline(0, color='red', linestyle=':', alpha=0.5)
    plt.title(f"Dinámica Emocional: {archivo}")
    plt.legend()
    plt.savefig(os.path.join(RUTA_DASHBOARD, f"{archivo}_comparativa.png"))
    plt.close()

    # 3. Envía los datos estadísticos a GPT para obtener un análisis cualitativo
    resumen_datos = {
        "estadisticas": df_pivot.describe().to_dict(),
        "tendencia_cliente": cliente_data.tolist(),
        "tendencia_agente": agente_data.tolist()
    }
    
    prompt = f"""
    Eres un auditor senior. Analiza los datos de sentimiento de una llamada:
    {json.dumps(resumen_datos)}
    
    Analiza la dinámica entre el Agente y el Cliente:
    - ¿Hubo una caída crítica en el sentimiento del cliente?
    - ¿El agente logró estabilizar o mejorar el sentimiento del cliente?
    - Basado en esta trayectoria, ¿se concluye que se logró la venta o el objetivo?
    
    Responde estrictamente en formato JSON:
    {{
        "analisis_dinamica": "Explicación de la montaña rusa emocional",
        "probabilidad_cierre": "Alta/Media/Baja",
        "conclusion": "Se logró o no la venta y por qué"
    }}
    """
    
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Responde solo JSON."}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    # 4. Guarda el análisis resultante en formato JSON
    analisis = json.loads(resp.choices[0].message.content)
    
    with open(os.path.join(RUTA_ANALISIS_GRAFICA, f"{archivo}_analisis.json"), "w", encoding="utf-8") as f:
        json.dump(analisis, f, indent=4, ensure_ascii=False)
        
    return analisis

def procesar_auditoria(texto_json):
    # Define el prompt para auditar la llamada según los indicadores cargados
    prompt = f"""
    Eres un auditor BPO experto y BENEVOLENTE.
    1. ANALISIS: Clasifica [AGENTE] vs [CLIENTE].
    2. SENTIMIENTO: Asigna a CADA segmento del cliente un valor de -1.0 a 1.0.
    3. VENTAS: Explica la causa raíz del éxito o fracaso de la venta.
    4. EVALUACIÓN: Evalúa al [AGENTE] con: {json.dumps(matriz_normalizada)}.
    
    REGLAS DE FLEXIBILIDAD:
    - Si el agente intenta realizar la acción, califica entre 0.85 y 1.0.
    - No califiques menos de 0.7 a menos que la omisión sea total.
    - REGLA DE APROBACIÓN: score_final >= 80 es "APROBADO", menor a 80 es "REPROBADO".
    
    Devuelve JSON exacto:
    {{
        "transcripcion_diarizada": [{{"tiempo": "MM:SS", "rol": "[AGENTE/CLIENTE]", "texto": "...", "sentimiento": float}}],
        "auditoria_agente": [{{"atributo": "Nombre", "peso_atributo": float, "cumplimiento": float, "observacion": "..."}}],
        "analisis_resultado": "...",
        "resultado_final": "APROBADO/REPROBADO",
        "observaciones_generales": "..."
    }}
    Transcripción: {texto_json}
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[{"role": "system", "content": "Responde solo JSON."}, {"role": "user", "content": prompt}], 
        response_format={"type": "json_object"}
    )
    data = json.loads(resp.choices[0].message.content)
    # Calcula el score final basado en el cumplimiento ponderado de cada atributo
    suma_scores = 0
    for item in data["auditoria_agente"]:
        item["score_obtenido"] = round(float(item["cumplimiento"]) * float(item["peso_atributo"]), 2)
        suma_scores += item["score_obtenido"]
    
    data["score_final"] = round(suma_scores, 2)
    return data

def generar_datos_dashboard():
    # Calcula el score final basado en el cumplimiento ponderado de cada atributo
    reportes = []
    lista_archivos = glob.glob(os.path.join(RUTA_REPORTES, "*.json"))
    
    for archivo in lista_archivos:
        with open(archivo, "r", encoding="utf-8") as f:
            reportes.append(json.load(f))
    
    # Añade el sentimiento promedio por archivo para enriquecer el dashboard
    for r in reportes:
        # Buscamos la transcripción asociada para obtener los sentimientos
        trans_path = os.path.join(RUTA_TRANS, r["archivo"] + ".json")
        if os.path.exists(trans_path):
            with open(trans_path, "r", encoding="utf-8") as f:
                trans = json.load(f)
                sentimientos = [s.get("sentimiento", 0) for s in trans if "sentimiento" in s]
                r["sentimiento_promedio"] = sum(sentimientos) / len(sentimientos) if sentimientos else 0
    
    with open("datos_reportes.json", "w", encoding="utf-8") as f:
        json.dump(reportes, f, indent=4, ensure_ascii=False)
    
    print(f"📊 Dashboard actualizado: {len(reportes)} reportes procesados con métricas de sentimiento.")

def procesar_llamadas():
    # Bucle principal: recorre audios, transcribe, audita, genera gráficas y exporta reportes
    """
    Función principal que recorre los archivos, realiza la transcripción,
    auditoría, análisis de sentimiento, generación de gráficas y análisis de IA.
    """
    # Verificamos si la carpeta de audios existe
    if not os.path.exists("audios"):
        print("❌ La carpeta 'audios' no existe.")
        return

    for archivo in os.listdir("audios"):
        if archivo.lower().endswith(('.wav', '.mp3', '.m4a')):
            print(f"🎙️ Procesando: {archivo}...")
            
            # 1. Transcripción con Whisper
            res = whisper_model.transcribe(os.path.join("audios", archivo), language="es")
            duracion = res["segments"][-1]["end"] if res["segments"] else 0
            
            # 2. Formateo para la IA
            lista_raw = [{"tiempo": f"{int(s['start']//60):02}:{int(s['start']%60):02}", "texto": s['text']} for s in res["segments"]]
            resultado = procesar_auditoria(json.dumps(lista_raw))
            
            # 3. Guardar transcripción
            with open(os.path.join(RUTA_TRANS, f"{archivo}.json"), "w", encoding="utf-8") as f:
                json.dump(resultado["transcripcion_diarizada"], f, indent=4, ensure_ascii=False)
            
            # 4. Guardar métricas de silencio
            with open(os.path.join(RUTA_SILENCIOS, f"{archivo}_silencio.json"), "w", encoding="utf-8") as f:
                json.dump(calcular_metricas_silencio(res["segments"], duracion), f, indent=4, ensure_ascii=False)
            
            # 5. Generar gráfica comparativa y análisis de IA sobre la gráfica
            analisis_ia = generar_grafica_comparativa_y_analisis(archivo, resultado["transcripcion_diarizada"])
            
            # 6. Guardar reporte consolidado
            with open(os.path.join(RUTA_REPORTES, f"{archivo}_reporte.json"), "w", encoding="utf-8") as f:
                json.dump({
                    "archivo": archivo,
                    "tiempo_ejecucion_segundos": duracion,
                    "score_final": resultado["score_final"],
                    "resultado_final": resultado["resultado_final"],
                    "analisis_resultado": resultado["analisis_resultado"],
                    "detalle_auditoria": resultado["auditoria_agente"],
                    "observaciones": resultado["observaciones_generales"],
                    "analisis_grafica_ia": analisis_ia # Incluye el análisis dinámico de la gráfica
                }, f, indent=4, ensure_ascii=False)

    # 7. Generar dashboard consolidado
    generar_datos_dashboard()
    print("✅ Proceso terminado. Datos y análisis exportados correctamente.")

if __name__ == "__main__":
    procesar_llamadas() # Punto de inicio del script