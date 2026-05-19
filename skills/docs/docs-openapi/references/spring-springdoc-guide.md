# Spring Boot — springdoc-openapi: guía de anotaciones

## Dependencia Maven (Spring Boot 3.x)

```xml
<dependency>
  <groupId>org.springdoc</groupId>
  <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
  <version>2.3.0</version>
</dependency>
```

Para WebFlux (reactivo):
```xml
<artifactId>springdoc-openapi-starter-webflux-ui</artifactId>
```

Para Spring Boot 2.x (legado):
```xml
<groupId>org.springdoc</groupId>
<artifactId>springdoc-openapi-ui</artifactId>
<version>1.8.0</version>
```

---

## URLs por defecto

| Recurso | URL |
|---|---|
| Swagger UI | `http://localhost:8080/swagger-ui.html` |
| OpenAPI JSON | `http://localhost:8080/v3/api-docs` |
| OpenAPI YAML | `http://localhost:8080/v3/api-docs.yaml` |

Personalizar en `application.properties`:
```properties
springdoc.api-docs.path=/api-docs
springdoc.swagger-ui.path=/swagger-ui.html
springdoc.packages-to-scan=com.example.controller
springdoc.paths-to-match=/api/v1/**
springdoc.swagger-ui.operationsSorter=method
springdoc.swagger-ui.tagsSorter=alpha
springdoc.swagger-ui.persistAuthorization=true
```

---

## Anotaciones en el controlador

### Clase

```java
@Tag(name = "Users", description = "Gestión de usuarios del sistema")
@RestController
@RequestMapping("/api/v1/users")
public class UserController { ... }
```

### Método — GET lista

```java
@Operation(
    summary = "Lista usuarios paginados",
    description = "Retorna todos los usuarios activos con soporte de paginación."
)
@ApiResponses({
    @ApiResponse(responseCode = "200", description = "OK",
        content = @Content(schema = @Schema(implementation = UserResponse.class))),
    @ApiResponse(responseCode = "401", description = "No autenticado",
        content = @Content(schema = @Schema(hidden = true)))
})
@GetMapping
public ResponseEntity<Page<UserResponse>> list(Pageable pageable) { ... }
```

### Método — GET por ID

```java
@Operation(summary = "Obtiene un usuario por ID")
@ApiResponse(responseCode = "200", description = "Usuario encontrado",
    content = @Content(schema = @Schema(implementation = UserResponse.class)))
@ApiResponse(responseCode = "404", description = "Usuario no encontrado")
@GetMapping("/{id}")
public ResponseEntity<UserResponse> getById(
    @Parameter(description = "ID del usuario", required = true, example = "1")
    @PathVariable Long id
) { ... }
```

### Método — POST

```java
@Operation(summary = "Crea un nuevo usuario")
@io.swagger.v3.oas.annotations.parameters.RequestBody(
    description = "Datos del usuario a crear",
    required = true,
    content = @Content(schema = @Schema(implementation = CreateUserRequest.class))
)
@ApiResponse(responseCode = "201", description = "Creado exitosamente")
@ApiResponse(responseCode = "400", description = "Datos inválidos")
@PostMapping
@ResponseStatus(HttpStatus.CREATED)
public ResponseEntity<UserResponse> create(@Valid @RequestBody CreateUserRequest req) { ... }
```

### Parámetros de query

```java
@Parameter(in = ParameterIn.QUERY, name = "status",
    description = "Filtrar por estado", required = false,
    schema = @Schema(type = "string", allowableValues = {"active", "inactive"}))
@GetMapping
public List<UserResponse> list(@RequestParam(required = false) String status) { ... }
```

---

## Anotaciones en DTOs

```java
@Schema(description = "Request para crear un usuario")
public class CreateUserRequest {

    @Schema(description = "Nombre completo", example = "Juan García", minLength = 1, maxLength = 100)
    @NotBlank
    private String name;

    @Schema(description = "Correo electrónico único", example = "juan@example.com", format = "email")
    @Email
    @NotBlank
    private String email;

    @Schema(description = "Rol del usuario", allowableValues = {"ADMIN", "USER", "VIEWER"})
    private String role;

    @Schema(description = "ID del departamento al que pertenece", example = "5", nullable = true)
    private Long departmentId;
}
```

---

## Ocultar endpoints del spec

```java
@Hidden                          // oculta el endpoint completo
@GetMapping("/internal/health")
public String health() { ... }
```

```java
// Ocultar un campo del DTO
@Schema(hidden = true)
private String internalAuditField;
```

---

## Agrupar controladores en múltiples specs (grupos)

```java
@Bean
public GroupedOpenApi publicApi() {
    return GroupedOpenApi.builder()
        .group("public")
        .pathsToMatch("/api/v1/**")
        .build();
}

@Bean
public GroupedOpenApi adminApi() {
    return GroupedOpenApi.builder()
        .group("admin")
        .pathsToMatch("/admin/**")
        .build();
}
```

Los grupos aparecen en un dropdown en la parte superior de Swagger UI.

---

## Exportar spec como archivo estático (CI/CD)

```bash
# Con el servidor corriendo
curl http://localhost:8080/v3/api-docs.yaml -o openapi.yaml

# Con Maven plugin (sin servidor):
# mvn springdoc-openapi:generate
```

Plugin Maven para generar en build time:
```xml
<plugin>
  <groupId>org.springdoc</groupId>
  <artifactId>springdoc-openapi-maven-plugin</artifactId>
  <version>1.4</version>
  <executions>
    <execution>
      <id>integration-test</id>
      <goals><goal>generate</goal></goals>
    </execution>
  </executions>
  <configuration>
    <apiDocsUrl>http://localhost:8080/v3/api-docs.yaml</apiDocsUrl>
    <outputFileName>openapi.yaml</outputFileName>
    <outputDir>${project.build.directory}</outputDir>
  </configuration>
</plugin>
```
