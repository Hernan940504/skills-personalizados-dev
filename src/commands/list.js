'use strict';
const fs = require('fs');
const path = require('path');
const { listSkills } = require('../resolvers/findSkill');
const { expandHome, defaultSkillsRoot } = require('../utils/fs');

function isInstalled(name, destRoot) {
  const root = expandHome(destRoot || defaultSkillsRoot());
  try { return fs.existsSync(path.join(root, name)); } catch (_) { return false; }
}

function list(opts = {}) {
  let skills = listSkills();
  if (opts.category) skills = skills.filter((s) => s.category === opts.category);
  if (opts.installed) skills = skills.filter((s) => isInstalled(s.name, opts.destRoot));

  if (!skills.length) { console.log('(sin skills que mostrar)'); return 0; }

  const w = Math.max(...skills.map((s) => s.name.length));
  for (const s of skills) {
    const tag = isInstalled(s.name, opts.destRoot) ? '●' : '○';
    const desc = String(s.data.description || '').replace(/\s+/g, ' ').slice(0, 90);
    console.log(`${tag} ${s.name.padEnd(w)}  [${s.category}]  ${desc}`);
  }
  console.log(`\n${skills.length} skill(s) · ● instalado · ○ disponible`);
  return 0;
}

module.exports = { list };
