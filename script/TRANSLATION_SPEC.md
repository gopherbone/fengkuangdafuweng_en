# Translation spec

Input batches: `script/tl_in/batchN.json`, a list of entries `{id, zh, refs, continues_into?, continuation_of?}` in ROM order
(which is mostly narrative order, so neighbouring entries give context).
Output: `script/tl_out/batchN.json` = `{ "<id>": "<english>" , ... }` — one key for every input id.
Read `script/glossary.md` first and follow it exactly for names, cards, places and terms.

## Control tokens in `zh`
| token | meaning | in your English |
|---|---|---|
| `<NAME>` `<NAME_E1>` `<NAME_E8>` `<E9>` | inserted name (player, other player, place, item) | keep each exactly as many times as in zh, place where grammar needs |
| `<FE>` | inserted card name (no word "card" in it) | keep |
| `<NUM>` `<EE>` `<EC>` `<EB>` `<EA>` `<EF>` | number printed by the game | keep (money: `$<NUM>0K`) |
| `<P0>`…`<P5>` | player/place name table insert | keep |
| `<WAIT><PAGE>` | button press, then new page — a "beat" | write `<PAGE>` between beats; you may merge or split beats sensibly |
| `<WAIT><F9>` | line scroll in the TV-news window (every ~9 hanzi) | ignore — just write continuous prose; the layout tool re-flows |
| `<NL>` | forced line break (e.g. after a speaker label `尤莉雅：`) | keep after speaker labels: `Julia:<NL>…` |
| `<WAIT>` before `<BOX>`/`<END>` | wait for button at the end | the tool copies the original's final behaviour; don't write `<WAIT>` |
| `<BOX>` / `<END>` | terminator | end your string with the same terminator as zh, and nothing else after it |
| `　` (ideographic space) | padding before a number | drop it |

Do NOT write `<WAIT>`, `<F9>`, `<NOP>`, or anything not in this table. Plain ASCII only (straight quotes `'` `"`,
`...` for ellipsis, `~` allowed for a sing-song tone like zh `～`).

## `<END>` + continuation
An entry ending in `<END>` is followed by a game-printed number, then its continuation entry (`continues_into`) —
e.g. `…撿到了<END>` + [number] + `萬！…` → `"…found $<END>"` + [number] + `"0K!…"`. Translate the pair so the
sentence reads correctly with the number in between. The continuation usually starts with 萬 → begin it with `0K`.

## Style
- Natural, lively English; keep jokes, onomatopoeia (呵呵呵 "Hohoho", 嗚 "Waah"), character voices
  (俺…咧 = folksy bumpkin; 人家…嘛 = cutesy/coy; the Fart Sage is pompous, Kenshiro is a stiff TV reporter).
- Dialogue pages hold ~2 lines × ~26 characters. Keep each beat (`<PAGE>`-separated chunk) ≲ 52 characters
  where possible; it's fine to add a `<PAGE>` to split a long beat.
- Short labels / menu-like entries (no punctuation, e.g. `是否`, `旅館`) must stay short.
- Source typos (稍侯, 渡假, 催殘, 徵罰, 移到到…) — just translate the intended meaning.
- If something is genuinely ambiguous, translate your best reading and add the id to a list `"_notes"` in the output
  with a short explanation (key `"_notes"`: `{ "<id>": "why" }`).
