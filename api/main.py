"""Prototipo FastAPI del recomendador en tiempo real (Punto 2.2).

Correr local:  uvicorn api.main:app --reload   ->  http://127.0.0.1:8000
"""

import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

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


# ---------------------------------------------------------------------------
# Agente de IA (Punto 3.2): chat con los system prompts personalizados + Claude en Bedrock
# ---------------------------------------------------------------------------

RUTA_ESCENARIOS = Path(__file__).resolve().parents[1] / "agent" / "prompts" / "ejemplos" / "escenarios.json"
ESCENARIOS = json.loads(RUTA_ESCENARIOS.read_text(encoding="utf-8"))
PAGINA_CHAT = (Path(__file__).parent / "static" / "chat.html").read_text(encoding="utf-8")
MODELO = os.getenv("MODELO_BEDROCK", "global.anthropic.claude-sonnet-4-6")


class Mensaje(BaseModel):
    role: str  # "user" o "assistant"
    content: str


class Conversacion(BaseModel):
    escenario: str
    mensajes: list[Mensaje]


@app.get("/chat", response_class=HTMLResponse, include_in_schema=False)
def chat_demo():
    return PAGINA_CHAT


@app.get("/api/escenarios")
def escenarios():
    """Ficha de cada cliente de ejemplo (sin el system prompt completo)."""
    return {e: {k: v for k, v in d.items() if k != "system_prompt"} for e, d in ESCENARIOS.items()}


@app.post("/api/chat")
def chat(conversacion: Conversacion):
    import boto3  # solo se necesita en el chat

    inicio = time.perf_counter()
    respuesta = boto3.client("bedrock-runtime", region_name="us-east-1").converse(
        modelId=MODELO,
        system=[{"text": ESCENARIOS[conversacion.escenario]["system_prompt"]}],
        messages=[{"role": m.role, "content": [{"text": m.content}]} for m in conversacion.mensajes[-12:]],
        inferenceConfig={"maxTokens": 600, "temperature": 0.5},
    )
    return {
        "respuesta": respuesta["output"]["message"]["content"][0]["text"],
        "latencia_ms": round((time.perf_counter() - inicio) * 1000),
    }


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
