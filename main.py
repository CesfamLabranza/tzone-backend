from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import re
from io import BytesIO
from datetime import datetime

app = FastAPI()

# 🔓 Permitir acceso desde cualquier origen (para GitHub Pages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REGEX PERFECTO (según tu formato exacto)
REGEX = r"(\d{2}/\d{2}/\d{4}),\s+(\d{2}:\d{2}:\d{2})\s+(\d+\.\d+)\s+(\d+\.\d+)"


@app.post("/procesar_pdf/")
async def procesar_pdf(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        pdf_buffer = BytesIO(file_bytes)

        datos = []

        # 📄 Leer PDF página por página
        with pdfplumber.open(pdf_buffer) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                if not text:
                    continue

                # Buscar todas las coincidencias en la página
                matches = re.findall(REGEX, text)

                for fecha, hora, temp, hum in matches:
                    datos.append({
                        "fecha": fecha,
                        "hora": hora,
                        "temp": float(temp),
                        "hum": float(hum),
                        "timestamp": datetime.strptime(f"{fecha} {hora}", "%d/%m/%Y %H:%M:%S")
                    })

        if len(datos) == 0:
            return {"error": "No se encontraron datos en el PDF"}

        # -------------------------------
        # 📊 Cálculo de máximos y mínimos
        # -------------------------------
        max_temp = max(datos, key=lambda x: x["temp"])
        min_temp = min(datos, key=lambda x: x["temp"])

        resumen_general = {
            "temp_max": max_temp["temp"],
            "fecha_max": max_temp["fecha"],
            "hora_max": max_temp["hora"],

            "temp_min": min_temp["temp"],
            "fecha_min": min_temp["fecha"],
            "hora_min": min_temp["hora"],
        }

        # Resumen por día
        resumen_dias = {}
        for d in datos:
            dia = d["fecha"]

            if dia not in resumen_dias:
                resumen_dias[dia] = {
                    "max": d,
                    "min": d
                }

            if d["temp"] > resumen_dias[dia]["max"]["temp"]:
                resumen_dias[dia]["max"] = d

            if d["temp"] < resumen_dias[dia]["min"]["temp"]:
                resumen_dias[dia]["min"] = d

        resumen_dias_final = []
        for dia, r in resumen_dias.items():
            resumen_dias_final.append({
                "fecha": dia,
                "temp_max": r["max"]["temp"],
                "hora_max": r["max"]["hora"],
                "temp_min": r["min"]["temp"],
                "hora_min": r["min"]["hora"]
            })

        # -------------------------------
        # 📤 Respuesta final al frontend
        # -------------------------------
        return {
            "resumen_general": resumen_general,
            "resumen_dias": resumen_dias_final,
            "datos": datos
        }

    except Exception as e:
        return {"error": str(e)}
