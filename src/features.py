"""Métricas y rankings de negocio construidos sobre los ítems enriquecidos."""

import pandas as pd

from src.data_loader import ETIQUETA_SIN_CATEGORIA


def ranking_por_categoria(items: pd.DataFrame, columna_categoria: str = "categoria_es") -> pd.DataFrame:
    """Métricas por categoría: volumen, ingresos, ticket promedio y participación.

    - Volumen = filas de items (1 fila = 1 unidad vendida).
    - Pedidos = `order_id` distintos, para no inflar categorías con pedidos de
      muchas unidades.
    - Ingresos = suma de `price` (sin flete, que no es ingreso del producto).
    """
    ranking = items.groupby(columna_categoria).agg(
        unidades=("price", "size"),
        pedidos=("order_id", "nunique"),
        ingresos=("price", "sum"),
        ingresos_con_flete=("ingreso_con_flete", "sum"),
        precio_promedio=("price", "mean"),
    )

    ranking["pct_unidades"] = ranking["unidades"] / ranking["unidades"].sum() * 100
    ranking["pct_ingresos"] = ranking["ingresos"] / ranking["ingresos"].sum() * 100
    ranking = ranking.sort_values("ingresos", ascending=False)
    ranking["pct_acum_ingresos"] = ranking["pct_ingresos"].cumsum()

    return ranking.round(2).reset_index()


def top_categorias(
    ranking: pd.DataFrame,
    metrica: str = "unidades",
    n: int = 5,
    columna_categoria: str = "categoria_es",
    excluir_sin_categoria: bool = True,
) -> pd.DataFrame:
    """Top n categorías por la métrica indicada.

    `sin_categoria` no es una categoría de negocio (son productos sin etiqueta en
    el catálogo), así que se excluye del ranking y se reporta aparte.
    """
    tabla = ranking
    if excluir_sin_categoria:
        etiquetas_excluidas = {ETIQUETA_SIN_CATEGORIA, "Sin categoría"}
        tabla = tabla[~tabla[columna_categoria].isin(etiquetas_excluidas)]
    return tabla.sort_values(metrica, ascending=False).head(n).reset_index(drop=True)


def ranking_por_producto(items: pd.DataFrame, metrica: str = "unidades", n: int = 5) -> pd.DataFrame:
    """Top n `product_id` por volumen o ingresos, con su categoría y precio promedio.

    Complementa al ranking por categoría: el dataset no trae nombre de producto,
    así que el SKU sirve de detalle, no de titular. Insumo del punto 3.1.
    """
    ranking = items.groupby("product_id").agg(
        categoria_es=("categoria_es", "first"),
        categoria_en=("categoria_en", "first"),
        unidades=("price", "size"),
        pedidos=("order_id", "nunique"),
        ingresos=("price", "sum"),
        precio_promedio=("price", "mean"),
    )
    return ranking.sort_values(metrica, ascending=False).head(n).round(2).reset_index()


def comparar_tops(
    top_volumen: pd.DataFrame,
    top_ingresos: pd.DataFrame,
    columna_categoria: str = "categoria_es",
) -> dict[str, list[str]]:
    """Categorías comunes a ambos tops y las exclusivas de cada uno."""
    volumen = list(top_volumen[columna_categoria])
    ingresos = list(top_ingresos[columna_categoria])
    return {
        "en_ambos": [c for c in volumen if c in ingresos],
        "solo_volumen": [c for c in volumen if c not in ingresos],
        "solo_ingresos": [c for c in ingresos if c not in volumen],
    }


def peso_sin_categoria(ranking: pd.DataFrame, columna_categoria: str = "categoria_es") -> dict[str, float]:
    """Cuánto pesan en unidades e ingresos los productos sin categoría."""
    etiquetas = {ETIQUETA_SIN_CATEGORIA, "Sin categoría"}
    fila = ranking[ranking[columna_categoria].isin(etiquetas)]
    if fila.empty:
        return {"unidades": 0.0, "ingresos": 0.0, "pct_unidades": 0.0, "pct_ingresos": 0.0}
    fila = fila.iloc[0]
    return {
        "unidades": float(fila["unidades"]),
        "ingresos": float(fila["ingresos"]),
        "pct_unidades": float(fila["pct_unidades"]),
        "pct_ingresos": float(fila["pct_ingresos"]),
    }


# ---------------------------------------------------------------------------
# Punto 1.2 – Experiencia del cliente (dolor)
# ---------------------------------------------------------------------------

# Una reseña de 1 o 2 estrellas es una mala experiencia declarada por el cliente.
UMBRAL_MALA_EXPERIENCIA = 2
# Estados que representan un pedido que nunca llegó al cliente.
ESTADOS_FALLIDOS = ["canceled", "unavailable"]
# Mínimo de pedidos para que una categoría entre a los rankings de tasas.
UMBRAL_PEDIDOS_CATEGORIA = 300


def deduplicar_resenas(resenas: pd.DataFrame) -> pd.DataFrame:
    """Deja una sola reseña por pedido: la más reciente.

    Hay 551 `order_id` repetidos; sin deduplicar, esos pedidos pesarían doble en
    todas las tasas.
    """
    return (
        resenas.sort_values("review_answer_timestamp")
        .drop_duplicates("order_id", keep="last")
        .reset_index(drop=True)
    )


def clasificar_rango_retraso(dias: float) -> str:
    """Agrupa el retraso en rangos para ver dónde se rompe la satisfacción."""
    if pd.isna(dias):
        return "sin dato"
    if dias <= 0:
        return "a tiempo"
    if dias <= 3:
        return "1-3 días"
    if dias <= 7:
        return "4-7 días"
    if dias <= 14:
        return "8-14 días"
    return "más de 14 días"


def agregar_por_pedido(items_pedido: pd.DataFrame) -> pd.DataFrame:
    """Resume `order_items` a nivel pedido: ítems, vendedores, valor y flete."""
    agregado = items_pedido.groupby("order_id").agg(
        n_items=("price", "size"),
        n_vendedores=("seller_id", "nunique"),
        n_productos=("product_id", "nunique"),
        valor_productos=("price", "sum"),
        flete_total=("freight_value", "sum"),
    )
    agregado["ratio_flete"] = agregado["flete_total"] / agregado["valor_productos"]
    return agregado.reset_index()


def construir_pedidos_experiencia(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Una fila por pedido con su reseña, su retraso y su composición.

    Incluye TODOS los estados: un pedido cancelado o que nunca llegó también es
    dolor del cliente. Los merges son `left` desde pedidos y ninguno puede
    aumentar las filas.
    """
    pedidos = dfs["pedidos"]
    resenas_unicas = deduplicar_resenas(dfs["resenas"])
    agregado_items = agregar_por_pedido(dfs["items_pedido"])
    clientes = dfs["clientes"][["customer_id", "customer_unique_id", "customer_state", "customer_city"]]

    columnas_resena = ["order_id", "review_score", "review_comment_title", "review_comment_message",
                       "review_creation_date"]

    filas_inicio = len(pedidos)
    exp = pedidos.merge(resenas_unicas[columnas_resena], on="order_id", how="left")
    exp = exp.merge(agregado_items, on="order_id", how="left")
    exp = exp.merge(clientes, on="customer_id", how="left")

    if len(exp) != filas_inicio:
        raise ValueError(f"El merge alteró las filas: {filas_inicio} -> {len(exp)}")

    exp["entregado"] = exp["order_status"].eq("delivered")
    exp["pedido_fallido"] = exp["order_status"].isin(ESTADOS_FALLIDOS)
    exp["tiene_resena"] = exp["review_score"].notna()
    exp["mala_experiencia"] = exp["review_score"] <= UMBRAL_MALA_EXPERIENCIA

    # El retraso se mide contra la fecha prometida al cliente, no contra la duración
    exp["retraso_dias"] = (
        exp["order_delivered_customer_date"] - exp["order_estimated_delivery_date"]
    ).dt.days
    exp["tarde"] = exp["retraso_dias"] > 0
    exp["rango_retraso"] = exp["retraso_dias"].apply(clasificar_rango_retraso)
    exp["dias_entrega"] = (
        exp["order_delivered_customer_date"] - exp["order_purchase_timestamp"]
    ).dt.days

    return exp


def tabla_dolores(exp: pd.DataFrame) -> pd.DataFrame:
    """Compara los candidatos a dolor: tasa de mala experiencia y volumen afectado.

    Cada fila contrasta un grupo expuesto al problema contra su grupo de control.
    El impacto se mide como número absoluto de malas experiencias, porque una tasa
    alta sobre pocos pedidos no mueve el negocio.
    """
    entregados = exp[exp["entregado"] & exp["retraso_dias"].notna()]
    con_resena = exp[exp["tiene_resena"]]
    entregados_a_tiempo = entregados[~entregados["tarde"]]

    # Entrega lenta pese a llegar dentro del plazo prometido
    mediana_dias = entregados_a_tiempo["dias_entrega"].median()
    lentos = entregados_a_tiempo[entregados_a_tiempo["dias_entrega"] > 2 * mediana_dias]

    # Flete caro respecto al valor del producto
    con_flete = con_resena[con_resena["ratio_flete"].notna()]
    flete_alto = con_flete[con_flete["ratio_flete"] > 0.5]

    grupos = {
        "Entrega tarde (retraso > 0 días)": entregados[entregados["tarde"]],
        "Entrega a tiempo (control)": entregados_a_tiempo,
        "Pedido cancelado o no disponible": exp[exp["pedido_fallido"]],
        f"Entrega lenta a tiempo (> {2 * mediana_dias:.0f} días)": lentos,
        "Flete > 50% del valor del producto": flete_alto,
        "Flete <= 50% (control)": con_flete[con_flete["ratio_flete"] <= 0.5],
        "Pedido con varios vendedores": con_resena[con_resena["n_vendedores"] > 1],
        "Pedido con varios ítems": con_resena[con_resena["n_items"] > 1],
        "Pedido de un solo ítem (control)": con_resena[con_resena["n_items"] == 1],
    }

    filas = []
    for nombre, grupo in grupos.items():
        con_score = grupo[grupo["tiene_resena"]]
        filas.append({
            "dolor": nombre,
            "pedidos": len(grupo),
            "pedidos_con_resena": len(con_score),
            "tasa_mala_experiencia": con_score["mala_experiencia"].mean() * 100,
            "score_promedio": con_score["review_score"].mean(),
            "malas_experiencias": int(con_score["mala_experiencia"].sum()),
        })

    return pd.DataFrame(filas).round(2)


def experiencia_por_rango_retraso(exp: pd.DataFrame) -> pd.DataFrame:
    """Satisfacción según cuántos días se incumplió la fecha prometida."""
    orden = ["a tiempo", "1-3 días", "4-7 días", "8-14 días", "más de 14 días"]
    base = exp[exp["entregado"] & exp["tiene_resena"] & exp["retraso_dias"].notna()]
    tabla = base.groupby("rango_retraso").agg(
        pedidos=("order_id", "size"),
        score_promedio=("review_score", "mean"),
        tasa_mala_experiencia=("mala_experiencia", "mean"),
    )
    tabla["tasa_mala_experiencia"] *= 100
    return tabla.reindex(orden).round(2).reset_index()


def dolor_por_categoria(
    items: pd.DataFrame,
    exp: pd.DataFrame,
    umbral_pedidos: int = UMBRAL_PEDIDOS_CATEGORIA,
    columna_categoria: str = "categoria_es",
) -> pd.DataFrame:
    """Tasa de mala experiencia, retraso e impacto absoluto por categoría.

    Se deduplica pedido-categoría para que un pedido con 3 ítems de la misma
    categoría no cuente 3 veces. Un pedido con 2 categorías sí cuenta en ambas.
    """
    pares = items[["order_id", columna_categoria]].drop_duplicates()
    columnas_exp = ["order_id", "review_score", "mala_experiencia", "tiene_resena",
                    "tarde", "retraso_dias"]
    cruce = pares.merge(exp[columnas_exp], on="order_id", how="inner")
    cruce = cruce[cruce["tiene_resena"]]

    tabla = cruce.groupby(columna_categoria).agg(
        pedidos=("order_id", "nunique"),
        score_promedio=("review_score", "mean"),
        tasa_mala_experiencia=("mala_experiencia", "mean"),
        malas_experiencias=("mala_experiencia", "sum"),
        pct_tarde=("tarde", "mean"),
        retraso_promedio_dias=("retraso_dias", "mean"),
    )
    tabla["tasa_mala_experiencia"] *= 100
    tabla["pct_tarde"] *= 100
    tabla = tabla[tabla["pedidos"] >= umbral_pedidos]
    return tabla.sort_values("malas_experiencias", ascending=False).round(2).reset_index()


def entregas_tarde_por_estado(exp: pd.DataFrame, minimo_pedidos: int = 300) -> pd.DataFrame:
    """% de entregas tarde y satisfacción por estado (UF) del cliente."""
    base = exp[exp["entregado"] & exp["retraso_dias"].notna()]
    tabla = base.groupby("customer_state").agg(
        pedidos=("order_id", "size"),
        pct_tarde=("tarde", "mean"),
        retraso_promedio_dias=("retraso_dias", "mean"),
        score_promedio=("review_score", "mean"),
    )
    tabla["pct_tarde"] *= 100
    tabla = tabla[tabla["pedidos"] >= minimo_pedidos]
    return tabla.sort_values("pct_tarde", ascending=False).round(2).reset_index()


def perfil_dolor_cliente(exp: pd.DataFrame, temas: pd.DataFrame | None = None) -> pd.DataFrame:
    """Resumen de dolor por cliente real (`customer_unique_id`) para 2.1 y 3.2."""
    base = exp.copy()
    if temas is not None:
        base = base.merge(temas[["order_id", "tema_principal"]], on="order_id", how="left")
    else:
        base["tema_principal"] = pd.NA

    def motivo(fila: pd.Series) -> str:
        """Motivo del peor pedido: el tema del comentario y, si no hay, el hecho objetivo."""
        if isinstance(fila["tema_principal"], str):
            return fila["tema_principal"]
        if fila["pedido_fallido"]:
            return "pedido no entregado"
        if fila["tarde"]:
            return "entrega tarde"
        return "sin motivo declarado"

    malas = base[base["mala_experiencia"]].copy()
    malas["motivo_principal"] = malas.apply(motivo, axis=1)
    motivo_cliente = (
        malas.sort_values("order_purchase_timestamp")
        .groupby("customer_unique_id")["motivo_principal"]
        .last()
    )

    perfil = base.groupby("customer_unique_id").agg(
        pedidos=("order_id", "nunique"),
        malas_experiencias=("mala_experiencia", "sum"),
        score_promedio=("review_score", "mean"),
        max_retraso_dias=("retraso_dias", "max"),
        pedidos_tarde=("tarde", "sum"),
        pedidos_fallidos=("pedido_fallido", "sum"),
    )
    perfil["tuvo_mala_experiencia"] = perfil["malas_experiencias"] > 0
    perfil["motivo_principal"] = perfil.index.map(motivo_cliente).fillna("sin mala experiencia")
    return perfil.round(2).reset_index()


# ---------------------------------------------------------------------------
# Punto 2.1 – variable HISTORIAL_COMPRAS para el agente de IA (punto 3.2)
# ---------------------------------------------------------------------------


def construir_historial_compras(clientes: pd.DataFrame) -> pd.Series:
    """Resumen en texto del comportamiento de cada cliente, listo para el prompt.

    El agente del 3.2 no puede recibir una tabla: recibe una frase corta con los
    hechos que cambian el tono de la conversación (cuánto compra, qué le gusta,
    hace cuánto no vuelve y si quedó mal atendido).
    """

    def linea(fila: pd.Series) -> str:
        partes = [
            f"{int(fila['frecuencia'])} pedido{'s' if fila['frecuencia'] != 1 else ''}",
            f"gasto total R${fila['gasto_total']:,.0f}",
            f"ticket prom. R${fila['ticket_promedio']:,.0f}",
            f"categoría favorita: {fila['categoria_favorita']}",
            f"última compra hace {int(fila['recencia'])} días",
        ]
        if pd.notna(fila["score_promedio"]):
            partes.append(f"score prom. {fila['score_promedio']:.1f}")
        partes.append("mala experiencia: " + ("sí" if fila["tuvo_mala_experiencia"] else "no"))
        if fila["tuvo_mala_experiencia"]:
            partes.append(f"motivo: {fila['motivo_principal']}")
        partes.append(f"segmento: {fila['segmento']}")
        return " | ".join(partes)

    return clientes.apply(linea, axis=1)
