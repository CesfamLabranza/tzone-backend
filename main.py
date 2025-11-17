from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import uvicorn

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
    """Convierte texto a número, manejando comas."""
    try:
        return float(valor.replace(",", "."))
    except:
        return None

@app.post("/procesar")
async def procesar_pdf(file: UploadFile = File(...)):
    try:
        contenido = await file.read()

        datos = []

        with pdfplumber.open(bytes(contenido)) as pdf:
            for pagina in pdf.pages:
                tablas = pagina.extract_tables()

                for tabla in tablas:
                    for fila in tabla:
                        # Saltar filas inválidas o encabezados
                        if not fila or "Fecha" in fila[0]:
                            continue

                        try:
                            fecha = fila[0].strip()
                            hora = fila[1].strip()
                            temp = limpiar_numero(fila[2])
                            hum = limpiar_numero(fila[3])

                            # Validar datos correctos
                            if temp is None or hum is None:
                                continue

                            datos.append({
                                "Fecha": fecha,
                                "Hora": hora,
                                "Temp_C": temp,
                                "RH": hum
                            })
                        except:
                            continue

        if not datos:
            return {"ok": False, "error": "No se encontraron datos válidos en el PDF."}

        return {"ok": True, "datos": datos}

    except Exception as e:
        return {"ok": False, "error": str(e)}


# Para correr localmente (Render NO usa esto)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
