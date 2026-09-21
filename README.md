# Prueba Técnica · Protección
### Científico de Datos para soluciones con IA – Equipo Atención de PQR

Solución de punta a punta sobre el e-commerce **Olist** (Brasil, ~100 mil pedidos, 2016-2018), tratado como si fuera "nuestra empresa". El trabajo sigue un hilo conductor: cada punto usa los resultados del anterior.

```
1. Diagnóstico            →  2. Inteligencia de clientes        →  3. Activación con IA
   ¿Qué se vende?             Segmentación (fieles, VIP, riesgo)     Base de conocimiento
   ¿Cuál es el mayor dolor?   Recomendador en tiempo real            System prompts personalizados
                              Ubicación de la tienda física          Agente conversacional
```

**En este repositorio encontrarás:** el código reproducible de cada punto, los notebooks con la narrativa y los resultados, la base de conocimiento y los system prompts del agente, y dos **demos publicados en AWS** que se pueden probar desde el navegador.

---

## 🚀 Demos en vivo (desplegados en AWS)

Los dos demos corren en **AWS Lambda** (serverless) con una URL pública, construidos con **FastAPI**. El agente usa **Claude en Amazon Bedrock**.

| Demo | Enlace | Qué vas a encontrar |
|---|---|---|
| **Recomendador en tiempo real** (punto 2.2) | https://e2ve24fowzbyfyeqmpobgfuyyu0lzuaf.lambda-url.us-east-1.on.aws/ | Eliges un cliente real (uno por segmento), buscas cualquier `customer_unique_id` o simulas un visitante nuevo. Ves su perfil (segmento, gasto, última compra, ubicación y si tuvo una mala experiencia), la estrategia aplicada, el top 5 de productos con el **motivo** de cada recomendación y la latencia. |
| **Agente de IA hiper-personalizado** (punto 3.2) | https://e2ve24fowzbyfyeqmpobgfuyyu0lzuaf.lambda-url.us-east-1.on.aws/chat | Un chat con tres clientes reales: joven digital, mayor con mala experiencia y VIP. El agente cambia de tono y de estrategia según el cliente: Sofi tutea y va al grano, Andrés se disculpa antes de vender y Valentina asesora como ejecutiva de cuenta. |
| Documentación de la API | https://e2ve24fowzbyfyeqmpobgfuyyu0lzuaf.lambda-url.us-east-1.on.aws/docs | Swagger interactivo: `GET /recomendar/{customer_unique_id}`, `GET /health`, `POST /api/chat`. |

> La primera visita después de un rato sin uso tarda unos segundos en arrancar (arranque en frío de Lambda); después responde en milisegundos. El chat tarda ~4 s por respuesta, que es el tiempo del modelo.
>
> Son prototipos de una prueba técnica, no servicios oficiales de Protección.

**Clientes para probar el recomendador:**

| Segmento | `customer_unique_id` |
|---|---|
| Fiel | `56e80e4b4a777631c5399e3fd0d6ee85` |
| VIP / Alto valor | `1573fa36d8bf101af8300e86e78fecbf` |
| Esporádico reciente | `b8ad8f9df8b6c2af329e1fd23cc77061` |
| En riesgo con mala experiencia | `6a3a1de50e1fc7374c2156d4c022f849` |
| Perdido / Inactivo | `b1770db9129bacc8c377c98a1ab14c73` |

Cualquier otro de los 94.990 clientes también funciona, y un ID desconocido se trata como cliente nuevo.

---

## 🗺️ Dónde está la solución de cada punto

| Punto | Pregunta | Notebook | Código | Resultado clave |
|---|---|---|---|---|
| **1.1** | Top 5 por volumen e ingresos | `notebooks/01_punto1_diagnostico.ipynb` | `src/features.py` | Cama, mesa y baño lidera en volumen; Belleza y salud, en ingresos |
| **1.2** | Mayor dolor del cliente | `notebooks/01_punto1_diagnostico.ipynb` | `src/features.py`, `src/nlp_resenas.py` | La **entrega tarde**: 62% de malas reseñas frente a 9% a tiempo |
| **2.1** | Segmentación de clientes | `notebooks/02_punto2_segmentacion_ubicacion.ipynb` | `src/segmentation.py` | 5 segmentos RFM; el 9,6% (VIP) genera el 36,9% de los ingresos |
| **2.2** | Recomendador en tiempo real | `notebooks/02_punto2_segmentacion_ubicacion.ipynb` | `src/recommender.py`, `api/` | Arquitectura offline/online; supera a la popularidad (~50% vs ~46%) |
| **2.3** | Ubicación de la tienda física | `notebooks/02_punto2_segmentacion_ubicacion.ipynb` | `src/ubicacion.py` | São Paulo, centro expandido: 20,6% de las ventas de la ciudad |
| **3.1** | Base de conocimiento | `notebooks/03_punto3_agente.ipynb` | `src/knowledge_base.py` | `agent/knowledge_base.json` con 3 productos y precios reales |
| **3.2** | System prompts | `notebooks/03_punto3_agente.ipynb` | `src/agent_context.py` | `agent/prompts/` (plantillas) y `agent/prompts/ejemplos/` (llenos) |

Los supuestos de cada punto están en `SUPUESTOS.md`.

---

## 📁 Estructura del proyecto

```
├── notebooks/            Narrativa, gráficos y validaciones de cada punto
│   ├── 01_punto1_diagnostico.ipynb
│   ├── 02_punto2_segmentacion_ubicacion.ipynb
│   └── 03_punto3_agente.ipynb
├── src/                  Lógica reutilizable (los notebooks solo la llaman)
│   ├── data_loader.py        Carga de los CSV y traducción de categorías
│   ├── features.py           Rankings (1.1), dolor del cliente (1.2) e historial (2.1)
│   ├── nlp_resenas.py        Clasificación de quejas en portugués (1.2)
│   ├── segmentation.py       RFM, reglas de negocio y K-Means (2.1)
│   ├── recommender.py        Recomendador: capa offline y capa online (2.2)
│   ├── ubicacion.py          Geolocalización y zonas de venta (2.3)
│   ├── knowledge_base.py     Base de conocimiento (3.1)
│   ├── agent_context.py      Llenado de los system prompts (3.2)
│   └── utils.py              Gráficos, formatos y checklist de validación
├── api/                  Aplicación FastAPI de los demos
│   ├── main.py               Endpoints del recomendador y del chat
│   ├── lambda_handler.py     Adaptador para AWS Lambda (Mangum)
│   └── static/               Páginas del recomendador (index.html) y del chat (chat.html)
├── agent/                Activación con IA
│   ├── knowledge_base.json   Base de conocimiento (3.1)
│   └── prompts/              3 system prompts y ejemplos llenos (3.2)
├── data/                 raw/ (CSV de Kaggle, no se suben) y processed/ (parquet intermedios)
├── reports/              Figuras y tablas que generan los notebooks
├── tasks/                Instrucciones de trabajo de cada punto
├── SUPUESTOS.md          Supuestos y decisiones de cada punto
└── requirements.txt
```

---

## ✨ Extras: más allá de lo que pedía la prueba

### Recomendador funcional en tiempo real (punto 2.2)
La prueba pedía la arquitectura y el flujo lógico; además se construyó y se publicó un prototipo funcional:
- **Dos capas:** una offline (batch diario) precalcula perfiles, candidatos y puntajes, y una online solo lee esas tablas. Responde en **~0,1 ms en el servidor** (objetivo: < 100 ms).
- **Estrategia por segmento:** favorita + categoría complementaria + tendencia de su estado; el VIP ve solo productos premium, y quien tuvo una mala experiencia no vuelve a ver esa categoría y solo recibe vendedores con entrega confiable.
- **Evaluado con datos:** con un split temporal en 3 cortes acierta la siguiente compra en ~50% de los casos, frente a ~46% de recomendar lo más vendido.

### Agente de IA conversacional (punto 3.2)
La prueba pedía los system prompts; además se conectaron a un modelo real:
- **Claude Sonnet 4.6 en Amazon Bedrock**, con los prompts llenos con datos reales de cada cliente.
- **Guardarraíles:** solo recomienda productos de la base de conocimiento, no inventa precios ni descuentos, usa la edad y el género solo para el tono y escala a un asesor humano ante quejas.
- **Aprende de las reseñas:** la base de conocimiento incluye las quejas reales de cada producto para que el agente no prometa de más.

---

## ⚙️ Cómo reproducirlo

1. Descargar el dataset de [Kaggle – Brazilian E-Commerce (Olist)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) y copiar los 9 CSV en `data/raw/`.
2. Instalar dependencias (Python 3.11):
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar los notebooks en orden: `01` → `02` → `03`. Generan los parquet de `data/processed/`, las figuras de `reports/`, la base de conocimiento y los prompts.
4. Levantar los demos en local desde la raíz del repo:
   ```bash
   uvicorn api.main:app --reload
   ```
   - http://127.0.0.1:8000 → recomendador
   - http://127.0.0.1:8000/chat → agente de IA (requiere credenciales de AWS con permiso `bedrock:InvokeModel`)
   - http://127.0.0.1:8000/docs → documentación de la API

**Stack:** Python 3.11 · pandas · scikit-learn · FastAPI · AWS Lambda · Amazon Bedrock (Claude).
