# 3.2 System prompts
# Tarea 3.2 – Tres System Prompts hiper-personalizados

## Enunciado (textual)
Queremos que nuestro Agente de IA hable con los clientes de forma hiper-personalizada. Nota: Como el dataset no contiene edad y género, asume que estas variables provienen de nuestro CRM y ya están disponibles en el perfil del cliente.

Crea 3 System Prompts distintos que modulen el tono y la recomendación del LLM. Cada prompt debe estar diseñado para ingerir dinámicamente las siguientes variables:
- [EDAD]
- [GÉNERO]
- [PERFIL_DE_CLIENTE] (El segmento definido en el punto 2.1)
- [HISTORIAL_COMPRAS] (Una variable calculada por ti que resuma su comportamiento)
- [BASE_CONOCIMIENTO] (La creada en el punto 3.1)

Escenarios:
1. Un cliente joven, perfil altamente digital y comprador frecuente.
2. Un cliente mayor, perfil conservador/inactivo, que tuvo una mala experiencia previa (dolor identificado en 1.2).
3. Un cliente corporativo o de alto volumen de gasto (VIP).

## Contexto
- Insumos: `agent/knowledge_base.json` (3.1), `clientes_segmentados.parquet` con `historial_compras` (2.1), `clientes_dolor.parquet` (1.2), hallazgos del mayor dolor en `reports/tables/1_2_dolores.csv`.
- Los placeholders deben escribirse EXACTAMENTE así: [EDAD], [GÉNERO], [PERFIL_DE_CLIENTE], [HISTORIAL_COMPRAS], [BASE_CONOCIMIENTO].

## Paso 0 – Plan
Presenta un plan de máximo 8 líneas y espera mi aprobación.

## Estructura obligatoria de cada prompt
1. **Rol e identidad** del agente.
2. **Contexto del cliente** con los 5 placeholders.
3. **Objetivo de la conversación** (según escenario).
4. **Tono y estilo** (longitud de mensajes, formalidad, uso de emojis, tuteo/usted).
5. **Estrategia de recomendación:** cómo usar historial y segmento para elegir de la base de conocimiento; máximo 2 productos por mensaje; explicar el porqué.
6. **Reglas y guardarraíles:** recomendar SOLO productos de [BASE_CONOCIMIENTO]; nunca inventar precios, descuentos ni promociones; usar edad/género solo para ajustar tono, sin estereotipos ni suposiciones de gustos; no revelar datos internos (segmento, score) al cliente; escalar a un asesor humano ante quejas, reembolsos o si el cliente lo pide; privacidad de datos.
7. **Formato de respuesta.**
8. **Ejemplo breve** de primer mensaje del agente.

## Particularidades por escenario
- **Joven digital frecuente (`joven_digital.md`):** cercano, ágil, mensajes cortos; destacar novedades, complementarios a lo que compra y facilidad de compra/pago; llamada a la acción clara.
- **Mayor conservador con mala experiencia (`mayor_mala_experiencia.md`):** usted, pausado, empático, claro y sin tecnicismos. PRIMERO reconocer la mala experiencia (usar el dolor del 1.2, ej. retraso en la entrega) y generar confianza; SEGUNDO recomendar con énfasis en `pct_entregas_a_tiempo` y confiabilidad; nunca presionar; ofrecer asesor humano.
- **VIP / corporativo (`vip.md`):** profesional, consultivo y exclusivo; enfoque en valor, volumen y atención prioritaria; puede sugerir compras en cantidad o combos de la base de conocimiento, sin inventar beneficios.

## Pasos
1. Redactar los 3 prompts en `agent/prompts/` (Markdown).
2. `src/agent_context.py`: función `construir_prompt(escenario, customer_unique_id, edad, genero)` que cargue la plantilla y reemplace los placeholders con datos reales (segmento, historial y la base de conocimiento en JSON compacto).
3. Elegir 1 cliente REAL por escenario desde `clientes_segmentados.parquet` que encaje con el perfil (frecuente, inactivo con mala experiencia, VIP); asignar edad y género simulados (CRM) y documentarlo.
4. Guardar los 3 prompts ya llenos en `agent/prompts/ejemplos/` para mostrar en la presentación.
5. Agregar sección 3.2 al notebook 03.
6. NO implementar el agente conversacional (`demo_agent.py`) salvo que lo pida explícitamente.

## Registro de resultados
Al terminar la tarea, reemplaza el texto "_Pendiente_" de la sección "## Punto X.X" en reports/RESULTADOS.md con:
- **Pregunta:** (copiar textual del enunciado en PRUEBA_TECNICA.md)
- **Respuesta directa:** 2-4 líneas con cifras clave
- **Método:** 1 línea
- **hallazgo principal:**2-4 líneas escribir los hallazgos mas importante que encontraste en esa tarea, es util para la sustentacion.
- **descripcion de los pasos:**en 5 paso muy breves de solo texto y de una linea cada uno me das una breve descripcion de la solucion que le diste a este punto.
- **Archivos de soporte:** rutas de tablas y figuras generadas

## Validación (checklist ✅/❌)
- Cada plantilla contiene los 5 placeholders exactos.
- Los prompts llenos no tienen placeholders sin reemplazar.
- Los clientes elegidos cumplen el perfil (mostrar segmento e historial de cada uno).
- Longitud de cada prompt lleno (tokens aprox.) razonable.

## Salida final en el chat
Máximo 5 líneas: diferencias clave entre los 3 prompts y los clientes de ejemplo elegidos.