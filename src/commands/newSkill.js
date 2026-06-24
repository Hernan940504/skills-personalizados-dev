'use strict';
const { spawnSync } = require('child_process');
const path = require('path');
const { REPO } = require('../resolvers/findSkill');

// Reusa el scaffolder bash (fuente única del template + sustitución).
function newSkill(opts = {}) {
  if (!opts.name) { console.error('Falta <name>.'); return 2; }
  if (!opts.category) { console.error('Falta --category.'); return 2; }
  const script = path.join(REPO, 'scripts', 'new-skill.sh');
  const args = [script, opts.name, '--category', opts.category];
  if (opts.author) args.push('--author', opts.author);
  const res = spawnSync('bash', args, { stdio: 'inherit' });
  if (res.error) { console.error('No se pudo ejecutar new-skill.sh:', res.error.message); return 1; }
  return res.status || 0;
}

module.exports = { newSkill };
