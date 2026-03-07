#!/usr/bin/env node
/**
 * build.js — Assemble paddy-parade.html from template + content JSON files.
 *
 * Run:  node build.js
 *
 * Reads:
 *   paddy-parade.template.html   (structural template with %%MARKER%% placeholders)
 *   content/lucky_coins.json
 *   content/questions.json
 *   content/dialogues.json
 *
 * Writes:
 *   paddy-parade.html
 */
'use strict';

const fs   = require('fs');
const path = require('path');

const TEMPLATE_FILE = path.join(__dirname, 'paddy-parade.template.html');
const OUT_FILE      = path.join(__dirname, 'paddy-parade.html');
const CONTENT_DIR   = path.join(__dirname, 'content');

// Check template exists
if (!fs.existsSync(TEMPLATE_FILE)) {
  console.error('ERROR: paddy-parade.template.html not found.');
  console.error('Run node extract-content.js once to create it.');
  process.exit(1);
}

// Read template
let output = fs.readFileSync(TEMPLATE_FILE, 'utf8');

// Read content files
function readJSON(filename) {
  const p = path.join(CONTENT_DIR, filename);
  if (!fs.existsSync(p)) {
    console.error(`ERROR: ${p} not found.  Run node extract-content.js first.`);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

const LUCKY_COINS   = readJSON('lucky_coins.json');
const QUESTION_BANK = readJSON('questions.json');
const DIALOGUES     = readJSON('dialogues.json');

// Replace markers (pretty-print so the output is readable and diffable)
output = output.replace('%%LUCKY_COINS%%',   JSON.stringify(LUCKY_COINS, null, 2));
output = output.replace('%%QUESTION_BANK%%', JSON.stringify(QUESTION_BANK, null, 2));
output = output.replace('%%DIALOGUES%%',     JSON.stringify(DIALOGUES, null, 2));

// Verify all markers filled
const remaining = ['%%LUCKY_COINS%%', '%%QUESTION_BANK%%', '%%DIALOGUES%%']
  .filter(m => output.includes(m));
if (remaining.length) {
  console.error(`ERROR: Unfilled markers in template: ${remaining.join(', ')}`);
  console.error('Check paddy-parade.template.html for missing %%MARKER%% entries.');
  process.exit(1);
}

fs.writeFileSync(OUT_FILE, output, 'utf8');
console.log(`✓ paddy-parade.html rebuilt`);
console.log(`  ${LUCKY_COINS.length} coins · ${QUESTION_BANK.length} questions · ${Object.keys(DIALOGUES).length} NPC trees`);
