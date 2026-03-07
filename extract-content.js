#!/usr/bin/env node
/**
 * extract-content.js — One-time tool (run from project root)
 *
 * Reads paddy-parade.html, extracts LUCKY_COINS, QUESTION_BANK, and
 * DIALOGUES into content/*.json, then produces paddy-parade.template.html
 * with %%MARKER%% placeholders that build.js can fill back in.
 *
 * Run once:  node extract-content.js
 * After that, edit content/*.json and run:  node build.js
 */
'use strict';

const fs   = require('fs');
const path = require('path');

const GAME_FILE    = path.join(__dirname, 'paddy-parade.html');
const TEMPLATE_OUT = path.join(__dirname, 'paddy-parade.template.html');
const CONTENT_DIR  = path.join(__dirname, 'content');

// ── Step 1: extract constants via direct regex on the source ──────────────────
//
// Instead of eval-ing the whole game script (where `const` leaks are blocked),
// we use anchored regexes to extract the raw JS value literal for each constant,
// then eval just that literal.  These are pure data structures (arrays/objects
// of strings and numbers) so no stubs are needed.

const src = fs.readFileSync(GAME_FILE, 'utf8');
const scriptMatch = src.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) { console.error('No <script> block found'); process.exit(1); }
const js = scriptMatch[1];

function extractValue(pattern, name) {
  const m = js.match(pattern);
  if (!m) {
    console.error(`Could not find ${name} in script.  Check the regex anchor.`);
    process.exit(1);
  }
  try {
    // eslint-disable-next-line no-eval
    return eval('(' + m[1] + ')');
  } catch (e) {
    console.error(`Failed to eval ${name}: ${e.message}`);
    process.exit(1);
  }
}

// Each pattern captures just the VALUE (group 1).
// The lookahead anchors on unique surrounding context so the lazy [\s\S]*? stops
// at exactly the right closing bracket/brace.
const LUCKY_COINS   = extractValue(
  /const LUCKY_COINS = (\[[\s\S]*?\]);\n(?=\nconst QUESTION_BANK)/,
  'LUCKY_COINS'
);
const QUESTION_BANK = extractValue(
  /const QUESTION_BANK = (\[[\s\S]*?\]);\n(?=\n\/\/ ═)/,
  'QUESTION_BANK'
);
const DIALOGUES     = extractValue(
  /const DIALOGUES = (\{[\s\S]*?\});\n(?=\nclass DialogueSystem)/,
  'DIALOGUES'
);

// ── Step 2: save JSON files ──────────────────────────────────────────────────

fs.mkdirSync(CONTENT_DIR, { recursive: true });

fs.writeFileSync(
  path.join(CONTENT_DIR, 'lucky_coins.json'),
  JSON.stringify(LUCKY_COINS, null, 2) + '\n',
  'utf8'
);
fs.writeFileSync(
  path.join(CONTENT_DIR, 'questions.json'),
  JSON.stringify(QUESTION_BANK, null, 2) + '\n',
  'utf8'
);
fs.writeFileSync(
  path.join(CONTENT_DIR, 'dialogues.json'),
  JSON.stringify(DIALOGUES, null, 2) + '\n',
  'utf8'
);

console.log(`✓ content/lucky_coins.json  (${LUCKY_COINS.length} coins)`);
console.log(`✓ content/questions.json    (${QUESTION_BANK.length} questions)`);
console.log(`✓ content/dialogues.json    (${Object.keys(DIALOGUES).length} NPC trees)`);

// ── Step 3: create template by replacing the three const blocks ──────────────

let template = src;

template = template.replace(
  /const LUCKY_COINS = \[[\s\S]*?\];\n(?=\nconst QUESTION_BANK)/,
  'const LUCKY_COINS = %%LUCKY_COINS%%;\n'
);
template = template.replace(
  /const QUESTION_BANK = \[[\s\S]*?\];\n(?=\n\/\/ ═)/,
  'const QUESTION_BANK = %%QUESTION_BANK%%;\n'
);
template = template.replace(
  /const DIALOGUES = \{[\s\S]*?\};\n(?=\nclass DialogueSystem)/,
  'const DIALOGUES = %%DIALOGUES%%;\n'
);

const missing = ['%%LUCKY_COINS%%', '%%QUESTION_BANK%%', '%%DIALOGUES%%']
  .filter(m => !template.includes(m));
if (missing.length) {
  console.error(`ERROR: Failed to insert markers: ${missing.join(', ')}`);
  console.error('Check the regex anchors in extract-content.js.');
  process.exit(1);
}

fs.writeFileSync(TEMPLATE_OUT, template, 'utf8');
console.log(`✓ paddy-parade.template.html`);
console.log(`\nNext steps:`);
console.log(`  Edit content/*.json  then run:  node build.js`);
