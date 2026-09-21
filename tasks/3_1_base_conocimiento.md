# 3.1 Base de conocimiento
# Tarea 3.1 – Base de conocimiento simulada (JSON)

## Enunciado (textual)
A partir de los productos más vendidos identificados en el punto 1.1, construye una pequeña base de conocimientos simulada (en formato JSON o diccionario de Python). Debes redactar descripciones atractivas para 3 de estos productos e incluir sus precios reales promedio extraídos del dataset.

## Contexto
- Insumos: `ranking_categorias.parquet`, `items_enriquecidos.parquet` (1.1), `pedidos_experiencia.parquet` (1.2), `clientes_segmentados.parquet` (2.1).
- Los productos NO tienen nombre en el dataset → el nombre comercial es simulado (marcarlo como tal).
- Esta base la consumen los system prompts del 3.2 como [BASE_CONOCIMIENTO].

## Paso 0 – Plan
Presenta un plan de máximo 8 líneas y espera mi aprobación.

- NOTA. que el texto de esos productos sea muy humano y que sea creativo pero que no sea demaciado largo, recuerda que es para la sustentacion.

## Decisiones (registrar en SUPUESTOS.md)
1. Seleccionar 3 productos (`product_id`) más vendidos pertenecientes a las categorías top del 1.1, priorizando que sean de 3 categorías distintas (variedad para el agente). Justificar la selección.
2. **Precio real promedio** = media de `price` de ese product_id en pedidos válidos. Reportar también mediana y rango p25-p75.
3. Descripciones en español, atractivas y comerciales (2-3 frases), sin inventar especificaciones técnicas verificables (marca, modelo, garantía). Todo dato inventado se marca como simulado.

## Estructura JSON por producto
- `id` (product_id real), `nombre_comercial` (simulado), `categoria` (es / en / pt)
- `descripcion` (atractiva), `beneficios_clave` (3 viñetas cortas)
- `precio_promedio_real` (BRL, 2 decimales), `precio_mediano`, `rango_precio_p25_p75`
- `flete_promedio`, `unidades_vendidas`, `score_promedio_resenas`
- `tiempo_entrega_promedio_dias`, `pct_entregas_a_tiempo` (del 1.2; útil para cliente con mala experiencia)
- `segmentos_objetivo` (del 2.1: qué segmentos compran más esa categoría)
- `argumentos_venta_por_perfil` (joven digital / conservador / VIP, 1 frase cada uno)
- Metadatos globales: `moneda`, `fuente`, `fecha_generacion`, `nota` ("descripciones y nombres simulados; precios y métricas reales del dataset Olist").

## Pasos
1. `src/knowledge_base.py`: calcula métricas reales desde los datos y ensambla el JSON (descripciones como textos definidos en el script) → reproducible.
2. Guardar `agent/knowledge_base.json` (UTF-8, indentado, `ensure_ascii=False`).
3. Agregar sección 3.1 al notebook `03_punto3_agente.ipynb` mostrando el JSON y una tabla resumen.

## Registro de resultados
Al terminar la tarea, reemplaza el texto "_Pendiente_" de la sección "## Punto X.X" en reports/RESULTADOS.md con:
- **Pregunta:** (copiar textual del enunciado en PRUEBA_TECNICA.md)
- **Respuesta directa:** 2-4 líneas con cifras clave
- **Método:** 1 línea
- **hallazgo principal:**2-4 líneas escribir los hallazgos mas importante que encontraste en esa tarea, es util para la sustentacion.
- **descripcion de los pasos:**en 5 paso muy breves de solo texto y de una linea cada uno me das una breve descripcion de la solucion que le diste a este punto.
- **Archivos de soporte:** rutas de tablas y figuras generadas

## Validación (checklist ✅/❌)
- Los 3 product_id existen y están dentro de categorías top del 1.1.
- `precio_promedio_real` recalculado independientemente coincide (diferencia 0).
- JSON válido (json.load sin error) y con las 3 entradas completas.

## Salida final en el chat
Máximo 5 líneas: 3 productos elegidos, su categoría y precio promedio real.