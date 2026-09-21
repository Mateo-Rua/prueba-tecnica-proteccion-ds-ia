"""Construye los system prompts del agente con datos reales del cliente (Punto 3.2)."""

import json
from pathlib import Path

import pandas as pd

RUTA_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_PROMPTS = RUTA_PROYECTO / "agent" / "prompts"
RUTA_KB = RUTA_PROYECTO / "agent" / "knowledge_base.json"
RUTA_CLIENTES = RUTA_PROYECTO / "data" / "processed" / "clientes_segmentados.parquet"

ESCENARIOS = ["joven_digital", "mayor_mala_experiencia", "vip"]
PLACEHOLDERS = ["[EDAD]", "[GÉNERO]", "[PERFIL_DE_CLIENTE]", "[HISTORIAL_COMPRAS]", "[BASE_CONOCIMIENTO]"]


def base_conocimiento_compacta() -> str:
    """La base del 3.1 en JSON compacto (menos tokens para el LLM)."""
    base = json.loads(RUTA_KB.read_text(encoding="utf-8"))
    return json.dumps(base["productos"], ensure_ascii=False, separators=(",", ":"))


def construir_prompt(escenario: str, customer_unique_id: str, edad: int, genero: str, clientes: pd.DataFrame | None = None) -> str:
    """Carga la plantilla del escenario y reemplaza los 5 placeholders con datos reales."""
    clientes = pd.read_parquet(RUTA_CLIENTES) if clientes is None else clientes
    cliente = clientes.set_index("customer_unique_id").loc[customer_unique_id]
    valores = {
        "[EDAD]": f"{edad} años (dato del CRM)",
        "[GÉNERO]": f"{genero} (dato del CRM)",
        "[PERFIL_DE_CLIENTE]": f"{cliente['segmento']} ({cliente['subsegmento']})",
        "[HISTORIAL_COMPRAS]": cliente["historial_compras"],
        "[BASE_CONOCIMIENTO]": base_conocimiento_compacta(),
    }
    prompt = (RUTA_PROMPTS / f"{escenario}.md").read_text(encoding="utf-8")
    for marcador, valor in valores.items():
        prompt = prompt.replace(marcador, valor)
    return prompt


def elegir_clientes(clientes: pd.DataFrame, semilla: int = 42) -> dict[str, str]:
    """Un cliente real por escenario, que encaje con su perfil."""
    joven = clientes[
        (clientes["segmento"] == "Fieles") & (clientes["metodo_pago"] == "credit_card")
        & ~clientes["tuvo_mala_experiencia"] & (clientes["frecuencia"] >= 3)
    ]
    mayor = clientes[
        clientes["segmento"].isin(["En riesgo de abandono", "Perdidos / Inactivos"])
        & (clientes["motivo_principal"] == "entrega / retraso")
    ]
    vip = clientes[(clientes["segmento"] == "VIP / Alto valor") & (clientes["subsegmento"] == "VIP activo")]
    vip = vip[vip["gasto_total"] >= vip["gasto_total"].quantile(0.9)]
    return {
        "joven_digital": joven.sample(1, random_state=semilla)["customer_unique_id"].iloc[0],
        "mayor_mala_experiencia": mayor.sample(1, random_state=semilla)["customer_unique_id"].iloc[0],
        "vip": vip.sample(1, random_state=semilla)["customer_unique_id"].iloc[0],
    }
