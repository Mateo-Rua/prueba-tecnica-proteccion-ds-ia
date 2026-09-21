"""Segmentación de clientes (Punto 2.1).

Dos enfoques sobre la misma tabla RFM a nivel `customer_unique_id`:
- `segmentar_reglas`: reglas de negocio interpretables (enfoque A).
- `segmentar_kmeans`: clustering no supervisado (enfoque B).

El reto del dataset es que el 97% de los clientes compró una sola vez, así que la
Frecuencia casi no discrimina: los umbrales de Recencia y Monetario se calculan de
los datos (percentiles) en lugar de fijarse a dedo.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

# Estados excluidos: no son venta ni historial de compra utilizable para marketing.
ESTADOS_EXCLUIDOS = ["canceled", "unavailable"]

# Un mes con menos del 10% del promedio mensual se considera incompleto (corte del dataset).
UMBRAL_MES_INCOMPLETO = 0.10

# Percentiles que definen los umbrales (se calculan sobre los datos, no se fijan a dedo).
PERCENTIL_RIESGO = 0.75  # días entre compras de los recompradores -> umbral de riesgo
PERCENTIL_PERDIDO = 0.90  # días entre compras -> umbral de cliente perdido
PERCENTIL_VIP = 0.90  # gasto total -> alto valor

SEMILLA = 42

# Orden de prioridad de las reglas (enfoque A); los segmentos son mutuamente excluyentes.
ORDEN_SEGMENTOS = [
    "Fieles",
    "VIP / Alto valor",
    "Esporádicos recientes",
    "En riesgo de abandono",
    "Perdidos / Inactivos",
]

ACCIONES_MARKETING = {
    "Fieles": "Programa de fidelización y cross-sell: son los únicos con hábito de recompra.",
    "VIP / Alto valor": "Atención preferente y recompra asistida; reactivar al VIP dormido antes que captar uno nuevo.",
    "Esporádicos recientes": "Segunda compra en caliente: cupón con vencimiento en las semanas siguientes.",
    "En riesgo de abandono": "Reactivación con oferta y, si tuvo mala experiencia, resolución del PQR antes de vender.",
    "Perdidos / Inactivos": "Campaña masiva de bajo costo (email/remarketing); no invertir en contacto uno a uno.",
}


def recortar_ventana(
    pedidos: pd.DataFrame,
    umbral: float = UMBRAL_MES_INCOMPLETO,
    verbose: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """Recorta los meses incompletos del final de la serie y fija la fecha de referencia.

    El dataset se corta a mitad de mes, así que el último mes tiene un puñado de
    pedidos. Si no se recorta, la Recencia de todos los clientes queda medida contra
    una fecha que no representa actividad real del negocio.
    """
    serie = pedidos.groupby(pedidos["order_purchase_timestamp"].dt.to_period("M")).size()
    minimo = serie.mean() * umbral

    meses_recortados = []
    for mes in reversed(serie.index):  # solo la cola de la serie
        if serie[mes] < minimo:
            meses_recortados.append(str(mes))
        else:
            break

    corte = None
    if meses_recortados:
        corte = min(pd.Period(m) for m in meses_recortados).to_timestamp()
        pedidos = pedidos[pedidos["order_purchase_timestamp"] < corte]

    fecha_referencia = pedidos["order_purchase_timestamp"].max().normalize() + pd.Timedelta(days=1)

    info = {
        "meses_recortados": meses_recortados,
        "pedidos_minimos_por_mes": round(minimo, 1),
        "fecha_corte": corte,
        "ultima_compra": pedidos["order_purchase_timestamp"].max(),
        "fecha_referencia": fecha_referencia,
        "pedidos_en_ventana": len(pedidos),
    }

    if verbose:
        print(f"Meses incompletos recortados : {meses_recortados or 'ninguno'} (< {minimo:,.0f} pedidos)")
        print(f"Pedidos en la ventana        : {len(pedidos):,}")
        print(f"Última compra                : {info['ultima_compra']}")
        print(f"Fecha de referencia          : {fecha_referencia.date()}")

    return pedidos, info


def construir_base_pedidos(dfs: dict[str, pd.DataFrame], verbose: bool = True) -> tuple[pd.DataFrame, dict]:
    """Un pedido por fila, con cliente real, monto pagado, medio de pago y UF.

    - Se excluyen `canceled` y `unavailable`: no son venta.
    - El monto sale de `order_payments` agregado POR PEDIDO (incluye flete); nunca se
      une pagos con items, porque tienen granularidad distinta y duplicaría montos.
    """
    pedidos = dfs["pedidos"]
    validos = pedidos[~pedidos["order_status"].isin(ESTADOS_EXCLUIDOS)].copy()
    validos, info = recortar_ventana(validos, verbose=verbose)

    filas = len(validos)
    validos = validos.merge(
        dfs["clientes"][["customer_id", "customer_unique_id", "customer_state", "customer_city"]],
        on="customer_id",
        how="left",
    )

    pagos = dfs["pagos"]
    por_pedido = pagos.groupby("order_id").agg(
        monto=("payment_value", "sum"),
        cuotas=("payment_installments", "max"),
    )
    # Medio de pago principal = el del pago de mayor valor del pedido.
    principal = (
        pagos.sort_values("payment_value", ascending=False)
        .drop_duplicates("order_id")
        .set_index("order_id")["payment_type"]
    )

    validos = validos.join(por_pedido, on="order_id")
    validos["metodo_pago"] = validos["order_id"].map(principal)

    # Respaldo para pedidos sin registro de pago: valor de los ítems (precio + flete).
    sin_pago = validos["monto"].isna().sum()
    if sin_pago:
        items = dfs["items_pedido"]
        respaldo = (items["price"] + items["freight_value"]).groupby(items["order_id"]).sum()
        validos["monto"] = validos["monto"].fillna(validos["order_id"].map(respaldo))

    validos["dia_compra"] = validos["order_purchase_timestamp"].dt.normalize()
    info["pedidos_sin_pago"] = int(sin_pago)

    if verbose:
        print(f"Merge con clientes conserva filas : {filas == len(validos)}")
        print(f"Nulos en customer_unique_id       : {validos['customer_unique_id'].isna().sum()}")
        print(f"Pedidos sin registro de pago      : {sin_pago} (monto tomado de los ítems)")
        print(f"Clientes reales en la ventana     : {validos['customer_unique_id'].nunique():,}")

    return validos, info


def umbrales_recencia(base: pd.DataFrame, verbose: bool = True) -> dict:
    """Umbral de riesgo y de abandono a partir de los días entre compras reales.

    Se miden los intervalos de los recompradores: si 3 de cada 4 recompras ocurren
    dentro de X días, un cliente que lleva más de X días sin volver ya salió del
    ciclo normal. Los intervalos de 0 días (un mismo carrito partido en varios
    pedidos el mismo día) se excluyen: no son recompra, son la misma compra.
    """
    base = base.sort_values(["customer_unique_id", "order_purchase_timestamp"])
    dias = base.groupby("customer_unique_id")["order_purchase_timestamp"].diff().dt.days
    intervalos = dias.dropna()
    reales = intervalos[intervalos > 0]

    umbrales = {
        "intervalos_totales": int(len(intervalos)),
        "intervalos_mismo_dia": int((intervalos == 0).sum()),
        "intervalos_reales": int(len(reales)),
        "mediana_dias": float(reales.median()),
        "umbral_riesgo": int(reales.quantile(PERCENTIL_RIESGO)),
        "umbral_perdido": int(reales.quantile(PERCENTIL_PERDIDO)),
        "serie_intervalos": reales,
    }

    if verbose:
        pct = umbrales["intervalos_mismo_dia"] / umbrales["intervalos_totales"] * 100
        print(f"Intervalos entre compras       : {umbrales['intervalos_totales']:,}")
        print(f"De los cuales el mismo día     : {umbrales['intervalos_mismo_dia']:,} ({pct:.1f}%) -> se excluyen")
        print(f"Mediana de días entre compras  : {umbrales['mediana_dias']:.0f}")
        print(f"Umbral de riesgo (p{PERCENTIL_RIESGO*100:.0f})       : {umbrales['umbral_riesgo']} días")
        print(f"Umbral de perdido (p{PERCENTIL_PERDIDO*100:.0f})      : {umbrales['umbral_perdido']} días")

    return umbrales


def construir_clientes(
    base: pd.DataFrame,
    items: pd.DataFrame,
    clientes_dolor: pd.DataFrame,
    fecha_referencia: pd.Timestamp,
    verbose: bool = True,
) -> pd.DataFrame:
    """Tabla a nivel `customer_unique_id`: RFM + comportamiento + dolor del 1.2.

    `frecuencia` cuenta pedidos distintos, pero `dias_compra` cuenta días distintos
    de compra: es la frecuencia honesta, porque el 30% de los segundos pedidos son
    del mismo día (carrito partido entre varios vendedores).
    """
    clientes = base.groupby("customer_unique_id").agg(
        frecuencia=("order_id", "nunique"),
        dias_compra=("dia_compra", "nunique"),
        gasto_total=("monto", "sum"),
        ticket_promedio=("monto", "mean"),
        primera_compra=("order_purchase_timestamp", "min"),
        ultima_compra=("order_purchase_timestamp", "max"),
        cuotas_promedio=("cuotas", "mean"),
        estado=("customer_state", "first"),
        ciudad=("customer_city", "first"),
    )
    clientes["recencia"] = (fecha_referencia - clientes["ultima_compra"]).dt.days
    clientes["antiguedad"] = (fecha_referencia - clientes["primera_compra"]).dt.days

    # Medio de pago preferido = el más usado por el cliente.
    pago = (
        base.groupby(["customer_unique_id", "metodo_pago"]).size().rename("n").reset_index()
        .sort_values(["customer_unique_id", "n"], ascending=[True, False])
        .drop_duplicates("customer_unique_id")
        .set_index("customer_unique_id")["metodo_pago"]
    )
    clientes["metodo_pago"] = pago

    # Categorías: se limita a los pedidos de la ventana para no mezclar periodos.
    items_ventana = items[items["order_id"].isin(base["order_id"])]
    items_ventana = items_ventana.merge(
        base[["order_id", "customer_unique_id"]], on="order_id", how="inner"
    )
    clientes["categorias_distintas"] = items_ventana.groupby("customer_unique_id")["categoria_es"].nunique()
    favorita = (
        items_ventana.groupby(["customer_unique_id", "categoria_es"])["price"].sum().rename("gasto")
        .reset_index()
        .sort_values(["customer_unique_id", "gasto"], ascending=[True, False])
        .drop_duplicates("customer_unique_id")
        .set_index("customer_unique_id")["categoria_es"]
    )
    clientes["categoria_favorita"] = favorita
    clientes["categorias_distintas"] = clientes["categorias_distintas"].fillna(0).astype(int)
    clientes["categoria_favorita"] = clientes["categoria_favorita"].fillna("sin_categoria")

    # Dolor del punto 1.2 (hilo conductor): score, mala experiencia y motivo.
    columnas_dolor = ["customer_unique_id", "score_promedio", "tuvo_mala_experiencia", "motivo_principal", "max_retraso_dias"]
    clientes = clientes.join(clientes_dolor.set_index("customer_unique_id")[columnas_dolor[1:]])
    clientes["tuvo_mala_experiencia"] = clientes["tuvo_mala_experiencia"].fillna(False).astype(bool)
    clientes["motivo_principal"] = clientes["motivo_principal"].fillna("sin reseña")

    if verbose:
        print(f"Clientes en la tabla        : {len(clientes):,}")
        print(f"Recencias negativas         : {(clientes['recencia'] < 0).sum()}")
        print(f"Gasto total                 : R$ {clientes['gasto_total'].sum():,.0f}")
        print(f"Clientes sin score de reseña: {clientes['score_promedio'].isna().sum():,}")

    return clientes.reset_index()


def segmentar_reglas(
    clientes: pd.DataFrame,
    umbral_riesgo: int,
    umbral_perdido: int,
    percentil_vip: float = PERCENTIL_VIP,
    verbose: bool = True,
) -> pd.DataFrame:
    """Enfoque A: segmentos por reglas, evaluadas en orden de prioridad explícito.

    1. Fieles: volvieron otro día (`dias_compra` >= 2) y siguen activos.
    2. VIP / Alto valor: gasto en el top 10%, cualquier frecuencia.
    3. Esporádicos recientes: una sola compra, dentro del ciclo normal de recompra.
    4. En riesgo de abandono: pasaron del umbral pero todavía no del de abandono.
    5. Perdidos / Inactivos: superaron el umbral de abandono.

    El orden importa: un cliente fiel de gasto medio interesa más a marketing como
    fiel que como no-VIP, y un comprador único de gasto alto interesa como VIP.
    """
    clientes = clientes.copy()
    corte_vip = clientes["gasto_total"].quantile(percentil_vip)

    es_fiel = (clientes["dias_compra"] >= 2) & (clientes["recencia"] <= umbral_riesgo)
    es_vip = clientes["gasto_total"] >= corte_vip
    es_reciente = clientes["recencia"] <= umbral_riesgo
    es_perdido = clientes["recencia"] > umbral_perdido

    clientes["segmento"] = np.select(
        [es_fiel, es_vip, es_reciente, es_perdido],
        ["Fieles", "VIP / Alto valor", "Esporádicos recientes", "Perdidos / Inactivos"],
        default="En riesgo de abandono",
    )
    clientes["segmento"] = pd.Categorical(clientes["segmento"], categories=ORDEN_SEGMENTOS, ordered=True)
    clientes["alto_valor"] = es_vip  # bandera transversal: hay fieles y perdidos de alto valor

    clientes["subsegmento"] = np.select(
        [
            (clientes["segmento"] == "VIP / Alto valor") & (clientes["recencia"] <= umbral_riesgo),
            (clientes["segmento"] == "VIP / Alto valor") & (clientes["recencia"] <= umbral_perdido),
            clientes["segmento"] == "VIP / Alto valor",
            (clientes["segmento"] == "En riesgo de abandono") & (clientes["dias_compra"] >= 2),
            (clientes["segmento"] == "En riesgo de abandono") & clientes["tuvo_mala_experiencia"],
            (clientes["segmento"] == "Perdidos / Inactivos") & clientes["tuvo_mala_experiencia"],
        ],
        [
            "VIP activo",
            "VIP en riesgo",
            "VIP dormido",
            "Recomprador inactivo",
            "Una compra con mala experiencia",
            "Perdido con mala experiencia",
        ],
        default=clientes["segmento"].astype(str),
    )

    if verbose:
        print(f"Corte de alto valor (p{percentil_vip*100:.0f} de gasto): R$ {corte_vip:,.2f}")
        print(f"Clientes sin segmento                : {clientes['segmento'].isna().sum()}")
    return clientes


VARIABLES_KMEANS = ["recencia", "frecuencia", "log_gasto", "score_promedio"]


def preparar_matriz_kmeans(clientes: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """Estandariza las variables del clustering.

    El gasto se transforma con log1p porque está muy sesgado a la derecha (unos
    pocos clientes de miles de reales dominarían la distancia euclídea). El score
    ausente se imputa con la mediana: no tener reseña no es un score bajo.
    """
    matriz = pd.DataFrame(index=clientes.index)
    matriz["recencia"] = clientes["recencia"]
    matriz["frecuencia"] = clientes["frecuencia"]
    matriz["log_gasto"] = np.log1p(clientes["gasto_total"])
    matriz["score_promedio"] = clientes["score_promedio"].fillna(clientes["score_promedio"].median())

    escalador = StandardScaler()
    return escalador.fit_transform(matriz), matriz


def evaluar_k(
    matriz: np.ndarray,
    ks: range = range(2, 9),
    muestra: int = 20_000,
    semilla: int = SEMILLA,
) -> pd.DataFrame:
    """Inercia (codo) y silhouette por cada k. El silhouette se mide sobre muestra."""
    rng = np.random.default_rng(semilla)
    indices = rng.choice(len(matriz), size=min(muestra, len(matriz)), replace=False)

    filas = []
    for k in ks:
        modelo = KMeans(n_clusters=k, random_state=semilla, n_init=10).fit(matriz)
        filas.append({
            "k": k,
            "inercia": modelo.inertia_,
            "silhouette": silhouette_score(matriz[indices], modelo.labels_[indices]),
        })
    return pd.DataFrame(filas)


def segmentar_kmeans(
    clientes: pd.DataFrame,
    matriz: np.ndarray,
    k: int,
    semilla: int = SEMILLA,
) -> pd.DataFrame:
    """Agrega la columna `cluster` con la etiqueta de K-Means."""
    clientes = clientes.copy()
    modelo = KMeans(n_clusters=k, random_state=semilla, n_init=10).fit(matriz)
    clientes["cluster"] = modelo.labels_
    return clientes


def perfil_segmentos(clientes: pd.DataFrame, columna: str = "segmento") -> pd.DataFrame:
    """Perfil de negocio por segmento: tamaño, ingresos, RFM medianos y dolor."""
    perfil = clientes.groupby(columna, observed=True).agg(
        clientes=("customer_unique_id", "size"),
        ingresos=("gasto_total", "sum"),
        recencia_mediana=("recencia", "median"),
        frecuencia_media=("frecuencia", "mean"),
        gasto_mediano=("gasto_total", "median"),
        ticket_mediano=("ticket_promedio", "median"),
        score_promedio=("score_promedio", "mean"),
        pct_mala_experiencia=("tuvo_mala_experiencia", "mean"),
    )
    perfil["pct_clientes"] = perfil["clientes"] / perfil["clientes"].sum() * 100
    perfil["pct_ingresos"] = perfil["ingresos"] / perfil["ingresos"].sum() * 100
    perfil["pct_mala_experiencia"] *= 100

    categorias = (
        clientes.groupby([columna, "categoria_favorita"], observed=True).size().rename("n").reset_index()
        .sort_values([columna, "n"], ascending=[True, False])
        .groupby(columna, observed=True)["categoria_favorita"]
        .apply(lambda s: ", ".join(s.head(3)))
        .rename("top_categorias")
    )
    perfil = perfil.join(categorias)

    columnas = [
        "clientes", "pct_clientes", "ingresos", "pct_ingresos", "recencia_mediana",
        "frecuencia_media", "gasto_mediano", "ticket_mediano", "score_promedio",
        "pct_mala_experiencia", "top_categorias",
    ]
    return perfil[columnas].round(2).reset_index()
