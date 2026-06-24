'use strict';
const fs = require('fs');
const path = require('path');
const { listSkills, findSkill } = require('../resolvers/findSkill');
const { install } = require('../adapters');
const { expandHome, defaultSkillsRoot } = require('../utils/fs');

// Re-aplica las instalaciones presentes en el destino claude-code, preservando
// el modo: si es symlink → link; si es carpeta → copy.
function sync(opts = {}) {
  const root = expandHome(opts.destRoot || defaultSkillsRoot());
  if (!fs.existsSync(root)) { console.log('Nada que sincronizar (no hay destino).'); return 0; }

  const catalog = new Set(listSkills().map((s) => s.name));
  let n = 0;
  for (const entry of fs.readdirSync(root)) {
    if (entry.startsWith('_')) continue;       // _lib u otros internos
    if (!catalog.has(entry)) continue;          // no es un skill del catálogo
    const dest = path.join(root, entry);
    const mode = fs.lstatSync(dest).isSymbolicLink() ? 'link' : 'copy';
    const skill = findSkill(entry);
    if (!skill) continue;
    install('claude-code', skill, { mode, destRoot: opts.destRoot });
    console.log(`↻ ${entry} (${mode})`);
    n++;
  }
  console.log(`✓ ${n} skill(s) sincronizado(s)`);
  return 0;
}

module.exports = { sync };
