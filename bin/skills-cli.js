#!/usr/bin/env node
'use strict';
const { list } = require('../src/commands/list');
const { validate } = require('../src/commands/validate');
const { add } = require('../src/commands/add');
const { remove } = require('../src/commands/remove');
const { sync } = require('../src/commands/sync');
const { newSkill } = require('../src/commands/newSkill');

const HELP = `@hbetancur/skills-dev — fábrica de skills agénticos

Uso:
  skills-dev list [--installed] [--category <cat>]
  skills-dev add <skill>... [--target <t>] [--mode link|copy] [--category <cat>] [--all] [--project]
  skills-dev remove <skill>...
  skills-dev sync
  skills-dev new <name> --category <cat> [--author <handle>]
  skills-dev validate [skills/cat/skill ...]

Targets: claude-code (default), cursor, kiro, opencode
Modos:   link (default, symlink al repo), copy (independiente)
`;

function parse(argv) {
  const args = { _: [], flags: {} };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const eq = a.indexOf('=');
      if (eq !== -1) { args.flags[a.slice(2, eq)] = a.slice(eq + 1); }
      else {
        const key = a.slice(2);
        const next = argv[i + 1];
        if (next !== undefined && !next.startsWith('--')) { args.flags[key] = next; i++; }
        else args.flags[key] = true;
      }
    } else {
      args._.push(a);
    }
  }
  return args;
}

function main() {
  const argv = process.argv.slice(2);
  const cmd = argv[0];
  const args = parse(argv.slice(1));
  const f = args.flags;

  switch (cmd) {
    case 'list':
      return list({ installed: !!f.installed, category: f.category });
    case 'add':
      return add({
        names: args._,
        target: f.target,
        mode: f.mode,
        category: f.category,
        all: !!f.all,
        project: !!f.project,
      });
    case 'remove':
      return remove({ names: args._ });
    case 'sync':
      return sync({});
    case 'new':
      return newSkill({ name: args._[0], category: f.category, author: f.author });
    case 'validate':
      return validate(args._);
    case 'help':
    case '--help':
    case '-h':
    case undefined:
      process.stdout.write(HELP);
      return 0;
    default:
      console.error(`Comando desconocido: ${cmd}\n`);
      process.stdout.write(HELP);
      return 2;
  }
}

process.exitCode = main();
