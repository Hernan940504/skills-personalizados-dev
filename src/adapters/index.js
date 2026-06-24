'use strict';
const fs = require('fs');
const path = require('path');
const yaml = require('../utils/yaml');
const { parseFrontmatter, stringifyFrontmatter } = require('../utils/frontmatter');
const { expandHome, defaultSkillsRoot, ensureDir, rmrf, copyDir, symlink, writeFile } = require('../utils/fs');
const { REPO, needsLib } = require('../resolvers/findSkill');

const ADAPTERS_DIR = path.join(REPO, 'adapters');
const TARGETS = ['claude-code', 'cursor', 'kiro', 'opencode'];

function loadAdapter(target) {
  const file = path.join(ADAPTERS_DIR, target, 'adapter.yml');
  if (!fs.existsSync(file)) throw new Error(`adapter.yml no encontrado para target: ${target}`);
  return yaml.parse(fs.readFileSync(file, 'utf8'));
}

function tagsToGlobs(tags, globMap) {
  const globs = [];
  for (const t of tags || []) {
    const g = globMap && globMap[t];
    if (g) for (const x of g) if (!globs.includes(x)) globs.push(x);
  }
  return globs;
}

function mapTools(tools, toolMap) {
  const mapped = [];
  const dropped = [];
  for (const t of tools || []) {
    if (toolMap && toolMap[t]) mapped.push(toolMap[t]);
    else dropped.push(t);
  }
  return { mapped, dropped };
}

// Aplica el frontmatter destino según las reglas declaradas (subset por target).
function buildFrontmatter(adapter, data) {
  const out = {};
  const warnings = [];
  const spec = adapter.frontmatter || {};
  for (const [key, tmpl] of Object.entries(spec)) {
    const m = /^{{\s*([\w.-]+)\s*(\|\s*[\w]+)?\s*}}$/.exec(String(tmpl));
    if (!m) { out[key] = tmpl; continue; }
    const field = m[1];
    const filter = m[2] ? m[2].replace('|', '').trim() : null;
    let val = data[field];
    if (filter === 'toGlobs') val = tagsToGlobs(data.tags, adapter.glob_map);
    else if (filter === 'toOpenCodeTools') {
      const { mapped, dropped } = mapTools(data['allowed-tools'], adapter.tool_map);
      if (dropped.length) warnings.push(`tools sin equivalente eliminadas: ${dropped.join(', ')}`);
      val = mapped;
    }
    if (val !== undefined && val !== '') out[key] = val;
  }
  return { frontmatter: out, warnings };
}

// claude-code: copia o symlink de la carpeta completa + _lib si aplica.
function installClaudeCode(skill, { mode, destRoot }) {
  const root = expandHome(destRoot || defaultSkillsRoot());
  ensureDir(root);
  const dest = path.join(root, skill.name);
  rmrf(dest);
  const warnings = [];

  if (mode === 'link') {
    symlink(skill.dir, dest);
  } else {
    copyDir(skill.dir, dest);
    if (needsLib(skill.dir)) {
      const libDest = path.join(root, '_lib');
      rmrf(libDest);
      copyDir(path.join(REPO, 'skills', '_lib'), libDest);
      // Reescribe wrappers de la COPIA: ../../../_lib → ../../_lib (layout plano).
      const scriptsDir = path.join(dest, 'scripts');
      if (fs.existsSync(scriptsDir)) {
        for (const f of fs.readdirSync(scriptsDir)) {
          if (!f.endsWith('.sh')) continue;
          const p = path.join(scriptsDir, f);
          const txt = fs.readFileSync(p, 'utf8').replace(/\.\.\/\.\.\/\.\.\/_lib\//g, '../../_lib/');
          fs.writeFileSync(p, txt);
        }
      }
    }
  }
  return { dest, warnings };
}

// cursor/kiro/opencode: reescribe frontmatter, copia body, escribe archivo único.
function installSingleFile(target, adapter, skill, { project, projectRoot }) {
  const md = fs.readFileSync(path.join(skill.dir, 'SKILL.md'), 'utf8');
  const { data, body } = parseFrontmatter(md);
  const { frontmatter, warnings } = buildFrontmatter(adapter, data);

  // Warnings declarados condicionalmente (ej. needs_lib).
  for (const w of adapter.warnings || []) {
    if (w.condition === 'needs_lib' && needsLib(skill.dir)) warnings.push(w.message);
  }

  const tmpl = project && adapter.output.project_path ? adapter.output.project_path : adapter.output.path;
  let outPath = tmpl.replace('{{name}}', skill.name);
  outPath = project ? path.join(projectRoot || process.cwd(), outPath) : expandHome(outPath);

  const content = stringifyFrontmatter(frontmatter) + '\n' + body;
  writeFile(outPath, content);
  return { dest: outPath, warnings };
}

function install(target, skill, opts = {}) {
  if (!TARGETS.includes(target)) throw new Error(`target inválido: ${target} (usa: ${TARGETS.join(', ')})`);
  const adapter = loadAdapter(target);
  if (target === 'claude-code') return installClaudeCode(skill, opts);
  return installSingleFile(target, adapter, skill, opts);
}

module.exports = { TARGETS, loadAdapter, buildFrontmatter, tagsToGlobs, mapTools, install };
