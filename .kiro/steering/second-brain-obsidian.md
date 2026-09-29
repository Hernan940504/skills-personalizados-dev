# Second Brain (Obsidian) — Consulta e indexación obligatoria

El usuario mantiene un **second brain** en un vault local de Obsidian en `~/second-brain`
(variable `OBSIDIAN_VAULT_PATH`, default `~/second-brain`). La interfaz es el skill
`obsidian-manager` (`skills/workspace/obsidian-manager/scripts/obsidian_cli.py`, Python 3.12+,
sin dependencias). Este vault es memoria persistente entre ventanas de contexto: contiene
contexto de proyectos, referencias, documentación de repos, hallazgos, pendientes y bitácoras.

## Regla 1 — Consultar el brain antes de responder desde cero

Cuando el usuario pregunte por algo que probablemente ya esté documentado — un proyecto, un
repositorio, una cuenta AWS, una arquitectura, un hallazgo, una decisión previa — **primero
buscar en el second brain** antes de investigar desde cero o pedir contexto.

```bash
python3 skills/workspace/obsidian-manager/scripts/obsidian_cli.py search --text "<tema>" --pretty
python3 skills/workspace/obsidian-manager/scripts/obsidian_cli.py search --tag "<tag>" --pretty
```

- Punto de entrada recomendado: `index.md` del vault y los MOC/índices (p. ej.
  `referencias/repos/_indice.md`). Desde ahí navegar por wikilinks/backlinks.
- Si hay una nota relevante, léela y úsala como fuente; cítala por su nombre de nota.
- Si NO hay nada, decirlo explícitamente ("no encontré nada en el second brain sobre X")
  y continuar con la investigación normal.
- No re-investigar lo que el brain ya responde. No duplicar notas existentes: si el tema ya
  tiene nota, actualizarla (`note append`/`note update`) en vez de crear otra.

## Regla 2 — Indexar en el brain lo que se genere

Cuando en la sesión se produzca conocimiento que valga la pena conservar — documentación,
análisis, un informe, un hallazgo, una decisión de arquitectura, contexto nuevo de un
proyecto — **ofrecer indexarlo en el second brain** en la ubicación que corresponda, y hacerlo
tras confirmación del usuario.

Ubicación por convención del vault:
- `proyectos/<proyecto>/` — contexto y notas por línea de negocio/proyecto (ciencuadras,
  libertador, notificador-transversal, wordpress-multitenant, mercadeo, proyectiva).
- `referencias/` — documentación de referencia (repos en `referencias/repos/`, contexto AWS,
  hallazgos de seguridad, inventarios).
- `inbox/` — captura rápida cuando no está claro dónde va (clasificar después).
- `daily/` — bitácora del día (avances, decisiones).
- Pendientes → `task add`.

Cómo indexar:
- Material ya en disco (un `.md`, informe, PDF): `ingest <archivo> --folder <carpeta> --project <proyecto> --tag <...>`.
- Conocimiento generado en la conversación: crear la nota con `note create` (o `ingest` desde
  un archivo temporal) en la carpeta correcta, con frontmatter, tags y wikilinks a notas
  relacionadas; actualizar el índice/MOC del dominio si existe.
- Registrar avances relevantes de la sesión con `daily --add "<resumen>"`.

## Cómo operar el CLI

- Todos los comandos devuelven **JSON en stdout**; parsearlo. Errores en stderr con exit code != 0.
- `--pretty` solo para mostrar al usuario. `--yes` para confirmar operaciones; `--dry-run` para simular.
- Comandos: `init`, `note create/append/update`, `search` (text/tag/backlinks),
  `graph backlinks/outlinks/orphans`, `ingest`, `daily`, `task`, `project`, `sources`,
  `trash`/`restore`. Sin borrado permanente (solo papelera reversible).
- Mantener el grafo sano: usar wikilinks entre notas relacionadas; al terminar un bloque de
  trabajo grande, verificar que no queden enlaces rotos ni notas huérfanas.

## Límites

- No consultar ni indexar por cada mensaje trivial: aplicar la Regla 1 cuando la pregunta
  huela a "esto ya lo trabajamos" y la Regla 2 cuando se genere algo que sobreviva a la sesión.
- No inventar rutas ni notas: si el vault no existe aún, ejecutar `init` una vez (o avisar).
- No ingerir secretos ni credenciales al vault; si un material los contiene, documentarlo
  por referencia/enmascarado como se hizo con los hallazgos de seguridad, nunca el valor.
- Descargar de Drive/Sheets no es de este skill (usar `google-drive-manager`/`sheets-connect`);
  este skill ingiere lo que ya está en disco.
