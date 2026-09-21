# 2.1 Segmentación de clientes
# Tarea 2.1 – Segmentación de clientes

## Enunciado (textual)
Diseña y ejecuta una segmentación de clientes que permita a nuestro equipo de marketing distinguir claramente a los "clientes fieles" de los compradores esporádicos o en riesgo de abandono.

## Contexto del EDA (ya validado)
- Cliente real = `customer_unique_id` (96.096). Solo 2.997 (~3%) compraron más de una vez.
- Periodo sep-2016 a oct-2018; los meses de los extremos están casi vacíos.
- Monto: usar `payment_value` agregado POR PEDIDO (incluye flete) o `price` desde items; nunca unir items con pagos.
- Insumos previos: `data/processed/clientes_dolor.parquet` (1.2), `items_enriquecidos.parquet` (1.1).

## Paso 0 – Plan
Presenta un plan de máximo 8 líneas y espera mi aprobación.

## Decisiones analíticas (registrar en SUPUESTOS.md)
1. **Pedidos incluidos:** excluir `canceled` y `unavailable`.
2. **Ventana y fecha de referencia:** detectar meses incompletos al final de la serie (pedidos < 10% del promedio mensual), recortarlos y usar como fecha de referencia el día siguiente a la última compra dentro de la ventana. Documentar.
3. **RFM a nivel `customer_unique_id`:** Recencia (días desde última compra), Frecuencia (pedidos distintos), Monetario (gasto total).
4. **Problema clave:** con 97% de compradores únicos, la Frecuencia casi no discrimina. La segmentación NO puede depender solo de F.

## Pasos
1. Construir tabla de clientes con: recencia, frecuencia, gasto total, ticket promedio, n° categorías distintas, categoría favorita, score promedio de reseñas, `tuvo_mala_experiencia`, método de pago preferido, cuotas promedio, estado (UF).
2. **Umbral de "riesgo de abandono" basado en datos:** en los recompradores, calcular días entre compras; usar un percentil (ej. p75 o p80) como umbral de recencia para considerar que un cliente "debería haber vuelto". Documentar el valor.
3. **Enfoque A – Reglas RFM de negocio (interpretables):** segmentos mínimos:
   - **Fieles:** frecuencia ≥ 2 y recencia ≤ umbral.
   - **VIP / Alto valor:** gasto en el top (ej. p90), cualquier frecuencia.
   - **Esporádicos recientes:** 1 compra, recencia ≤ umbral.
   - **En riesgo de abandono:** recencia > umbral (incluir sub-grupo recompradores inactivos y 1 compra con mala experiencia).
   - **Perdidos / Inactivos:** recencia muy alta (ej. > p90).
   Ajustar si los datos lo justifican; los segmentos deben ser mutuamente excluyentes con un orden de prioridad explícito.
4. **Enfoque B – K-Means** sobre variables transformadas (log de monetario, recencia escalada, frecuencia, score promedio). Elegir k con codo + silhouette (sobre muestra si es costoso). Perfilar cada cluster.
5. **Comparar A vs B** (tabla de cruce) y elegir uno para marketing, justificando interpretabilidad, tamaño de segmentos y accionabilidad.
6. Perfil por segmento: n° clientes, % clientes, % ingresos, recencia/frecuencia/gasto medianos, score promedio, % mala experiencia, top categorías.
7. Acción de marketing sugerida por segmento (1 línea cada una).
8. Crear variable **HISTORIAL_COMPRAS** por cliente (texto resumen para el agente del 3.2), ej.: "3 pedidos | gasto total R$540 | ticket prom. R$180 | categoría favorita: salud y belleza | última compra hace 45 días | score prom. 4,7 | mala experiencia: no".
9. al final del notebookc dame una conclusion d elo que encontraste con RFM y con K-Means y explicame que podemos aporvechar del uno y del otro para la sustentacion.
10. Crear `notebooks/02_punto2_segmentacion_ubicacion.ipynb` (sección 2.1).
11. Recuerda que todo archivo .py o .ipynb que tengas que crear con condigo debe ser lo mas preciso, sencillo y entendible posible el codigo que va dentro de esos archivos,no te extiendas mucho haciendo el coddigo, halso lo mas simple y corto posible

## Entregables
- `src/segmentation.py` (RFM, reglas, K-Means, perfilado) y funciones de historial en `src/features.py`.
- `data/processed/clientes_segmentados.parquet` (incluye segmento, variables RFM e `historial_compras`).
- `reports/tables/2_1_perfil_segmentos.csv`
- Figuras: tamaño e ingresos por segmento, distribución de días entre compras con el umbral, scatter recencia vs gasto por segmento, silhouette/codo.

## Registro de resultados
Al terminar la tarea, reemplaza el texto "_Pendiente_" de la sección "## Punto X.X" en reports/RESULTADOS.md con:
- **Pregunta:** (copiar textual del enunciado en PRUEBA_TECNICA.md)
- **Respuesta directa:** 2-4 líneas con cifras clave
- **Método:** 1 línea
- **hallazgo principal:**2-4 líneas escribir los hallazgos mas importante que encontraste en esa tarea, es util para la sustentacion.
- **descripcion de los pasos:**en 5 paso muy breves de solo texto y de una linea cada uno me das una breve descripcion de la solucion que le diste a este punto.
- **Archivos de soporte:** rutas de tablas y figuras generadas

No modifiques secciones de otros puntos ni el resto del archivo.

## Validación (checklist ✅/❌)
- N° clientes en la tabla = `customer_unique_id` únicos con pedidos válidos.
- Suma de clientes por segmento = total (sin duplicados ni clientes sin segmento).
- Suma del gasto por segmento = gasto total de pedidos válidos.
- Recencia sin negativos.

## Salida final en el chat
Máximo 5 líneas: enfoque elegido, segmentos con su % de clientes y % de ingresos, y el umbral de riesgo. Registrar supuestos en SUPUESTOS.md.

