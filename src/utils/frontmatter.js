'use strict';
const yaml = require('./yaml');

// Separa un SKILL.md en { data: <frontmatter>, body: <markdown> }.
function parseFrontmatter(text) {
  const norm = text.replace(/\r\n/g, '\n');
  if (!norm.startsWith('---')) {
    return { data: {}, body: norm, ok: false, error: "no empieza con '---'" };
  }
  const end = norm.indexOf('\n---', 3);
  if (end === -1) {
    return { data: {}, body: norm, ok: false, error: "frontmatter sin cierre '---'" };
  }
  const raw = norm.slice(3, end).replace(/^\n/, '');
  const body = norm.slice(end + 4).replace(/^\n/, '');
  let data = {};
  try {
    data = yaml.parse(raw) || {};
  } catch (e) {
    return { data: {}, body, ok: false, error: 'YAML inválido: ' + e.message };
  }
  return { data, body, ok: true };
}

// Serializa un objeto plano de frontmatter a YAML simple (para .mdc / steering / opencode).
function stringifyFrontmatter(data) {
  const lines = ['---'];
  for (const [k, v] of Object.entries(data)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) {
      const items = v.map((x) => {
        const s = String(x);
        // En flow YAML, un escalar con * : # , etc. (o que empieza con *,?,&)
        // debe ir entre comillas (ej. globs "**/*.ts").
        return /^[\w./-]+$/.test(s) ? s : JSON.stringify(s);
      });
      lines.push(`${k}: [${items.join(', ')}]`);
    } else if (typeof v === 'boolean' || typeof v === 'number') {
      lines.push(`${k}: ${v}`);
    } else {
      const s = String(v);
      const needsQuote = /[:#]/.test(s);
      lines.push(`${k}: ${needsQuote ? JSON.stringify(s) : s}`);
    }
  }
  lines.push('---', '');
  return lines.join('\n');
}

module.exports = { parseFrontmatter, stringifyFrontmatter };
