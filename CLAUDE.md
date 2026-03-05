# Paddy's Parade Day Adventure

Single-file HTML5 canvas game set during the Scranton, PA St. Patrick's Day Parade.

## Key Files
- `paddy-parade.html` — entire game (HTML + CSS + JS, ~3350 lines)
- `paddy-parade-creator.html` — hotspot visualizer/debugging tool
- `paddy-parade-docs.html` — developer reference (standalone HTML)
- `validate_scenes.py` — dev-only Python validation tool (requires Node.js)
- `CLAUDE.md` — this file

## Tech Constraints
- **No external dependencies** — pure Canvas 2D only, no libraries, no image files
- **Single file** — all game code lives in paddy-parade.html
- **320×240 virtual canvas** scaled to viewport via CSS; `devicePixelRatio` applied at boot
- `VIEWPORT_H = 195` — playable area; `INVENTORY_Y = 195`, `INVENTORY_H = 45` — bottom bar

## Code Structure (10 sections)
1. Constants & Palette (`W`, `H`, `PALETTE`, `LUCKY_COINS`, `QUESTION_BANK`)
2. GameState class (flags, score)
3. Input class (pointer events → logical coords)
4. Sprite Helpers (`drawPaddy`, `drawNPC`, `drawShamrock`, `drawItemIcon`, `roundRect`, `wrapText`)
5. Scene Backgrounds (6 × `drawBg*` functions, all cached in `bgCache`)
6. Scene Definitions (`SCENES` object)
7. Dialogue System (`DIALOGUES` trees + `DialogueSystem` class)
8. UI System (`UISystem`: inventory, popups, HUD)
9. Game Engine (`Game` class: loop, walk, transitions, coins, help screen, difficulty)
10. Boot (`window.onload`)

## Phase 4 Additions — Footrace Scene
- **Scene flow**: pub → **footrace** → cathedral → steamtown → lackawanna → parade
- **New scene**: `footrace` — Brian P. Kelly Memorial Footrace (10:00 AM on Parade Day)
  - NPC: `race_director` (reflective vest + whistle + clipboard)
  - Item: `race_bib` (green bib #1) — gated on `quiz_footrace_done`
  - Exit: `exit_cathedral` → `cathedral`
  - Lucky Coin at x=280, y=155
- **5th inventory slot** — inventory slotW changed from `W/4` to `W/ITEM_IDS.length`
- **HUD dots updated** — now 5 dots (PUB, RACE, CAT, STM, LAC), 33px apart from x=(W-hudW+6)
- **QUESTION_BANK** — 6 new footrace questions (2 per difficulty, scene: 'footrace')
- **Marshal** checks 5 items now: `has_shamrock`, `has_bib`, `has_banner`, `has_horseshoe`, `has_bulb`
- **validate_scenes.py** — Python dev tool that uses Node.js to validate scene schema/cross-refs
  - Run: `python validate_scenes.py` (all scenes) or `python validate_scenes.py footrace`
  - `--template` flag prints copy-pasteable JS template for new scenes
- **Pub exit sign** now points to 'Footrace' (was "St. Peter's")

## Phase 3 Additions (major upgrade)
- **QUESTION_BANK** — 45 questions (15 per difficulty tier: easy/medium/hard)
  - Each has: `id`, `scene`, `difficulty`, `question`, `options[]`, `correct`, `hint`
  - DIALOGUES quiz nodes now use `{ quizFromBank: { scene } }` instead of hardcoded questions
  - Session questions cached at game start via `_cacheSessionQuestions()` — randomized each play
- **Difficulty selection screen** — `'difficulty'` mode between title and game start
  - Easy (×1), Medium (×1.5), Hard (×2) score multipliers
  - Sets `game.difficulty` and `game.scoreMultiplier`
- **Hotspot overlaps fixed** (parade crowd/float/marshal, steamtown locomotive)
  - crowd: (0,60,95,55), float: (130,100,110,50), marshal NPC x=225, locomotive: (90,90,110,60)
- **NPC head-turn** — `drawNPC(ctx, x, y, type, animFrame, facing)` — NPCs face Paddy within 40px
- **Coal cart push animation** — `cartPushTimer` / `cartOffset` slide cart 15px right
- **Float decoration** — `floatDecorated` flag draws item icons + star on float surface
- **Crowd talk** — 'talk' on crowd → dialogue box instead of showMessage
- **Use float** — 'use' float → walks Paddy to float, lists missing items or confirms all set
- **Creator tool** (`paddy-parade-creator.html`) — scene selector, 2× scaled canvas, color-coded hotspot overlays, overlap detection, hover tooltip
- **Exit signs** (`_renderExitSigns`) — pulsing green directional signs appear near each exit after the scene's key item is collected
  - Definitions: `{ pub→"Footrace", footrace→"St. Peter's", cathedral→"Steamtown", steamtown→"Elec. City", lackawanna→"Parade!" }`
  - Gated on flags: `has_shamrock`, `has_bib`, `has_banner`, `has_horseshoe`, `has_bulb`
- **Exit warning** — `handleVerb 'go'` blocks departure if key item not yet collected
  - Two tiers: quiz not done → "talk to NPC first"; quiz done but item not taken → "don't forget item"
- **Quiz feedback modal** — answering a quiz shows a modal panel (y=88, h=142) covering all 4 options
  - "✓ Correct!" / "✗ Not quite!" header; hint or score message; "Continue ▶" / "Try Again ▶" button
  - Button coords from `DialogueSystem.FEEDBACK_BTN = { x: W/2-42, y: 216, w: 84, h: 14 }`
  - Correct: dismiss quiz entirely; Wrong: dismiss feedback only (player can retry)
  - Panel covers entire option area (y=88..230) so player never sees partial option list during feedback
- **In-game help button** — small "?" button at top-left (x=2..14, y=1..12) of scene label bar
  - Tapping opens help screen; `_helpReturnMode` stores prior mode so "Close/Done" returns to play
  - `this._helpReturnMode = 'play'` set on tap; help exit uses `this.mode = this._helpReturnMode`

## Common Gotchas
- Background functions are **cached** (drawn once to offscreen canvas). Do NOT use `Math.random()` inside them.
- `wrapText(ctx, text, x, y, maxW, lineH)` **returns the final y** — use it to chain layout.
- `fillText` y is the **baseline**, not the top. For Npx font, top of glyphs ≈ y − N.
- Quiz options must fit within canvas height 240. `by0 + 4*(optionH + optionGap) < 240`.
  - Current values: `by0=92, optionH=30, optionGap=3` → last option ends at y=221 ✓
  - Feedback modal overlays y=142–230 (covers last 2 options + below) — button at y=216 ✓
- The `animTimer` is incremented in `title`, `help`, `difficulty`, and `play` modes — not in `dialogue`.
- Coins are drawn live (not in bgCache) via `_renderCoins()`.
- NPCs and Paddy are depth-sorted by Y before drawing (higher Y = closer to camera).
- `_renderAmbient(ctx)` draws animated overlays on top of bgCache (fire, steam, crowd wave, cart offset).
- `_renderExitSigns(ctx)` is called after `_renderAmbient` and before entity rendering in play mode.
- `_getHoverLabel()` returns the current sentence-line text (hovered name or action string).
- Walk target indicator uses `walkTargetTimer`, `walkTargetX/Y` in Game state.
- `drawNPC` now accepts optional 6th param `facing` (-1 or 1) — applies ctx.scale(-1,1) for mirror.
- `quizFromBank` nodes in DIALOGUES pull from `game.sessionQuestions[scene]` by pointer index.
- Score multiplier: Easy=1, Medium=1.5, Hard=2 (applied in `_handleQuizTap`).
- Quiz feedback uses tap-to-dismiss (no timer) — `DialogueSystem.update(dt)` is a no-op.

## Adding Content
See `paddy-parade-docs.html` for full step-by-step guides on adding scenes, NPCs, quiz questions, and Lucky Coins.

To add questions to QUESTION_BANK: add object with `{ id, scene, difficulty, question, options[], correct, hint }`. Questions auto-pool into sessions based on scene + difficulty.

## Development
Open `paddy-parade.html` directly in a browser (no server needed).
Open `paddy-parade-creator.html` to visually inspect hotspot rects and detect overlaps.
Run `python validate_scenes.py` to check all scene definitions for schema compliance.
Test on mobile via Chrome DevTools → device mode → 375×667 (iPhone SE).
