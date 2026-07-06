#!/usr/bin/env node
// =====================================================================
// build-manual.mjs — Ensambla el manual de usuario en Markdown a partir de
// `manual.config.json` y las capturas generadas en `manual-output/img/`.
//
// Sin dependencias. Ejecutar DESDE el directorio del proyecto E2E:
//   node /ruta/al/skill/scripts/build-manual.mjs
//
// Overrides por entorno:
//   MANUAL_CONFIG  (default: ./manual.config.json)
//   MANUAL_OUT     (default: ./manual-output)
// =====================================================================
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';

const cfgPath = process.env.MANUAL_CONFIG ?? 'manual.config.json';
const outDir = process.env.MANUAL_OUT ?? 'manual-output';

if (!existsSync(cfgPath)) {
  console.error(`No encuentro ${cfgPath}. Copia templates/manual.config.example.json y edítalo.`);
  process.exit(1);
}

const cfg = JSON.parse(readFileSync(cfgPath, 'utf-8'));
const modules = Array.isArray(cfg.modules) ? cfg.modules : [];

const slug = (s) =>
  String(s)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // elimina diacríticos combinados
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

let md = `# ${cfg.title ?? 'Manual de Usuario'}\n\n`;
if (cfg.intro) md += `${cfg.intro}\n\n`;
md += `> Documento generado con el skill \`docs-portal-manual\` (Playwright).`;
if (cfg.baseURL) md += ` Portal: ${cfg.baseURL}`;
md += `\n\n## Contenido\n\n`;
modules.forEach((m, i) => {
  md += `${i + 1}. [${m.name}](#${slug(m.name)})\n`;
});
md += `\n`;

let missing = 0;
modules.forEach((m, i) => {
  const idx = String(i + 1).padStart(2, '0');
  const rel = `img/${idx}-${m.slug}.png`;
  md += `## ${m.name}\n\n`;
  if (m.description) md += `${m.description}\n\n`;
  if (existsSync(path.join(outDir, rel))) {
    md += `![${m.name}](${rel})\n\n`;
  } else {
    missing++;
    md += `> _Captura pendiente (${rel}). Ejecuta \`npm run manual\` para generarla._\n\n`;
  }
  if (Array.isArray(m.steps) && m.steps.length) {
    md += `**Cómo usarlo:**\n\n`;
    m.steps.forEach((s, j) => {
      md += `${j + 1}. ${s}\n`;
    });
    md += `\n`;
  }
  if (Array.isArray(m.notes) && m.notes.length) {
    md += m.notes.map((n) => `> ℹ️ ${n}`).join('\n') + '\n\n';
  }
});

mkdirSync(outDir, { recursive: true });
const outFile = path.join(outDir, 'manual.md');
writeFileSync(outFile, md);
console.log(`Manual escrito en ${outFile} (${modules.length} módulos, ${missing} captura(s) pendiente(s)).`);
