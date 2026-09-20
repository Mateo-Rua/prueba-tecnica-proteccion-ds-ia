"""Carga de los CSV de Olist desde data/raw/.

Módulo reutilizable por todas las tareas de la prueba. Expone:
- `cargar_datos()`: lee los 9 CSV y convierte las fechas a datetime.
- `traducir_categorias()`: categoría en portugués, inglés y español.
- `construir_items_enriquecidos()`: tabla base de análisis (1 fila = 1 unidad vendida).
"""

from pathlib import Path

import pandas as pd

RUTA_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_RAW = RUTA_PROYECTO / "data" / "raw"
RUTA_PROCESSED = RUTA_PROYECTO / "data" / "processed"

# Nombre en español -> archivo CSV
ARCHIVOS = {
    "clientes": "olist_customers_dataset.csv",
    "geolocalizacion": "olist_geolocation_dataset.csv",
    "items_pedido": "olist_order_items_dataset.csv",
    "pagos": "olist_order_payments_dataset.csv",
    "resenas": "olist_order_reviews_dataset.csv",
    "pedidos": "olist_orders_dataset.csv",
    "productos": "olist_products_dataset.csv",
    "vendedores": "olist_sellers_dataset.csv",
    "traduccion_categorias": "product_category_name_translation.csv",
}

# Columnas de fecha que vienen como texto en los CSV
COLUMNAS_FECHA = {
    "items_pedido": ["shipping_limit_date"],
    "resenas": ["review_creation_date", "review_answer_timestamp"],
    "pedidos": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
}

# Escenarios de filtro por estado del pedido (decisión analítica 1 de la tarea 1.1)
ESTADOS_PRINCIPAL = ["delivered"]
ESTADOS_SENSIBILIDAD = [
    "delivered",
    "shipped",
    "invoiced",
    "processing",
    "approved",
    "created",
]

# Las 2 categorías que no están en product_category_name_translation.csv
TRADUCCIONES_FALTANTES = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "portable_kitchen_food_preparers",
}

# Nombre en español de cada categoría, para la presentación ejecutiva
CATEGORIAS_ESPANOL = {
    "agro_industria_e_comercio": "Agroindustria y comercio",
    "alimentos": "Alimentos",
    "alimentos_bebidas": "Alimentos y bebidas",
    "artes": "Arte",
    "artes_e_artesanato": "Arte y artesanía",
    "artigos_de_festas": "Artículos de fiesta",
    "artigos_de_natal": "Artículos de navidad",
    "audio": "Audio",
    "automotivo": "Automotriz",
    "bebes": "Bebés",
    "bebidas": "Bebidas",
    "beleza_saude": "Belleza y salud",
    "brinquedos": "Juguetes",
    "cama_mesa_banho": "Cama, mesa y baño",
    "casa_conforto": "Confort para el hogar",
    "casa_conforto_2": "Confort para el hogar 2",
    "casa_construcao": "Casa y construcción",
    "cds_dvds_musicais": "CD y DVD musicales",
    "cine_foto": "Cine y fotografía",
    "climatizacao": "Climatización",
    "consoles_games": "Consolas y videojuegos",
    "construcao_ferramentas_construcao": "Construcción: herramientas",
    "construcao_ferramentas_ferramentas": "Construcción: herramienta manual",
    "construcao_ferramentas_iluminacao": "Construcción: iluminación",
    "construcao_ferramentas_jardim": "Construcción: jardín",
    "construcao_ferramentas_seguranca": "Construcción: seguridad",
    "cool_stuff": "Novedades",
    "dvds_blu_ray": "DVD y Blu-ray",
    "eletrodomesticos": "Electrodomésticos",
    "eletrodomesticos_2": "Electrodomésticos 2",
    "eletronicos": "Electrónica",
    "eletroportateis": "Electrodomésticos pequeños",
    "esporte_lazer": "Deporte y ocio",
    "fashion_bolsas_e_acessorios": "Moda: bolsos y accesorios",
    "fashion_calcados": "Moda: calzado",
    "fashion_esporte": "Moda deportiva",
    "fashion_roupa_feminina": "Moda: ropa femenina",
    "fashion_roupa_infanto_juvenil": "Moda: ropa infantil",
    "fashion_roupa_masculina": "Moda: ropa masculina",
    "fashion_underwear_e_moda_praia": "Moda: ropa interior y playa",
    "ferramentas_jardim": "Herramientas de jardín",
    "flores": "Flores",
    "fraldas_higiene": "Pañales e higiene",
    "industria_comercio_e_negocios": "Industria y negocios",
    "informatica_acessorios": "Informática y accesorios",
    "instrumentos_musicais": "Instrumentos musicales",
    "la_cuisine": "La Cuisine (cocina gourmet)",
    "livros_importados": "Libros importados",
    "livros_interesse_geral": "Libros de interés general",
    "livros_tecnicos": "Libros técnicos",
    "malas_acessorios": "Maletas y accesorios",
    "market_place": "Marketplace",
    "moveis_colchao_e_estofado": "Muebles: colchones y tapicería",
    "moveis_cozinha_area_de_servico_jantar_e_jardim": "Muebles: cocina, comedor y jardín",
    "moveis_decoracao": "Muebles y decoración",
    "moveis_escritorio": "Muebles de oficina",
    "moveis_quarto": "Muebles de dormitorio",
    "moveis_sala": "Muebles de sala",
    "musica": "Música",
    "papelaria": "Papelería",
    "pc_gamer": "PC gamer",
    "pcs": "Computadores",
    "perfumaria": "Perfumería",
    "pet_shop": "Mascotas",
    "portateis_casa_forno_e_cafe": "Horno y café para el hogar",
    "portateis_cozinha_e_preparadores_de_alimentos": "Procesadores de alimentos",
    "relogios_presentes": "Relojes y regalos",
    "seguros_e_servicos": "Seguros y servicios",
    "sinalizacao_e_seguranca": "Señalización y seguridad",
    "tablets_impressao_imagem": "Tablets, impresión e imagen",
    "telefonia": "Telefonía",
    "telefonia_fixa": "Telefonía fija",
    "utilidades_domesticas": "Utensilios domésticos",
    "sin_categoria": "Sin categoría",
}

ETIQUETA_SIN_CATEGORIA = "sin_categoria"


def cargar_datos(ruta_raw: Path = RUTA_RAW) -> dict[str, pd.DataFrame]:
    """Lee los 9 CSV de Olist y devuelve un dict con nombres en español."""
    dfs = {}
    for nombre, archivo in ARCHIVOS.items():
        df = pd.read_csv(ruta_raw / archivo)
        for columna in COLUMNAS_FECHA.get(nombre, []):
            df[columna] = pd.to_datetime(df[columna])
        dfs[nombre] = df
    return dfs


def traducir_categorias(productos: pd.DataFrame, traduccion: pd.DataFrame) -> pd.DataFrame:
    """Devuelve product_id con su categoría en portugués, inglés y español.

    Los productos sin categoría quedan marcados como `sin_categoria` en lugar de
    nulo, para poder medir cuánto pesan en el negocio en vez de perderlos.
    """
    mapa_ingles = dict(zip(traduccion["product_category_name"], traduccion["product_category_name_english"]))
    mapa_ingles.update(TRADUCCIONES_FALTANTES)  # las 2 que faltan en el CSV oficial

    catalogo = productos[["product_id", "product_category_name"]].copy()
    catalogo["categoria_pt"] = catalogo["product_category_name"].fillna(ETIQUETA_SIN_CATEGORIA)
    catalogo["categoria_en"] = catalogo["categoria_pt"].map(mapa_ingles).fillna(ETIQUETA_SIN_CATEGORIA)
    catalogo["categoria_es"] = catalogo["categoria_pt"].map(CATEGORIAS_ESPANOL).fillna(ETIQUETA_SIN_CATEGORIA)
    return catalogo.drop(columns="product_category_name")


def construir_items_enriquecidos(
    dfs: dict[str, pd.DataFrame],
    estados_validos: list[str] = ESTADOS_PRINCIPAL,
    verbose: bool = True,
) -> pd.DataFrame:
    """Tabla base del análisis: 1 fila = 1 unidad vendida en un pedido válido.

    Une `items_pedido` con el estado y las fechas del pedido y con la categoría del
    producto. Ninguno de los dos merges puede cambiar el número de filas, porque
    `order_id` es único en pedidos y `product_id` es único en productos.
    """
    items = dfs["items_pedido"]
    pedidos = dfs["pedidos"]

    pedidos_validos = pedidos[pedidos["order_status"].isin(estados_validos)]
    columnas_pedido = [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    filas_inicio = len(items)
    items_validos = items.merge(pedidos_validos[columnas_pedido], on="order_id", how="inner")
    filas_tras_pedidos = len(items_validos)

    catalogo = traducir_categorias(dfs["productos"], dfs["traduccion_categorias"])
    items_enriquecidos = items_validos.merge(catalogo, on="product_id", how="left")
    filas_tras_productos = len(items_enriquecidos)

    items_enriquecidos["ingreso_con_flete"] = (
        items_enriquecidos["price"] + items_enriquecidos["freight_value"]
    )

    if verbose:
        print(f"Ítems totales                  : {filas_inicio:,}")
        print(f"Ítems de pedidos válidos       : {filas_tras_pedidos:,} ({estados_validos})")
        print(f"Ítems tras unir categoría      : {filas_tras_productos:,}")
        print(f"Merge con productos conserva filas: {filas_tras_pedidos == filas_tras_productos}")
        print(f"Categorías nulas tras el merge : {items_enriquecidos['categoria_pt'].isna().sum()}")

    return items_enriquecidos
