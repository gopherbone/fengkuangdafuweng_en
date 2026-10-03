# Translation review spec

You review one batch of the English draft against the Chinese source. Inputs:
- `script/tl_in/batchN.json` (source entries: id, zh, refs, continues_into / continuation_of)
- `script/tl_out/batchN.json` (current English, same ids)
- `script/glossary.md` (mandatory names/terms — note: Meatball is a BOY imp ("he"), Dubi is a boy angel ("he"),
  Penny/Sachiko/Xianglan are female, Wu/Hanamura/Xiao Ming male; Queen Sago is Meatball's mother, the Demon Queen)
- `script/TRANSLATION_SPEC.md` (token rules — still apply)
- the whole decoded script `script/strings.json` for context.

Check every entry for:
1. Accuracy: meaning matches the Chinese (watch for misreadings, dropped clauses, wrong speaker/subject).
2. Glossary consistency (names, card names, places, NPCs, terms).
3. Natural, idiomatic, fun English in the right character voice; no stiff literalism; consistent tone.
4. Token correctness: same insert tokens as zh, same terminator, `$<CODE>0K` money convention, no <WAIT>/<F9>.
5. Length: a dialogue beat (<PAGE>-separated) should stay under ~80 characters; split long beats with <PAGE>.
6. Gender/pronouns per the glossary; `<NAME>` can be any player (avoid gendered pronouns for <NAME>/<NAME_E1>,
   use "they"/rephrase).

Output `script/tl_review/batchN.json`: `{ "<id>": "<corrected English>" }` ONLY for entries you change, plus
`"_notes": { "<id>": "what/why" }` for every change (one line). Validate the same token rules as the spec before
finishing. Do not edit any other file.
