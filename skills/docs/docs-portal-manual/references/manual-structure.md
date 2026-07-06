# Estructura de un buen manual de usuario

Cómo organizar el contenido para que el manual sea útil a un usuario final (no
técnico) del portal.

## Principios

- **Orientado a tareas, no a features.** El usuario quiere "emitir una póliza",
  no "usar el formulario X". Redacta los pasos como objetivos.
- **Una pantalla = una sección.** Cada módulo lleva: para qué sirve, captura,
  pasos numerados, y notas/advertencias.
- **Lenguaje claro y en segunda persona.** "Haz clic en Guardar", no "el sistema
  persiste la entidad".
- **Captura real por pantalla.** La imagen ancla la explicación; el texto guía.

## Plantilla por módulo (en `manual.config.json`)

| Campo | Uso |
|---|---|
| `name` | Título de la sección (visible en el índice). |
| `slug` | Identificador para el nombre del archivo de imagen. |
| `path` | Ruta relativa del módulo (Playwright navega a `baseURL + path`). |
| `description` | 1-3 frases: qué es y para qué sirve. |
| `steps` | Lista ordenada de acciones del usuario (el corazón del manual). |
| `waitFor` | `networkidle` por defecto; ajústalo si la pantalla carga distinto. |
| `mask` | Selectores a tapar en la captura (datos sensibles, zonas dinámicas). |
| `notes` | Advertencias, atajos, errores comunes. |

## Orden recomendado de secciones

1. **Introducción** (`intro`): qué es el portal, a quién va dirigido, requisitos.
2. **Acceso** (login): cómo entrar, recuperación de contraseña si aplica.
3. **Inicio / Dashboard**: visión general y navegación.
4. **Módulos funcionales**: uno por sección, en el orden del flujo de trabajo real.
5. **(Opcional) Preguntas frecuentes / Solución de problemas**.

## Buenas prácticas de redacción de pasos

- Empieza cada paso con un **verbo de acción** ("Selecciona", "Ingresa", "Pulsa").
- Un paso = una acción. Si necesitas "y", probablemente son dos pasos.
- Nombra los controles como los ve el usuario ("el botón **Guardar**").
- Indica el **resultado esperado** cuando ayude ("aparecerá el mensaje *Guardado*").

## Salida

`build-manual.mjs` genera `manual-output/manual.md` con índice, capturas
embebidas y pasos. Puedes convertirlo a PDF/HTML con cualquier conversor de
Markdown, o exportar pantallas individuales a PDF con `page.pdf()`
(ver `screenshot-guide.md`).
