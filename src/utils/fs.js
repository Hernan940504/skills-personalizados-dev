'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

function expandHome(p) {
  if (!p) return p;
  if (p === '~') return os.homedir();
  if (p.startsWith('~/')) return path.join(os.homedir(), p.slice(2));
  return p;
}

// Destino por defecto para Claude Code; honra CLAUDE_SKILLS_DIR (paridad con install.sh).
function defaultSkillsRoot() {
  return process.env.CLAUDE_SKILLS_DIR || '~/.claude/skills';
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function rmrf(target) {
  fs.rmSync(target, { recursive: true, force: true });
}

// Copia recursiva, excluyendo __pycache__ y *.pyc.
function copyDir(src, dest) {
  ensureDir(dest);
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (entry.name === '__pycache__') continue;
    if (entry.name.endsWith('.pyc')) continue;
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else if (entry.isSymbolicLink()) fs.symlinkSync(fs.readlinkSync(s), d);
    else fs.copyFileSync(s, d);
  }
}

function symlink(src, dest) {
  rmrf(dest);
  fs.symlinkSync(src, dest, 'dir');
}

function writeFile(file, content) {
  ensureDir(path.dirname(file));
  fs.writeFileSync(file, content, 'utf8');
}

module.exports = { expandHome, defaultSkillsRoot, ensureDir, rmrf, copyDir, symlink, writeFile };
