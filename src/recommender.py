"""Recomendador de productos en tiempo real (Punto 2.2).

Dos capas, igual que en la arquitectura:
- Offline (`construir_artefactos`): con pandas precalcula tablas pequeñas (catálogo con
  puntaje, populares por UF, co-ocurrencia de categorías y perfil de cada cliente) y
  las guarda en un JSON comprimido.
- Online (`recomendar`): solo diccionarios de Python, sin pandas, para responder en
  milisegundos y poder desplegarse como función serverless liviana.
"""

import gzip
import json
from collections import Counter
from pathlib import Path

try:  # solo la capa offline necesita pandas; el servicio online no
    import pandas as pd
except ImportError:
    pd = None

RUTA_ARTEFACTOS = Path(__file__).resolve().parents[1] / "data" / "processed" / "recomendador.json.gz"

SIN_CATEGORIA = "sin_categoria"
MIN_VENTAS = 3  # evidencia mínima para recomendar un producto
DIAS_DISPONIBLE = 365  # "disponible" = vendido en el último año de la ventana
DIAS_TENDENCIA = 180  # populares por UF: últimos 6 meses (tendencia / temporada)
MIN_CLIENTES_PAR = 3  # soporte mínimo de un par de categorías en la co-ocurrencia
MAX_POR_CATEGORIA = 1  # diversidad: 1 producto por categoría (validado en la evaluación offline)
N_COMPLEMENTARIAS = 1  # categorías complementarias por cliente; el resto, populares de su UF
PESOS = {"ventas": 0.5, "entrega": 0.3, "resena": 0.2}


# ---------------------------------------------------------------------------
# Capa offline (batch): construye los artefactos
# ---------------------------------------------------------------------------


def catalogo_productos(items: "pd.DataFrame", experiencia: "pd.DataFrame", fecha_ref) -> "pd.DataFrame":
    """Un producto por fila con precio, ventas, reputación de entrega y puntaje."""
    datos = items.merge(experiencia[["order_id", "entregado", "tarde", "review_score"]], on="order_id", how="left")
    datos["a_tiempo"] = (~datos["tarde"]).where(datos["entregado"]).astype(float)

    prod = datos.groupby("product_id").agg(
        categoria=("categoria_es", "first"),
        categoria_pt=("categoria_pt", "first"),
        precio=("price", "mean"),
        ventas=("order_id", "size"),
        a_tiempo=("a_tiempo", "mean"),
        resena=("review_score", "mean"),
        ultima_venta=("order_purchase_timestamp", "max"),
    )
    prod = prod[
        (prod["categoria_pt"] != SIN_CATEGORIA)
        & (prod["ventas"] >= MIN_VENTAS)
        & (prod["ultima_venta"] >= fecha_ref - pd.Timedelta(days=DIAS_DISPONIBLE))
    ].copy()

    prod["a_tiempo"] = prod["a_tiempo"].fillna(prod["a_tiempo"].median())
    prod["resena"] = prod["resena"].fillna(prod["resena"].median())
    prod["puntaje"] = (
        PESOS["ventas"] * prod["ventas"].rank(pct=True)
        + PESOS["entrega"] * prod["a_tiempo"]
        + PESOS["resena"] * prod["resena"] / 5
    )
    prod["premium"] = prod["precio"] >= prod.groupby("categoria")["precio"].transform("quantile", 0.75)
    prod["confiable"] = (prod["a_tiempo"] >= 0.95) & (prod["resena"] >= 4)
    return prod.sort_values("puntaje", ascending=False)


def populares_por_uf(base: "pd.DataFrame", items: "pd.DataFrame", fecha_ref, top: int = 8) -> dict:
    """Categorías más vendidas por estado en los últimos meses (+ global como respaldo)."""
    recientes = items[items["order_purchase_timestamp"] >= fecha_ref - pd.Timedelta(days=DIAS_TENDENCIA)]
    recientes = recientes[recientes["categoria_pt"] != SIN_CATEGORIA]
    recientes = recientes.merge(base[["order_id", "customer_state"]], on="order_id", how="inner")

    conteo = recientes.groupby(["customer_state", "categoria_es"]).size().rename("n").reset_index()
    conteo = conteo.sort_values("n", ascending=False)
    populares = conteo.groupby("customer_state")["categoria_es"].apply(lambda s: list(s.head(top))).to_dict()
    populares["_global"] = list(recientes["categoria_es"].value_counts().head(top).index)
    return populares


def coocurrencia_categorias(base: "pd.DataFrame", items: "pd.DataFrame", top: int = 5) -> dict:
    """'Quien compró X también compró Y': pares de categorías compradas por el mismo cliente."""
    compras = items[items["categoria_pt"] != SIN_CATEGORIA][["order_id", "categoria_es"]]
    compras = compras.merge(base[["order_id", "customer_unique_id"]], on="order_id", how="inner")
    compras = compras.drop_duplicates(["customer_unique_id", "categoria_es"])

    multi = compras[compras.groupby("customer_unique_id")["categoria_es"].transform("size") > 1]
    pares = multi.merge(multi, on="customer_unique_id")
    pares = pares[pares["categoria_es_x"] != pares["categoria_es_y"]]

    conteo = pares.groupby(["categoria_es_x", "categoria_es_y"]).size().rename("clientes").reset_index()
    conteo = conteo[conteo["clientes"] >= MIN_CLIENTES_PAR].sort_values("clientes", ascending=False)
    return conteo.groupby("categoria_es_x")["categoria_es_y"].apply(lambda s: list(s.head(top))).to_dict()


def perfiles_clientes(clientes: "pd.DataFrame", base: "pd.DataFrame", items: "pd.DataFrame", experiencia: "pd.DataFrame") -> dict:
    """Perfil compacto por cliente: segmento (2.1), historial y dolor (1.2)."""
    compras = items[["order_id", "product_id", "categoria_es"]].merge(
        base[["order_id", "customer_unique_id"]], on="order_id", how="inner"
    )
    comprados = compras.groupby("customer_unique_id")["product_id"].agg(lambda s: sorted(set(s)))

    malos = experiencia.loc[experiencia["mala_experiencia"], ["order_id", "customer_unique_id"]]
    malos = malos.merge(items[["order_id", "categoria_es"]], on="order_id", how="inner")
    cats_malas = malos.groupby("customer_unique_id")["categoria_es"].agg(lambda s: sorted(set(s)))

    perfiles = {}
    for fila in clientes.itertuples(index=False):
        cid = fila.customer_unique_id
        perfiles[cid] = {
            "segmento": str(fila.segmento),
            "subsegmento": fila.subsegmento,
            "uf": fila.estado,
            "favorita": fila.categoria_favorita,
            "frecuencia": int(fila.frecuencia),
            "gasto": round(float(fila.gasto_total), 2),
            "recencia": int(fila.recencia),
            "score": None if pd.isna(fila.score_promedio) else round(float(fila.score_promedio), 1),
            "mala_experiencia": bool(fila.tuvo_mala_experiencia),
            "cats_malas": cats_malas.get(cid, []),
            "comprados": comprados.get(cid, []),
        }
    return perfiles


def elegir_ejemplos(clientes: "pd.DataFrame", semilla: int = 42) -> list[dict]:
    """Un cliente real por tipo de perfil para la demo."""
    conocidos = clientes[clientes["categoria_favorita"] != "Sin categoría"]
    filtros = {
        "Fieles": conocidos["segmento"] == "Fieles",
        "VIP / Alto valor": (conocidos["segmento"] == "VIP / Alto valor") & (conocidos["recencia"] <= 171),
        "Esporádicos recientes": conocidos["segmento"] == "Esporádicos recientes",
        "En riesgo de abandono": (conocidos["segmento"] == "En riesgo de abandono") & conocidos["tuvo_mala_experiencia"],
        "Perdidos / Inactivos": conocidos["segmento"] == "Perdidos / Inactivos",
    }
    return [
        {"id": conocidos[filtro].sample(1, random_state=semilla)["customer_unique_id"].iloc[0], "segmento": segmento}
        for segmento, filtro in filtros.items()
    ]


def construir_artefactos(base, items, experiencia, clientes, fecha_ref, ruta: Path | None = RUTA_ARTEFACTOS) -> dict:
    """Ejecuta toda la capa offline y guarda el resultado (si se indica ruta)."""
    catalogo = catalogo_productos(items, experiencia, fecha_ref)
    artefactos = {
        "productos": {
            pid: {
                "categoria": f.categoria,
                "precio": round(f.precio, 2),
                "puntaje": round(f.puntaje, 4),
                "premium": bool(f.premium),
                "confiable": bool(f.confiable),
                "a_tiempo": round(f.a_tiempo, 3),
                "resena": round(f.resena, 2),
                "ventas": int(f.ventas),
            }
            for pid, f in catalogo.iterrows()
        },
        "por_categoria": catalogo.groupby("categoria", sort=False).apply(lambda g: list(g.index)).to_dict(),
        "populares": populares_por_uf(base, items, fecha_ref),
        "coocurrencia": coocurrencia_categorias(base, items),
        "clientes": perfiles_clientes(clientes, base, items, experiencia),
        "ejemplos": elegir_ejemplos(clientes),
    }
    if ruta is not None:
        with gzip.open(ruta, "wt", encoding="utf-8") as archivo:
            json.dump(artefactos, archivo, ensure_ascii=False)
    return artefactos


# ---------------------------------------------------------------------------
# Capa online (tiempo real): sin pandas
# ---------------------------------------------------------------------------


def cargar_artefactos(ruta: Path = RUTA_ARTEFACTOS) -> dict:
    with gzip.open(ruta, "rt", encoding="utf-8") as archivo:
        return json.load(archivo)


def estrategia(perfil: dict | None, art: dict, uf: str) -> tuple[str, list[tuple[str, str]], str]:
    """Según el perfil: nombre de la estrategia, categorías candidatas con su motivo y filtro."""
    populares = [(c, f"Lo más vendido en {uf}") for c in art["populares"].get(uf, art["populares"]["_global"])]
    if perfil is None:
        return "Cliente nuevo: populares de su estado", populares, "ninguno"

    # Mezcla validada offline: favorita + complementarias + tendencia de su estado.
    # El segmento decide el orden y el filtro de productos.
    fav = perfil["favorita"]
    favorita = [(fav, "Su categoría favorita")]
    complementarias = [
        (c, f"Quienes compran {fav} también compran esto")
        for c in art["coocurrencia"].get(fav, [])[:N_COMPLEMENTARIAS]
    ]
    segmento = perfil["segmento"]

    if segmento == "Fieles":
        nombre, candidatas, filtro = "Fiel: afinidad con su favorita + complementarias", favorita + complementarias, "ninguno"
    elif segmento == "VIP / Alto valor":
        nombre, candidatas, filtro = "VIP: productos premium de su favorita y complementarias", favorita + complementarias, "premium"
    elif segmento == "Esporádicos recientes":
        nombre, candidatas, filtro = "Una compra: complementarias para la segunda compra", complementarias + favorita, "ninguno"
    else:
        nombre, candidatas, filtro = "Reactivación: productos con entrega confiable", favorita + complementarias, "confiable"

    if perfil["mala_experiencia"]:
        # Dolor del 1.2: no volver a ofrecer la categoría del mal episodio y exigir buena entrega
        malas = set(perfil["cats_malas"])
        candidatas = [(c, m) for c, m in candidatas if c not in malas]
        populares = [(c, m) for c, m in populares if c not in malas]
        nombre += " (evita la categoría de su mala experiencia)"
        filtro = "confiable" if filtro == "ninguno" else filtro

    unicas = {}
    for categoria, motivo in candidatas + populares:
        unicas.setdefault(categoria, motivo)  # conserva el primer motivo (el más específico)
    return nombre, list(unicas.items()), filtro


def recomendar(customer_unique_id: str, art: dict, k: int = 5, uf: str | None = None) -> dict:
    """Top-k productos: candidatos por estrategia -> ranking por puntaje -> reglas de negocio."""
    perfil = art["clientes"].get(customer_unique_id)
    uf = uf or (perfil["uf"] if perfil else "SP")
    nombre, candidatas, filtro = estrategia(perfil, art, uf)
    comprados = set(perfil["comprados"]) if perfil else set()

    elegidos, por_categoria = {}, Counter()
    # 1ª pasada con el filtro del segmento; 2ª sin filtro, solo si faltan productos
    for exigir_filtro in (True, False):
        for categoria, motivo in candidatas:
            for pid in art["por_categoria"].get(categoria, []):  # ya vienen ordenados por puntaje
                if len(elegidos) == k:
                    break
                p = art["productos"][pid]
                if pid in comprados or pid in elegidos:  # regla: nada ya comprado ni repetido
                    continue
                if por_categoria[categoria] >= MAX_POR_CATEGORIA:  # regla: diversidad
                    break
                if exigir_filtro and filtro != "ninguno" and not p[filtro]:
                    continue
                elegidos[pid] = {"product_id": pid, **p, "motivo": motivo}
                por_categoria[categoria] += 1

    return {
        "customer_unique_id": customer_unique_id,
        "cliente_conocido": perfil is not None,
        "uf": uf,
        "perfil": {c: v for c, v in (perfil or {"uf": uf}).items() if c != "comprados"},
        "estrategia": nombre,
        "recomendaciones": list(elegidos.values()),
    }


def hit_rate(art: dict, compras_prueba: dict[str, set], k: int = 5) -> dict:
    """% de clientes que compraron después alguna categoría de sus k recomendaciones.

    Se compara contra el baseline de popularidad: los k más vendidos a nivel nacional.
    """
    populares = {r["categoria"] for r in recomendar("", art, k, uf="_global")["recomendaciones"]}
    aciertos_modelo = aciertos_base = 0
    for cid, categorias in compras_prueba.items():
        recomendadas = {r["categoria"] for r in recomendar(cid, art, k)["recomendaciones"]}
        aciertos_modelo += bool(recomendadas & categorias)
        aciertos_base += bool(populares & categorias)
    n = len(compras_prueba)
    return {"clientes": n, "hit_rate_modelo": aciertos_modelo / n, "hit_rate_popularidad": aciertos_base / n}


def evaluar_corte(base, items, experiencia, clientes_dolor, fecha_ref, dias: int, k: int = 5) -> dict:
    """Split temporal: artefactos con lo anterior al corte; prueba = categorías compradas después.

    Solo entran los clientes con compras antes y después del corte (recompradores).
    """
    from src.segmentation import construir_clientes, segmentar_reglas  # solo offline

    corte = fecha_ref - pd.Timedelta(days=dias)
    base_tr = base[base["order_purchase_timestamp"] < corte]
    items_tr = items[items["order_id"].isin(base_tr["order_id"])]
    exp_tr = experiencia[experiencia["order_id"].isin(base_tr["order_id"])]

    clientes = construir_clientes(base_tr, items_tr, clientes_dolor, corte, verbose=False)
    # la mala experiencia también se limita a lo ocurrido antes del corte (sin fuga de información)
    malos = exp_tr.loc[exp_tr["mala_experiencia"], "customer_unique_id"]
    clientes["tuvo_mala_experiencia"] = clientes["customer_unique_id"].isin(malos)
    clientes = segmentar_reglas(clientes, 171, 281, verbose=False)
    art = construir_artefactos(base_tr, items_tr, exp_tr, clientes, corte, ruta=None)

    despues = items[~items["order_id"].isin(base_tr["order_id"]) & (items["categoria_pt"] != SIN_CATEGORIA)]
    despues = despues.merge(base[["order_id", "customer_unique_id"]], on="order_id", how="inner")
    despues = despues[despues["customer_unique_id"].isin(clientes["customer_unique_id"])]
    prueba = despues.groupby("customer_unique_id")["categoria_es"].agg(set).to_dict()
    return {"corte": corte.date(), **hit_rate(art, prueba, k)}
