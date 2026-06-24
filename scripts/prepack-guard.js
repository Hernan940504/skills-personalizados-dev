#!/usr/bin/env node
'use strict';
// Red de seguridad de publicación: aborta `npm pack`/`npm publish` si el set a
// empaquetar contiene datos sensibles o artefactos. Es fiable aunque el whitelist
// `files` de package.json tenga prioridad sobre .npmignore.
//
// Se ejecuta como `prepack`. Para publicar de verdad hay que resolver primero
// lo que este guard detecte (ver docs/ARCHITECTURE.md §7).

const { execSync } = require('child_process');
const path = require('path');

const REPO = path.resolve(__dirname, '..');

// Patrones que NUNCA deben publicarse.
const FORBIDDEN = [
  { re: /skills\/devops\/aws-sso-refresh\//, why: 'skill personal con Account IDs / config de empresa' },
  { re: /\/config\.env$/, why: 'configuración con posibles Account IDs' },
  { re: /\.pyc$/, why: 'artefacto Python compilado' },
  { re: /__pycache__\//, why: 'caché Python' },
];

function packList() {
  // `npm pack --dry-run --json` lista exactamente lo que se empaquetaría.
  // --ignore-scripts evita recursión (este guard ES el prepack).
  const out = execSync('npm pack --dry-run --json --ignore-scripts', {
    cwd: REPO,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'ignore'], // descarta los npm notice de stderr
  });
  const data = JSON.parse(out);
  const files = (data[0] && data[0].files) || [];
  return files.map((f) => f.path);
}

function main() {
  let files;
  try {
    files = packList();
  } catch (e) {
    console.error('prepack-guard: no se pudo obtener la lista de pack:', e.message);
    process.exit(1);
  }

  const hits = [];
  for (const f of files) {
    const rule = FORBIDDEN.find((r) => r.re.test(f)); // primera regla que matchea
    if (rule) hits.push(`  ✗ ${f}  (${rule.why})`);
  }

  if (hits.length) {
    console.error('\n🚫 prepack-guard: publicación BLOQUEADA — archivos sensibles/artefactos:\n');
    console.error(hits.join('\n'));
    console.error(
      '\nResuelve antes de publicar:\n' +
      '  • aws-sso-refresh: sácalo del repo público o muévelo a un repo privado.\n' +
      '  • .pyc/__pycache__: `git rm -r --cached skills/_lib/**/__pycache__` (ya están en .gitignore).\n'
    );
    process.exit(1);
  }
  console.log('✓ prepack-guard: sin archivos sensibles en el paquete.');
}

main();
