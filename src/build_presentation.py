"""Genera la presentación ejecutiva de la sustentación (reports/presentacion_ejecutiva.pptx).

Cifras tomadas de reports/RESULTADOS.md, reports/tables/*.csv, SUPUESTOS.md y agent/.
Paleta tomada del CSS de proteccion.com (sin logo).
Uso:  python -m src.build_presentation
"""

import json
from pathlib import Path

import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parents[1]
TABLAS, FIGURAS = RAIZ / "reports" / "tables", RAIZ / "reports" / "figures"
SALIDA = RAIZ / "reports" / "presentacion_ejecutiva.pptx"

AZUL, AZUL_OSC, AZUL_CLARO = RGBColor(0x00, 0x33, 0xA0), RGBColor(0x0B, 0x29, 0x87), RGBColor(0x71, 0x9E, 0xCE)
AMARILLO, TEXTO, GRIS = RGBColor(0xE3, 0xE8, 0x29), RGBColor(0x29, 0x27, 0x30), RGBColor(0x62, 0x62, 0x77)
FONDO, BLANCO = RGBColor(0xEE, 0xF2, 0xF7), RGBColor(0xFF, 0xFF, 0xFF)
FUENTE = "Calibri"
PIE = "Prueba técnica · Científico de Datos IA – PQR · Mateo Londoño"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)


# ---------------------------------------------------------------------------
# Utilidades de diseño
# ---------------------------------------------------------------------------


def texto(slide, x, y, w, h, lineas, tam=16, color=TEXTO, negrita=False, alinear=PP_ALIGN.LEFT, ancla=MSO_ANCHOR.TOP):
    """Caja de texto. `lineas`: str o lista de str / (texto, tam, color, negrita)."""
    caja = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = caja.text_frame
    tf.word_wrap, tf.vertical_anchor = True, ancla
    tf.margin_left = tf.margin_right = Inches(0.05)
    for i, linea in enumerate([lineas] if isinstance(lineas, str) else lineas):
        t, s, c, b = (linea, tam, color, negrita) if isinstance(linea, str) else (list(linea) + [tam, color, negrita][len(linea) - 1:])[:4]
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment, p.space_after = alinear, Pt(6)
        run = p.add_run()
        run.text = t
        run.font.name, run.font.size, run.font.bold, run.font.color.rgb = FUENTE, Pt(s), b, c
    return caja


def rect(slide, x, y, w, h, relleno=FONDO, borde=None, redondo=True):
    forma = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if redondo else MSO_SHAPE.RECTANGLE,
                                   Inches(x), Inches(y), Inches(w), Inches(h))
    forma.fill.solid()
    forma.fill.fore_color.rgb = relleno
    if borde:
        forma.line.color.rgb, forma.line.width = borde, Pt(1)
    else:
        forma.line.fill.background()
    forma.shadow.inherit = False
    if redondo:
        forma.adjustments[0] = 0.06
    return forma


def imagen(slide, ruta, x, y, w, h):
    """Inserta la imagen centrada en la caja, sin deformarla."""
    ancho, alto = Image.open(ruta).size
    escala = min(w / ancho, h / alto)
    iw, ih = ancho * escala, alto * escala
    slide.shapes.add_picture(str(ruta), Inches(x + (w - iw) / 2), Inches(y + (h - ih) / 2), Inches(iw), Inches(ih))


def nueva(titulo, notas, oscura=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    if oscura:
        rect(slide, 0, 0, 13.333, 7.5, AZUL_OSC, redondo=False)
    else:
        texto(slide, 0.5, 0.3, 12.3, 1.0, titulo, tam=28, color=AZUL, negrita=True, ancla=MSO_ANCHOR.MIDDLE)
    n = len(prs.slides)
    color_pie = BLANCO if oscura else GRIS
    texto(slide, 0.5, 7.0, 10.5, 0.35, PIE, tam=10, color=color_pie)
    texto(slide, 11.8, 7.0, 1.0, 0.35, str(n), tam=10, color=color_pie, alinear=PP_ALIGN.RIGHT)
    slide.notes_slide.notes_text_frame.text = "\n".join(f"• {n}" for n in notas)
    return slide


def panel_derecho(slide, hallazgos, supuesto):
    """Cajas fijas 'Hallazgos' y 'Supuesto' (misma posición y estilo en todas las diapositivas de resultados)."""
    rect(slide, 8.3, 1.45, 4.55, 3.95, FONDO)
    texto(slide, 8.5, 1.55, 4.2, 0.4, "Hallazgos", tam=16, color=AZUL, negrita=True)
    texto(slide, 8.5, 2.0, 4.2, 3.35, [f"• {h}" for h in hallazgos], tam=14)
    rect(slide, 8.3, 5.55, 4.55, 1.3, BLANCO, borde=AZUL_CLARO)
    texto(slide, 8.5, 5.6, 4.2, 0.35, "Supuesto", tam=14, color=AZUL, negrita=True)
    texto(slide, 8.5, 5.95, 4.2, 0.9, supuesto, tam=13, color=GRIS)


def barras(slide, x, y, w, h, categorias, valores, titulo, formato='0.0"%"', resaltar=0, color=AZUL_CLARO):
    datos = CategoryChartData()
    datos.categories = categorias
    datos.add_series(titulo, valores)
    chart = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), datos).chart
    chart.has_title, chart.has_legend = True, False
    chart.chart_title.text_frame.text = titulo
    fuente_titulo = chart.chart_title.text_frame.paragraphs[0].runs[0].font
    fuente_titulo.size, fuente_titulo.bold, fuente_titulo.color.rgb, fuente_titulo.name = Pt(14), True, TEXTO, FUENTE
    plot = chart.plots[0]
    plot.gap_width = 60
    plot.has_data_labels = True
    etiquetas = plot.data_labels
    etiquetas.number_format, etiquetas.number_format_is_linked = formato, False
    etiquetas.position, etiquetas.font.size, etiquetas.font.name = XL_LABEL_POSITION.OUTSIDE_END, Pt(12), FUENTE
    serie = plot.series[0]
    for i in range(len(valores)):
        punto = serie.points[i]
        punto.format.fill.solid()
        punto.format.fill.fore_color.rgb = AZUL if i == resaltar else color
    chart.value_axis.visible = False
    chart.value_axis.maximum_scale = max(valores) * 1.25  # espacio para las etiquetas
    chart.value_axis.has_major_gridlines = False
    chart.category_axis.reverse_order = True
    chart.category_axis.tick_labels.font.size, chart.category_axis.tick_labels.font.name = Pt(12), FUENTE
    chart.category_axis.format.line.fill.background()
    return chart


def cifra(slide, x, y, w, valor, etiqueta, fondo=AZUL, color_valor=AMARILLO, tam=34):
    rect(slide, x, y, w, 1.35, fondo)
    texto(slide, x + 0.15, y + 0.08, w - 0.3, 0.7, valor, tam=tam, color=color_valor, negrita=True)
    texto(slide, x + 0.15, y + 0.78, w - 0.3, 0.55, etiqueta, tam=12, color=BLANCO)


def tabla(slide, x, y, w, filas, anchos, tam=13, alto_fila=0.5):
    t = slide.shapes.add_table(len(filas), len(filas[0]), Inches(x), Inches(y), Inches(w), Inches(alto_fila * len(filas))).table
    for j, ancho in enumerate(anchos):
        t.columns[j].width = Inches(ancho)
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            celda = t.cell(i, j)
            celda.fill.solid()
            celda.fill.fore_color.rgb = AZUL if i == 0 else (FONDO if i % 2 else BLANCO)
            celda.margin_left = celda.margin_right = Inches(0.06)
            tf = celda.text_frame
            tf.word_wrap = True
            run = tf.paragraphs[0].add_run()
            run.text = str(valor)
            run.font.name, run.font.size = FUENTE, Pt(tam)
            run.font.bold = i == 0
            run.font.color.rgb = BLANCO if i == 0 else TEXTO
    return t


# ---------------------------------------------------------------------------
# Diapositivas
# ---------------------------------------------------------------------------

vol = pd.read_csv(TABLAS / "1_1_top5_volumen.csv")
ing = pd.read_csv(TABLAS / "1_1_top5_ingresos.csv")
cat_dolor = pd.read_csv(TABLAS / "1_2_categorias_dolor.csv")
segmentos = pd.read_csv(TABLAS / "2_1_perfil_segmentos.csv")
evaluacion = pd.read_csv(TABLAS / "2_2_evaluacion_offline.csv")
zonas = pd.read_csv(TABLAS / "2_3_zonas.csv")
kb = json.loads((RAIZ / "agent" / "knowledge_base.json").read_text(encoding="utf-8"))

# 1. Portada ---------------------------------------------------------------
s = nueva("", [
    "Presentarme y el objetivo: convertir datos transaccionales en decisiones de venta y servicio que alimenten un Agente de IA.",
    "La prueba usa Olist como 'nuestra empresa': cada punto alimenta al siguiente.",
    "Todo es reproducible: código en GitHub y dos demos publicados en AWS (recomendador y agente).",
], oscura=True)
texto(s, 0.8, 1.2, 11.5, 0.5, "PROTECCIÓN", tam=18, color=AMARILLO, negrita=True)
texto(s, 0.8, 1.9, 11.5, 2.2, "Inteligencia de clientes y Agentes de IA para experiencias hiper-personalizadas",
      tam=40, color=BLANCO, negrita=True)
texto(s, 0.8, 4.3, 11.5, 0.9, "Prueba técnica – Científico de Datos para soluciones con IA · Equipo Atención de PQR", tam=20, color=BLANCO)
texto(s, 0.8, 5.4, 11.5, 0.9, [("Mateo Londoño", 18, AMARILLO, True), ("Septiembre de 2026", 14, BLANCO, False)])

# 2. Problema de negocio ---------------------------------------------------
s = nueva("De datos transaccionales a conversaciones personalizadas que venden y sirven mejor", [
    "El reto de la vacante: orquestar modelos predictivos que alimenten Agentes de IA y personalicen ventas y servicio.",
    "Por eso la solución es un hilo conductor, no siete respuestas sueltas.",
    "P1 dice qué se vende y qué duele; P2 dice quién es cada cliente y qué ofrecerle; P3 lo convierte en conversaciones.",
    "El dolor del 1.2 atraviesa todo: segmentación, recomendador y tono del agente.",
])
bloques = [
    ("1 · Diagnóstico", "¿Qué se vende más y cuál es el mayor dolor del cliente?", "Top categorías · dolor y categorías asociadas"),
    ("2 · Inteligencia de clientes", "¿Quién es cada cliente y qué ofrecerle?", "Segmentación · recomendador en tiempo real · tienda física"),
    ("3 · Activación con IA", "¿Cómo conversar con cada cliente?", "Base de conocimiento · system prompts · agente"),
]
for i, (tit, pregunta, entregables) in enumerate(bloques):
    x = 0.5 + i * 4.2
    rect(s, x, 1.7, 3.85, 3.6, AZUL if i == 2 else FONDO)
    c1, c2 = (AMARILLO, BLANCO) if i == 2 else (AZUL, TEXTO)
    texto(s, x + 0.25, 1.9, 3.4, 0.6, tit, tam=20, color=c1, negrita=True)
    texto(s, x + 0.25, 2.65, 3.4, 1.3, pregunta, tam=16, color=c2)
    texto(s, x + 0.25, 4.1, 3.4, 1.1, entregables, tam=14, color=c2)
    if i < 2:
        texto(s, x + 3.8, 3.1, 0.45, 0.6, "→", tam=28, color=AZUL, negrita=True, alinear=PP_ALIGN.CENTER)
texto(s, 0.5, 5.65, 12.3, 1.0, [("Misión de la vacante: ", 16, AZUL, True),
      ("orquestar modelos predictivos que alimenten Agentes de IA y conviertan interacciones multicanal en experiencias hiper-personalizadas.", 16, TEXTO, False)])

# 3. Insumos ---------------------------------------------------------------
s = nueva("Un e-commerce real de 2 años: 99 mil pedidos de 96 mil clientes en 9 tablas conectadas", [
    "Dataset público Olist (Kaggle): e-commerce brasileño, sep-2016 a oct-2018.",
    "La tabla central es orders: une clientes, ítems, pagos y reseñas.",
    "Regla clave: el cliente real es customer_unique_id; customer_id cambia en cada pedido.",
    "Nunca unir ítems con pagos directamente: duplica montos (payment_value incluye flete).",
    "Cifra de ítems (112.650) tomada del EDA (explorer.ipynb).",
])
for i, (v, e) in enumerate([("99.441", "pedidos"), ("96.096", "clientes únicos"), ("112.650", "ítems vendidos*"), ("99.224", "reseñas")]):
    cifra(s, 0.5 + i * 2.05, 1.5, 1.9, v, e, tam=28)
tablas_olist = [
    "orders – pedido, estado y fechas (tabla central)", "customers – cliente, ciudad y estado", "order_items – 1 fila = 1 unidad vendida",
    "order_payments – medio de pago y cuotas", "order_reviews – nota 1-5 y comentario", "products – categoría (sin nombre)",
    "sellers – vendedor y ubicación", "geolocation – coordenadas por código postal", "category_translation – portugués → inglés",
]
texto(s, 0.5, 3.05, 5.2, 3.3, [f"• {t}" for t in tablas_olist], tam=14)
imagen(s, FIGURAS / "diagrama_relaciones_tablas.png", 5.8, 3.0, 7.05, 3.3)
texto(s, 0.5, 6.35, 12.3, 0.6, "Calidad: llaves 100% íntegras; se trataron 261.831 duplicados en geolocalización, reseñas repetidas y 584 productos sin categoría.  *Fuente: EDA.",
      tam=12, color=GRIS)

# 4. Punto 1.1 -------------------------------------------------------------
s = nueva("Belleza y salud es la única categoría que lidera en volumen y en ingresos", [
    "Volumen = unidades (filas de order_items); ingresos = suma de price sin flete, solo pedidos entregados.",
    "Cuatro categorías están en ambos tops; la diferencia la explica el ticket.",
    "Relojes y regalos entra por ingresos con ticket de R$ 199; Muebles y decoración entra por volumen con R$ 87.",
    "Defensa: el top 5 no cambia con el filtro laxo de estados ni sumando el flete.",
    "Cada pedido tiene 1,14 unidades: no hay venta cruzada, argumento para el recomendador.",
])
barras(s, 0.4, 1.45, 3.9, 5.3, list(vol["categoria_es"]), list(vol["pct_unidades"]), "Top 5 por volumen (% unidades)", resaltar=1)
barras(s, 4.3, 1.45, 3.9, 5.3, list(ing["categoria_es"]), list(ing["pct_ingresos"]), "Top 5 por ingresos (% ingresos)", resaltar=0)
panel_derecho(s, [
    "Belleza y salud: 1ª en ingresos (R$ 1.233.132) y 2ª en volumen.",
    "El ticket separa los rankings: Relojes (R$ 199) entra por ingresos y Muebles (R$ 87) por volumen.",
    "Negocio fragmentado: el top 5 suma solo el 39,8% de los ingresos.",
], "Pedidos entregados (96.478). Volumen = unidades; ingresos = price sin flete.")

# 5. Punto 1.2 (a) ---------------------------------------------------------
s = nueva("La entrega tarde es el mayor dolor: 62% de malas reseñas frente a 9% a tiempo", [
    "Mala experiencia = reseña de 1-2 estrellas: es el dolor declarado por el cliente.",
    "Se demuestra con grupo de control: tarde 62,4% vs a tiempo 9,3% (6,7 veces más).",
    "El texto lo confirma: 56,4% de los comentarios negativos habla de entrega.",
    "Umbral accionable: 1-3 días de retraso ya lleva al 32%; de 8-14 días, al 80%.",
    "Lo que NO es dolor: el flete caro (14,9% vs 14,1%).",
])
cifra(s, 0.5, 1.5, 3.7, "62,4%", "malas reseñas si llega tarde", fondo=AZUL)
cifra(s, 4.4, 1.5, 3.7, "9,3%", "malas reseñas si llega a tiempo", fondo=AZUL_CLARO, color_valor=BLANCO)
barras(s, 0.4, 3.05, 7.8, 3.8, ["Entrega / retraso", "Atención / vendedor", "Producto errado", "Reembolso", "Producto defectuoso"],
       [56.4, 17.9, 17.1, 14.7, 13.5], "Top dolores: % de comentarios negativos por tema (NLP)")
panel_derecho(s, [
    "Top 3 dolores: entrega (56,4%), atención (17,9%) y producto errado (17,1%).",
    "El daño tiene umbral: 1-3 días de retraso → 32,1%; 8-14 días → 80,2%.",
    "El flete caro no es dolor (14,9% vs 14,1%); los pedidos de varios vendedores sí (47,3%).",
], "Mala experiencia = reseña de 1-2★; una reseña por pedido (la más reciente).")

# 6. Punto 1.2 (b) ---------------------------------------------------------
top_impacto = cat_dolor.nlargest(5, "malas_experiencias")
s = nueva("Donde más se vende es donde más duele: las categorías líderes concentran las malas experiencias", [
    "Dos rankings, dos decisiones: el impacto dice dónde invertir y la tasa dice dónde el proceso está roto.",
    "Cama, mesa y baño: 1.471 clientes molestos; Audio: la peor tasa (21,7%) pero con solo 75 afectados.",
    "Hay que separar causas: Audio falla por logística (11,6% tarde), Muebles de oficina por producto (score 3,64 con 8% tarde).",
    "Solo entran al ranking por tasa las categorías con ≥ 300 pedidos, para evitar tasas infladas.",
])
barras(s, 0.4, 1.45, 4.6, 5.3, list(top_impacto["categoria_es"]), list(top_impacto["malas_experiencias"]),
       "Top categorías por impacto (n° malas experiencias)", formato="#,##0")
tabla(s, 5.1, 1.7, 3.0, [["Por tasa", "% mala exp.", "Causa"],
                          ["Muebles oficina", "22,0%", "Producto"], ["Audio", "21,7%", "Logística"], ["Confort hogar", "18,7%", "Logística"]],
      [1.25, 0.9, 0.85], tam=12, alto_fila=0.55)
texto(s, 5.1, 4.1, 3.0, 2.2, "Logística: retraso muy por encima del 6,8% promedio (Audio 11,6%, Confort 9,5%). Producto: nota baja con retraso cercano al promedio (Muebles de oficina: 3,64 con 8,0%).",
      tam=12, color=GRIS)
panel_derecho(s, [
    "Top 3 por impacto: Cama, mesa y baño (1.471), Belleza y salud (985) y Muebles y decoración (961).",
    "Top 3 por tasa: Muebles de oficina (22,0%), Audio (21,7%) y Confort para el hogar (18,7%).",
    "Audio falla por logística (11,6% tarde); Muebles de oficina, por producto (score 3,64).",
], "Ranking por tasa con ≥ 300 pedidos; un pedido cuenta en cada categoría que contiene.")

# 7. Punto 2.1 (a) ---------------------------------------------------------
s = nueva("Con 97% de compradores únicos, la segmentación se apoya en recencia y valor, no en frecuencia", [
    "RFM por customer_unique_id; el reto es que solo 3% recompra, así que la F casi no discrimina.",
    "Umbral de riesgo calculado con datos: el 75% de las recompras reales ocurre dentro de 171 días.",
    "Se excluyen los segundos pedidos del mismo día (30%): son un carrito partido, no una recompra.",
    "VIP = gasto en el top 10% (≥ R$ 319): 9,6% de clientes que generan el 36,9% de los ingresos.",
    "K-Means como contraste: con k=2 solo separa recompradores; con k=4 descubre un cluster insatisfecho (16.358 clientes, score 1,6): la población natural de PQR.",
    "Elegí reglas para marketing: interpretables, estables y con precio por segmento; el K-Means valida que el dolor del 1.2 es estructural.",
])
imagen(s, FIGURAS / "2_1_dias_entre_compras.png", 0.4, 1.45, 7.7, 3.7)
for i, (v, e) in enumerate([("3%", "clientes recompran"), ("171 días", "umbral de riesgo (p75)"), ("17%", "cluster insatisfecho (K-Means)")]):
    cifra(s, 0.5 + i * 2.6, 5.35, 2.45, v, e, tam=28)
panel_derecho(s, [
    "La F no sirve sola: con 97% de compra única, un RFM clásico dejaría a casi todos en el mismo grupo.",
    "El 30% de las «recompras» era el mismo carrito del mismo día: contarlas inflaba la fidelidad.",
    "El 75% de quien vuelve lo hace en 171 días: pasado ese plazo, el cliente entra en riesgo.",
    "1 de cada 10 clientes (gasto ≥ R$ 319) aporta el 37% de los ingresos: la R y la M sí separan.",
    "El K-Means no agrupó por valor sino por satisfacción: 17% de clientes con 78% de malas experiencias.",
], "Frecuencia = días distintos de compra; ventana hasta ago-2018 (sep-2018 incompleto).")

# 8. Punto 2.1 (b) ---------------------------------------------------------
s = nueva("El 9,6% de los clientes (VIP) genera el 36,9% de los ingresos; el 55% ya salió del ciclo", [
    "Fieles son solo 1,1%: la meta realista no es fidelizar sino lograr la segunda compra.",
    "VIP: 9,6% de clientes y 36,9% de ingresos, es donde más rinde el presupuesto de retención.",
    "En riesgo + perdidos = 55% de la base y 37,6% de los ingresos históricos.",
    "Cada segmento tiene una acción distinta; al cliente con mala experiencia primero se le resuelve el PQR.",
])
acciones = ["Fidelización y cross-sell", "Atención preferente y recompra asistida", "Cupón para la 2ª compra",
            "Reactivar; si tuvo mala exp., resolver PQR primero", "Campaña masiva de bajo costo"]
filas = [["Segmento", "% clientes", "% ingresos", "Acción de marketing"]] + [
    [r.segmento, f"{r.pct_clientes:.1f}%".replace(".", ","), f"{r.pct_ingresos:.1f}%".replace(".", ","), a]
    for r, a in zip(segmentos.itertuples(), acciones)]
tabla(s, 0.5, 1.6, 7.6, filas, [2.0, 1.1, 1.1, 3.4], tam=13, alto_fila=0.8)
panel_derecho(s, [
    "Casi no hay fieles: 1.060 clientes (1,1%). El objetivo es la segunda compra.",
    "El valor está concentrado: VIP = 9,6% de clientes y 36,9% de ingresos.",
    "El 55% está en riesgo o perdido y aporta el 37,6% de los ingresos.",
], "En riesgo: más de 171 días sin comprar; perdido: más de 281; VIP: gasto ≥ R$ 319 (p90).")

# 9. Punto 2.2 (a) ---------------------------------------------------------
s = nueva("Lo pesado se calcula una vez al día; en línea solo se lee y se decide en milisegundos", [
    "Capa offline (batch diario): ingesta, features de cliente (segmento, RFM, historial, dolor), candidatos, ranking y carga al feature store.",
    "Capa online: visita web → API Gateway → FastAPI serverless → perfil → candidatos → ranking → reglas → top-K → log de eventos.",
    "Ranking fase 1: puntaje (ventas, entrega, reseñas); fase 2: LightGBM cuando haya eventos web.",
    "El mismo endpoint es una herramienta del Agente de IA del punto 3.",
])
imagen(s, FIGURAS / "arquitectura_2_2.png", 0.5, 1.4, 12.3, 5.5)

# 10. Punto 2.2 (b) --------------------------------------------------------
s = nueva("El recomendador supera a la popularidad y responde en 0,07 ms en el servidor", [
    "Flujo: el cliente entra → se lee su perfil → la estrategia depende del segmento → candidatos → ranking → reglas → top 5 con motivo.",
    "Estrategia: nuevo = populares de su estado; 1 compra = complementaria; fiel = favorita; VIP = premium; en riesgo/mala exp. = entrega confiable.",
    "Evaluado con split temporal en 3 cortes: 49-50% vs 46% de la popularidad.",
    "Serverless (Lambda) escala solo y cuesta cero sin uso; el arranque en frío se mitiga con concurrencia aprovisionada.",
    "Demo en vivo: https://e2ve24fowzbyfyeqmpobgfuyyu0lzuaf.lambda-url.us-east-1.on.aws/",
])
tabla(s, 0.5, 1.5, 6.2, [["Tipo de cliente", "Qué recibe"],
                          ["Nuevo (cold start)", "Lo más vendido en su estado"],
                          ["1 compra", "Categoría complementaria + favorita"],
                          ["Fiel", "Su favorita + complementaria"],
                          ["VIP", "Solo productos premium"],
                          ["En riesgo / mala exp.", "Vendedores con entrega confiable"]],
      [2.3, 3.9], tam=13, alto_fila=0.5)
cifra(s, 7.0, 1.5, 2.8, "0,07 ms", "latencia en el servidor")
cifra(s, 10.0, 1.5, 2.83, "8 ms", "con HTTP (p95 10,6 ms)")
cifra(s, 7.0, 3.05, 5.83, "~50% vs ~46%", "acierto de la siguiente compra vs popularidad (3 cortes)", tam=30)
rect(s, 0.5, 4.75, 12.33, 2.05, RGBColor(0x1C, 0x24, 0x34))
texto(s, 0.7, 4.85, 12.0, 1.9, [
    ("GET /recomendar/{customer_unique_id}?k=5   ·   demo publicado en AWS Lambda", 14, AMARILLO, True),
    ('{"estrategia": "Reactivación: productos con entrega confiable (evita la categoría de su mala experiencia)",', 13, BLANCO, False),
    (' "recomendaciones": [{"categoria": "Cama, mesa y baño", "precio": 194.79, "motivo": "Lo más vendido en RJ"}, …],', 13, BLANCO, False),
    (' "latencia_ms": 0.09}', 13, BLANCO, False),
    ("Flujo: visita → perfil (2.1 + dolor 1.2) → candidatos → ranking → reglas → top 5 · Serverless: escala solo y cuesta $0 sin uso · El Agente de IA usa este endpoint", 13, AZUL_CLARO, True)])

# 11. Punto 2.3 ------------------------------------------------------------
z = zonas.iloc[0]
s = nueva("La tienda insignia va en el centro expandido de São Paulo: 21% de las ventas en 3 km", [
    "São Paulo es la ciudad con más ventas: 14,1% del país, casi el doble que Río.",
    "Se agruparon los prefijos postales con K-Means ponderado por ingresos (k=9 por silhouette).",
    "Zona ganadora: lat -23,554 / lng -46,652 (Paulista / Jardins / Consolação, aprox.).",
    "Robustez: gana con 4 esquemas de pesos y se mueve menos de 4 km con otro número de zonas.",
    "Ojo: esa zona ya recibe rápido (7 días); la tienda es apuesta de marca, no solución logística.",
])
imagen(s, FIGURAS / "2_3_mapa_zonas.png", 0.4, 1.4, 4.6, 5.5)
for i, (v, e) in enumerate([("14,1%", "de las ventas del país en São Paulo"), (f"{z.pct_ingresos_ciudad:.1f}%".replace(".", ","), "de las ventas de la ciudad en la zona"),
                            (f"{int(z.clientes):,}".replace(",", "."), "clientes en la zona"), ("R$ 136", "ticket vs R$ 124 de la ciudad")]):
    cifra(s, 5.2, 1.45 + i * 1.45, 2.9, v, e, tam=28)
panel_derecho(s, [
    f"Zona de {int(z.prefijos)} prefijos y {int(z.pedidos):,} pedidos; la mitad de sus ventas son categorías top del 1.1.".replace(",", "."),
    "Robusta: la misma zona gana con 4 esquemas de pesos.",
    "Ya recibe en 7 días (vs 12 en Brasil): la tienda es apuesta de marca y cercanía al cliente de mayor ticket.",
], "Venta ubicada en la dirección del cliente; coordenadas = mediana por prefijo postal.")

# 12. Punto 3.1 ------------------------------------------------------------
s = nueva("Tres productos reales, con precios reales y nombres inferidos de las reseñas", [
    "Regla: el producto con más ingresos de Belleza y salud, Cama, mesa y baño y Muebles y decoración.",
    "El dataset no trae nombres: las reseñas revelan que son un adipómetro, un juego de toallas y un perchero.",
    "Textos simulados, sin marcas ni especificaciones inventadas; métricas 100% reales (diferencia de precio = 0).",
    "Las quejas reales quedan como nota para el agente: evita prometer de más.",
])
lineas_cortas = ["Mide la grasa corporal como lo hacen nutricionistas y entrenadores.",
                 "Toallas amplias con estampado floral y bordado para el día a día.",
                 "Libera el clóset: ropa a la vista, fácil de armar y de mover."]
for i, (p, linea) in enumerate(zip(kb["productos"], lineas_cortas)):
    x = 0.5 + i * 4.15
    rect(s, x, 1.5, 3.95, 2.9, FONDO)
    texto(s, x + 0.2, 1.6, 3.6, 0.35, p["categoria"]["es"], tam=12, color=GRIS)
    texto(s, x + 0.2, 1.95, 3.6, 0.75, p["nombre_comercial"].replace(" (simulado)", ""), tam=18, color=AZUL, negrita=True)
    texto(s, x + 0.2, 2.7, 3.6, 0.6, f"R$ {p['precio_promedio_real']:.2f}".replace(".", ","), tam=26, color=TEXTO, negrita=True)
    texto(s, x + 0.2, 3.35, 3.6, 1.0, linea, tam=13)
rect(s, 0.5, 4.6, 12.33, 2.2, RGBColor(0x1C, 0x24, 0x34))
p = kb["productos"][2]
texto(s, 0.7, 4.7, 12.0, 2.0, [
    ("agent/knowledge_base.json (fragmento)", 12, AMARILLO, True),
    (f'{{"id": "{p["id"]}", "nombre_comercial": "{p["nombre_comercial"]}",', 13, BLANCO, False),
    (f' "precio_promedio_real": {p["precio_promedio_real"]}, "unidades_vendidas": {p["unidades_vendidas"]}, "pct_entregas_a_tiempo": {p["pct_entregas_a_tiempo"]},', 13, BLANCO, False),
    (f' "nota_para_el_agente": "{p["nota_para_el_agente"]}"}}', 13, BLANCO, False)])

# 13. Punto 3.2 (a) --------------------------------------------------------
s = nueva("Una misma estructura de 8 partes; los datos reales del cliente entran por 5 variables", [
    "Los tres prompts comparten estructura: así el comportamiento es predecible y auditable.",
    "HISTORIAL_COMPRAS es una variable calculada en el 2.1: pedidos, gasto, ticket, favorita, recencia, reseña y mala experiencia con su motivo.",
    "construir_prompt() reemplaza las 5 variables con datos reales del cliente y el JSON del 3.1.",
    "Edad y género vienen del CRM (simulados) y solo ajustan el tono.",
])
partes = ["Rol e identidad", "Contexto (5 variables)", "Objetivo", "Tono y estilo", "Estrategia de recomendación",
          "Guardarraíles", "Formato de respuesta", "Ejemplo de primer mensaje"]
for i, parte in enumerate(partes):
    x, y = 0.5 + (i % 2) * 3.0, 1.5 + (i // 2) * 1.3
    rect(s, x, y, 2.85, 1.1, AZUL if i in (1, 5) else FONDO)
    texto(s, x + 0.15, y + 0.1, 2.55, 0.9, [(f"{i + 1}", 20, AMARILLO if i in (1, 5) else AZUL, True),
                                              (parte, 14, BLANCO if i in (1, 5) else TEXTO, True)])
variables = [("[EDAD] · [GÉNERO]", "CRM (simulado): solo modula el tono"),
             ("[PERFIL_DE_CLIENTE]", "Segmento y subsegmento del 2.1"),
             ("[HISTORIAL_COMPRAS]", "Resumen en texto calculado en el 2.1"),
             ("[BASE_CONOCIMIENTO]", "JSON del 3.1 (compacto)")]
texto(s, 6.8, 1.45, 6.0, 0.4, "Cómo se llenan las variables", tam=16, color=AZUL, negrita=True)
for i, (var, fuente) in enumerate(variables):
    y = 1.95 + i * 0.85
    rect(s, 6.8, y, 6.03, 0.72, FONDO)
    texto(s, 6.95, y + 0.08, 2.6, 0.6, var, tam=14, color=AZUL, negrita=True, ancla=MSO_ANCHOR.MIDDLE)
    texto(s, 9.55, y + 0.08, 3.2, 0.6, fuente, tam=13, ancla=MSO_ANCHOR.MIDDLE)
rect(s, 6.8, 5.45, 6.03, 1.35, RGBColor(0x1C, 0x24, 0x34))
texto(s, 6.95, 5.5, 5.8, 1.3, [("Ejemplo real de [HISTORIAL_COMPRAS]", 12, AMARILLO, True),
      ("1 pedido | gasto total R$44 | categoría favorita: Mascotas | última compra hace 354 días | mala experiencia: sí | motivo: entrega / retraso", 13, BLANCO, False)])

# 14. Punto 3.2 (b) --------------------------------------------------------
s = nueva("Tres personalidades para tres clientes: con quien sufrió un retraso, primero se repara y luego se vende", [
    "Sofi (joven digital): tutea, mensajes cortos, complementarios y llamada a la acción.",
    "Andrés (mayor con mala experiencia): usted, primero disculpa y escucha; luego productos con mayor % a tiempo y nunca el Adipómetro (84,9%).",
    "Valentina (VIP): consultiva, pregunta antes de recomendar y propone cantidades con precios reales.",
    "Guardarraíles comunes: solo productos de la base, sin descuentos inventados, sin estereotipos y con escalamiento humano.",
    "Demo: el chat con Claude en Amazon Bedrock está en /chat del mismo enlace.",
])
tabla(s, 0.5, 1.45, 7.6, [
    ["", "Joven digital", "Mayor con mala exp.", "VIP / corporativo"],
    ["Tono", "Tutea, corto, 1-2 emojis", "Usted, pausado, sin emojis", "Usted, consultivo"],
    ["Objetivo", "Nueva compra hoy", "Recuperar la confianza", "Mayor valor y volumen"],
    ["Estrategia", "Complementar su favorita", "Solo productos que llegan a tiempo", "Diagnóstico y cantidades"],
    ["Extracto", "“¿Te lo dejo en el carrito?”", "“Antes que nada, quiero pedirle disculpas”", "“¿Es para uso personal o para su empresa?”"],
], [1.3, 2.0, 2.15, 2.15], tam=13, alto_fila=0.95)
panel_derecho(s, [
    "Reparar antes de vender: con el cliente del retraso, el primer mensaje es una disculpa.",
    "Datos reales generan confianza: prioriza el % de entregas a tiempo y descarta el Adipómetro (84,9%).",
    "Edad y género solo para el tono: prohibido suponer gustos o estereotipos.",
], "Edad y género simulados (CRM); clientes reales: un Fiel, un Perdido por retraso y un VIP.")

# 15. Insights accionables -------------------------------------------------
s = nueva("", [
    "Cierro traduciendo lo aprendido en Olist a Protección: pensiones, cesantías, ahorro e inversión y PQR.",
    "1) Cumplir la promesa: alertas proactivas antes de que un trámite supere el tiempo prometido.",
    "2) Retención: propensión de abandono/traslado y campañas por segmento.",
    "3) Voz del cliente: clasificar PQR y llamadas por tema y urgencia.",
    "4) Agente con contexto del afiliado para servicio y venta cruzada.",
], oscura=True)
texto(s, 0.5, 0.3, 12.3, 1.0, "Cuatro aprendizajes que Protección puede activar en pensiones, cesantías y atención de PQR",
      tam=28, color=BLANCO, negrita=True, ancla=MSO_ANCHOR.MIDDLE)
tarjetas = [
    ("Cumplir la promesa es el mayor generador de satisfacción", "62% de malas reseñas si llega tarde vs 9% a tiempo",
     "Alertas proactivas antes de que un retiro de cesantías, una pensión o una PQR supere el tiempo prometido.", "% de PQR por demora · NPS"),
    ("La mayoría de clientes no vuelve", "Solo 3% recompra y el 55% ya salió del ciclo",
     "Modelo de propensión de abandono o traslado y retención por segmento (en riesgo, VIP).", "Tasa de traslados · retención por segmento"),
    ("La voz del cliente ya explica los problemas", "El NLP clasificó el 84% de las quejas; 56% hablan de entrega",
     "Speech-to-insights: transcribir llamadas y clasificar PQR por tema y urgencia.", "Tiempo de respuesta · resolución en primer contacto"),
    ("Personalizar el tono cambia la conversación", "Con quien sufrió un retraso, el agente repara antes de vender",
     "Agente de IA con el contexto del afiliado (segmento, historial, PQR) para servicio y venta cruzada.", "Conversión cross-sell · satisfacción post-contacto"),
]
for i, (insight, dato, accion, kpi) in enumerate(tarjetas):
    x, y = 0.5 + (i % 2) * 6.25, 1.45 + (i // 2) * 2.55
    rect(s, x, y, 6.05, 2.35, BLANCO)
    texto(s, x + 0.2, y + 0.1, 5.65, 2.2, [(insight, 16, AZUL, True), (dato, 14, AZUL_OSC, True),
                                           ("Acción: " + accion, 13, TEXTO, False), ("KPI: " + kpi, 12, GRIS, False)])
texto(s, 0.5, 6.55, 12.3, 0.4, "De datos transaccionales a decisiones: diagnosticar → segmentar → activar con IA",
      tam=16, color=AMARILLO, negrita=True, alinear=PP_ALIGN.CENTER)

prs.save(SALIDA)
print(f"Presentación guardada: {SALIDA} · {len(prs.slides)} diapositivas")
