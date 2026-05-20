# Guía del modelo C4 — niveles y diagramas suplementarios

El modelo C4 (Context, Containers, Components, Code) de Simon Brown describe una arquitectura
de software a distintos niveles de zoom, como un mapa: empiezas lejos y haces zoom progresivo.
Cada nivel responde a una audiencia distinta.

---

## Los 4 niveles jerárquicos

### Nivel 1 — System Context (Contexto del Sistema)
- **Pregunta que responde:** ¿Qué sistema construimos y con qué/quién interactúa?
- **Muestra:** el sistema en foco (1 caja), los actores (personas) y los sistemas externos.
- **NO muestra:** tecnologías internas, contenedores, BDs, APIs.
- **Audiencia:** todos — negocio, stakeholders no técnicos, equipo.
- **Lenguaje:** capacidades de negocio. "Sistema de Facturación", no "Microservicio Node".
- En el modelo JSON: el sistema en foco es un `system` con `scope:true`; actores `person`; lo demás `system` con `external:true`.

### Nivel 2 — Containers (Contenedores)
- **Pregunta:** ¿Cuáles son las piezas desplegables y qué tecnología usa cada una?
- **Muestra:** apps (web, móvil, SPA), APIs/servicios, bases de datos, colas, file systems — todo lo que se despliega y ejecuta por separado. Un "contenedor" C4 ≠ contenedor Docker; es una unidad ejecutable/desplegable.
- **NO muestra:** clases/componentes internos de cada contenedor.
- **Audiencia:** arquitectos, desarrolladores, operaciones.
- **Lenguaje:** técnico. "API Application [Java, Spring MVC]", "Database [PostgreSQL 15]".
- En el JSON: `container`, `database`, `queue` con `scope:true` dentro del `scopeBoundary`; sistemas externos siguen como `system external:true`.

### Nivel 3 — Components (Componentes)
- **Pregunta:** ¿Cómo está estructurado internamente UN contenedor?
- **Muestra:** los componentes/módulos lógicos dentro de un único contenedor (ej. controllers, services, repositories, gateways) y sus relaciones.
- **Regla clave:** se hace zoom a **un solo contenedor** por diagrama. El `scopeBoundary` representa ese contenedor (no el sistema completo).
- **NO muestra:** sistemas externos que no toquen directamente esos componentes.
- **Audiencia:** desarrolladores de ese contenedor.
- En el JSON: `component` con `scope:true`; dependencias externas como `system`/`container` externos.

### Nivel 4 — Code (Código)
- Diagrama de clases/UML del componente. Casi siempre **innecesario** y se genera mejor desde el IDE.
- Este skill normalmente se detiene en Nivel 3. Solo genera Nivel 4 si el usuario lo pide explícitamente.

---

## Diagramas suplementarios (mejoran el entendimiento)

Estos no son niveles de zoom, sino vistas complementarias. Ofrécelos cuando aporten claridad:

### System Landscape (Paisaje de sistemas)
- Mapa de **varios** sistemas de software de la organización y cómo se relacionan, sin un único sistema en foco.
- Útil para arquitectura empresarial y para situar el sistema nuevo en el ecosistema existente.
- En el JSON: varios `system`, sin `scopeBoundary` o con varios límites; actores arriba.

### Dynamic (Dinámico)
- Muestra **cómo colaboran** elementos para un caso de uso concreto, paso a paso.
- Las relaciones se **numeran** (1, 2, 3…) según el orden del flujo — incluye el número al inicio de `description` (ej. `"1. Envía credenciales"`).
- Sustituye a un diagrama de secuencia cuando quieres mantener la notación C4.

### Deployment (Despliegue)
- Mapea contenedores a la **infraestructura** real: nodos, servidores, regiones cloud, clústeres.
- Útil para operaciones y para discutir escalado, redundancia, latencia.
- Modela los nodos de infra como `system`/`container` y usa el `scopeBoundary`/agrupaciones para zonas (ej. "AWS us-east-1", "Kubernetes Cluster").

---

## Cómo elegir qué generar

| El usuario quiere… | Genera |
|---|---|
| "panorama general", visión de negocio | Nivel 1 (Contexto) |
| "la arquitectura técnica", servicios y BDs | Nivel 2 (Contenedores) |
| "cómo funciona por dentro el servicio X" | Nivel 3 (Componentes de X) |
| "el flujo de checkout / login paso a paso" | Dynamic |
| "cómo se despliega en AWS/k8s" | Deployment |
| "todos nuestros sistemas y cómo se conectan" | System Landscape |
| "la arquitectura completa" | Secuencia: Contexto → Contenedores → Componentes del contenedor clave (un .drawio por nivel) |

**Regla de oro:** un diagrama, un nivel de abstracción, una audiencia. Si dudas, empieza por Contexto y profundiza.
