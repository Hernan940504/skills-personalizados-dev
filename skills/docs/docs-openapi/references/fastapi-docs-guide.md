# FastAPI — documentación built-in: guía de enriquecimiento

FastAPI genera OpenAPI 3.0 automáticamente desde el código Python. Este skill se enfoca en **enriquecer** lo que ya genera para obtener un spec completo y usable.

---

## URLs por defecto

| Recurso | URL |
|---|---|
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |

Personalizar o deshabilitar:
```python
app = FastAPI(
    docs_url="/api-docs",      # cambiar URL de Swagger UI
    redoc_url="/api-redoc",    # cambiar URL de ReDoc
    openapi_url="/openapi.json",
    # docs_url=None,           # deshabilitar Swagger UI
)
```

---

## Metadatos de la aplicación

```python
app = FastAPI(
    title="Mi API",
    description="""
## Descripción de la API

Soporta **Markdown completo** aquí.

### Secciones
- Autenticación: JWT Bearer en header `Authorization`
- Paginación: parámetros `page` y `size`
    """,
    version="1.0.0",
    terms_of_service="https://example.com/terms",
    contact={
        "name": "Equipo de Desarrollo",
        "url": "https://example.com/soporte",
        "email": "dev@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {"name": "users", "description": "Operaciones sobre usuarios"},
        {"name": "auth", "description": "Autenticación y autorización"},
    ],
)
```

---

## Enriquecer rutas

### summary, description y tags

```python
@router.get(
    "/{id}",
    summary="Obtiene un usuario por ID",
    description="Busca y retorna un usuario por su ID único. Retorna 404 si no existe.",
    tags=["users"],
    response_description="Usuario encontrado exitosamente",
)
async def get_user(id: int): ...
```

### Documentar múltiples respuestas

```python
from fastapi import status

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    responses={
        400: {
            "description": "Datos de entrada inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "El email ya está en uso"}
                }
            },
        },
        422: {"description": "Error de validación Pydantic"},
    },
)
async def create_user(data: CreateUserRequest): ...
```

### Deprecar un endpoint

```python
@router.get("/old-endpoint", deprecated=True)
async def old_endpoint(): ...
```

---

## Pydantic models — enriquecimiento con Field

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    viewer = "viewer"

class CreateUserRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Juan García",
                "email": "juan@example.com",
                "role": "user",
            }
        }
    }

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre completo del usuario",
        example="Juan García",
    )
    email: EmailStr = Field(
        ...,
        description="Correo electrónico único del usuario",
        example="juan@example.com",
    )
    role: UserRole = Field(
        UserRole.user,
        description="Rol del usuario en el sistema",
    )
    department_id: Optional[int] = Field(
        None,
        description="ID del departamento (opcional)",
        example=5,
        gt=0,
    )
```

---

## Parámetros de path, query y header

```python
from fastapi import Path, Query, Header, Depends

@router.get("/{user_id}/orders")
async def get_user_orders(
    user_id: int = Path(
        ...,
        gt=0,
        description="ID del usuario",
        example=1,
    ),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(20, ge=1, le=100, description="Items por página"),
    status: Optional[str] = Query(
        None,
        description="Filtrar por estado",
        regex="^(pending|completed|cancelled)$",
    ),
    x_request_id: Optional[str] = Header(None, description="ID de traza del request"),
): ...
```

---

## Seguridad (JWT Bearer)

```python
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Token JWT. Obtenerlo en POST /auth/login",
)

@router.get("/protected", dependencies=[Depends(security_scheme)])
async def protected_route(): ...
```

Configurar el scheme en el spec globalmente:
```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi
```

---

## Exportar openapi.yaml

```bash
# Método 1 — con servidor corriendo
curl http://localhost:8000/openapi.json | python3 -c "
import sys, json, yaml
print(yaml.dump(json.load(sys.stdin), allow_unicode=True, sort_keys=False))
" > openapi.yaml

# Método 2 — sin servidor (importando la app)
python3 -c "
import yaml
from app.main import app
with open('openapi.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(app.openapi(), f, allow_unicode=True, sort_keys=False)
print('openapi.yaml generado')
"
```

Dependencia necesaria: `pip install pyyaml`

---

## Estructurar por routers con prefijo y tags

```python
# app/routers/users.py
router = APIRouter(prefix="/users", tags=["users"])

# app/main.py
from app.routers import users, orders, auth

app.include_router(auth.router,   prefix="/api/v1", tags=["auth"])
app.include_router(users.router,  prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
```

Los `tags` del router se heredan a todos sus endpoints, pero se pueden sobrescribir por endpoint.
