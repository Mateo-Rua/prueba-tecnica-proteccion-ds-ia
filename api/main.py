"""Prototipo FastAPI del recomendador en tiempo real (Punto 2.2).

Correr local:  uvicorn api.main:app --reload   ->  http://127.0.0.1:8000
"""

import os
import time
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from src.recommender import RUTA_ARTEFACTOS, cargar_artefactos, recomendar

# Artefactos cargados UNA vez al iniciar (no por request): el request solo consulta diccionarios
ARTEFACTOS = cargar_artefactos(Path(os.getenv("RUTA_ARTEFACTOS", RUTA_ARTEFACTOS)))
PAGINA_DEMO = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")

app = FastAPI(title="Recomendador en tiempo real – Olist", version="1.0")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def demo():
    return PAGINA_DEMO


@app.get("/health")
def health():
    return {
        "estado": "ok",
        "clientes": len(ARTEFACTOS["clientes"]),
        "productos": len(ARTEFACTOS["productos"]),
    }


@app.get("/ejemplos")
def ejemplos():
    """Un cliente real por segmento y la lista de estados, para la página de demo."""
    estados = sorted(uf for uf in ARTEFACTOS["populares"] if uf != "_global")
    return {"clientes": ARTEFACTOS["ejemplos"], "estados": estados}


@app.get("/recomendar/{customer_unique_id}")
def recomendar_productos(
    customer_unique_id: str,
    k: int = Query(5, ge=1, le=10),
    uf: str | None = Query(None, description="Estado del visitante (solo para clientes nuevos)"),
):
    inicio = time.perf_counter()
    respuesta = recomendar(customer_unique_id, ARTEFACTOS, k=k, uf=uf)
    respuesta["latencia_ms"] = round((time.perf_counter() - inicio) * 1000, 3)
    return respuesta
