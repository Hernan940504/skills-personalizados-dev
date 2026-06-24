'use strict';
const { listSkills, findSkill } = require('../resolvers/findSkill');
const { install, TARGETS } = require('../adapters');

function resolveTargets(opts) {
  if (opts.all) return listSkills();
  if (opts.category) return listSkills().filter((s) => s.category === opts.category);
  const out = [];
  for (const name of opts.names || []) {
    const s = findSkill(name);
    if (!s) { console.error(`No encontrado: ${name}`); process.exitCode = 1; continue; }
    out.push(s);
  }
  return out;
}

function add(opts = {}) {
  const target = opts.target || 'claude-code';
  if (!TARGETS.includes(target)) { console.error(`target inválido: ${target}`); return 2; }
  const mode = opts.mode || 'link';

  const skills = resolveTargets(opts);
  if (!skills.length) { console.error('Nada que instalar. Indica <skill>, --category o --all.'); return 2; }

  let n = 0;
  for (const skill of skills) {
    try {
      const { dest, warnings } = install(target, skill, {
        mode,
        destRoot: opts.destRoot,
        project: opts.project,
        projectRoot: opts.projectRoot,
      });
      console.log(`↳ ${target}/${mode}  ${skill.name} → ${dest}`);
      for (const w of warnings || []) console.log(`    ⚠ ${w}`);
      n++;
    } catch (e) {
      console.error(`✗ ${skill.name}: ${e.message}`);
      process.exitCode = 1;
    }
  }
  console.log(`✓ ${n}/${skills.length} skill(s) instalado(s) (target: ${target})`);
  return 0;
}

module.exports = { add };
