'use strict';
const fs = require('fs');
const path = require('path');
const { expandHome, defaultSkillsRoot, rmrf } = require('../utils/fs');

// Solo elimina del target claude-code (carpeta/symlink). Otros targets son
// archivos sueltos: se eliminan por ruta directa si se pasa --project.
function remove(opts = {}) {
  const root = expandHome(opts.destRoot || defaultSkillsRoot());
  let n = 0;
  for (const name of opts.names || []) {
    const dest = path.join(root, name);
    if (safeExists(dest)) {
      rmrf(dest);
      console.log(`✗ removido ${name} (${dest})`);
      n++;
    } else {
      console.error(`No instalado: ${name}`);
      process.exitCode = 1;
    }
  }
  console.log(`✓ ${n} skill(s) removido(s)`);
  return 0;
}

function safeExists(p) {
  try { fs.lstatSync(p); return true; } catch (_) { return false; }
}

module.exports = { remove };
