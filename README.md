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

## Resultados
