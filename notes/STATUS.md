# Status

## Pipeline
- `tools/extract.py` → `script/strings.json` (table-verified strings, banks $06/$27/$42/$25/$38/$4C).
- `font/table_p0..5.json` glyph table (bitmap transcription + context review).
- Script: `script/glossary.md`, `script/TRANSLATION_SPEC.md`, draft `script/tl_out/`, review corrections
  `script/tl_review/` (override the draft), `script/strips.json` (fixed-slot label strips incl. the name keyboard),
  `script/intro_en.json` (character intro stories), `script/index_lock.json` (permanent string indices).
- Engine `asm/engine.asm` (ROM0 $2000; font $3800; far-copy helper $1F00): hooks $0A3B/$0A43, F6 redirects,
  proportional font, runtime word wrap + paging, 3 chars/frame, margins, tab/pad controls, inline ASCII names,
  numbers formatted as dollars (dialogue + bank $14 number fields for HUD/popups), name keyboard patches (bank 07).
- Graphics: `tools/gfx.py` + `gfx/specs.json` → `gfx/patch.json` (per-screen patches), generators
  `tools/gfx_profiles.py`, `tools/gfx_roulette.py`, `tools/gfx_intro.py`, `tools/gfx_bubbles.py`.
- `tools/build.py` → `build/fkdfw_en.gbc`.

## Bank map (new data)
$58 string table · $59-$5C English text · $70-$77 intro pages (one per character) · $7C profile per-character tiles ·
$7D setup screen · $60-$67 wish-scene (ending) text pages, one per character · free space at the end of $39 (roulette)
and $4F (profiles) · bank 0 $1D28-$3FFF engine/font.

## Done (verified in the emulator)
Dialogue/news/portrait boxes, names (preset + typed), places, cards, money ($), HUD, popups, title menu, save slots,
setup, character select, profiles, name keyboard, goal roulette (city codes), intro stories, town bubbles,
step counter, TV-news window (two-line scroll ring at $C0BF), disaster region names (bank $30),
winner's wish scene text (`script/endings_en.json`, `tools/gfx_endings.py`, loader hook $0C:$4091),
Other > Assets / Setup screens (1bpp strips in bank $08, `gfx/specs.json`, `tools/gfx_badge.py`), sell-off screen
(bank $3D strips `tools/gfx_sell.py`, SellAmount/SellHeader big-digit dollars), compact money popup ($C129 = popup up).

## Open
- Investment screen prices (game units, big digits), any remaining menus (Other submenu, stock market, card shop),
  endings / year-end screens — being surveyed.
- Translation review pass (in progress).
- 臺灣 logo on the roulette panel left as is (TAIWAN already printed under it).
- Sell-off screen message box sits half off-screen (same in the original), so longer English lines are cut.
- 女王 lettering in Penny's ending picture (bank $32 picture, descriptor table $57:$5942) left as artwork.
