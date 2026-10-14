from pathlib import Path
from typing import Annotated
import os

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

# En Vercel el sistema de archivos es de solo lectura, excepto /tmp
if os.environ.get("VERCEL"):
    UPLOAD_DIR = Path("/tmp/subidas")
else:
    UPLOAD_DIR = BASE_DIR / "subidas"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Vercel limita el cuerpo de la petición a ~4.5 MB
MAX_BYTES = 4 * 1024 * 1024

app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def listar_archivos() -> list[dict[str, str]]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)  # /tmp puede estar vacío en una instancia nueva
    archivos = sorted([f for f in UPLOAD_DIR.iterdir() if f.is_file()], reverse=True)
    return [
        {"nombre": archivo.name, "tamano": f"{archivo.stat().st_size / 1024:.1f} KB"}
        for archivo in archivos
    ]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"archivos": listar_archivos()}
    )


# Lista de archivos en JSON
@app.get("/subidas")
def listar_directorio():
    return listar_archivos()


# Descargar o ver un archivo específico
@app.get("/subidas/{nombre_archivo}")
def obtener_archivo(nombre_archivo: str):
    # Path(...).name evita rutas tipo ../../etc/passwd
    archivo_path = UPLOAD_DIR / Path(nombre_archivo).name
    if not archivo_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(archivo_path)


@app.post("/subir", response_class=HTMLResponse)
async def subir(request: Request, archivo: Annotated[UploadFile, File()]):
    nombre = Path(archivo.filename or "").name
    if not nombre:
        raise HTTPException(status_code=400, detail="No se envió ningún archivo")

    contenido = await archivo.read()
    if len(contenido) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="El archivo supera los 4 MB")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / nombre).write_bytes(contenido)

    return templates.TemplateResponse(
        request, "_archivos.html", {"archivos": listar_archivos()}
    )