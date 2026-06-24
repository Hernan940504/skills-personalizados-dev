'use strict';
// Parser YAML mínimo (subset) — cero dependencias.
// Soporta: comentarios (#), mapas anidados por indentación (2 espacios),
// listas en bloque (- item), listas inline [a, b], escalares con/sin comillas,
// booleanos y valores plegados multilínea triviales. Pensado para los YAML
// que este repo controla (frontmatter de SKILL.md y adapters/*/adapter.yml).
// No es un parser YAML completo; evita features avanzadas (anchors, flow maps).

function stripComment(line) {
  // Quita comentarios fuera de comillas.
  let inS = false, inD = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (c === "'" && !inD) inS = !inS;
    else if (c === '"' && !inS) inD = !inD;
    else if (c === '#' && !inS && !inD && (i === 0 || line[i - 1] === ' ')) {
      return line.slice(0, i);
    }
  }
  return line;
}

function coerce(raw) {
  if (raw === undefined) return undefined;
  let v = raw.trim();
  if (v === '') return '';
  if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
    return v.slice(1, -1);
  }
  if (v.startsWith('[') && v.endsWith(']')) {
    const inner = v.slice(1, -1).trim();
    if (!inner) return [];
    return inner.split(',').map((s) => coerce(s));
  }
  if (v === 'true') return true;
  if (v === 'false') return false;
  if (v === 'null' || v === '~') return null;
  if (/^-?\d+$/.test(v)) return parseInt(v, 10);
  return v;
}

function indentOf(line) {
  return line.length - line.replace(/^ +/, '').length;
}

// Parsea un bloque de líneas a un nivel de indentación dado.
function parseBlock(lines, start, end, baseIndent) {
  // Detecta lista en bloque.
  let i = start;
  while (i < end && lines[i].trim() === '') i++;
  if (i < end && /^\s*-\s?/.test(lines[i]) && indentOf(lines[i]) === baseIndent) {
    const arr = [];
    let j = i;
    while (j < end) {
      const line = lines[j];
      if (line.trim() === '') { j++; continue; }
      const ind = indentOf(line);
      if (ind < baseIndent) break;
      if (ind === baseIndent && /^\s*-\s?/.test(line)) {
        const rest = line.replace(/^\s*-\s?/, '');
        // ¿item escalar o item mapa (key: ...) ?
        if (/^[\w-]+\s*:/.test(rest)) {
          // mapa inline en item: recoge sub-líneas
          const subStart = j;
          // reescribimos la primera línea quitando "- " manteniendo indent
          const collected = [' '.repeat(baseIndent + 2) + rest];
          let k = j + 1;
          while (k < end) {
            if (lines[k].trim() === '') { k++; continue; }
            if (indentOf(lines[k]) <= baseIndent) break;
            collected.push(lines[k]);
            k++;
          }
          arr.push(parseBlock(collected, 0, collected.length, baseIndent + 2).value);
          j = k;
        } else {
          arr.push(coerce(rest));
          j++;
        }
      } else {
        break;
      }
    }
    return { value: arr, next: j };
  }

  // Mapa.
  const obj = {};
  let j = i;
  while (j < end) {
    const line = lines[j];
    if (line.trim() === '') { j++; continue; }
    const ind = indentOf(line);
    if (ind < baseIndent) break;
    if (ind > baseIndent) { j++; continue; } // defensivo
    const m = line.slice(baseIndent).match(/^([\w.-]+):\s?(.*)$/);
    if (!m) { j++; continue; }
    const key = m[1];
    const inline = m[2];
    if (inline !== '') {
      // ¿escalar plegado multilínea? Une continuaciones más indentadas que no
      // sean una nueva clave ni un item de lista (estilo "plain" de YAML).
      let buf = inline;
      let k = j + 1;
      while (k < end) {
        if (lines[k].trim() === '') { k++; continue; }
        if (indentOf(lines[k]) <= baseIndent) break;
        const t = lines[k].trim();
        if (/^[\w-]+:(\s|$)/.test(t) || /^-\s/.test(t)) break;
        buf += ' ' + t;
        k++;
      }
      obj[key] = coerce(buf);
      j = k;
    } else {
      // valor anidado (mapa/lista) o vacío
      let k = j + 1;
      while (k < end && lines[k].trim() === '') k++;
      if (k < end && indentOf(lines[k]) > baseIndent) {
        const childIndent = indentOf(lines[k]);
        const sub = parseBlock(lines, j + 1, end, childIndent);
        obj[key] = sub.value;
        j = sub.next;
      } else {
        obj[key] = '';
        j++;
      }
    }
  }
  return { value: obj, next: j };
}

function parse(text) {
  const lines = text
    .replace(/\r\n/g, '\n')
    .split('\n')
    .map(stripComment)
    .map((l) => l.replace(/\s+$/, ''));
  // documento inicia en indent 0
  const { value } = parseBlock(lines, 0, lines.length, 0);
  return value;
}

module.exports = { parse };
