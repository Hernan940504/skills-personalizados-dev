# Correo de respuesta — Sizing CIDR Ciencuadras PROD

> Borrador para envío. Reemplazar los campos entre `[ ]` antes de enviar.

---

**Para:** [equipo de red / autor del informe de sizing]
**CC:** [arquitectura, DevOps Ciencuadras]
**Asunto:** Sizing CIDR cuenta Ciencuadras PROD — decisión: /21 (sustentado)

---

Hola [nombre],

Gracias por el reporte de sizing de la cuenta Seguros-Bolivar-ciencuadras-PROD. Lo revisamos a fondo y validamos sus cifras directamente contra la cuenta de origen (`290296201161`); coinciden con lo medido, en particular el driver del sizing: la demanda pico de ~328 IPs, dominada por ECS Fargate (280 IPs por el techo de autoescalado).

Sobre la recomendación del informe (**/22**), estamos de acuerdo en que es técnicamente correcta para operación corriente. Sin embargo, para esta cuenta vamos a asignar un **/21**. La razón es que el objetivo de la separación de ambientes no es solo cubrir la demanda actual, sino no quedar cortos ante el crecimiento y las funcionalidades futuras, y tenemos evidencia medida que respalda esa necesidad.

**Lo que sustenta el /21:**

1. **Crecimiento real y sostenido.** Analizamos 15 meses de comportamiento en producción (el máximo que retiene CloudWatch). El tráfico creció **+82 % punta a punta** (~+54 % anualizado), sin caídas estructurales. La demanda no está plana: sube de forma sostenida, y ya hay carga nueva de IA materializándose en producción.

2. **Proyección sobre el sizing.** Aplicando ese crecimiento a la demanda pico actual (~328 IPs), en aproximadamente 18 meses se superan las ~500 IPs, punto en el que el /22 empieza a apretarse. El /21 absorbe esa proyección manteniéndose por debajo del 30 % de ocupación.

3. **Margen por zona de disponibilidad.** Con /22, el diseño en 3 AZ deja una sola subred privada /24 por AZ (~37 % de ocupación en pico por AZ). Con /21 usamos privadas /23 por AZ y bajamos a ~19 %, eliminando el riesgo de agotamiento zonal en despliegues o picos concentrados.

4. **Sin sobredimensionar.** El /21 queda en ~16 % de ocupación en pico. Descartamos /20 y /19 precisamente para no repetir el sobredimensionamiento del /16 actual (hoy al 0.9 % de uso), que es lo que este proyecto busca corregir. El /21 es un consumo moderado y responsable del plan de direccionamiento.

En resumen: el /22 cubre el hoy; el /21 cubre el hoy y el crecimiento medido, sin caer en el derroche. Por eso optamos por el /21.

**Puntos a coordinar con ustedes antes de crear la VPC:**

- Validar el rango /21 candidato contra lo anunciado en el Transit Gateway y las redes on-premise, para evitar solapamientos.
- Confirmar disponibilidad del /21 en el plan IPAM corporativo.

Adjunto el documento completo de justificación con la comparativa de prefijos (/24 a /19), el análisis histórico de 15 meses y las consideraciones de implementación, por si quieren revisar el detalle o discutirlo en una breve reunión.

Quedo atento a sus comentarios.

Saludos,
[Nombre]
[Cargo — Arquitectura]
[Contacto]

---

## Nota de anexo

Adjuntar: `justificacion-cidr-prod.md` (o su versión en PDF).
