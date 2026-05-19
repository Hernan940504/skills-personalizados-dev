# docs-openapi

> Skill de documentación activa de endpoints REST — genera especificaciones OpenAPI 3.0 y configura Swagger UI en múltiples frameworks backend.

---

## Qué hace este skill

El agente analiza el código fuente de la API y:

1. **Detecta el framework** automáticamente (Spring Boot, NestJS, Express, FastAPI, Gin).
2. **Escanea los controladores/handlers** e identifica rutas, métodos HTTP, parámetros y tipos de request/response.
3. **Añade anotaciones al código fuente** con el formato nativo del framework:
   - Spring Boot → `@Operation`, `@ApiResponse`, `@Schema`
   - NestJS → `@ApiOperation`, `@ApiProperty`, `@ApiBearerAuth`
   - Express → JSDoc `@swagger` sobre cada ruta
   - FastAPI → `Field(...)`, docstrings, `responses={...}`
4. **Genera o actualiza `openapi.yaml`** con el spec OpenAPI 3.0 completo.
5. **Configura Swagger UI** para que quede accesible en una URL local.
6. **Valida el spec** con Redocly CLI al finalizar.

---

## Pre-requisitos

| Framework | Runtime | Dependencia principal |
|---|---|---|
| Spring Boot | Java 17+ | `springdoc-openapi-starter-webmvc-ui:2.3.0` |
| NestJS | Node 18+ | `@nestjs/swagger` + `swagger-ui-express` |
| Express | Node 16+ | `swagger-jsdoc` + `swagger-ui-express` |
| FastAPI | Python 3.9+ | Built-in (sin dependencias extra) |
| Gin | Go 1.21+ | `swaggo/swag` |

---

## Ejemplos de prompts que activan este skill

```
"Documenta todos los endpoints de este proyecto"
"Genera el openapi.yaml de la API"
"Agrega anotaciones @Operation a los controladores"
"Quiero habilitar /swagger-ui en este proyecto Spring Boot"
"Crea el swagger para el UserController"
"Documenta las entradas y salidas del endpoint POST /users"
"Añade @ApiProperty a todos los DTOs"
"¿Cómo documento los códigos de respuesta de este endpoint?"
```

---

## Estructura del skill

```
docs-openapi/
├── SKILL.md                         # Instrucciones para el agente (leer primero)
├── README.md                        # Este archivo
├── scripts/
│   ├── detect-framework.sh          # Detecta Spring Boot | NestJS | Express | FastAPI | Gin
│   └── validate-openapi.sh          # Valida openapi.yaml con Redocly CLI
├── templates/
│   ├── openapi-base.yaml.tmpl       # Estructura OpenAPI 3.0 completa
│   ├── spring-swagger-config.java.tmpl          # Clase OpenApiConfig
│   ├── spring-controller-annotations.java.tmpl  # Controlador anotado completo
│   ├── nestjs-swagger-config.ts.tmpl            # SwaggerModule en main.ts
│   ├── nestjs-swagger-decorator.ts.tmpl         # Decoradores por endpoint
│   ├── express-swagger-config.js.tmpl           # Setup swagger-jsdoc
│   ├── express-jsdoc-route.js.tmpl              # Rutas Express con JSDoc completo
│   └── fastapi-route-docstring.py.tmpl          # Router FastAPI documentado
└── references/
    ├── openapi3-quick-reference.md              # Cheatsheet OpenAPI 3.0
    ├── spring-springdoc-guide.md                # springdoc-openapi: anotaciones y config
    ├── nestjs-swagger-guide.md                  # @nestjs/swagger: decoradores completos
    ├── express-swagger-jsdoc-guide.md           # swagger-jsdoc: formato JSDoc
    └── fastapi-docs-guide.md                    # FastAPI: enriquecimiento built-in
```

---

## Cómo el agente usa este skill

```
1. Ejecuta scripts/detect-framework.sh
2. Lee el workflow correspondiente en SKILL.md (Workflow A/B/C/D/E)
3. Copia el template de configuración Swagger y lo adapta
4. Escanea controladores/handlers con grep/glob
5. Para cada endpoint: añade anotaciones desde el template de controlador
6. Genera openapi.yaml desde templates/openapi-base.yaml.tmpl
7. Ejecuta scripts/validate-openapi.sh
8. Reporta URLs de Swagger UI disponibles
```

---

## Convenciones de output

- Swagger UI: siempre en `/api-docs` (configurable).
- Spec YAML: `openapi.yaml` en la raíz del proyecto.
- Spec JSON: `openapi.json` en la raíz (opcional, generado a demanda).
- Códigos de respuesta mínimos documentados: `200/201`, `400`, `401`, `404`, `500`.

---

## Limitaciones conocidas

| Limitación | Workaround |
|---|---|
| No puede inferir tipos si el código usa `any` o `Object` sin generics | El agente pedirá el tipo al usuario |
| Express sin TypeScript: los tipos de request/response no son inferibles | Definir schemas manualmente en JSDoc |
| Gin: requiere instalar `swag` CLI globalmente | El agente muestra el comando de instalación |
| Proyectos muy grandes (+100 endpoints): el scan puede ser lento | Usar `--path-filter` para limitar por módulo |

---

## Compatibilidad de herramientas

| Herramienta | Comportamiento |
|---|---|
| Claude Code | Nativo — todos los workflows disponibles |
| Cursor | Funciona — las reglas MDC guían la anotación de código |
| Kiro | Funciona — steering file orienta la generación |
| OpenCode | Funciona — con tools básicas de Read/Edit/Write |

---

## Versionado

`0.1.0` — versión inicial. Cubre Spring Boot, NestJS, Express, FastAPI. Gin en beta.

---

## Contribuir mejoras

Ver [`docs/CONTRIBUTING-SKILLS.md`](../../../../docs/CONTRIBUTING-SKILLS.md) para el proceso de PR.

Issues frecuentes a mejorar:
- Añadir soporte para Flask y Django REST Framework.
- Generar código cliente desde el spec (openapi-generator).
- Detectar cambios en endpoints vs spec existente (diff mode).
