# 1.2 Dolor de clientes
# Tarea 1.2 – Mayor dolor del cliente y categorías asociadas

## Enunciado (textual)
¿Cuál es el mayor dolor de nuestros clientes y qué productos o categorías están directamente relacionados con estas malas experiencias?

## Contexto del EDA (ya validado)
- `order_reviews`: 99.224 filas. Score: 5★ 57,8%, 4★ 19,3%, 1★ 11,5%.
- Título nulo 88%, mensaje nulo 59% (esperado). Comentarios en PORTUGUÉS.
- 814 `review_id` y 551 `order_id` repetidos en reseñas → deduplicar antes de unir.
- `orders`: fechas de entrega real (`order_delivered_customer_date`) y estimada (`order_estimated_delivery_date`); 2.965 pedidos sin fecha de entrega.
- Reutilizar `src/data_loader.py` y `data/processed/items_enriquecidos.parquet` de la tarea 1.1.

## Paso 0 – Plan
Presenta un plan de máximo 8 líneas y espera mi aprobación.

## Decisiones analíticas (registrar en SUPUESTOS.md)
1. **Mala experiencia:** `review_score <= 2`. Neutral = 3. Buena = 4-5.
2. **Reseñas duplicadas:** 1 reseña por pedido; si hay varias, conservar la más reciente (`review_answer_timestamp`).
3. **Pedidos incluidos:** todos los estados. Los cancelados/no disponibles son parte del dolor; analizarlos como grupo aparte.
4. **Retraso:** `retraso_dias = entrega_real - entrega_estimada` (días). `tarde = retraso_dias > 0`. Solo aplica a pedidos con fecha de entrega.
5. **Umbral para rankings por categoría:** solo categorías con ≥ 300 pedidos (evita tasas infladas por muestras pequeñas). Documentar el umbral.

## Pasos
1. Construir tabla a nivel pedido: pedido + reseña deduplicada + retraso + tiempo total de entrega + estado + flete/precio (agregado por pedido) + estado del cliente.
2. **Cuantificar posibles dolores** (comparar tasa de mala experiencia y score promedio):
   - Entrega tarde vs a tiempo (y por rangos de retraso: 0, 1-3, 4-7, 8-14, >14 días).
   - Pedido no entregado / cancelado / no disponible.
   - Tiempo total de entrega largo (aunque llegue a tiempo).
   - Flete alto relativo al precio (`freight_value / price`).
   - Pedidos con varios vendedores o varios ítems.
3. **Análisis de texto (NLP) de comentarios con score ≤ 2:**
   - Limpieza básica en portugués (minúsculas, sin tildes, stopwords en portugués).
   - Top unigramas y bigramas (TF-IDF o conteos) de malas vs buenas reseñas.
   - Clasificación por temas con diccionario de palabras clave (regex) en portugués: entrega/retraso (atraso, não recebi, não chegou, prazo, entrega), producto defectuoso/calidad (defeito, quebrado, qualidade, ruim), producto errado/incompleto (errado, diferente, faltando, incompleto), atención/vendedor (atendimento, resposta, contato), reembolso/cancelación (reembolso, estorno, cancelar, devolução). Un comentario puede tener varios temas.
   - Reportar % de comentarios negativos por tema y 3 ejemplos cortos por tema (máx. 15 palabras cada uno, traducidos al español).
4. **Conclusión del mayor dolor:** el dolor con mayor impacto = (% de malas experiencias que explica) × (volumen afectado). Sustentar con números.
5. **Categorías relacionadas:** por categoría calcular pedidos, % mala experiencia, % entregas tarde, retraso promedio, score promedio, y **impacto** = número de malas experiencias. Rankear por tasa y por impacto; separar categorías con problema de logística vs de producto (según temas del NLP).
6. Complemento: estados (UF) con mayor % de entregas tarde.
7. Guardar a nivel cliente (`customer_unique_id`): `tuvo_mala_experiencia`, `motivo_principal` (tema/retraso), `max_retraso_dias`. Lo usan los puntos 2.1 y 3.2.
8. Agregar sección 1.2 al notebook 01.

## Entregables
- `src/features.py` con funciones de construcción de la tabla de pedidos y del retraso.
- `src/nlp_resenas.py` con limpieza y clasificación por temas.
- `data/processed/pedidos_experiencia.parquet`, `data/processed/clientes_dolor.parquet`
- `reports/tables/1_2_dolores.csv`, `reports/tables/1_2_categorias_dolor.csv`
- Figuras: score vs rango de retraso, temas de quejas, top categorías por impacto.

## Validación (checklist ✅/❌)
- Reseñas: filas antes/después de deduplicar; 1 reseña por pedido.
- Pedidos sin fecha de entrega excluidos solo del cálculo de retraso (reportar cuántos).
- Suma de malas experiencias por categoría coherente con el total (explicar si un pedido multi-categoría cuenta más de una vez).
- % de comentarios negativos clasificados en al menos un tema.

## Salida final en el chat
Máximo 5 líneas: mayor dolor con su cifra clave y top 3 categorías asociadas. Registrar supuestos en SUPUESTOS.md.

## Registro de resultados
Al terminar la tarea, reemplaza el texto "_Pendiente_" de la sección "## Punto X.X" en reports/RESULTADOS.md con:
- **Pregunta:** (copiar textual del enunciado en PRUEBA_TECNICA.md)
- **Respuesta directa:** 2-4 líneas con cifras clave
- **Método:** 1 línea
- **hallazgo principal:**2-4 líneas escribir los hallazgos mas importante que encontraste en esa tarea, es util para la sustentacion.
- **Archivos de soporte:** rutas de tablas y figuras generadas


No modifiques secciones de otros puntos ni el resto del archivo.