# Text engine and string tables

## Renderer (bank 0)
- `$0A3B`: load string pointer from `$C0DE/$C0DF`, fall into `$0A43`.
- `$0A43` loop: `LD A,[HL+]` from the currently mapped ROMX bank, dispatch:
  - `FF` → `$0D77` (DE=`$590C`; advances tile cursor one column, then a bank-$14 call) — end of segment
  - `FE` → `$0D9D` insert sub-string from pointer `$D690` (word table, e.g. card name), rendered with `$C0C4=$81`
  - `FD` → `$0B16` end of message: `[$D678]=A`, clear `$C0C4` high nibble
  - `FC` → `$0CF3` new page (clears box via `$0A0B`, resets cursor to `$D686`)
  - `FB` → `$0B22` newline (cursor = `$C12E`)
  - `FA` → `$0B32` wait for button (blinking prompt, sprite at `$0B78` table)
  - `F9` → `$0C85` scroll/next line in the news/TV window (`$D6A2`, `$D66D`)
  - `F0`–`F8` → `$0AF7` page select: bank = 9 + (n>>1), base `$4001`/`$6001`; the following byte is then
    re-dispatched (so glyph slots `E0`–`FF` are unreachable)
  - `EF` → `$0D53` (cursor = `$C12E`+`$20`, bank-$14 routine `$70C2`) — number field
  - `EE` → `$0D7C` (DE=`$5911`) ; `EA` → `$0D72` (DE=`$5907`) ; `EC` → `$0D34` (`$58C7`) ; `EB` → `$0D15` (`$58BE`)
    — all bank-$14 helpers drawing numbers/icons into the next column(s)
  - `ED` → no-op
  - `E9` → name/word from `$C17B` ; `E8` → `$D6D4` ; `E1` → `$C210` ; `E0` → pointer `$C1D8`
  - `E2`–`E7` → `$0DE2`: player-name table at `$0E04` indexed by `$C0D3`
  - otherwise glyph: `[$C0C7]=index`, save HL to `$C0DE`, copy 32 bytes from font bank `[$C0E0]`,
    base `[$C0E1]:[$C0E2]` + 32*index to VRAM at `[$C0C8]`, each byte written twice (both bitplanes);
    then if `$C0C4` bit 0 → loop (instant), else RET (typewriter: one glyph per call)
- Glyph VRAM layout: 64 bytes = 4 tiles = two 8px columns of two stacked tiles. The box tilemap is pre-laid
  column-major, so the renderer just streams tiles.
- Glyph `000` is a blank used as a space for padding before numbers.

## String tables
Each text bank starts with the same accessor (bank id byte at `$4000`, code from `$4001`):
`string = sub[ top[ [$D685] ] ][ [$C0DD] ]` → `$C0DE`. Additionally `[$D68F]` indexes a word table → `$D690`
(used by `FE`).

| bank | top table | groups |
|---|---|---|
| $06 | `$4068` | g0 `$4070` keyboard pages (2), g1 `$4074` card names (88, also the `FE` word table), g2 `$4124` card texts (88), g3 `$41D4` events (256) |
| $27 | `$4051` | g0–3 dummy, g4 `$405D`, g5 `$40F1` |
| $42 | `$4175` | g0–5 dummy, g6 `$4183` (system/story) |
| $4C | `$4D58` | single level: 8 character names (index `$D67C`) |
| $25 | records at `$455E` (index `$C0D3`), names block `$4785`–`$4C1C` | property/location names |

After an `FF` the game may print a number itself and then resume at the following byte
("continuation" segments, flagged `orphan` in `script/strings.json`).

`tools/extract.py` → `script/strings.json` (1,247 entries: id `BB:AAAA`, refs, raw bytes, decoded zh).
