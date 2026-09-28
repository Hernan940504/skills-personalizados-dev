# google-drive-manager

Skill para operar **Google Drive** (Mi unidad y unidades compartidas / Shared Drives) desde un
CLI Python sobre la Drive API v3: descargar, exportar, subir, actualizar y organizar archivos.

> Documentación para humanos. Las instrucciones que consume el agente están en `SKILL.md`.

---

## 1. Requisitos

- Python 3.12+.
- Acceso a un proyecto de Google Cloud (GCP) con permiso para habilitar APIs y crear credenciales OAuth.
- Cuenta de Google/Workspace con acceso a las unidades que vas a operar.

## 2. Instalación de dependencias

Instalar desde el mirror institucional **JFrog Artifactory** (configura tu `pip` para apuntar a JFrog):

```bash
pip install -r requirements.txt
```

Dependencias (versiones pinneadas en `requirements.txt`):

```
google-api-python-client==2.198.0
google-auth==2.48.0
google-auth-oauthlib==1.2.2
google-auth-httplib2==0.2.0
```

> Si alguna versión no está disponible en JFrog, ajusta a la versión aprobada más cercana y
> documenta el cambio en el CHANGELOG.

## 3. Configuración en Google Cloud (paso a paso)

### 3.1 Crear/seleccionar el proyecto

1. Entra a la consola de Google Cloud.
2. Crea un proyecto nuevo (o selecciona uno existente destinado a integraciones).

### 3.2 Habilitar la Google Drive API

1. En el proyecto, ve a **APIs y servicios → Biblioteca**.
2. Busca **Google Drive API** y pulsa **Habilitar**.

### 3.3 Configurar la pantalla de consentimiento OAuth

1. Ve a **APIs y servicios → Pantalla de consentimiento de OAuth**.
2. Tipo de usuario:
   - **Interno** si es una organización Google Workspace (recomendado en entorno corporativo:
     restringe el acceso a usuarios del dominio).
   - **Externo** solo si necesitas cuentas fuera del dominio.
3. Completa nombre de la app, correo de soporte y de contacto.
4. En **Scopes**, añade el scope de Drive que vayas a usar (ver sección 5).
5. Si es Externo y no publicas la app, agrega tu cuenta como **usuario de prueba**.

### 3.4 Crear las credenciales OAuth (aplicación de escritorio)

1. Ve a **APIs y servicios → Credenciales → Crear credenciales → ID de cliente de OAuth**.
2. Tipo de aplicación: **Aplicación de escritorio** (installed app).
3. Descarga el JSON de credenciales.

### 3.5 Guardar las credenciales fuera del repositorio

Coloca el JSON descargado en la ruta por defecto (fuera del repo) o define la variable de entorno:

```bash
mkdir -p ~/.config/gdrive-skill
mv ~/Descargas/client_secret_*.json ~/.config/gdrive-skill/credentials.json
```

> **Nunca** versiones `credentials.json` ni `token.json`. Ya están en el `.gitignore` del repo.

## 4. Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `GDRIVE_CREDENTIALS_PATH` | `~/.config/gdrive-skill/credentials.json` | Ruta al JSON de cliente OAuth. |
| `GDRIVE_TOKEN_PATH` | `~/.config/gdrive-skill/token.json` | Ruta donde se guarda el token (se crea en el primer login). |
| `GDRIVE_SCOPES` | `https://www.googleapis.com/auth/drive` | Scopes OAuth, separados por espacios. |

## 5. Scopes: `drive` vs `drive.file`

| Scope | Alcance | Cuándo usarlo |
|---|---|---|
| `https://www.googleapis.com/auth/drive.file` | Solo archivos creados o abiertos por esta app. Menor privilegio. | Si únicamente subes/gestionas archivos propios de la app. |
| `https://www.googleapis.com/auth/drive` | Acceso completo a los archivos del usuario. | **Default de este skill**: `organize` (mover/renombrar/copiar/trash) opera sobre archivos existentes que la app no creó, y eso `drive.file` no lo permite. |

Cambia el scope con `GDRIVE_SCOPES`. Si reduces el scope, algunas operaciones de organización
sobre archivos ajenos a la app dejarán de funcionar. Tras cambiar scopes, borra el `token.json`
y vuelve a ejecutar `auth`.

## 6. Primer login

```bash
python3 scripts/drive_cli.py auth
```

Se abrirá el navegador para autorizar. Al terminar se guarda `token.json` (permisos `0600`) y las
siguientes ejecuciones renuevan el token automáticamente. Si el refresh se revoca, el CLI devuelve
código de salida 7: vuelve a ejecutar `auth`.

## 7. Uso — ejemplos por subcomando

Todos los comandos imprimen **JSON** en stdout. Añade `--pretty` para lectura humana.

### Listar unidades compartidas
```bash
python3 scripts/drive_cli.py drives --pretty
```

### Buscar / listar
```bash
# Por subcadena de nombre y tipo, en todas las unidades
python3 scripts/drive_cli.py search --name-contains "informe" --mime-type application/pdf

# Dentro de una carpeta de una Shared Drive
python3 scripts/drive_cli.py search --drive <DRIVE_ID> --parent <FOLDER_ID>

# Solo Mi unidad, modificados después de una fecha
python3 scripts/drive_cli.py search --scope mydrive --modified-after 2026-01-01T00:00:00

# Limitar/ampliar resultados (default 200; marca "truncated" si hay más)
python3 scripts/drive_cli.py search --name-contains "acta" --limit 50
python3 scripts/drive_cli.py search --parent <FOLDER_ID> --all
```

> Los flags globales (`--pretty`, `--dry-run`, `--yes`, `--log-level`) se aceptan antes o después
> del subcomando: `drive_cli.py drives --pretty` y `drive_cli.py --pretty drives` son equivalentes.

### Descargar / exportar
```bash
# Archivo binario
python3 scripts/drive_cli.py download <FILE_ID> ./descargas/archivo.pdf

# Google Doc exportado a PDF (la extensión se añade sola)
python3 scripts/drive_cli.py download <DOC_ID> ./descargas/informe --export pdf

# Carpeta completa a PDF, conservando estructura
python3 scripts/drive_cli.py download <FOLDER_ID> ./descargas/Contratos --recursive --export pdf
```

**Caso completo: "descarga la carpeta Contratos de la unidad compartida Legal como PDF"**
```bash
# 1) Ubicar la Shared Drive "Legal"
python3 scripts/drive_cli.py drives
# 2) Ubicar la carpeta "Contratos" dentro de esa unidad
python3 scripts/drive_cli.py search --drive <ID_LEGAL> --name "Contratos"
# 3) Descargar recursivamente como PDF
python3 scripts/drive_cli.py download <ID_CONTRATOS> ./Contratos --recursive --export pdf
```

### Subir
```bash
# Simple/resumable automático según tamaño (umbral 5 MB)
python3 scripts/drive_cli.py upload ./archivo.pdf <PARENT_ID>

# Convertir a formato Google (CSV -> Google Sheet)
python3 scripts/drive_cli.py upload ./datos.csv <PARENT_ID> --convert

# Resolver conflicto de nombre existente
python3 scripts/drive_cli.py upload ./doc.docx <PARENT_ID> --on-conflict version
```

### Actualizar
```bash
# Reemplazar contenido (destructivo: requiere --yes)
python3 scripts/drive_cli.py --yes update <FILE_ID> --content ./nueva-version.pdf

# Actualizar metadatos (no destructivo)
python3 scripts/drive_cli.py update <FILE_ID> --name "Contrato v2" --description "Revisión legal"
```

### Organizar
```bash
python3 scripts/drive_cli.py organize mkdir "Proyectos/2026/Q3" --root <PARENT_ID>
python3 scripts/drive_cli.py organize move <FILE_ID> <DEST_FOLDER_ID>
python3 scripts/drive_cli.py organize rename <FILE_ID> "nuevo-nombre.pdf"
python3 scripts/drive_cli.py organize copy <FILE_ID> --name "copia.pdf" --parent <DEST_ID>
python3 scripts/drive_cli.py --yes organize trash <FILE_ID>
python3 scripts/drive_cli.py organize restore <FILE_ID>
```

### Vista previa sin ejecutar (`--dry-run`)
Disponible en toda operación que modifica estado:
```bash
python3 scripts/drive_cli.py --dry-run organize move <FILE_ID> <DEST_FOLDER_ID>
python3 scripts/drive_cli.py --dry-run upload ./archivo.pdf <PARENT_ID>
```

## 8. Códigos de salida

| Código | Significado |
|---|---|
| 0 | Éxito |
| 2 | Error de uso/argumentos |
| 3 | Permisos insuficientes |
| 4 | No encontrado (o ruta ambigua: revisa los candidatos) |
| 5 | Cuota o rate limit excedido |
| 6 | Conflicto no resuelto o confirmación requerida |
| 7 | Autenticación requerida (ejecuta `auth`) |

## 9. Seguridad

- `credentials.json` y `token.json` nunca se versionan (están en `.gitignore`) y viven fuera del repo por defecto.
- Sin secretos hardcodeados; sin telemetría externa.
- Logging estructurado sin contenido de archivos ni tokens.
- Confirmación explícita (`--yes`) o `--dry-run` obligatorios en operaciones destructivas/masivas
  (papelera, reemplazo de contenido, lotes > 10).
- **No hay borrado permanente**: el skill no implementa `files.delete` ni vaciar la papelera; solo
  `trash` (reversible) y `restore`.

## 10. Pruebas

Los tests usan mocks de la Drive API y **no requieren credenciales reales ni red**:

```bash
python3 -m pytest tests/ -q
```

## 11. Estructura

```
google-drive-manager/
├── SKILL.md            # Instrucciones para el agente
├── README.md           # Esta guía
├── requirements.txt    # Dependencias pinneadas
├── scripts/
│   ├── drive_cli.py    # CLI con subcomandos
│   ├── auth.py         # Credenciales/token OAuth
│   ├── drive_client.py # Wrapper de la Drive API (paginación, reintentos)
│   └── mime_map.py     # Mapeo de exportación/conversión
└── tests/              # Tests con mocks (sin llamadas reales)
```

## Autores

- Hernan940504
