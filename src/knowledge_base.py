"""Base de conocimiento simulada para el agente de IA (Punto 3.1).

Las métricas (precio, ventas, reseñas, entrega, segmentos) son reales del dataset Olist.
Los textos comerciales son simulados. El dataset no trae nombres de producto: el tipo de
producto se infirió leyendo las reseñas de sus compradores.
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd

RUTA_KB = Path(__file__).resolve().parents[1] / "agent" / "knowledge_base.json"

# Regla: el producto con más ingresos de cada categoría (en Muebles y Cama coincide con el más vendido)
CATEGORIAS = ["Belleza y salud", "Cama, mesa y baño", "Muebles y decoración"]

# Textos SIMULADOS por categoría: humanos, breves y sin especificaciones técnicas inventadas
TEXTOS = {
    "Belleza y salud": {
        "nombre_comercial": "Adipómetro Profesional",
        "identificado_por": "Reseñas: 'Adipômetro... vai me ajudar muito na prática clínica'",
        "descripcion": (
            "Para quien se toma en serio el bienestar: mide la grasa corporal como lo hacen "
            "nutricionistas y entrenadores. Liviano, fácil de llevar a consulta y hecho para "
            "acompañar cada evaluación de tus pacientes o de tu propio progreso."
        ),
        "beneficios_clave": ["Seguimiento real del progreso, no solo del peso", "Portátil y liviano", "Pensado para uso profesional"],
        "argumentos_venta_por_perfil": {
            "joven_digital": "Deja de adivinar: mide tu progreso en el gym y compártelo con datos reales.",
            "conservador": "Una herramienta confiable para cuidar su salud con el acompañamiento de su profesional.",
            "vip": "El instrumento que usan los profesionales: ideal para dotar su consultorio o equipo.",
        },
        "nota_para_el_agente": "Algunos clientes reportaron pedidos no entregados: confirmar el seguimiento del envío.",
    },
    "Cama, mesa y baño": {
        "nombre_comercial": "Juego de Toallas Jardín Bordado",
        "identificado_por": "Reseñas: 'Gostei muito do jogo de banho. A estampa florida, o bordado...'",
        "descripcion": (
            "Ese detalle que hace que el baño se sienta como un hotel: toallas amplias, con estampado "
            "floral y bordado que alegran cualquier rincón. Prácticas para el día a día y en varios colores "
            "para combinar con tu estilo."
        ),
        "beneficios_clave": ["Tamaño amplio para uso diario", "Estampado y bordado decorativo", "Varios colores disponibles"],
        "argumentos_venta_por_perfil": {
            "joven_digital": "Renueva tu baño en un clic: el toque de diseño que tu apartamento estaba pidiendo.",
            "conservador": "Un clásico para el hogar, bonito y práctico, que llega a tiempo a su casa.",
            "vip": "Un detalle elegante para regalar o para renovar la casa sin complicaciones.",
        },
        "nota_para_el_agente": "Varios clientes las encontraron delgadas: no prometer toallas gruesas ni 'premium'.",
    },
    "Muebles y decoración": {
        "nombre_comercial": "Perchero Organizador con Ruedas",
        "identificado_por": "Reseñas: 'Produto prático e uma ótima opção para liberar espaço no guarda-roupa'",
        "descripcion": (
            "Más espacio, menos desorden: este perchero con ruedas libera tu clóset y deja tu ropa a la "
            "vista y lista para usar. Se arma fácil, aguanta buen peso y lo mueves a donde lo necesites."
        ),
        "beneficios_clave": ["Libera espacio en el clóset", "Fácil de armar y de mover", "Resiste buen peso de ropa"],
        "argumentos_venta_por_perfil": {
            "joven_digital": "El hack de orden para tu cuarto: ropa a la vista y cero caos, en minutos.",
            "conservador": "Práctico y resistente para organizar la ropa sin hacer obras en casa.",
            "vip": "Solución de orden para vestidores, tiendas o espacios de trabajo, a buen precio.",
        },
        "nota_para_el_agente": "Hubo quejas de pedidos de varias unidades que llegaron incompletos: confirmar cantidades.",
    },
}


def elegir_productos(items: pd.DataFrame) -> dict[str, str]:
    """Categoría -> product_id con más ingresos (suma de price) en pedidos entregados."""
    ingresos = items[items["categoria_es"].isin(CATEGORIAS)].groupby(["categoria_es", "product_id"])["price"].sum()
    return {categoria: ingresos[categoria].idxmax() for categoria in CATEGORIAS}


def metricas_producto(items: pd.DataFrame, experiencia: pd.DataFrame, product_id: str) -> dict:
    """Precio, ventas, reseñas y entrega reales del producto."""
    ventas = items[items["product_id"] == product_id]
    pedidos = experiencia[experiencia["order_id"].isin(ventas["order_id"])]
    precio = ventas["price"]
    return {
        "precio_promedio_real": round(precio.mean(), 2),
        "precio_mediano": round(precio.median(), 2),
        "rango_precio_p25_p75": [round(precio.quantile(0.25), 2), round(precio.quantile(0.75), 2)],
        "flete_promedio": round(ventas["freight_value"].mean(), 2),
        "unidades_vendidas": int(len(ventas)),
        "ingresos_totales": round(precio.sum(), 2),
        "score_promedio_resenas": round(pedidos["review_score"].mean(), 2),
        "tiempo_entrega_promedio_dias": round(pedidos["dias_entrega"].mean(), 1),
        "pct_entregas_a_tiempo": round((1 - pedidos.loc[pedidos["entregado"], "tarde"].mean()) * 100, 1),
    }


def segmentos_objetivo(items: pd.DataFrame, experiencia: pd.DataFrame, segmentados: pd.DataFrame, categoria: str) -> list[dict]:
    """Segmentos del 2.1 sobrerrepresentados entre los compradores de la categoría (índice > 1)."""
    pedidos = items.loc[items["categoria_es"] == categoria, "order_id"]
    compradores = experiencia.loc[experiencia["order_id"].isin(pedidos), "customer_unique_id"].unique()
    segmento = segmentados.set_index("customer_unique_id")["segmento"]

    en_categoria = segmento.reindex(compradores).dropna().value_counts(normalize=True)
    en_base = segmento.value_counts(normalize=True)
    tabla = pd.DataFrame({"pct_compradores": en_categoria * 100, "indice": en_categoria / en_base}).dropna()
    tabla = tabla[tabla["indice"] > 1].sort_values("indice", ascending=False).round(2)
    return [{"segmento": s, **fila} for s, fila in tabla.to_dict("index").items()]


def construir_base(items: pd.DataFrame, experiencia: pd.DataFrame, segmentados: pd.DataFrame) -> dict:
    productos = []
    for categoria, product_id in elegir_productos(items).items():
        fila = items[items["product_id"] == product_id].iloc[0]
        textos = TEXTOS[categoria]
        productos.append({
            "id": product_id,
            "nombre_comercial": textos["nombre_comercial"] + " (simulado)",
            "identificado_por": textos["identificado_por"],
            "categoria": {"es": categoria, "en": fila["categoria_en"], "pt": fila["categoria_pt"]},
            "descripcion": textos["descripcion"],
            "beneficios_clave": textos["beneficios_clave"],
            **metricas_producto(items, experiencia, product_id),
            "segmentos_objetivo": segmentos_objetivo(items, experiencia, segmentados, categoria),
            "argumentos_venta_por_perfil": textos["argumentos_venta_por_perfil"],
            "nota_para_el_agente": textos["nota_para_el_agente"],
        })
    return {
        "moneda": "BRL",
        "fuente": "Dataset Olist (Kaggle), pedidos entregados 2016-2018",
        "fecha_generacion": date.today().isoformat(),
        "criterio_seleccion": "Producto con más ingresos de Belleza y salud, Cama, mesa y baño y Muebles y decoración (categorías top del 1.1)",
        "nota": "Nombres, descripciones y argumentos simulados (el tipo de producto se infirió de las reseñas); precios y métricas reales del dataset Olist.",
        "productos": productos,
    }


def guardar_base(base: dict, ruta: Path = RUTA_KB) -> Path:
    ruta.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta
