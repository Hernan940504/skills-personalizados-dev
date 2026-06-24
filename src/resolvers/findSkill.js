'use strict';
const fs = require('fs');
const path = require('path');
const { parseFrontmatter } = require('../utils/frontmatter');

const REPO = path.resolve(__dirname, '..', '..');
const SKILLS_DIR = path.join(REPO, 'skills');

// Lista todas las carpetas de skill (skills/<categoria>/<name>/SKILL.md),
// excluyendo _lib y cualquier carpeta que empiece con "_".
function listSkills() {
  const out = [];
  if (!fs.existsSync(SKILLS_DIR)) return out;
  for (const cat of fs.readdirSync(SKILLS_DIR, { withFileTypes: true })) {
    if (!cat.isDirectory() || cat.name.startsWith('_')) continue;
    const catDir = path.join(SKILLS_DIR, cat.name);
    for (const skill of fs.readdirSync(catDir, { withFileTypes: true })) {
      if (!skill.isDirectory()) continue;
      const dir = path.join(catDir, skill.name);
      const md = path.join(dir, 'SKILL.md');
      if (!fs.existsSync(md)) continue;
      let data = {};
      try {
        data = parseFrontmatter(fs.readFileSync(md, 'utf8')).data;
      } catch (_) { /* ignora frontmatter roto en el listado */ }
      out.push({ name: skill.name, category: cat.name, dir, data });
    }
  }
  return out.sort((a, b) => a.name.localeCompare(b.name));
}

// Resuelve un nombre → registro de skill, o null.
function findSkill(name) {
  return listSkills().find((s) => s.name === name) || null;
}

// ¿El skill depende del motor compartido _lib?
function needsLib(skillDir) {
  const probes = [path.join(skillDir, 'SKILL.md'), path.join(skillDir, 'scripts')];
  for (const p of probes) {
    if (!fs.existsSync(p)) continue;
    const stat = fs.statSync(p);
    const files = stat.isDirectory()
      ? fs.readdirSync(p).map((f) => path.join(p, f))
      : [p];
    for (const f of files) {
      try {
        if (fs.statSync(f).isFile() && fs.readFileSync(f, 'utf8').includes('_lib/')) return true;
      } catch (_) { /* skip */ }
    }
  }
  return false;
}

module.exports = { REPO, SKILLS_DIR, listSkills, findSkill, needsLib };
