# Status — 2026-10-02

## Pipeline (all in this directory)
- `tools/extract.py` → `script/strings.json`: 1,307 table-verified entries (banks $06/$27/$42/$25/$38/$4C).
- `font/table_p0..5.json`: glyph table, transcribed from bitmaps + context-reviewed (fixes applied, source typos noted
  in `script/review_typo_*.json`).
- `script/glossary.md`, `script/TRANSLATION_SPEC.md`; translations in `script/tl_out/` (first full draft, all strings).
- `script/strips.json`: fixed-slot label strips (HUD, menus, yes/no).
- `script/index_lock.json`: permanent string indices (RAM name buffers and saves hold `F6 idx` redirects — never renumber).
- `asm/engine.asm` + `font/en_font.py`: English VWF engine in ROM0 $3000-$3FFF, hooks at $0A3B/$0A43 only.
- `tools/build.py` → `build/fkdfw_en.gbc` (+ .sym/.map). English data in banks $58 (table) and $59-$5C.
- Test tools: `tools/play.py`, `tools/step.py`, `tools/survey.py` (autoplay + contact sheets + per-shot states),
  `tools/leaks.py` + `tools/leakreport.py` (logs every Chinese glyph drawn by the original renderer),
  `tools/trace_en.py` (logs each English string start with box geometry).

## Verified in play
Title "no save" message (repeatable, no corruption), TV-news window with line scrolling, dialogs with word wrap and
auto paging, portrait boxes, name inserts (player/place/card), numbers, HUD strip (Move/Cards/Other, Yr, To <city>,
Cash), goal roulette text. Leak survey: no untranslated script text reached the renderer.

## Open work
1. Graphics text (pre-drawn tiles, not script): title menu, game setup, character select header, profile screens,
   step counter 步, money popup 萬, roulette header + city grid, board city labels, intro story crawl, name keyboard.
2. Engine: windows whose box variables are stale (text drawn outside its box seen once — root cause was stale RAM
   name indices, fixed by the index lock; keep watching), verify strips 06:6E6A / 27:73B2 / 27:747E in game,
   English name keyboard (F7 inline ASCII names).
3. Translation review pass (consistency, length, the agents' `_notes`), place-name abbreviations (Snow Mtn., Kentucky Hen).
4. Exhaustive render test: draw every string through the engine directly and screenshot it.
