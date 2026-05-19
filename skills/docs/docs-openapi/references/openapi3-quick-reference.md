# OpenAPI 3.0 — Referencia rápida

Cheatsheet de los constructores más usados en un `openapi.yaml`. Consultar cuando el agente necesite generar o editar el spec directamente.

---

## Estructura raíz obligatoria

```yaml
openapi: "3.0.3"
info:
  title: "Nombre API"
  version: "1.0.0"
paths: {}
```

---

## Tipos de datos más comunes

| Tipo OpenAPI | Ejemplo |
|---|---|
| `type: string` | `"texto"` |
| `type: string, format: date-time` | `"2024-01-15T10:30:00Z"` |
| `type: string, format: date` | `"2024-01-15"` |
| `type: string, format: uuid` | `"550e8400-e29b-41d4-a716..."` |
| `type: string, format: email` | `"user@example.com"` |
| `type: integer, format: int64` | `9007199254740991` |
| `type: number, format: float` | `3.14` |
| `type: boolean` | `true` |
| `type: array, items: {type: string}` | `["a", "b"]` |
| `type: object` | `{}` |

---

## Parámetros

```yaml
parameters:
  # Path param
  - in: path
    name: id
    required: true
    schema:
      type: integer
    description: "ID del recurso"

  # Query param opcional
  - in: query
    name: page
    required: false
    schema:
      type: integer
      default: 1

  # Header
  - in: header
    name: X-Request-ID
    schema:
      type: string
      format: uuid

  # Cookie
  - in: cookie
    name: session
    schema:
      type: string
```

---

## Request body

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        $ref: '#/components/schemas/CreateUserRequest'
      example:
        name: "Juan"
        email: "juan@example.com"
    multipart/form-data:    # para subida de archivos
      schema:
        type: object
        properties:
          file:
            type: string
            format: binary
```

---

## Responses

```yaml
responses:
  "200":
    description: "OK"
    headers:
      X-Total-Count:
        schema:
          type: integer
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/UserResponse'
  "204":
    description: "Sin contenido"       # no tiene content
  "400":
    $ref: '#/components/responses/BadRequest'
  "401":
    $ref: '#/components/responses/Unauthorized'
  "403":
    $ref: '#/components/responses/Forbidden'
  "404":
    $ref: '#/components/responses/NotFound'
  "409":
    description: "Conflicto — el recurso ya existe"
  "422":
    $ref: '#/components/responses/UnprocessableEntity'
  "500":
    $ref: '#/components/responses/InternalServerError'
```

---

## Schemas avanzados

### Herencia / discriminador

```yaml
components:
  schemas:
    Animal:
      type: object
      required: [type]
      discriminator:
        propertyName: type
      properties:
        type:
          type: string
        name:
          type: string

    Dog:
      allOf:
        - $ref: '#/components/schemas/Animal'
        - type: object
          properties:
            breed:
              type: string
```

### oneOf / anyOf

```yaml
# Un schema u otro (oneOf = exactamente uno, anyOf = al menos uno)
schema:
  oneOf:
    - $ref: '#/components/schemas/CreditCardPayment'
    - $ref: '#/components/schemas/BankTransferPayment'
  discriminator:
    propertyName: method
```

### Enum

```yaml
status:
  type: string
  enum: [active, inactive, pending]
  example: active
```

### Nullable (OpenAPI 3.0)

```yaml
middleName:
  type: string
  nullable: true      # en 3.1 se usa: {type: [string, 'null']}
```

### Array con restricciones

```yaml
tags:
  type: array
  items:
    type: string
  minItems: 1
  maxItems: 10
  uniqueItems: true
```

---

## Security schemes

```yaml
components:
  securitySchemes:
    # JWT Bearer
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

    # API Key en header
    ApiKeyHeader:
      type: apiKey
      in: header
      name: X-API-Key

    # OAuth2
    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/oauth/authorize
          tokenUrl: https://auth.example.com/oauth/token
          scopes:
            read:users: Leer usuarios
            write:users: Crear y editar usuarios
```

Aplicar globalmente:
```yaml
security:
  - BearerAuth: []
```

Sobrescribir en un endpoint (sin auth):
```yaml
/health:
  get:
    security: []    # endpoint público
```

---

## Links útiles

- Spec oficial: https://spec.openapis.org/oas/v3.0.3
- Swagger Editor online: https://editor.swagger.io
- Validador Redocly: `npx @redocly/cli lint openapi.yaml`
- Conversor YAML↔JSON: `npx js-yaml openapi.yaml`
