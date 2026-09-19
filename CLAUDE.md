# CLAUDE.md – Prueba Técnica Protección (Científico de Datos IA – PQR)

Este es un desarrollo de una pruaba tecnica para una empresa en Medllin que se llama Protección y el cargo de la vacante es Científico de Datos para soluciones con IA - Equipo Atención de PQR

## ⚠️ Modo de trabajo (LEER PRIMERO)
- Todas las respuestas que me des y las preguntas que me hagas por la consola deben ser en español, resumidas y precizas, para horrar tiemp y tokens
- Este archivo es SOLO CONTEXTO. No implica ninguna acción por sí mismo.
- NO escribas código, NO crees ni modifiques archivos por iniciativa propia.
- El trabajo está dividido en tareas en `tasks/*.md` (una por punto de la prueba).
- Ejecuta ÚNICAMENTE la tarea que el usuario indique explícitamente (ej. "Ejecuta @tasks/1_1_top_productos.md").
- No adelantes, combines ni anticipes otras tareas, aunque estén en el enunciado.
- Si una instrucción es ambigua o falta información, pregunta antes de actuar.
- Al terminar una tarea, detente y espera la siguiente orden.

## Enunciado completo de la prueba
@PRUEBA_TECNICA.md

## Objetivo de negocio
Contexto: prueba técnica para el cargo "Científico de Datos para soluciones con IA – Equipo Atención de PQR" en Protección (Medellín). Protección busca a alguien que orqueste modelos predictivos para alimentar Agentes de IA y que convierta interacciones multicanal en experiencias hiper-personalizadas de ventas y servicio. La prueba simula ese reto con el e-commerce Olist (Brasil, ~100k pedidos, 2016-2018), tratándolo como si fuera "nuestra empresa".

El hilo conductor conecta los puntos entre sí; cada resultado alimenta al siguiente:

Diagnóstico (Punto 1): entender qué se vende más (volumen e ingresos) y cuál es el mayor dolor del cliente, con las categorías asociadas.
Inteligencia de clientes (Punto 2): segmentar clientes (fieles vs esporádicos vs en riesgo) para marketing, diseñar un recomendador en tiempo real basado en el segmento y el historial, y elegir la mejor ubicación física según las ventas.
Activación con IA (Punto 3): usar los productos top (1.1), el dolor (1.2) y los segmentos (2.1) para construir una base de conocimiento y system prompts que permitan a un Agente de IA conversar de forma hiper-personalizada.

Lo que se evalúa: rigor analítico, decisiones sustentadas con datos, supuestos explícitos ante ambigüedad, visión de producto end-to-end y comunicación ejecutiva orientada al negocio.

## Datos (data/raw/, NO subir al repo)
customers, geolocation, order_items, order_payments, order_reviews, orders, products, sellers, product_category_name_translation.
Reglas clave:
- Cliente real = `customer_unique_id` (customer_id cambia por pedido).
- Un pedido puede tener varios ítems y vendedores.
- NO unir order_items con order_payments directamente (duplica montos).
- Categorías en portugués: traducir con product_category_name_translation.
- El filtro por order_status se define en cada tarea (tasks/*.md). No asumir ninguno por defecto.

## Convenciones
- Python 3.11, pandas, código y comentarios en español.
- Lógica reutilizable en src/; notebooks solo para narrativa y gráficos.
- Figuras en reports/figures/ (png, títulos claros en español).
- Datos intermedios en data/processed/ (parquet).
- Secretos en .env (GEMINI_API_KEY). Nunca hardcodear llaves.

## Reglas de trabajo (ahorro de tokens)
- NO imprimir DataFrames grandes; solo shape, head(5) y métricas.
- Proponer plan breve antes de cambios grandes.
- Respuestas finales: resumen de máximo 5 líneas, sin explicaciones largas.

## Validación obligatoria (al final de cada tarea)
- Filas antes/después de cada join (detectar duplicados).
- Nulos en llaves.
- Totales que cuadren (ej. ingresos = order_items.price.sum() filtrado).
- Imprimir checklist ✅/❌ con los números clave.
- Registrar supuestos nuevos en SUPUESTOS.md (1 línea cada uno).


## Estructura
- tasks/: instrucciones por punto (solo leer la indicada)
- src/: lógica reutilizable (carga, features, segmentación, recomendador)
- notebooks/: narrativa y gráficos por punto
- api/: prototipo FastAPI del recomendador (2.2)
- agent/: knowledge_base.json (3.1) y prompts/ (3.2)
- reports/figures/: gráficos para la presentación
- data/raw/ (CSV originales) · data/processed/ (parquet intermedios)


