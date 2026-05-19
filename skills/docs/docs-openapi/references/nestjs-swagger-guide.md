# NestJS — @nestjs/swagger: guía de decoradores

## Instalación

```bash
npm install @nestjs/swagger swagger-ui-express
# Para Fastify en vez de Express:
npm install @nestjs/swagger fastify-swagger
```

---

## URLs por defecto (configuración en main.ts)

| Recurso | URL |
|---|---|
| Swagger UI | `http://localhost:3000/api-docs` |
| Spec JSON | `http://localhost:3000/api-docs-json` |
| Spec YAML | `http://localhost:3000/api-docs-yaml` |

---

## Decoradores por ámbito

### En el módulo / main.ts

```typescript
// DocumentBuilder — construye los metadatos del spec
const config = new DocumentBuilder()
  .setTitle('Mi API')
  .setDescription('Descripción de la API')
  .setVersion('1.0')
  .addBearerAuth()          // JWT Bearer
  .addApiKey()              // API Key
  .addOAuth2()              // OAuth2
  .addTag('users', 'Operaciones de usuario')
  .build();
```

### En el controlador (clase)

```typescript
@ApiTags('users')                          // agrupa en Swagger UI
@ApiBearerAuth()                           // requiere JWT
@ApiUnauthorizedResponse({ description: 'No autenticado' })
@Controller('users')
export class UserController {}
```

### En cada endpoint

```typescript
@ApiOperation({
  summary: 'Resumen corto (aparece en la lista)',
  description: 'Descripción larga con **Markdown** soportado.',
  operationId: 'createUser',               // ID único para generación de clientes
  deprecated: false,
})
@ApiParam({
  name: 'id',
  type: Number,
  description: 'ID del usuario',
  example: 1,
})
@ApiQuery({
  name: 'status',
  enum: ['active', 'inactive'],
  required: false,
  description: 'Filtrar por estado',
})
@ApiBody({ type: CreateUserDto, description: 'Datos del usuario' })
@ApiCreatedResponse({ type: UserResponseDto, description: 'Creado exitosamente' })
@ApiBadRequestResponse({ description: 'Datos inválidos' })
@ApiNotFoundResponse({ description: 'No encontrado' })
```

### Respuestas tipadas — atajos

```typescript
@ApiOkResponse({ type: UserResponseDto })          // 200
@ApiCreatedResponse({ type: UserResponseDto })     // 201
@ApiNoContentResponse()                            // 204
@ApiBadRequestResponse()                           // 400
@ApiUnauthorizedResponse()                         // 401
@ApiForbiddenResponse()                            // 403
@ApiNotFoundResponse()                             // 404
@ApiConflictResponse()                             // 409
@ApiUnprocessableEntityResponse()                  // 422
@ApiInternalServerErrorResponse()                  // 500
```

---

## Decoradores en DTOs

```typescript
import { ApiProperty, ApiPropertyOptional, ApiHideProperty } from '@nestjs/swagger';

export class CreateUserDto {
  @ApiProperty({
    description: 'Nombre completo del usuario',
    example: 'Juan García',
    minLength: 1,
    maxLength: 100,
  })
  name: string;

  @ApiProperty({
    description: 'Correo electrónico único',
    example: 'juan@example.com',
    format: 'email',
  })
  email: string;

  @ApiPropertyOptional({
    description: 'Rol asignado',
    enum: ['ADMIN', 'USER', 'VIEWER'],
    default: 'USER',
  })
  role?: string;

  @ApiHideProperty()         // no aparece en Swagger
  internalFlag: boolean;
}
```

### Array de DTOs como respuesta

```typescript
@ApiOkResponse({ type: [UserResponseDto] })        // array
// O con clase envolvente:
@ApiOkResponse({ type: PaginatedUsersResponse })   // objeto con data: UserResponseDto[]
```

### Herencia de DTOs

```typescript
export class UpdateUserDto extends PartialType(CreateUserDto) {}
// PartialType marca todos los campos como opcionales y conserva los @ApiProperty
```

---

## Seguridad por endpoint

```typescript
// Global en DocumentBuilder → addBearerAuth('jwt-auth')
// Referencia en el controlador o endpoint:
@ApiBearerAuth('jwt-auth')

// Endpoint público (sin auth aunque la clase tenga @ApiBearerAuth):
@ApiSecurity({})   // o manejar con guards que no afecten el spec
```

---

## Ocultar endpoints

```typescript
@ApiExcludeEndpoint()      // oculta un endpoint del spec
@ApiExcludeController()    // oculta todo el controlador
```

---

## Exportar spec como archivo

```typescript
// En main.ts, después de createDocument():
import * as fs from 'fs';
import * as yaml from 'js-yaml';

const document = SwaggerModule.createDocument(app, config);
fs.writeFileSync('./openapi.yaml', yaml.dump(document, { noRefs: false }));
fs.writeFileSync('./openapi.json', JSON.stringify(document, null, 2));
```

---

## Plugin CLI (recomendado para tipos correctos)

El plugin de NestJS CLI mejora el soporte de tipos en la generación automática:

```json
// nest-cli.json
{
  "compilerOptions": {
    "plugins": ["@nestjs/swagger"]
  }
}
```

Con el plugin activo, `@ApiProperty` se infiere automáticamente de los tipos TypeScript y no necesitas decorar cada campo del DTO manualmente.
