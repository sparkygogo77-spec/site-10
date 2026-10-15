# Retiring a Lantern Ring chat (and passing its knowledge on)

A chat is retired when it gets long, slow, or its range is finished. Nothing it knows may live only in the chat:
everything goes to the repo or into the skills, so the next chat starts from it.

## 1. J pastes this into the old chat

```
Retire this chat. Follow docs/handoff/RETIRING-A-CHAT.md on claude/lantern-redesign-pass2 (pull first), step 2.
```

## 2. The old chat does, in order

1. **Finish or park** the pass in progress: push its script; if unfinished, say so in its INBOX entry ("PARKED: <what's
   left>").
2. **INBOX and DECISIONS**: every entry in its range has a correct status; every decision J made in this chat is one
   line in `docs/blender/review/DECISIONS.md` (his words, newest first).
3. **Retirement note** `docs/handoff/retired/<date>-<range or role>.md`, with these headings:
   - **Range / role** and the last pass number used.
   - **Open work**: WAITING passes (`.blend` path + camera), PARKED work, promises made to J.
   - **Files**: anything on J's PC that is stray or superseded (should go to `_to_delete\`).
   - **Lessons for the design skill**: new rules J taught in this chat, each as one rule line, with his words in
     quotes and the pass it came from. Only things that should hold for every future chat (feel, look, workflow,
     Blender gotchas), not one-off picks.
   - **Gotchas**: tool or pipeline traps that cost time, with the fix.
4. **Commit and push** once; reply to J with the note's path and "safe to close".

## 3. The coordinator does (next time it runs, or when J says "fold in")

1. Reads new files in `docs/handoff/retired/`.
2. Merges the **Lessons** into the `lantern-ring-design` skill and **Gotchas** into the skill they belong to
   (`lantern-blender-modeller`, `lantern-coordinator`), proposing the full updated skill for J to save
   (skills only change when J saves the card). Contradictions with existing rules: ask J which wins.
3. Moves the open work to the chat that owns the range (or lists it for J if no chat is running).
4. Marks the note `FOLDED <date>` at its top and pushes.

## 4. Starting the replacement

Same short starter as any new chat (START-HERE). It reads DECISIONS.md, RATINGS.md, the INBOX entries in its range and
the retirement note for its range, so it picks up exactly where the old one stopped.
