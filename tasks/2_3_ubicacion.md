# 2.3 Ubicación centro comercial insignia
# Tarea 2.3 – Ubicación de la tienda física insignia

## Enunciado (textual)
La dirección de la empresa desea dar el salto al mundo físico y necesita saber cuál es el mejor punto de la ciudad con mayores ventas para ubicar un centro comercial insignia que ofrezca nuestros mejores productos.

## Contexto del EDA (ya validado)
- SP concentra ~42% de los clientes.
- `geolocation`: 1.000.163 filas, 261.831 duplicadas, 19.015 prefijos únicos con muchas coordenadas cada uno → agregar por prefijo (mediana de lat/lng) antes de unir.
- 0,28% de prefijos de clientes no están en geolocation.
- Los nombres de ciudad pueden venir con/sin tildes o mayúsculas → normalizar.
- Insumos: `items_enriquecidos.parquet` y `ranking_categorias.parquet` (1.1).

## Paso 0 – Plan
Presenta un plan de máximo 8 líneas y espera mi aprobación.

## Decisiones analíticas (registrar en SUPUESTOS.md)
1. **Ventas:** ingresos = suma de `price` en pedidos válidos (mismo criterio que 1.1). Reportar también n° pedidos y n° clientes.
2. **Ubicación de la venta:** la dirección del CLIENTE (demanda), no del vendedor.
3. **"Mejores productos":** top categorías del 1.1; la zona elegida debe tener alta demanda de esas categorías.
4. Prefijo postal = 5 dígitos (unidad geográfica más fina disponible). No hay barrios en los datos: cualquier nombre de barrio se marca como aproximado.

## Pasos
1. **Nivel ciudad:** ranking de ciudades por ingresos, pedidos y clientes (normalizar nombres + estado). Confirmar la ciudad con mayores ventas.
2. **Nivel zona dentro de esa ciudad:**
   - Geolocalización agregada por prefijo (mediana lat/lng, filtrar coordenadas fuera de Brasil/fuera de la ciudad).
   - Métricas por prefijo: ingresos, pedidos, clientes, ticket promedio, % ingresos en top categorías, score promedio.
   - Clustering espacial ponderado por ingresos (K-Means ponderado o DBSCAN sobre lat/lng) para encontrar la zona de mayor concentración de ventas.
3. **Puntaje de ubicación** por cluster/zona: combinación documentada de ingresos (peso principal), clientes, ticket promedio y demanda de top categorías. Mostrar sensibilidad si cambian los pesos.
4. **Recomendación final:** coordenadas del centroide ponderado de la mejor zona, prefijos postales que cubre, % de ingresos de la ciudad que concentra y top categorías de la zona.
5. Complemento: ¿cuánto ahorraría en flete/tiempo de entrega esa zona? (flete y retraso promedio actuales de sus clientes).
6. Agregar sección 2.3 al notebook 02.

## Entregables
- `src/ubicacion.py`
- `reports/tables/2_3_ranking_ciudades.csv`, `reports/tables/2_3_zonas.csv`
- `reports/figures/2_3_top_ciudades.png`, `reports/figures/2_3_mapa_zonas.png` (scatter lat/lng con tamaño = ingresos y color = cluster; marcar el punto recomendado). Si se agrega folium, guardar además `reports/figures/2_3_mapa.html` y añadir folium a requirements.txt.

## Validación (checklist ✅/❌)
- Geolocalización: 1 fila por prefijo tras agregar.
- Filas antes/después de unir clientes con geolocalización; % de clientes sin coordenadas.
- Suma de ingresos por prefijo de la ciudad = ingresos totales de la ciudad.

## Salida final en el chat
Máximo 5 líneas: ciudad, zona/coordenadas recomendadas, % de ventas que concentra y justificación. Registrar supuestos en SUPUESTOS.md.
