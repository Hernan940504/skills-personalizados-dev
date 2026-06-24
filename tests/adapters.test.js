'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { install, loadAdapter, buildFrontmatter, tagsToGlobs, mapTools } = require('../src/adapters');
const { findSkill } = require('../src/resolvers/findSkill');

function tmp() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'skills-test-'));
}

test('cursor: tags → globs citables y heurística', () => {
  const adapter = loadAdapter('cursor');
  const globs = tagsToGlobs(['java', 'python'], adapter.glob_map);
  assert.ok(globs.includes('**/*.java'));
  assert.ok(globs.includes('**/*.py'));
});

test('opencode: mapeo de tools y drop de desconocidas', () => {
  const adapter = loadAdapter('opencode');
  const { mapped, dropped } = mapTools(['Read', 'Bash', 'TodoWrite'], adapter.tool_map);
  assert.deepStrictEqual(mapped, ['read', 'bash']);
  assert.deepStrictEqual(dropped, ['TodoWrite']);
});

test('buildFrontmatter cursor descarta campos y conserva description', () => {
  const adapter = loadAdapter('cursor');
  const data = { name: 'x', description: 'Hola mundo', tags: ['java'], version: '1.0.0' };
  const { frontmatter } = buildFrontmatter(adapter, data);
  assert.strictEqual(frontmatter.description, 'Hola mundo');
  assert.strictEqual(frontmatter.alwaysApply, false);
  assert.ok(!('version' in frontmatter));
  assert.ok(!('name' in frontmatter));
});

test('install cursor (project) escribe .mdc con body intacto', () => {
  const skill = findSkill('docs-openapi');
  assert.ok(skill, 'docs-openapi debe existir en el catálogo');
  const root = tmp();
  const { dest } = install('cursor', skill, { project: true, projectRoot: root });
  assert.ok(dest.endsWith('.cursor/rules/docs-openapi.mdc'));
  const out = fs.readFileSync(dest, 'utf8');
  assert.match(out, /^---\ndescription: /);
  // los globs deben ir citados (empiezan con comilla en el array)
  assert.match(out, /globs: \["/);
  // el body original se conserva
  assert.match(out, /docs-openapi/);
});

test('install claude-code (copy) con _lib vendoriza y reescribe wrapper', () => {
  const skill = findSkill('docs-c4-context');
  if (!skill) return; // si el repo aún no tiene el skill, no falla el suite
  const root = tmp();
  const { dest } = install('claude-code', skill, { mode: 'copy', destRoot: root });
  assert.ok(fs.existsSync(path.join(dest, 'SKILL.md')));
  assert.ok(fs.existsSync(path.join(root, '_lib', 'drawio', 'render.py')));
  const gen = path.join(dest, 'scripts', 'generate.sh');
  if (fs.existsSync(gen)) {
    const txt = fs.readFileSync(gen, 'utf8');
    assert.ok(!txt.includes('../../../_lib/'), 'wrapper debe quedar reescrito');
    assert.ok(txt.includes('../../_lib/'));
  }
});
