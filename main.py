from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io
import re

app = FastAPI()

# Permitir llamadas desde cualquier origen (GitHub Pages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Regex basado en tu PDF real
PATRON = re.compile(r"(\d{2}/\d{2}/\d{4}),\s*(\d{2}:\d{2}:\d{2})\s+([\d\.]+)\s+([\d\.]+)")


@app.post("/procesar_pdf")
async def procesar_pdf(file: UploadFile = File(...)):
    contenido = await file.read()
    datos = []

    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        for page in pdf.pages:
            texto = page.extract_text() or ""
            lineas = texto.split("\n")

            for linea in lineas:
                m = PATRON.search(linea)
                if m:
                    datos.append({
                        "fecha": m.group(1),
                        "hora": m.group(2),
                        "temp": float(m.group(3)),
                        "rh": float(m.group(4)),
                    })

    return {"datos": datos}
