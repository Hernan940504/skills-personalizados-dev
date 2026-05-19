---
name: docs-openapi
description: Analiza controladores y handlers de API REST para generar especificaciones
  OpenAPI 3.0 completas (openapi.yaml), añadir anotaciones Swagger al código fuente
  y configurar Swagger UI. Soporta Spring Boot (springdoc-openapi), NestJS (@nestjs/swagger),
  Express (swagger-jsdoc), FastAPI (built-in) y Gin (swaggo). Úsalo cuando el usuario
  tenga endpoints sin documentar, pida generar un openapi.yaml, quiera habilitar
  /docs o /swagger-ui, o necesite documentar entradas, salidas y códigos de respuesta.
version: 0.1.0
author: HernanBetancurBolivar01
category: docs
tags: [openapi, swagger, rest-api, spring-boot, nestjs, express, fastapi, gin, documentation]
compatibility: [claude-code, cursor, kiro, opencode]
allowed-tools: [Read, Edit, Write, Bash, Grep, Glob]
examples:
  - prompt: "documenta todos los endpoints de este proyecto"
  - prompt: "genera el swagger de la API"
  - prompt: "crea el openapi.yaml para este controlador"
  - prompt: "agrega anotaciones @Operation a los endpoints de Spring Boot"
  - prompt: "habilita /api-docs con springdoc"
  - prompt: "quiero ver el swagger-ui de este proyecto"
---

# docs-openapi — Documentación activa de endpoints REST

## Cuándo usar este skill

- El proyecto tiene endpoints sin documentar o con documentación desactualizada.
- El usuario pide generar un `openapi.yaml`, `swagger.json` o similar.
- El usuario quiere habilitar Swagger UI (`/swagger-ui`, `/docs`, `/api-docs`).
- El usuario quiere añadir anotaciones `@Operation`, `@ApiResponse`, JSDoc, o docstrings a sus endpoints.
- El usuario pregunta "¿cómo documento las entradas y salidas de mis endpoints?".

## Cuándo NO usar

- La API no es REST (GraphQL, gRPC, WebSocket) → usar skill específico cuando exista.
- El proyecto ya tiene `openapi.yaml` actualizado y solo se pide un pequeño fix → editar directamente.
- El usuario pide generar tests de la API → usar `testing-generation`.

---

## Paso 0 — Detección del framework

Ejecutar `scripts/detect-framework.sh` antes de cualquier otra acción. Retorna uno de:
`spring-boot` | `nestjs` | `express` | `fastapi` | `gin` | `unknown`

```bash
bash skills/docs/docs-openapi/scripts/detect-framework.sh
```

Si retorna `unknown`, pedir al usuario que especifique el framework.

---

## Workflow A — Spring Boot (springdoc-openapi)

### A1. Verificar dependencia springdoc

Buscar en `pom.xml` o `build.gradle`:

```bash
grep -r "springdoc" pom.xml build.gradle 2>/dev/null
```

Si no existe, añadir a `pom.xml`:

```xml
<dependency>
  <groupId>org.springdoc</groupId>
  <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
  <version>2.3.0</version>
</dependency>
```

O en `build.gradle`:
```groovy
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.3.0'
```

### A2. Crear configuración OpenAPI

Crear `src/main/java/.../config/OpenApiConfig.java` usando `templates/spring-swagger-config.java.tmpl`.
Reemplazar `{{basePackage}}`, `{{title}}`, `{{version}}`, `{{description}}`.

### A3. Escanear controladores

```bash
grep -r "@RestController\|@Controller" src/main/java --include="*.java" -l
```

Para cada controlador, leer el archivo e identificar:
- Clase: `@RequestMapping` base path
- Métodos: `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`
- Parámetros: `@PathVariable`, `@RequestParam`, `@RequestBody`
- Tipos de retorno: `ResponseEntity<T>`, `T`, `List<T>`

### A4. Anotar cada endpoint

Usar `templates/spring-controller-annotations.java.tmpl` como guía.
Añadir en la clase:
```java
@Tag(name = "{{ResourceName}}", description = "{{descripción del recurso}}")
```

Añadir en cada método:
```java
@Operation(summary = "{{resumen}}", description = "{{detalle opcional}}")
@ApiResponses({
  @ApiResponse(responseCode = "200", description = "OK",
    content = @Content(schema = @Schema(implementation = {{ResponseDTO}}.class))),
  @ApiResponse(responseCode = "400", description = "Solicitud inválida"),
  @ApiResponse(responseCode = "404", description = "No encontrado"),
  @ApiResponse(responseCode = "500", description = "Error interno")
})
```

Para `@RequestBody`:
```java
@io.swagger.v3.oas.annotations.parameters.RequestBody(
  description = "{{descripción del body}}",
  required = true,
  content = @Content(schema = @Schema(implementation = {{RequestDTO}}.class))
)
```

### A5. Anotar DTOs con @Schema

En cada clase DTO usada como request/response:
```java
@Schema(description = "{{descripción de la clase}}")
public class {{DTO}} {
  @Schema(description = "{{descripción}}", example = "{{ejemplo}}")
  private {{tipo}} {{campo}};
}
```

### A6. Configurar propiedades (opcional)

Añadir en `application.properties` o `application.yml`:
```properties
springdoc.api-docs.path=/api-docs
springdoc.swagger-ui.path=/swagger-ui.html
springdoc.swagger-ui.operationsSorter=method
springdoc.packages-to-scan={{basePackage}}.controller
```

### A7. Generar openapi.yaml estático (opcional)

Con el servidor corriendo:
```bash
curl http://localhost:8080/api-docs.yaml -o openapi.yaml
```

---

## Workflow B — NestJS (@nestjs/swagger)

### B1. Verificar dependencia

```bash
grep "@nestjs/swagger" package.json
```

Si no existe:
```bash
npm install @nestjs/swagger swagger-ui-express
```

### B2. Configurar SwaggerModule en main.ts

Usar `templates/nestjs-swagger-config.ts.tmpl` para editar `src/main.ts`.

### B3. Escanear controladores

```bash
grep -r "@Controller\|@Get\|@Post\|@Put\|@Delete\|@Patch" src --include="*.ts" -l
```

Para cada controlador identificar: clase, rutas, DTOs de request y response.

### B4. Anotar controladores

Añadir en la clase:
```typescript
@ApiTags('{{nombre-recurso}}')
@Controller('{{ruta}}')
```

En cada método, usar `templates/nestjs-swagger-decorator.ts.tmpl`:
```typescript
@ApiOperation({ summary: '{{resumen}}', description: '{{detalle}}' })
@ApiParam({ name: '{{param}}', description: '{{desc}}', type: String })
@ApiBody({ type: {{RequestDTO}} })
@ApiResponse({ status: 200, description: 'OK', type: {{ResponseDTO}} })
@ApiResponse({ status: 400, description: 'Solicitud inválida' })
@ApiResponse({ status: 404, description: 'No encontrado' })
```

### B5. Anotar DTOs con @ApiProperty

```typescript
export class {{DTO}} {
  @ApiProperty({ description: '{{desc}}', example: {{ejemplo}} })
  {{campo}}: {{tipo}};
}
```

Para campos opcionales: `@ApiPropertyOptional`.

### B6. Exportar openapi.yaml

```bash
# Con el servidor corriendo
curl http://localhost:3000/api-json -o openapi.json
# O desde código en main.ts: SwaggerModule.createDocument(app, config)
```

---

## Workflow C — Express (swagger-jsdoc + swagger-ui-express)

### C1. Instalar dependencias

```bash
npm install swagger-jsdoc swagger-ui-express
npm install --save-dev @types/swagger-jsdoc @types/swagger-ui-express  # si TypeScript
```

### C2. Crear archivo de configuración Swagger

Crear `src/swagger.js` (o `.ts`) usando `templates/express-swagger-config.js.tmpl`.

### C3. Escanear rutas

```bash
grep -r "router\.\(get\|post\|put\|delete\|patch\)\|app\.\(get\|post\|put\|delete\|patch\)" \
  src --include="*.js" --include="*.ts" -l
```

### C4. Añadir JSDoc a cada ruta

Usar `templates/express-jsdoc-route.js.tmpl` como base. Añadir bloque JSDoc inmediatamente antes de cada handler:

```javascript
/**
 * @swagger
 * /{{path}}:
 *   {{method}}:
 *     tags: [{{Tag}}]
 *     summary: {{resumen}}
 *     parameters:
 *       - in: path
 *         name: {{param}}
 *         required: true
 *         schema:
 *           type: string
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/{{RequestSchema}}'
 *     responses:
 *       200:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/{{ResponseSchema}}'
 *       400:
 *         description: Solicitud inválida
 *       404:
 *         description: No encontrado
 */
```

### C5. Definir schemas en sección `components`

En el archivo de configuración Swagger, añadir definición de cada schema bajo `components.schemas`.

---

## Workflow D — FastAPI (built-in)

FastAPI genera OpenAPI automáticamente desde el código. El skill se enfoca en **enriquecer** la documentación existente.

### D1. Verificar endpoint `/docs` activo

```bash
grep -r "FastAPI\|APIRouter" app --include="*.py" -l
```

FastAPI expone `/docs` (Swagger UI) y `/redoc` por defecto. Si están desactivados, activarlos:
```python
app = FastAPI(docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")
```

### D2. Enriquecer metadatos de la app

En el archivo principal donde se instancia `FastAPI(...)`:
```python
app = FastAPI(
    title="{{título de la API}}",
    description="{{descripción larga, soporta Markdown}}",
    version="{{versión}}",
    contact={"name": "{{nombre}}", "email": "{{email}}"},
    license_info={"name": "MIT"},
)
```

### D3. Anotar rutas con summary y description

Usar `templates/fastapi-route-docstring.py.tmpl`:
```python
@router.get("/{{path}}", response_model={{ResponseModel}}, summary="{{resumen}}", tags=["{{tag}}"])
async def {{nombre_función}}({{params}}):
    """
    {{descripción detallada del endpoint}}

    - **{{campo}}**: {{descripción del campo}}
    """
```

### D4. Anotar Pydantic models con Field

```python
from pydantic import BaseModel, Field

class {{Schema}}(BaseModel):
    {{campo}}: {{tipo}} = Field(..., description="{{descripción}}", example={{ejemplo}})
    {{campo_opcional}}: Optional[{{tipo}}] = Field(None, description="{{descripción}}")
```

### D5. Documentar parámetros de query/path

```python
from fastapi import Path, Query

@router.get("/{id}")
async def get_item(
    id: int = Path(..., description="ID del recurso", gt=0),
    page: int = Query(1, description="Número de página", ge=1),
):
```

### D6. Exportar openapi.yaml

```bash
python -c "
import yaml, json
from app.main import app
spec = app.openapi()
with open('openapi.yaml', 'w') as f:
    yaml.dump(spec, f, allow_unicode=True, sort_keys=False)
"
```

---

## Workflow E — Gin (swaggo/swag)

### E1. Instalar swag

```bash
go install github.com/swaggo/swag/cmd/swag@latest
go get github.com/swaggo/gin-swagger
go get github.com/swaggo/files
```

### E2. Anotar main.go

```go
// @title           {{título de la API}}
// @version         {{versión}}
// @description     {{descripción}}
// @host            localhost:{{puerto}}
// @BasePath        /api/v1
```

### E3. Anotar cada handler

```go
// {{NombreFunción}} {{descripción corta del endpoint}}
// @Summary     {{resumen}}
// @Description {{descripción larga}}
// @Tags        {{tag}}
// @Accept      json
// @Produce     json
// @Param       id   path     int          true  "ID del recurso"
// @Param       body body     {{RequestStruct}} true  "Body de la petición"
// @Success     200  {object} {{ResponseStruct}}
// @Failure     400  {object} ErrorResponse
// @Failure     404  {object} ErrorResponse
// @Router      /{{path}} [{{method}}]
```

### E4. Registrar la ruta de Swagger UI

```go
import (
  ginSwagger "github.com/swaggo/gin-swagger"
  swaggerFiles "github.com/swaggo/files"
  _ "{{modulo}}/docs"
)

r.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
```

### E5. Generar docs

```bash
swag init -g main.go --output docs/
```

---

## Convenciones transversales

- **Códigos de respuesta mínimos a documentar:** `200` (o `201` para POST), `400`, `401` (si tiene auth), `403` (si tiene roles), `404`, `500`.
- **Nombres de tags:** usar el nombre del recurso en PascalCase o kebab-case consistente en todo el proyecto.
- **Schemas:** siempre referenciar con `$ref` en vez de inlinear — más reutilizable y legible.
- **Ejemplos:** añadir al menos un ejemplo por schema request. Mejora drásticamente la usabilidad de Swagger UI.
- **Security schemes:** si la API usa JWT, añadir bearer auth al spec. Ver `references/openapi3-quick-reference.md`.

## Anti-patrones

- No documentar solo el happy path (200) — siempre incluir 400, 404, 500 como mínimo.
- No usar descripciones genéricas como "Get item" — escribir lo que hace realmente: "Obtiene el perfil del usuario por ID".
- No inlinear schemas grandes — siempre usar `$ref: '#/components/schemas/NombreSchema'`.
- No documentar campos internos de implementación (IDs de BD, timestamps de auditoría interna) en el schema público.

## Recursos

- `scripts/detect-framework.sh` — detecta el framework del proyecto automáticamente
- `scripts/validate-openapi.sh` — valida la sintaxis y semántica del `openapi.yaml` generado
- `templates/openapi-base.yaml.tmpl` — estructura base de un OpenAPI 3.0 completo
- `templates/spring-swagger-config.java.tmpl` — clase `OpenApiConfig` para Spring Boot
- `templates/spring-controller-annotations.java.tmpl` — ejemplo anotado completo
- `templates/nestjs-swagger-config.ts.tmpl` — configuración SwaggerModule en main.ts
- `templates/nestjs-swagger-decorator.ts.tmpl` — decoradores por método
- `templates/express-swagger-config.js.tmpl` — setup swagger-jsdoc + swagger-ui-express
- `templates/express-jsdoc-route.js.tmpl` — JSDoc completo para un endpoint Express
- `templates/fastapi-route-docstring.py.tmpl` — decoradores y docstrings FastAPI
- `references/openapi3-quick-reference.md` — cheatsheet OpenAPI 3.0
- `references/spring-springdoc-guide.md` — springdoc-openapi: anotaciones y config
- `references/nestjs-swagger-guide.md` — @nestjs/swagger: decoradores completos
- `references/express-swagger-jsdoc-guide.md` — swagger-jsdoc: formato JSDoc
- `references/fastapi-docs-guide.md` — FastAPI: enriquecimiento de docs built-in
