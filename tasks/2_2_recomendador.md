# 2.2 Recomendador en tiempo real
# Tarea 2.2 – Arquitectura y flujo lógico del recomendador en tiempo real

## Enunciado (textual)
Crea la arquitectura y el flujo lógico de un modelo de recomendación automática de productos. Este modelo debe actuar en tiempo real cuando un cliente visita nuestra página web, basándose en su perfil de cliente (obtenido en el punto anterior) y su historial de compras.

## Contexto
- Entregable principal = DISEÑO (arquitectura + flujo). Se complementa con un prototipo ligero para demostrarlo.
- Insumos: `clientes_segmentados.parquet` (2.1), `items_enriquecidos.parquet` (1.1), `clientes_dolor.parquet` / `pedidos_experiencia.parquet` (1.2).
- Realidad de los datos: 97% compra una sola vez → casi todo es cold start o historial de 1 compra. Productos sin nombre (usar product_id + categoría).
- La vacante pide: FastAPI, gestión de latencia, serverless y servicios de IA en la nube.

## Paso 0 – Plan
Presenta un plan de máximo 8 líneas y espera mi aprobación.

- NOTA. Recuerda que todo archivo .py o .ipynb que tengas que crear con condigo debe ser lo mas preciso, sencillo y entendible posible el codigo que va dentro de esos archivos,no te extiendas mucho haciendo el coddigo, halso lo mas simple y corto posible.

## Parte A – Documento de arquitectura (`reports/arquitectura_2_2.md`)
1. **Diagrama en Mermaid** con dos capas:
   - **Offline (batch diario):** ingesta → features de cliente (segmento, RFM, historial, dolor) → generación de candidatos → entrenamiento del modelo de ranking → carga a feature store / cache.
   - **Online (tiempo real):** visita web → API Gateway → servicio FastAPI (serverless) → lectura del perfil en feature store online → candidatos → ranking → reglas de negocio → respuesta top-K → log de eventos.
2. **Flujo lógico paso a paso** (qué ocurre desde que el cliente entra hasta que ve recomendaciones).
3. **Estrategia por tipo de cliente:**
   - Cliente nuevo/anónimo (cold start): populares por estado (UF) y temporada.
   - 1 compra: categorías complementarias (co-ocurrencia de categorías entre clientes).
   - Recomprador/Fiel: afinidad a su categoría favorita + complementarias.
   - VIP: ticket alto y categorías premium.
   - En riesgo / con mala experiencia: priorizar vendedores con buen cumplimiento de entrega y evitar la categoría/vendedor del mal episodio.
4. **Modelo:** generación de candidatos (popularidad por segmento/estado + co-ocurrencia) + ranking con modelo de propensión (ej. LightGBM) con features de cliente, producto y contexto. Explicar qué features y qué target.
5. **Reglas de negocio:** excluir productos ya comprados, diversidad de categorías, disponibilidad.
6. **Requisitos no funcionales:** presupuesto de latencia (< 100 ms p95) desglosado por componente, cache, escalabilidad, fallback si el modelo falla.
7. **Tecnología en nube** (mapeo AWS y GCP): API Gateway + Lambda / Cloud Run; Redis/DynamoDB/Firestore como feature store online; SageMaker / Vertex AI para entrenamiento; orquestación batch.
8. **Evaluación y monitoreo:** offline (hit rate@K, NDCG vs baseline de popularidad), online (A/B test, CTR, conversión, ticket), drift y reentrenamiento.
9. **Conexión con el Agente de IA (punto 3):** el mismo endpoint alimenta al agente como herramienta.

## Parte B – Prototipo ligero
1. `src/recommender.py`: precomputar tablas (populares por UF y segmento, matriz de co-ocurrencia de categorías, mejores productos por categoría según ventas y buena reputación de entrega). Función `recomendar(customer_unique_id, k=5)` que aplique la estrategia según el segmento y devuelva product_id, categoría (es), precio promedio y **motivo** de la recomendación.
2. `api/main.py` (FastAPI): `GET /recomendar/{customer_unique_id}?k=5` y `GET /health`. Cargar artefactos al iniciar (no por request). Devolver `latencia_ms` en la respuesta. Cliente desconocido → cold start.
3. Evaluación offline simple: split temporal en recompradores (última compra = test) → hit rate@5 a nivel categoría vs baseline de popularidad. Ser honesto con el tamaño de muestra.
4. Documentar en README cómo correrlo (`uvicorn api.main:app --reload`).

## Entregables
- `reports/arquitectura_2_2.md` (con Mermaid) y `reports/figures/arquitectura_2_2.png` si es posible exportarlo.
- `src/recommender.py`, `api/main.py`, artefactos en `data/processed/`.

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
- El endpoint responde para: 1 cliente fiel, 1 VIP, 1 esporádico, 1 en riesgo y 1 id inexistente (mostrar las 5 respuestas resumidas).
- Latencia promedio medida sobre 100 requests.
- Ningún producto recomendado fue comprado antes por ese cliente.

## Salida final en el chat
Máximo 5 líneas: componentes clave, latencia medida y resultado de la evaluación offline. Registrar supuestos en SUPUESTOS.md.