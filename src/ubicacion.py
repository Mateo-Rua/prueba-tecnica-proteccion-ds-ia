"""Ubicación de la tienda física insignia (Punto 2.3).

La venta se ubica por la dirección del CLIENTE (demanda). La unidad geográfica más fina
es el prefijo postal de 5 dígitos; sus coordenadas son la mediana de `geolocation`.
"""

import unicodedata

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

LIMITES_BRASIL = {"lat": (-34.0, 5.5), "lng": (-74.0, -34.0)}
RADIO_CIUDAD_KM = 40  # un prefijo a más de 40 km del centro de la ciudad es una coordenada errónea
PESOS = {"ingresos": 0.50, "clientes": 0.20, "ticket": 0.15, "pct_top": 0.15}
SEMILLA = 42


def normalizar(texto: pd.Series) -> pd.Series:
    """Minúsculas, sin tildes y sin espacios sobrantes ('São Paulo' -> 'sao paulo')."""
    sin_tildes = texto.map(lambda t: unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode())
    return sin_tildes.str.lower().str.strip()


def geolocalizacion_por_prefijo(geo: pd.DataFrame) -> pd.DataFrame:
    """Una fila por prefijo postal: mediana de lat/lng, descartando coordenadas fuera de Brasil."""
    dentro = geo[
        geo["geolocation_lat"].between(*LIMITES_BRASIL["lat"])
        & geo["geolocation_lng"].between(*LIMITES_BRASIL["lng"])
    ]
    return (
        dentro.groupby("geolocation_zip_code_prefix")[["geolocation_lat", "geolocation_lng"]]
        .median()
        .rename(columns={"geolocation_lat": "lat", "geolocation_lng": "lng"})
    )


def categorias_top(items: pd.DataFrame, n: int = 5) -> list[str]:
    """'Mejores productos' = unión del top 5 por volumen y por ingresos del punto 1.1."""
    validos = items[items["categoria_pt"] != "sin_categoria"]
    por_volumen = validos["categoria_es"].value_counts().head(n).index
    por_ingresos = validos.groupby("categoria_es")["price"].sum().nlargest(n).index
    return sorted(set(por_volumen) | set(por_ingresos))


def ventas_por_pedido(items: pd.DataFrame, experiencia: pd.DataFrame, clientes: pd.DataFrame, top: list[str]) -> pd.DataFrame:
    """Un pedido por fila: ingresos (price), flete, ingresos en top categorías, cliente y prefijo."""
    items = items.assign(ingreso_top=items["price"].where(items["categoria_es"].isin(top), 0))
    pedidos = items.groupby("order_id").agg(
        customer_id=("customer_id", "first"),
        ingresos=("price", "sum"),
        flete=("freight_value", "sum"),
        ingreso_top=("ingreso_top", "sum"),
    ).reset_index()

    columnas = ["order_id", "customer_unique_id", "customer_state", "customer_city", "dias_entrega", "tarde", "review_score"]
    pedidos = pedidos.merge(experiencia[columnas], on="order_id", how="left")
    pedidos = pedidos.merge(clientes[["customer_id", "customer_zip_code_prefix"]], on="customer_id", how="left")
    pedidos["ciudad"] = normalizar(pedidos["customer_city"])
    return pedidos


def ranking_ciudades(pedidos: pd.DataFrame) -> pd.DataFrame:
    ranking = pedidos.groupby(["ciudad", "customer_state"]).agg(
        ingresos=("ingresos", "sum"),
        pedidos=("order_id", "size"),
        clientes=("customer_unique_id", "nunique"),
    ).reset_index()
    ranking["ticket"] = ranking["ingresos"] / ranking["pedidos"]
    ranking["pct_ingresos"] = ranking["ingresos"] / ranking["ingresos"].sum() * 100
    return ranking.sort_values("ingresos", ascending=False).reset_index(drop=True)


def zonas_por_prefijo(pedidos: pd.DataFrame, geo_prefijo: pd.DataFrame, ciudad: str, estado: str) -> pd.DataFrame:
    """Métricas por prefijo postal de la ciudad, con sus coordenadas (NaN si no hay)."""
    en_ciudad = pedidos[(pedidos["ciudad"] == ciudad) & (pedidos["customer_state"] == estado)]
    prefijos = en_ciudad.groupby("customer_zip_code_prefix").agg(
        ingresos=("ingresos", "sum"),
        pedidos=("order_id", "size"),
        clientes=("customer_unique_id", "nunique"),
        ingreso_top=("ingreso_top", "sum"),
        flete=("flete", "mean"),
        dias_entrega=("dias_entrega", "mean"),
        pct_tarde=("tarde", "mean"),
        score=("review_score", "mean"),
    )
    return prefijos.join(geo_prefijo, how="left")


def distancia_km(lat, lng, lat0: float, lng0: float):
    """Distancia aproximada en km (proyección equirectangular, precisa a escala de ciudad)."""
    dx = (lng - lng0) * 111.32 * np.cos(np.radians(lat0))
    dy = (lat - lat0) * 110.57
    return np.sqrt(dx**2 + dy**2)


def filtrar_coordenadas(prefijos: pd.DataFrame) -> pd.DataFrame:
    """Quita prefijos sin coordenadas o a más de RADIO_CIUDAD_KM del centro de la ciudad."""
    con_coordenadas = prefijos.dropna(subset=["lat", "lng"])
    lat0, lng0 = con_coordenadas["lat"].median(), con_coordenadas["lng"].median()
    cerca = distancia_km(con_coordenadas["lat"], con_coordenadas["lng"], lat0, lng0) <= RADIO_CIUDAD_KM
    return con_coordenadas[cerca].copy()


def coordenadas_km(prefijos: pd.DataFrame) -> np.ndarray:
    """Lat/lng a km para que el clustering mida distancias reales (1° de lng < 1° de lat)."""
    lat0 = prefijos["lat"].median()
    return np.column_stack([prefijos["lng"] * 111.32 * np.cos(np.radians(lat0)), prefijos["lat"] * 110.57])


def evaluar_k(prefijos: pd.DataFrame, ks=range(4, 11)) -> pd.DataFrame:
    """Silhouette por k del K-Means ponderado por ingresos."""
    x = coordenadas_km(prefijos)
    filas = []
    for k in ks:
        etiquetas = KMeans(k, random_state=SEMILLA, n_init=10).fit_predict(x, sample_weight=prefijos["ingresos"])
        filas.append({"k": k, "silhouette": silhouette_score(x, etiquetas)})
    return pd.DataFrame(filas)


def agrupar_zonas(prefijos: pd.DataFrame, k: int) -> pd.DataFrame:
    """K-Means sobre lat/lng ponderado por ingresos: los centros caen donde se concentra la venta."""
    prefijos = prefijos.copy()
    modelo = KMeans(k, random_state=SEMILLA, n_init=10).fit(coordenadas_km(prefijos), sample_weight=prefijos["ingresos"])
    prefijos["zona"] = modelo.labels_ + 1
    return prefijos


def resumen_zonas(prefijos: pd.DataFrame, pesos: dict = PESOS) -> pd.DataFrame:
    """Métricas por zona, centroide ponderado por ingresos y puntaje de ubicación."""
    promedio = lambda col: (prefijos[col] * prefijos["pedidos"]).groupby(prefijos["zona"]).sum() / prefijos.groupby("zona")["pedidos"].sum()
    zonas = prefijos.groupby("zona").agg(
        prefijos=("ingresos", "size"),
        ingresos=("ingresos", "sum"),
        pedidos=("pedidos", "sum"),
        clientes=("clientes", "sum"),
        ingreso_top=("ingreso_top", "sum"),
    )
    zonas["lat"] = (prefijos["lat"] * prefijos["ingresos"]).groupby(prefijos["zona"]).sum() / zonas["ingresos"]
    zonas["lng"] = (prefijos["lng"] * prefijos["ingresos"]).groupby(prefijos["zona"]).sum() / zonas["ingresos"]
    zonas["ticket"] = zonas["ingresos"] / zonas["pedidos"]
    zonas["pct_top"] = zonas["ingreso_top"] / zonas["ingresos"] * 100
    zonas["pct_ingresos_ciudad"] = zonas["ingresos"] / zonas["ingresos"].sum() * 100
    for col in ["flete", "dias_entrega", "pct_tarde", "score"]:
        zonas[col] = promedio(col)
    zonas["pct_tarde"] *= 100
    zonas["puntaje"] = puntaje(zonas, pesos)
    return zonas.sort_values("puntaje", ascending=False).round(4)


def puntaje(zonas: pd.DataFrame, pesos: dict) -> pd.Series:
    """Suma ponderada de las métricas escaladas 0-1 (min-max) entre zonas."""
    escalar = lambda s: (s - s.min()) / (s.max() - s.min())
    return sum(peso * escalar(zonas[col]) for col, peso in pesos.items())
