# Prueba Técnica Protección – Científico de Datos IA (PQR)

## Contexto

## Estructura

## Cómo reproducir

### Recomendador en tiempo real (punto 2.2)

1. Generar los artefactos: ejecutar `notebooks/02_punto2_segmentacion_ubicacion.ipynb`, que crea `data/processed/recomendador.json.gz`.
2. Levantar la API desde la raíz del repo:

   ```bash
   uvicorn api.main:app --reload
   ```

3. Abrir:
   - http://127.0.0.1:8000 → página de demo (clientes de ejemplo por segmento, búsqueda por ID y visitante nuevo).
   - http://127.0.0.1:8000/docs → documentación interactiva de la API.
   - `GET /recomendar/{customer_unique_id}?k=5` → recomendaciones en JSON con `latencia_ms`. Un ID desconocido recibe populares de su estado (`?uf=SP`).
   - `GET /health` → estado del servicio.

Tip: `http://127.0.0.1:8000/?cliente=<customer_unique_id>` abre la demo directamente con ese cliente.

Diseño completo: `reports/arquitectura_2_2.md`.

### Agente de IA (punto 3)

- Base de conocimiento: `agent/knowledge_base.json` (generada por `src/knowledge_base.py`).
- System prompts: `agent/prompts/` (plantillas) y `agent/prompts/ejemplos/` (llenos con clientes reales), generados con `notebooks/03_punto3_agente.ipynb`.
- Chat: con la API levantada, abrir http://127.0.0.1:8000/chat. Usa Claude en Amazon Bedrock, así que requiere credenciales de AWS con permiso `bedrock:InvokeModel`.

### Demo publicado (AWS Lambda)

- Recomendador: https://e2ve24fowzbyfyeqmpobgfuyyu0lzuaf.lambda-url.us-east-1.on.aws/
- Agente de IA: https://e2ve24fowzbyfyeqmpobgfuyyu0lzuaf.lambda-url.us-east-1.on.aws/chat

## Resultados
