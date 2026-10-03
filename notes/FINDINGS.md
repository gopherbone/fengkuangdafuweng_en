# Feng Kuang Da Fu Weng (瘋狂大富翁) — independent assessment, 2026-10-02

Everything here was re-derived from the original ROM (`orig/fkdfw.gbc`, md5 0302066cf764b39159922594f31e3445)
with the SameBoy CLI. Nothing from ~/crazyrichman_en was taken on trust.

## Text engine (verified by trace + disassembly)
- Renderer: `$0A3B` (loads string ptr from `$C0DE/$C0DF`) → loop at `$0A43`. String bytes are read from the
  currently mapped ROMX bank (each bank's byte at `$4000` holds its own bank number; the engine saves/restores it).
- Encoding:
  - `F0`–`F5 xx`: select font page (low nibble) **and** draw glyph `xx`. The page is **sticky**.
  - `00`–`DF`: draw glyph from the current page.
  - `E0`–`FF`: control codes. The byte after a page prefix is re-dispatched through the control chain, so glyph
    slots `E0`–`FF` are unusable (they're blank in the font).
- Font: 16×16 1bpp, 32 bytes/glyph (left 8px column rows 0–15, then right column). Page p, index x →
  file offset `(9 + (p>>1))*0x4000 + (p&1)*0x2000 + 1 + x*32`. Real glyphs only on pages 0–5 (banks 9–B),
  1,342 glyphs. Pages 6–8 (banks C–D) are pre-drawn graphics, not font.
- VRAM: each glyph → 4 tiles, written as two 8px-wide columns of 2 stacked tiles (each source byte written twice =
  both bitplanes). The renderer copies to `[$C0C8]` and advances. This column structure is what makes a VWF easy here.
- Control codes seen: `FF` end, `FD` end-of-message/box, `FC` new page, `FB` newline, `FA` wait for button,
  `F9` (paged-text helper), `E0`/`E1`/`E8` insert names from RAM (`$C210`/`$C1D8` ptr/`$D6D4`), `E2`–`E7` player
  table names, `EC` number, `E9` from `$C17B`, `FE`/`EF`/`EE`/`EB`/`EA` not yet characterised.
- Names in RAM use the same 2-byte format and go through the same renderer.

## Script inventory (static scan, `script/static_dump.tsv`)
| bank | strings | CJK chars | content |
|---|---|---|---|
| $06 | ~410 | ~6.1k | cards, news-report events (尤莉雅/拳四郎), little-devil companion, name keyboard |
| $27 | ~300 | ~7.0k | board events (thief, pickpocket, glutton, …), card full, earn/fine spots |
| $42 | ~222 | ~2.8k | system msgs (save/load), story/race intro, misc events (pointer table at $42:$4175) |
| $25 | ~96 | ~0.7k | property/location names (台北, 永和豆漿, 圓山飯店, …) |
| $4C | 8 | — | playable character names |
Total ≈ 17k characters, ~1,000 unique strings. A few block heads in $06/$27/$25 are data decoded as text
(noise rows); exact boundaries still need to come from pointer tables.

Graphical text (not in the script; needs tile editing): title menu (繼續遊戲/新的進度/拷貝進度), game setup screen,
character-select header, OKAY/CANCEL buttons, character profile labels, intro story crawl (小惡魔這才知道…),
name-entry keyboard.

Character names ($4C): 貢丸湯, 嘟比, 錢美美, 吳氣魄, 幸子, 花村, 黃香蘭, 小明 — mostly joke names
(meatball soup; "Money Meimei"; pun on 無氣魄 "no guts").

## State of ~/crazyrichman_en (latest dist v1_9_9_4)
Don't build on it. Reasons, all reproduced here:
1. **Its Chinese source text is wrong.** Its code table (`research/code_table.json`) is misaligned by 1–16 slots
   on pages 4–5, has misreads on 0–3, and is missing characters (e.g. 獄). Its decoder also turns control codes into
   characters (FA→服, FD→自/蕭, E0→司/禦/方). The English was translated from that corrupted text, e.g.
   `可慾的魔鬼和看我的屬害…必友?千手閃田` → "Thousand kick!"; `怎…怎麼回失？…現己跳起來` → "It popped up?"
   (real: 我的卡片怎麼自己動起來了 "why is my card moving on its own?"); thugs 啊咚/啊鏘 → "AH-RU, AH-JI".
2. **Names are placeholders or wrong:** 嘟比 → "Nezha", others → "Tubby", 貢丸湯 → "Soup-Maru".
3. **Visible bugs:** "No save data yet" turns into garbage the second time it's shown; name keyboard broken
   (row 4 repeats a–h, malformed letters, stray dots in entered names); profile age shows 11 where the original says
   10; trait text overlaps; labels cut off ("NAM", "NAT").
4. **Architecture:** ~160 KB of pre-rendered per-string bitmaps (banks $70–$7A), a dozen hooks in the text
   engine, and almost all of bank 0's free space used up (~8 KB). Coverage by its own count is ~38% of rows.
5. **Process:** ~2,400 commits, ~48k lines of tooling, 1.1 GB .git, mostly gating/ledger bureaucracy around
   the wrong foundation.
Possibly worth reusing: the look of its small VWF font and its edited title/setup-screen tiles, as visual reference only.

## Proposed path (fresh, in this directory)
1. Exact string boundaries from pointer tables (+ dynamic logging, `tools/autoplay.py`) → `script/` source of truth.
2. A context-based review pass on the glyph table. The agent transcriptions are good, but I found and fixed
   errors on spot checks ($062 恐, $528 徵, $0BF Z).
3. Translate the whole script from the corrected source, with a glossary and properly localised names.
4. One renderer patch: replace the glyph copy at `$0AAD`–`$0AE2` with a VWF that packs proportional glyphs into
   the existing 8px column tiles; put English strings in free banks ($58–$7F are empty in the original) and repoint
   the tables. No per-string bitmaps.
5. Tile edits for graphical text.
6. Verification: render every string by calling `$0A3B` directly in the emulator and screenshotting the result,
   so coverage doesn't depend on reaching each event in play.

## Files
- `tools/fkdfw.py` — codec (decode; table loader). `tools/dump_script.py` — static scan.
- `tools/emu.py`, `tools/step.py`, `tools/play.py`, `tools/autoplay.py`, `tools/tracecap.py` — emulator drivers.
- `font/table_p0..5.json` — new glyph table (ids are page+index hex, e.g. "48F"); `font/uncertain_*.json`.
- `snaps/orig_gamestart.state` — original ROM, 4-player game just started.
