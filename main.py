from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
from io import BytesIO
import uvicorn
import re

app = FastAPI()

# Habilitar CORS para permitir acceso desde GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def limpiar_numero(valor):
    """Convierte texto con coma a float."""
    try:
        return float(valor.replace(",", "."))
    except:
        return None

# 🔎 Detecta filas del PDF TZone con REGEX
PATRON = re.compile(
    r"(\d{2}/\d{2}/\d{4}),?\s+(\d{2}:\d{2}:\d{2})\s+([\d.,]+)\s+([\d.,]+)"
)

@app.post("/procesar")
async def procesar_pdf(file: UploadFile = File(...)):
    try:
        # Leemos el contenido del PDF
        contenido = await file.read()
        archivo_memoria = BytesIO(contenido)

        datos = []

        # Abrir PDF desde BytesIO (compatible Render)
        with pdfplumber.open(archivo_memoria) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()

                if not texto:
                    continue

                # Procesar línea por línea
                for linea in texto.split("\n"):
                    coincide = PATRON.search(linea)
                    if coincide:
                        fecha, hora, temp, rh = coincide.groups()

                        temp = limpiar_numero(temp)
                        rh = limpiar_numero(rh)

                        if temp is None or rh is None:
                            continue

                        datos.append({
                            "Fecha": fecha,
                            "Hora": hora,
                            "Temp_C": temp,
                            "RH": rh
                        })

        if not datos:
            return {"ok": False, "error": "No se encontraron datos válidos en el PDF."}

        return {"ok": True, "datos": datos}

    except Exception as e:
        return {"ok": False, "error": str(e)}

# Para correr localmente
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
