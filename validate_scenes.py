#!/usr/bin/env python3
"""
validate_scenes.py — Dev tool for Paddy's Parade Day Adventure
Validates scene definitions against required schema and cross-references.

Usage:
  python validate_scenes.py              # validate all scenes
  python validate_scenes.py <scene_id>  # validate one scene
  python validate_scenes.py --template  # print copy-pasteable JS template
"""

import sys
import json
import os
import subprocess
import re

GAME_FILE = os.path.join(os.path.dirname(__file__), 'paddy-parade.html')

# ── Node.js extractor script ─────────────────────────────────────────────────

NODE_EXTRACTOR = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');

// Extract script block
const scriptMatch = src.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) { console.error('No script block found'); process.exit(1); }
const js = scriptMatch[1];

// Polyfill minimal browser APIs
const W = 320, H = 240, VIEWPORT_H = 195;
function makeRect(x,y,w,h){return{x,y,w,h};}
function roundRect(){}
function drawBgPub(){}
function drawBgCathedral(){}
function drawBgSteamtown(){}
function drawBgLackawanna(){}
function drawBgParade(){}
function drawBgFootrace(){}
function drawNPC(){}
function drawPaddy(){}
function drawShamrock(){}
function drawItemIcon(){}
function wrapText(){}

// Stub classes
class SoundSystem { coin(){} correct(){} wrong(){} pickup(){} }
class GameState { constructor(){this.flags={};this.score=0;} getFlag(f){return this.flags[f];} setFlag(f,v){this.flags[f]=v;} reset(){} }
class Input { constructor(){} }
class UISystem { constructor(){} render(){} handleInventoryTap(){return false;} closePopup(){} }
class DialogueSystem { constructor(){} async run(){} render(){} }
class Game { constructor(){} }
const Storage = { save(){}, load(k,d){return d;}, clear(){} };
const document = { createElement(){ return { getContext(){ return { createLinearGradient(){return{addColorStop:()=>{}};}, createRadialGradient(){return{addColorStop:()=>{}};}, fillRect(){}, strokeRect(){}, beginPath(){}, moveTo(){}, lineTo(){}, arc(){}, ellipse(){}, bezierCurveTo(){}, quadraticCurveTo(){}, closePath(){}, fill(){}, stroke(){}, fillText(){}, measureText(){return{width:0};}, save(){}, restore(){}, translate(){}, rotate(){}, scale(){}, setLineDash(){}, drawImage(){} }; } }; } };
const window = { onload: null, AudioContext: function(){}, webkitAudioContext: function(){} };
const canvas = { getContext(){ return {}; }, addEventListener(){} };

// Execute the script
try {
    eval(js.replace(/'use strict';/, '').replace(/window\.onload\s*=.*$/ms, ''));
} catch(e) {
    // ignore runtime errors from game startup — we just need the constants
}

// Serialize what we need
const out = {
  SCENES: Object.fromEntries(Object.entries(SCENES).map(([k,v]) => [k, {
    id: v.id,
    name: v.name,
    paddyStart: v.paddyStart,
    hasBg: typeof v.drawBg === 'function',
    npcs: (v.npcs||[]).map(n => ({id:n.id, type:n.type, dialogueId:n.dialogueId})),
    hotspots: (v.hotspots||[]).map(h => ({
      id:h.id, name:h.name,
      rect:h.rect, verbs:h.verbs,
      isExit:h.isExit||false, exitTo:h.exitTo||null,
      item:h.item||null, flag:h.flag||null, requireFlag:h.requireFlag||null
    })),
    dialogueKeys: Object.keys(v.dialogues||{}),
  }])),
  DIALOGUE_KEYS: Object.keys(DIALOGUES),
  DIALOGUE_NODES: Object.fromEntries(Object.entries(DIALOGUES).map(([k,v]) => [k, Object.keys(v)])),
  DIALOGUE_FAREWELL_FLAGS: Object.fromEntries(
    Object.entries(DIALOGUES)
      .filter(([,v]) => v.farewell && v.farewell.doneFlag)
      .map(([k,v]) => [k, v.farewell.doneFlag])
  ),
  DIALOGUE_QUIZ_SCENES: Object.fromEntries(
    Object.entries(DIALOGUES).map(([k,v]) => {
      const scenes = [];
      for (const [,node] of Object.entries(v)) {
        if (node && node.quizFromBank) scenes.push(node.quizFromBank.scene);
      }
      return [k, scenes];
    })
  ),
  QUESTION_BANK_SCENES: QUESTION_BANK.reduce((acc, q) => {
    if (!acc[q.scene]) acc[q.scene] = {1:0,2:0,3:0};
    acc[q.scene][q.difficulty] = (acc[q.scene][q.difficulty]||0)+1;
    return acc;
  }, {}),
  LUCKY_COIN_SCENES: LUCKY_COINS.map(c => c.scene),
  ITEM_IDS: ITEM_IDS,
};
console.log(JSON.stringify(out, null, 2));
"""

# ── Template output ──────────────────────────────────────────────────────────

TEMPLATE = """
// ── NEW SCENE TEMPLATE ──────────────────────────────────────────────────────
// 1. Create drawBgMyScene(ctx) in Section 5 (NO Math.random() inside it!)
// 2. Add NPC type to drawNPC() if needed
// 3. Add to SCENES (inside the SCENES const object):
my_scene: {
  id: 'my_scene',
  name: 'My Scene Name',
  paddyStart: { x: 80, y: 155 },
  drawBg: drawBgMyScene,
  npcs: [{ id: 'my_npc', type: 'existing_type', x: 240, y: 155, dialogueId: 'my_npc' }],
  hotspots: [
    { id: 'prop_1',     name: 'Prop Name',   rect: makeRect(x,y,w,h), verbs: ['look'] },
    { id: 'my_item',   name: 'Item Name',   rect: makeRect(x,y,w,h), verbs: ['look','take'],
      item: 'my_item_id', flag: 'has_my_item', requireFlag: 'quiz_my_scene_done' },
    { id: 'exit_next', name: 'Exit Name',   rect: makeRect(0,y,w,h), verbs: ['look','use'],
      isExit: true, exitTo: 'next_scene' },
  ],
  dialogues: {
    prop_1:    'Description of prop.',
    my_item:   'Description of item.',
    exit_next: 'Description of exit.',
  },
},
// 4. Add dialogue tree to DIALOGUES:
my_npc: {
  root: { lines: ['...'], next: 'quiz1' },
  quiz1: { quizFromBank: { scene: 'my_scene' }, next: 'farewell' },
  farewell: { lines: ['...'], doneFlag: 'quiz_my_scene_done' },
  already_done: { lines: ['...'] },
},
// 5.  Add item to ITEM_IDS + ITEM_NAMES + drawItemIcon() switch
// 6.  Add item pickup rendering to _renderPickupItems()
// 7.  Add exit sign entry to _renderExitSigns() defs
// 8.  Add to handleVerb 'go' itemWarnings + quizFlag map
// 9.  Add 6+ questions to QUESTION_BANK (2 per difficulty level)
// 10. Add coin to LUCKY_COINS array
// 11. Add 'my_scene' to _cacheSessionQuestions() scenes array
// 12. Update marshal checkItems flag list for new item flag
// 13. Update ITEM_IDS, HUD dots, inventory bar slot width, help screen
// 14. Update float item list in _renderAmbient, handleVerb 'use', _useItemOnHotspot
// 15. Run: python validate_scenes.py my_scene
"""

# ── Extractor ────────────────────────────────────────────────────────────────

def extract_game_data():
    """Run node.js to extract game constants from the HTML file."""
    try:
        result = subprocess.run(
            ['node', '-e', NODE_EXTRACTOR, '--', GAME_FILE],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print(f"  [Node error] {result.stderr[:300]}")
            return None
        return json.loads(result.stdout)
    except FileNotFoundError:
        print("  ERROR: node.js not found. Install Node.js to use this tool.")
        return None
    except json.JSONDecodeError as e:
        print(f"  ERROR: Could not parse Node.js output: {e}")
        return None
    except subprocess.TimeoutExpired:
        print("  ERROR: Node.js timed out")
        return None

# ── Validators ───────────────────────────────────────────────────────────────

def validate_scene(scene_id, data):
    checks_pass = 0
    checks_total = 0
    errors = []

    scene = data['SCENES'].get(scene_id)
    if not scene:
        print(f"  ERROR: scene '{scene_id}' not found in SCENES")
        return 0, 1

    def check(label, cond, detail=''):
        nonlocal checks_pass, checks_total
        checks_total += 1
        if cond:
            print(f"  ✓ {label}")
            checks_pass += 1
        else:
            print(f"  ✗ {label}{(' — ' + detail) if detail else ''}")

    # 1. Required fields
    has_id = scene.get('id') == scene_id
    has_name = bool(scene.get('name'))
    has_start = scene.get('paddyStart') and 'x' in scene['paddyStart'] and 'y' in scene['paddyStart']
    has_bg = scene.get('hasBg', False)
    has_npcs = isinstance(scene.get('npcs'), list)
    has_hotspots = isinstance(scene.get('hotspots'), list)
    has_dialogues = isinstance(scene.get('dialogueKeys'), list)
    check('Required fields present',
          all([has_id, has_name, has_start, has_bg, has_npcs, has_hotspots, has_dialogues]),
          'missing: ' + ', '.join(f for f,v in [
              ('id',has_id),('name',has_name),('paddyStart',has_start),
              ('drawBg',has_bg),('npcs',has_npcs),('hotspots',has_hotspots),('dialogues',has_dialogues)
          ] if not v))

    # 2. At least one exit hotspot
    exits = [h for h in scene['hotspots'] if h.get('isExit')]
    check('Exit hotspot found',
          len(exits) > 0,
          f"{len(exits)} exits found")
    if exits:
        for ex in exits:
            print(f"    → {ex['id']} → {ex.get('exitTo','?')}")

    # 3. Item hotspots have flag + requireFlag
    item_spots = [h for h in scene['hotspots'] if h.get('item')]
    for hs in item_spots:
        has_flag = bool(hs.get('flag'))
        has_req = bool(hs.get('requireFlag'))
        check(f"Item hotspot '{hs['id']}' has flag + requireFlag",
              has_flag and has_req,
              f"flag={hs.get('flag')!r} requireFlag={hs.get('requireFlag')!r}")

    # 4. NPC dialogueId matches a DIALOGUES tree
    for npc in scene['npcs']:
        did = npc.get('dialogueId')
        in_dialogues = did in data['DIALOGUE_KEYS']
        check(f"NPC '{npc['id']}' has dialogue tree ('{did}')", in_dialogues)

        if in_dialogues:
            nodes = data['DIALOGUE_NODES'].get(did, [])
            has_root = 'root' in nodes
            has_farewell = 'farewell' in nodes
            has_already = 'already_done' in nodes
            check(f"  Dialogue tree '{did}' has root/farewell/already_done",
                  has_root and has_farewell and has_already,
                  'missing: ' + ', '.join(n for n,v in [
                      ('root',has_root),('farewell',has_farewell),('already_done',has_already)
                  ] if not v))
            has_done_flag = did in data['DIALOGUE_FAREWELL_FLAGS']
            check(f"  Dialogue '{did}' farewell sets doneFlag", has_done_flag)

    # 5. quizFromBank scenes have questions
    for npc in scene['npcs']:
        did = npc.get('dialogueId')
        if not did:
            continue
        quiz_scenes = data['DIALOGUE_QUIZ_SCENES'].get(did, [])
        for qs in quiz_scenes:
            qbank = data['QUESTION_BANK_SCENES'].get(qs, {})
            easy_count = qbank.get(1, 0) + qbank.get(2, 0)
            check(f"  QUESTION_BANK has ≥2 easy/medium questions for '{qs}'",
                  easy_count >= 2,
                  f"found {easy_count}")
            total = sum(qbank.values()) if qbank else 0
            check(f"  QUESTION_BANK has ≥4 total questions for '{qs}'",
                  total >= 4,
                  f"found {total}")

    # 6. Lucky coin exists for scene
    coin_scenes = data['LUCKY_COIN_SCENES']
    check(f"LUCKY_COINS entry exists for '{scene_id}'", scene_id in coin_scenes)

    # 7. No hotspot rect overlaps
    hotspots = scene['hotspots']
    overlaps = []
    for i in range(len(hotspots)):
        for j in range(i+1, len(hotspots)):
            a, b = hotspots[i]['rect'], hotspots[j]['rect']
            if a['x'] < b['x']+b['w'] and a['x']+a['w'] > b['x'] and a['y'] < b['y']+b['h'] and a['y']+a['h'] > b['y']:
                overlaps.append((hotspots[i]['id'], hotspots[j]['id']))
    check('No hotspot rect overlaps',
          len(overlaps) == 0,
          f"overlapping: {overlaps}")

    return checks_pass, checks_total

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if '--template' in args:
        print(TEMPLATE)
        return

    print(f"Loading game data from {os.path.basename(GAME_FILE)}...")
    data = extract_game_data()
    if data is None:
        sys.exit(1)

    all_scenes = list(data['SCENES'].keys())
    target_scenes = [a for a in args if not a.startswith('-')] or all_scenes

    total_pass = 0
    total_checks = 0
    all_passed = True

    for scene_id in target_scenes:
        print(f"\n=== Validating: {scene_id} ===")
        p, t = validate_scene(scene_id, data)
        total_pass += p
        total_checks += t
        passed = p == t
        all_passed = all_passed and passed
        status = 'PASS' if passed else 'FAIL'
        print(f"  {status} ({p}/{t} checks)")

    if len(target_scenes) > 1:
        overall = 'ALL PASS' if all_passed else 'SOME FAILED'
        print(f"\n{'='*40}")
        print(f"Overall: {overall} — {total_pass}/{total_checks} checks passed")

    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
