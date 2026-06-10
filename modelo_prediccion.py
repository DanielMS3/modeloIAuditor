import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# ✅ 1. Cargar datos
with open("datos_dashboard.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# ✅ 2. Transformar
rows = []

for d in data:
    resumen = d.get("semaforo", {}).get("resumen", {})

    positivos = resumen.get("positivos", 0)
    negativos = resumen.get("negativos", 0)
    total = resumen.get("total_segmentos", 1)

    row = {
        "score": d.get("score_final", 0),
        "sentimiento": d.get("sentimiento_promedio", 0),
        "variabilidad": d.get("variabilidad", 0),
        "ratio_negativos": negativos / total if total else 0,
        "momentos_criticos": len(resumen.get("momentos_criticos", [])),
        "resultado": 1 if d["resultado"] == "APROBADO" else 0
    }

    rows.append(row)

df = pd.DataFrame(rows)

# ✅ 3. Variables
X = df.drop("resultado", axis=1)
y = df["resultado"]

# ✅ 4. Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# ✅ 5. Modelo
modelo = RandomForestClassifier(n_estimators=100)
modelo.fit(X_train, y_train)

# ✅ 6. Evaluación
pred = modelo.predict(X_test)

print("\n📊 REPORTE MODELO:\n")
print(classification_report(y_test, pred))

# ✅ 7. Importancia variables
importancias = pd.DataFrame({
    "feature": X.columns,
    "importancia": modelo.feature_importances_
})

print("\n🔥 VARIABLES CLAVE:\n")
print(importancias.sort_values(by="importancia", ascending=False))
