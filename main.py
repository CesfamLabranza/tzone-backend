from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import pandas as pd
from io import BytesIO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"msg": "API funcionando"}

@app.post("/procesar")
async def procesar(file: UploadFile = File(...)):
    try:
        contenido = await file.read()
        pdf = pdfplumber.open(BytesIO(contenido))

        data = []

        for pagina in pdf.pages:
            tablas = pagina.extract_tables()
            for tabla in tablas:
                for fila in tabla:
                    if fila[0] == "Date":
                        continue

                    try:
                        fecha = fila[0]
                        hora = fila[1]
                        temp = float(fila[2])
                        rh = float(fila[3])
                        data.append({
                            "fecha": fecha,
                            "hora": hora,
                            "temp": temp,
                            "humedad": rh
                        })
                    except:
                        pass

        if not data:
            return {"ok": False, "error": "No se pudieron leer datos del PDF"}

        return {"ok": True, "registros": data}

    except Exception as e:
        return {"ok": False, "error": str(e)}
