# 1.1 Top productos (volumen e ingresos)

# Tarea 1.1 – Top 5 categorías/productos por volumen y por ingresos

## Enunciado (textual)
¿Cuáles son los 5 productos (o categorías de productos) más vendidos en términos de volumen y cuáles en términos de ingresos totales?

## Contexto del EDA (ya validado)
- `order_items`: 112.650 filas; 1 fila = 1 unidad vendida. Es la fuente de volumen e ingresos.
- `products` no tiene nombre de producto → el análisis principal es por CATEGORÍA (73 categorías).
- 610 productos sin categoría. Faltan 2 traducciones: `pc_gamer` y `portateis_cozinha_e_preparadores_de_alimentos`.
- `orders`: 97% delivered; fechas vienen como texto.
- `payment_value` incluye flete (≈R$16,0M) vs `price` (≈R$13,6M). NO unir items con payments.

## Paso 0 – Plan
Antes de escribir código, presenta un plan de máximo 8 líneas y espera mi aprobación.

## Decisiones analíticas (usar estas; registrar en SUPUESTOS.md)
1. **Pedidos válidos:** principal = `order_status == 'delivered'`. Sensibilidad: todos excepto `canceled` y `unavailable`. Reportar si el top 5 cambia entre ambos.
2. **Volumen:** unidades vendidas = número de filas de `order_items`. Reportar además pedidos distintos (`order_id` único) como métrica secundaria.
3. **Ingresos:** suma de `price` (ingreso por producto, sin flete). Reportar `price + freight_value` como sensibilidad.
4. **Categorías:** traducir a inglés con la tabla de traducción; completar manualmente las 2 faltantes (`pc_gamer` → `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos` → `portable_kitchen_food_preparers`). Agregar columna con nombre en español para la presentación. Productos sin categoría → `sin_categoria`: se excluyen del ranking pero se reporta su peso (% unidades e ingresos).
5. **Complemento a nivel producto:** top 5 `product_id` por volumen y por ingresos, con su categoría y precio promedio (útil para el punto 3.1).

## Pasos
1. Crear `src/data_loader.py` (reutilizable en todas las tareas):
   - `cargar_datos()` → dict con nombres en español: pedidos, clientes, items_pedido, pagos, resenas, productos, vendedores, geolocalizacion, traduccion_categorias.
   - Conversión de todas las columnas de fecha a datetime.
   - `traducir_categorias(productos, traduccion)` con las 2 traducciones manuales.
   - `construir_items_enriquecidos(dfs, estados_validos)` → items + estado/fecha del pedido + categoría (pt/en/es). Validar filas antes/después de cada merge.
2. Guardar `data/processed/items_enriquecidos.parquet`.
3. Calcular por categoría: unidades, pedidos distintos, ingresos (price), ingresos con flete, precio promedio, % participación y % acumulado.
4. Generar top 5 por volumen y top 5 por ingresos (escenario principal y sensibilidad).
5. Identificar categorías que están en un top y no en el otro (ej. alto volumen/bajo ticket vs bajo volumen/alto ticket) y explicarlo con el precio promedio.
6. Top 5 `product_id` por volumen y por ingresos.
7. Crear `notebooks/01_punto1_diagnostico.ipynb` (sección 1.1) que importe desde `src/`, con narrativa corta en markdown y gráficos.

## Entregables
- `src/data_loader.py`
- `data/processed/items_enriquecidos.parquet`
- `data/processed/ranking_categorias.parquet` (todas las categorías con sus métricas; lo usa el punto 3.1)
- `reports/tables/1_1_top5_volumen.csv`, `reports/tables/1_1_top5_ingresos.csv`
- `reports/figures/1_1_top5_volumen.png`, `reports/figures/1_1_top5_ingresos.png` (barras horizontales, etiquetas con valor y %, títulos en español)
- Sección 1.1 en el notebook 01.

## Validación (imprimir checklist ✅/❌)
- Filas de items antes y después de cada merge (deben ser iguales).
- Suma de unidades por categoría = total de filas de items filtrados.
- Suma de ingresos por categoría = `items_pedido.price` filtrado (diferencia = 0).
- Total de `price` sin filtro ≈ R$13,6M.
- % de unidades e ingresos en `sin_categoria`.

## Salida final en el chat
Máximo 5 líneas: top 5 por volumen, top 5 por ingresos y el hallazgo principal. Registrar supuestos en SUPUESTOS.md.


## Registro de resultados
Al terminar la tarea, reemplaza el texto "_Pendiente_" de la sección "## Punto X.X" en reports/RESULTADOS.md con:
- **Pregunta:** (copiar textual del enunciado en PRUEBA_TECNICA.md)
- **Respuesta directa:** 2-4 líneas con cifras clave
- **Método:** 1 línea
- **hallazgo principal:**2-4 líneas escribir los hallazgos mas importante que encontraste en esa tarea, es util para la sustentacion.
- **Archivos de soporte:** rutas de tablas y figuras generadas


No modifiques secciones de otros puntos ni el resto del archivo.