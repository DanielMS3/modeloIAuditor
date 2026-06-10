import os
import json
import glob
import whisper
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from openai import OpenAI
from dotenv import load_dotenv

# --- 1. CONFIGURACIÓN ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
whisper_model = whisper.load_model("small")

# --- 2. RUTAS ---
RUTA_TRANS = "transcripciones"
RUTA_REPORTES = "reportes_qa"
RUTA_SILENCIOS = "metricas_silencio"
RUTA_DASHBOARD = "dashboard_graficas"
RUTA_ANALISIS_GRAFICA = "analisis_grafica"

for r in [RUTA_TRANS, RUTA_REPORTES, RUTA_SILENCIOS, RUTA_DASHBOARD, RUTA_ANALISIS_GRAFICA]:
    os.makedirs(r, exist_ok=True)

# --- 3. INDICADORES ---
with open("indicadores.json", "r", encoding="utf-8") as f:
    datos_raw = json.load(f)

matriz_normalizada = []
for i in datos_raw:
    score_str = str(i.get("score", "0")).replace("%", "").strip()
    val = float(score_str)
    matriz_normalizada.append({
        "atributo": i["atributo"],
        "peso_atributo": val * 100 if val < 1 else val
    })

# --- 4. FUNCIONES ---

def safe_float(valor, default=0.0):
    try:
        return float(valor)
    except:
        return default

def clasificar_semaforo(sentimiento):
    try:
        sentimiento = float(sentimiento)
    except (TypeError, ValueError):
        sentimiento = 0.0  # fallback seguro

    if sentimiento <= -1.0:
        return "NEGATIVO"
    elif sentimiento > 0:
        return "POSITIVO"
    else:
        return "NEUTRO"

def generar_semaforo_sentimientos(segmentos):
    detalle = []
    momentos_criticos = []
    transiciones = []

    for i, seg in enumerate(segmentos):
        sentimiento = safe_float(seg.get("sentimiento"))
        estado = clasificar_semaforo(sentimiento)

        item = {
            "tiempo": seg["tiempo"],
            "rol": seg["rol"],
            "sentimiento": sentimiento,
            "estado": estado
        }

        if i > 0:            
            anterior = safe_float(segmentos[i - 1].get("sentimiento"))
            diferencia = sentimiento - anterior

            if diferencia <= -0.7:
                momentos_criticos.append({
                    "tiempo": seg["tiempo"],
                    "impacto": round(diferencia, 2)
                })

            estado_prev = clasificar_semaforo(anterior)
            if estado_prev != estado:
                transiciones.append({
                    "tiempo": seg["tiempo"],
                    "de": estado_prev,
                    "a": estado
                })

        detalle.append(item)

    resumen = {
        "total_segmentos": len(detalle),
        "positivos": sum(1 for d in detalle if d["estado"] == "POSITIVO"),
        "neutros": sum(1 for d in detalle if d["estado"] == "NEUTRO"),
        "negativos": sum(1 for d in detalle if d["estado"] == "NEGATIVO"),
        "momentos_criticos": momentos_criticos,
        "transiciones": transiciones
    }

    return detalle, resumen

def calcular_metricas_silencio(segmentos, duracion_total):
    silencios = [
        {"inicio": round(s1['end'], 2), "fin": round(s2['start'], 2),
         "duracion": round(s2['start'] - s1['end'], 2)}
        for s1, s2 in zip(segmentos, segmentos[1:])
        if (s2['start'] - s1['end']) > 1.5
    ]

    total = sum(s['duracion'] for s in silencios)

    return {
        "duracion_total_audio": round(duracion_total, 2),
        "total_silencio_segundos": round(total, 2),
        "porcentaje_silencio": round((total / duracion_total) * 100, 2) if duracion_total > 0 else 0,
        "cantidad_pausas_largas": len(silencios)
    }

def procesar_auditoria(texto_json):
    prompt = f"""
        Eres un auditor BPO experto y BENEVOLENTE.

        TAREAS:
        1. Clasifica cada intervención como AGENTE o CLIENTE.
        2. Asigna un valor de sentimiento a CADA intervención (AGENTE y CLIENTE) en un rango de -1.0 a 1.0.
        3. Evalúa al AGENTE usando TODOS los indicadores proporcionados.

        INDICADORES:
        {json.dumps(matriz_normalizada)}

        REGLAS OBLIGATORIAS:
        - Debes evaluar TODOS los atributos (no dejar ninguno vacío)
        - cumplimiento SIEMPRE debe ser un número entre 0 y 1
        - NO retornar listas vacías

        REGLAS GENERALES:
        - No dejes valores null en sentimiento
        - Usa sentido lógico (ej: agente empático → positivo)
        - Cliente molesto → negativo
        - Responde SOLO JSON válido
        - Mantén coherencia en los tiempos
        - No califiques menos de 0.7 a menos que la omisión sea total.
        
        - REGLA DE APROBACIÓN: score_final >= 80 es "APROBADO", menor a 80 es "REPROBADO".

        FORMATO:
        {{
            "transcripcion_diarizada": [
                {{
                    "tiempo": "MM:SS",
                    "rol": "AGENTE/CLIENTE",
                    "texto": "...",
                    "sentimiento": float
                }}
            ],
            "auditoria_agente": [
                {{
                    "atributo": "string",
                    "peso_atributo": float,
                    "cumplimiento": float,
                    "observacion": "string"
                }}
            ],
            "analisis_resultado": "string",
            "resultado_final": "APROBADO/REPROBADO",
            "observaciones_generales": "string"
        }}

        Transcripción:
        {texto_json}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responde SOLO JSON válido sin texto extra."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        content = resp.choices[0].message.content
        data = json.loads(content)

    except Exception as e:
        print(f"⚠️ Error IA: {e}")
        return None

    # ✅ VALIDACIÓN ESTRUCTURA
    if not all(k in data for k in [
        "transcripcion_diarizada",
        "auditoria_agente",
        "resultado_final"
    ]):
        print("⚠️ Respuesta incompleta o mal estructurada")
        print("👉 Contenido recibido:", data)
        return None

    # ✅ 🔥 FIX CRÍTICO → SI VIENE VACÍA LA AUDITORÍA
    if not data.get("auditoria_agente") or len(data["auditoria_agente"]) == 0:
        print("⚠️ Auditoría vacía, generando valores default")

        data["auditoria_agente"] = [
            {
                "atributo": i["atributo"],
                "peso_atributo": i["peso_atributo"],
                "cumplimiento": 0.8,
                "observacion": "Valor por defecto debido a respuesta incompleta del modelo"
            }
            for i in matriz_normalizada
        ]

    # ✅ CÁLCULO DE SCORE
    suma = 0
    for item in data["auditoria_agente"]:
        cumplimiento = safe_float(item.get("cumplimiento"))
        peso = safe_float(item.get("peso_atributo"))

        item["score_obtenido"] = round(cumplimiento * peso, 2)
        suma += item["score_obtenido"]

    data["score_final"] = round(suma, 2)

    return data

def generar_grafica_comparativa_y_analisis(archivo, segmentos, resultado_global):
    df = pd.DataFrame(segmentos)

    # ✅ Limpieza
    df["sentimiento"] = df["sentimiento"].apply(lambda x: safe_float(x))

    df_pivot = df.pivot_table(
        index="tiempo",
        columns="rol",
        values="sentimiento"
    ).ffill().fillna(0)

    cliente = df_pivot.get("CLIENTE", pd.Series(0, index=df_pivot.index))
    agente = df_pivot.get("AGENTE", pd.Series(0, index=df_pivot.index))

    # ✅ GRÁFICA
    plt.figure(figsize=(12, 6))
    plt.plot(df_pivot.index, cliente, label="Cliente", marker="o")
    plt.plot(df_pivot.index, agente, label="Agente", linestyle="--")
    plt.axhline(0, color='red', linestyle=':')
    plt.legend()
    plt.title(f"Dinámica emocional: {archivo}")
    plt.savefig(os.path.join(RUTA_DASHBOARD, f"{archivo}.png"))
    plt.close()

    # ✅ DETECTAR TIEMPO CRÍTICO (mínimo del cliente)
    tiempo_critico = cliente.idxmin() if len(cliente) > 0 else "00:00"
    min_sentimiento = float(cliente.min()) if len(cliente) > 0 else 0

    # ✅ RESUMEN PARA IA
    resumen = {
        "cliente_promedio": float(cliente.mean()),
        "agente_promedio": float(agente.mean()),
        "cliente_min": min_sentimiento,
        "cliente_max": float(cliente.max()),
        "agente_min": float(agente.min()),
        "agente_max": float(agente.max()),
        "tiempo_critico": tiempo_critico
    }

    prompt = f"""
    Analiza esta llamada:

    {json.dumps(resumen)}

    REGLAS:
    - Determina si la llamada fue APROBADA o REPROBADA
    - Explica qué pasó en la llamada
    - Evalúa comportamiento del agente
    - Usa el tiempo crítico como referencia

    Devuelve JSON:
    {{
        "analisis": "...",
        "observaciones": "...",
        "conclusionIA": "..."
    }}
    """

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Responde SOLO JSON válido"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        data_ia = json.loads(resp.choices[0].message.content)

    except Exception as e:
        print(f"⚠️ Error análisis gráfica: {e}")
        data_ia = {
            "analisis": "No disponible",
            "observaciones": "No disponible",
            "conclusionIA": "No disponible"
        }

    # ✅ ✅ JSON FINAL COMPLETO (LO QUE NECESITAS)
    analisis_final = {
        "resultado": resultado_global,  # ← viene del score QA
        "tiempo": tiempo_critico,
        "analisis": data_ia.get("analisis", ""),
        "observaciones": data_ia.get("observaciones", ""),
        "conclusionIA": data_ia.get("conclusionIA", "")
    }

    # ✅ GUARDAR EN CARPETA analisis_grafica
    try:
        path = os.path.join(RUTA_ANALISIS_GRAFICA, f"{archivo}_analisis.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(analisis_final, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error guardando análisis: {e}")

    return analisis_final


def generar_datos_dashboard():
    reportes = []
    lista_archivos = glob.glob(os.path.join(RUTA_REPORTES, "*.json"))

    for archivo in lista_archivos:
        with open(archivo, "r", encoding="utf-8") as f:
            r = json.load(f)

            trans_path = os.path.join(RUTA_TRANS, r["archivo"] + ".json")
            if os.path.exists(trans_path):
                with open(trans_path, "r", encoding="utf-8") as t:
                    trans = json.load(t)
                    sentimientos = [s.get("sentimiento", 0) for s in trans]

                    if sentimientos:
                        r["sentimiento_promedio"] = sum(sentimientos) / len(sentimientos)
                        r["sentimiento_max"] = max(sentimientos)
                        r["sentimiento_min"] = min(sentimientos)
                        r["variabilidad"] = float(np.std(sentimientos))

            reportes.append(r)

    with open("datos_dashboard.json", "w", encoding="utf-8") as f:
        json.dump(reportes, f, indent=4, ensure_ascii=False)

def procesar_llamadas():
    if not os.path.exists("audios"):
        print("❌ Carpeta audios no existe")
        return

    for archivo in os.listdir("audios"):
        if not archivo.lower().endswith(('.wav', '.mp3', '.m4a')):
            continue

        try:
            print(f"🎙️ {archivo}")

            path_reporte = os.path.join(RUTA_REPORTES, f"{archivo}_reporte.json")
            if os.path.exists(path_reporte):
                print(f"⏩ Ya procesado")
                continue

            res = whisper_model.transcribe(os.path.join("audios", archivo), language="es")

            if not res.get("segments"):
                continue

            duracion = res["segments"][-1]["end"]

            lista_raw = [
                {
                    "tiempo": f"{int(s['start']//60):02}:{int(s['start']%60):02}",
                    "texto": s["text"]
                }
                for s in res["segments"]
            ]

            resultado = procesar_auditoria(json.dumps(lista_raw))
            if not resultado:
                continue

            trans = resultado["transcripcion_diarizada"]

            sem_detalle, sem_resumen = generar_semaforo_sentimientos(trans)

            with open(os.path.join(RUTA_TRANS, f"{archivo}.json"), "w", encoding="utf-8") as f:
                json.dump(trans, f, indent=4, ensure_ascii=False)

            with open(os.path.join(RUTA_SILENCIOS, f"{archivo}_silencio.json"), "w") as f:
                json.dump(calcular_metricas_silencio(res["segments"], duracion), f, indent=4)

            analisis_ia = generar_grafica_comparativa_y_analisis(
                            archivo,
                            trans,
                            resultado["resultado_final"]
                        )

            with open(path_reporte, "w", encoding="utf-8") as f:
                json.dump({
                    "archivo": archivo,
                    "duracion": duracion,
                    "score_final": resultado["score_final"],
                    "resultado": resultado["resultado_final"],
                    "analisis": resultado["analisis_resultado"],
                    "auditoria": resultado["auditoria_agente"],
                    "observaciones": resultado["observaciones_generales"],

                    "semaforo": {
                        "detalle": sem_detalle,
                        "resumen": sem_resumen
                    },

                    "analisis_grafica": analisis_ia

                }, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"❌ Error {archivo}: {e}")

    generar_datos_dashboard()
    print("✅ Proceso finalizado")

if __name__ == "__main__":
    procesar_llamadas()
