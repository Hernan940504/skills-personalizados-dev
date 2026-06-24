'use strict';
const { spawnSync } = require('child_process');
const path = require('path');
const { REPO } = require('../resolvers/findSkill');

// Reusa el validador Python (fuente de verdad de las reglas de SKILL-FORMAT §5).
function validate(targets = []) {
  const script = path.join(REPO, 'scripts', 'validate.py');
  const res = spawnSync('python3', [script, ...targets], { stdio: 'inherit' });
  if (res.error) {
    console.error('No se pudo ejecutar python3 scripts/validate.py:', res.error.message);
    return 1;
  }
  return res.status || 0;
}

module.exports = { validate };
