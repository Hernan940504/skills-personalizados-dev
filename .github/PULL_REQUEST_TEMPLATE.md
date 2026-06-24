<!-- Describe el cambio en una línea en el título: feat(skill): add <name> | fix(cli): ... -->

## Qué cambia

<!-- Resumen breve. Si añade un skill, di cuál y en qué categoría. -->

## Tipo

- [ ] Nuevo skill
- [ ] Mejora a skill existente
- [ ] CLI / adaptadores / infraestructura
- [ ] Documentación

## Checklist

- [ ] `python3 scripts/validate.py` pasa sin errores
- [ ] `node --test tests/` pasa
- [ ] Si es skill: tiene `SKILL.md` + `README.md` y secciones `## Cuándo usar` / `## Cuándo NO usar`
- [ ] `version` correcta (0.1.0 para skill nuevo; bump según SKILL-FORMAT §6)
- [ ] Sin secretos, Account IDs, paths absolutos del autor ni datos personales
- [ ] Si usa `skills/_lib/`: el contacto es vía `scripts/generate.sh` (no llama `_lib/` directo)
