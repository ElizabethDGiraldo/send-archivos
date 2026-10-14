from pathlib import Path
from typing import Annotated
import os

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).parent

# En Vercel usamos /tmp ya que es la única ruta con permisos de escritura
if os.environ.get("VERCEL"):
    UPLOAD_DIR = Path("/tmp/subidas")
else:
    UPLOAD_DIR = BASE_DIR / "subidas"

UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def listar_archivos() -> list[dict[str, str]]:
    if not UPLOAD_DIR.exists():
        return []
    archivos = sorted([f for f in UPLOAD_DIR.iterdir() if f.is_file()], reverse=True)
    return [
        {"nombre": archivo.name, "tamano": f"{archivo.stat().st_size / 1024:.1f} KB"}
        for archivo in archivos
    ]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"archivos": listar_archivos()})


# Endpoint para ver la lista de archivos en formato JSON si entran a /subidas
@app.get("/subidas")
def listar_directorio():
    return listar_archivos()


# Endpoint para descargar o ver un archivo específico
@app.get("/subidas/{nombre_archivo}")
def obtener_archivo(nombre_archivo: str):
    archivo_path = UPLOAD_DIR / nombre_archivo
    if not archivo_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(archivo_path)


@app.post("/subir", response_class=HTMLResponse)
async def subir(request: Request, archivo: Annotated[UploadFile, File()]):
    if not archivo.filename:
        raise HTTPException(status_code=400, detail="No se envió ningún archivo")

    contenido = await archivo.read()
    (UPLOAD_DIR / Path(archivo.filename).name).write_bytes(contenido)

    return templates.TemplateResponse(request, "_archivos.html", {"archivos": listar_archivos()})