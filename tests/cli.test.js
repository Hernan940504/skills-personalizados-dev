'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const REPO = path.resolve(__dirname, '..');
const CLI = path.join(REPO, 'bin', 'skills-cli.js');

function run(args, env = {}) {
  return spawnSync('node', [CLI, ...args], {
    encoding: 'utf8',
    env: { ...process.env, ...env },
  });
}

test('list muestra el catálogo', () => {
  const r = run(['list']);
  assert.strictEqual(r.status, 0);
  assert.match(r.stdout, /skill\(s\)/);
});

test('validate sale 0 si no hay errores (o reporta)', () => {
  const r = run(['validate', 'skills/docs/docs-openapi']);
  assert.match(r.stdout, /docs-openapi/);
});

test('add claude-code copy + list --installed en sandbox', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'skills-cli-'));
  const env = { CLAUDE_SKILLS_DIR: root };
  const a = run(['add', 'cloud-well-architected-review', '--mode', 'copy'], env);
  assert.strictEqual(a.status, 0, a.stderr);
  assert.ok(fs.existsSync(path.join(root, 'cloud-well-architected-review', 'SKILL.md')));
  const l = run(['list', '--installed'], env);
  assert.match(l.stdout, /cloud-well-architected-review/);
  // remove
  const rm = run(['remove', 'cloud-well-architected-review'], env);
  assert.strictEqual(rm.status, 0);
  assert.ok(!fs.existsSync(path.join(root, 'cloud-well-architected-review')));
});

test('help con comando desconocido sale != 0', () => {
  const r = run(['frobnicate']);
  assert.notStrictEqual(r.status, 0);
});
