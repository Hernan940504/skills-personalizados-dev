# Guía de deep research — validación y crítica (obligatorios)

Todo planteamiento inicial (PRD / Internal Solution Brief / Product Vision Board)
requiere **dos** deep research antes de darse por cerrado. No son decorativos:
uno da fundamento a la propuesta (Ideation) y el otro la somete a estrés
(Inception + gates). Origen del patrón: material Hardcore AI (Estación 1 — deep
research de validación/contexto y deep research de crítica/riesgos).

## Reglas al generar los prompts

- **Aplícalos al caso concreto.** No entregues plantillas genéricas: rellena
  dominio, proceso actual, marcas/áreas, restricciones y stack aprobado.
- **Exige fuentes citadas** y prioriza material reciente (últimos 2 años).
- **Exige honestidad sobre limitaciones.** El prompt debe pedir explícitamente
  que NO se presente la solución como trivialmente resuelta.
- **Sin PII ni datos reales** de clientes/pólizas en el prompt.
- **Respeta los guardrails** de Seguros Bolívar (stack aprobado, PostgreSQL/
  PgVector/Pinecone, JFrog, Habeas Data, retención ≤ 90 días). Ver
  `seguros-bolivar-guardrails.md`.
- **Documenta los hallazgos** en Markdown junto al PRD y cítalos en el documento.

## Cómo mapean al PRD / AI-DLC

| Deep research | Alimenta secciones del PRD | Fase AI-DLC |
|---|---|---|
| Validación / contexto | §1 Problema, §4 Estado futuro, §5 Criterios de éxito, §7 Enfoque técnico | Ideation |
| Crítica / riesgos | §6 Restricciones, §7 Enfoque técnico, §8 Riesgos, §9 Alcance | Inception + Gates |

---

## Plantilla 1 — Deep research de VALIDACIÓN / CONTEXTO

Reemplaza los campos `{{...}}` antes de entregar.

```
Actúa como analista de investigación senior. Necesito un deep research
fundamentado y con fuentes citadas (prioriza material de los últimos 2 años)
para VALIDAR el fundamento de una iniciativa antes de comprometer su desarrollo.

CONTEXTO DE LA INICIATIVA:
- Organización / área: {{organizacion_o_area}}
- Problema a resolver: {{problema_cuantificado}}
- Proceso actual y su costo: {{estado_actual_y_costo}}
- Resultado esperado: {{estado_futuro_deseado}}
- Restricciones relevantes: {{restricciones_stack_datos_compliance}}

INVESTIGA Y RESPONDE:
1. ¿Cómo han resuelto otras organizaciones (idealmente del mismo sector o de
   sectores regulados comparables) un problema similar? Da casos concretos.
2. ¿Qué tecnologías, patrones de arquitectura y enfoques aplicaron? ¿Cuáles se
   consideran hoy el estado del arte?
3. ¿Qué resultados/beneficios medibles obtuvieron (tiempo, costo, errores,
   adopción)? Cuantifica cuando haya datos.
4. ¿Qué alternativas existen al enfoque propuesto y en qué casos cada una es
   superior?
5. ¿Qué evidencia respalda o contradice que este enfoque sea el correcto para
   el contexto descrito?

FORMATO DE SALIDA:
- Resumen ejecutivo con el veredicto de validación (¿tiene fundamento? ¿con qué
  matices?).
- Una sección por cada punto (1-5) con análisis y tablas comparativas donde
  aplique.
- Recomendaciones concretas que alimenten los criterios de éxito y el enfoque
  técnico.
- Lista de fuentes citadas.
- Sé honesto sobre lo que la evidencia NO respalda; no infles la propuesta.
```

---

## Plantilla 2 — Deep research de CRÍTICA / RIESGOS

Reemplaza los campos `{{...}}` antes de entregar.

```
Actúa como revisor crítico y arquitecto escéptico. Necesito un deep research
fundamentado y con fuentes citadas (prioriza material de los últimos 2 años)
que busque activamente las razones por las que esta iniciativa PODRÍA FALLAR en
un contexto corporativo regulado.

CONTEXTO DE LA INICIATIVA:
- Organización / área: {{organizacion_o_area}}
- Solución propuesta: {{solucion_propuesta}}
- Enfoque técnico de alto nivel: {{enfoque_tecnico}}
- Restricciones (stack aprobado, datos sensibles, compliance): {{restricciones}}
- Usuarios y quién puede bloquear la adopción: {{stakeholders_y_bloqueadores}}

INVESTIGA Y RESPONDE:
1. ¿Por qué fallan este tipo de soluciones en organizaciones grandes/reguladas?
   Antipatrones documentados y causas raíz.
2. ¿Cuáles son los principales riesgos de ADOPCIÓN (resistencia al cambio,
   curva de aprendizaje, dependencia de personas clave)?
3. ¿Qué riesgos TÉCNICOS y de DEUDA (mantenibilidad, escalabilidad, obsolescencia,
   acoplamiento) son típicos de este enfoque?
4. ¿Qué riesgos de DATOS y COMPLIANCE aplican (privacidad, protección de datos
   personales, trazabilidad, retención, seguridad multitenant)?
5. ¿Qué COSTOS OCULTOS suelen subestimarse (operación, licenciamiento, soporte,
   migración)?
6. Para cada riesgo relevante, propone una MITIGACIÓN accionable.

FORMATO DE SALIDA:
- Resumen ejecutivo con los 3-5 riesgos más severos (probabilidad x impacto).
- Una sección por cada punto (1-6), con tabla riesgo → causa → mitigación.
- Señales tempranas de alerta que deberían vigilarse en los gates del proyecto.
- Lista de fuentes citadas.
- No suavices los hallazgos: el valor de este research está en encontrar lo que
  puede salir mal.
```

---

## Checklist de este paso

- [ ] Prompt de validación generado y aplicado al caso concreto.
- [ ] Prompt de crítica/riesgos generado y aplicado al caso concreto.
- [ ] Ambos piden fuentes citadas y honestidad sobre limitaciones.
- [ ] Sin PII ni datos reales en los prompts.
- [ ] (Si ya se ejecutaron) hallazgos documentados en Markdown y citados en el PRD.
