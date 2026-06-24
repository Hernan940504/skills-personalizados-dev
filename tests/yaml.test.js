'use strict';
const { test } = require('node:test');
const assert = require('node:assert');
const yaml = require('../src/utils/yaml');

test('escalares, booleanos y enteros', () => {
  const d = yaml.parse('name: foo\nflag: true\nn: 3\nempty:');
  assert.strictEqual(d.name, 'foo');
  assert.strictEqual(d.flag, true);
  assert.strictEqual(d.n, 3);
  assert.strictEqual(d.empty, '');
});

test('lista inline', () => {
  const d = yaml.parse('tags: [a, b, c]');
  assert.deepStrictEqual(d.tags, ['a', 'b', 'c']);
});

test('lista en bloque', () => {
  const d = yaml.parse('items:\n  - x\n  - y');
  assert.deepStrictEqual(d.items, ['x', 'y']);
});

test('mapa anidado', () => {
  const d = yaml.parse('output:\n  path: "~/x/{{name}}"\n  format: mdc');
  assert.deepStrictEqual(d.output, { path: '~/x/{{name}}', format: 'mdc' });
});

test('escalar plegado multilínea (estilo plain)', () => {
  const src = 'description: Genera el diagrama\n  en varias líneas\n  unidas con espacio\nversion: 0.1.0';
  const d = yaml.parse(src);
  assert.strictEqual(d.description, 'Genera el diagrama en varias líneas unidas con espacio');
  assert.strictEqual(d.version, '0.1.0');
});

test('lista de mapas (examples)', () => {
  const d = yaml.parse('examples:\n  - prompt: "uno"\n  - prompt: "dos"');
  assert.deepStrictEqual(d.examples, [{ prompt: 'uno' }, { prompt: 'dos' }]);
});

test('ignora comentarios', () => {
  const d = yaml.parse('# comentario\nname: foo # inline\n');
  assert.strictEqual(d.name, 'foo');
});
