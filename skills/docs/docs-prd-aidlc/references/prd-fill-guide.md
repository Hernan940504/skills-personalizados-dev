# Guía de llenado del PRD — qué preguntar y errores comunes

Lectura bajo demanda para conducir la entrevista de las 9 secciones. Objetivo:
obtener hechos cuantificados, no adjetivos. Cuando el usuario no tenga el dato,
regístralo como `⚠️ POR VALIDAR (preguntar al sponsor)`.

---

## Base: ¿producto propio o problema interno?

- **Producto propio / startup** → base *Product Vision Board*: foco en visión,
  segmento de cliente, propuesta de valor, necesidades del mercado.
- **Problema interno de Seguros Bolívar** → base *Internal Solution Brief*: foco
  en el proceso actual, sponsor, adopción y restricciones corporativas.

Pregunta esto primero; cambia el énfasis de las preguntas siguientes.

---

## Sección 1 — Problema de negocio

Preguntas:
- ¿Cuál es el dolor concreto y a quién afecta?
- ¿Cuánto cuesta hoy? Pide número: horas/persona, días de ciclo, % de error,
  reprocesos, tickets, dinero, NPS/insatisfacción.
- ¿Desde cuándo existe? ¿Se ha intensificado?

Errores comunes:
- "Es lento / ineficiente / manual" sin número → inservible.
- Confundir síntoma con causa raíz.
- Describir la solución en vez del problema.

Bueno: "El ajuste a un agente toma ~3 semanas y bloquea capacidad del equipo dev."

---

## Sección 2 — Stakeholders y sponsor

Preguntas:
- ¿Quién aprueba recursos y adopta? (sponsor real, no un patrocinador nominal)
- ¿Quiénes usan la solución día a día? (perfiles, no áreas genéricas)
- ¿Quién puede **bloquear**? Piensa en Seguridad de la Información, Compliance /
  Superintendencia Financiera, Arquitectura Empresarial, líderes de línea.

Errores comunes:
- Listar solo usuarios y olvidar a quién puede vetar la adopción.
- Sponsor sin autoridad presupuestal.

---

## Sección 3 — Estado actual

Preguntas:
- Paso a paso, ¿cómo se resuelve hoy? (proceso real, con tiempos)
- ¿Qué herramientas se usan?
- ¿Qué funciona bien y NO hay que tocar? (respétalo en el diseño)
- ¿Qué no funciona? (oportunidad)

Errores comunes:
- Saltarse el proceso actual → la solución no se adopta.
- No identificar lo que funciona → se rompe algo valioso.

---

## Sección 4 — Estado futuro deseado

Preguntas:
- Si funciona perfecto, ¿cómo se ve el flujo end-to-end?
- ¿Qué cambia en concreto para el usuario final?

Errores comunes:
- Describir features, no el resultado para el usuario.
- Estado futuro que ignora las restricciones (irrealizable).

---

## Sección 5 — Criterios de éxito

Preguntas:
- ¿Qué 2-3 métricas demuestran que funcionó?
- ¿Valor actual y target de cada una?

Reglas:
- Medibles y entendibles por el sponsor.
- Deben poder auditarse (de dónde sale el dato).

Errores comunes:
- Métricas de vanidad ("más uso") sin línea base.
- Sin target numérico.

---

## Sección 6 — Restricciones

Recorre las 4 categorías (técnica, datos, organizacional, compliance). Contrasta
siempre con `seguros-bolivar-guardrails.md`. Si el usuario no conoce una política,
NO la inventes: `⚠️ POR VALIDAR`.

Errores comunes:
- Proponer stack/librerías fuera de lo aprobado.
- Ignorar Habeas Data, redacción de PII o retención de datos.

---

## Sección 7 — Enfoque técnico (AI-First)

Preguntas:
- ¿Qué capacidad de IA aplica? (clasificación, extracción, generación,
  orquestación de agentes, automatización de workflow)
- ¿Por qué IA y no reglas/RPA? (justifica con lenguaje natural, contexto,
  decisiones no predefinidas)
- Arquitectura de alto nivel con el stack aprobado.

Errores comunes:
- "IA porque sí" sin justificar frente a automatización tradicional.
- Respuestas de IA no estructuradas (rompen orquestadores).
- Inferencia síncrona en operaciones pesadas.

---

## Sección 8 — Riesgos y dependencias

Preguntas:
- Top 2-3 riesgos (adopción, datos sensibles, madurez tecnológica, cuellos de
  botella de aprobación) con su mitigación.
- Dependencias externas: APIs, accesos, aprobaciones pendientes.

Errores comunes:
- Riesgos genéricos sin mitigación accionable.
- Omitir dependencias que bloquean el arranque.

---

## Sección 9 — Límites de alcance

Preguntas:
- ¿Qué SÍ entra en el MVP? (3-5 bullets concretos)
- ¿Qué queda explícitamente FUERA?

Errores comunes:
- MVP inflado.
- No declarar lo fuera de alcance → expectativas infladas.
