**FOLDED 2026-10-19** (card and colour lessons -> design skill; decisions workflow and gotchas -> coordinator; chats.json and red-stays-open -> lantern-router)

# Retired: decision manager chat (PC, Claude Code), 2026-10-19

## Range / role
A side chat that built the decision manager. J: "I need a decision manager built into chat that gives me better
descriptions and visuals and controls this chat, and if we can then embed this in the website". No Blender passes.
- site-10: 7525905 (tools + brief), ab45e09 (colours), the answers commits. review-site: 8062571b (Decisions view),
  46b09559 (colours).
- Pieces: `tools/review_site/gen_decisions.py` (cards; gen_control.py runs it on every render run),
  `decision_stills.py` (a picture sheet per pass), `record_decision.py add|pull` (answers), `docs/decisions/`
  (`chats.json` = what chats are waiting on, `answers.json`, `OUTBOX.md`), PC-CHAT-BRIEF.md section 2a
  `Menu: decisions` + `Menu: decided <id>: <pick>`, menu.html "Decisions" button, review site header "Decisions" /
  Control > Decisions (`#decisions`).

## Open work
- **Saving from the site works now** (GITHUB_TOKEN is in; answers go to the `site-data` branch through `/api/files`, and
  `record_decision.py pull` reads them through the same API: tested 2026-10-19, 0 saved yet). The 🔴 "turn on saving"
  card is closed. Not yet tested end to end: a real Save on the site followed by a `pull` in a PC chat.
- J's answers so far (DECISIONS.md "Decision manager"): 864 next round "3 variations of each" of G3a/G3b/G3c, sent to
  the pc-lanterns chat (it built 865 since; check whether 865 is that round, and if so record it as done).
  Dark Lantern swirl: "Haven't tried yet" (card stays open).
- 29 handover questions (Part 1 of `2026-10-18-total-handover.md`, minus 28) are still open as 🟡 game-question cards.
  Their answers go to `OUTBOX.md` for a project thread; nobody has posted any yet.
- `chats.json` is hand-kept: whoever learns what a chat is waiting on adds a row, and drops it once it's done.

## Files
- `LanternLive\_previews\decisions\` holds the picture sheets (cached, can be regenerated). Nothing stray.

## Lessons for the design skill
- Workflow: J wants every open choice as a card: what it is in plain words, why it matters (what it unblocks), a
  picture, options with a ★. "better descriptions and visuals" (2026-10-18).
- Workflow: J's colours everywhere, cards and reply first lines: 🟡 his answer, 🔴 only he can do it (sign-in, token,
  approval, merge), 🔵 done (2026-10-18). A 🔴 card stays open after he answers until the job is actually done.

## Gotchas
- Blender reads a **relative** movie path as black frames, and the scene fps must match the clip (the site's clips run
  at 5-10 fps): `decision_stills.py` uses absolute paths and sets `scene.render.fps = strip.fps`.
- `lantern-review-j.vercel.app` 307-redirects to the review-site branch alias: check it with `curl -L` or the browser,
  or a plain curl looks like "the deploy isn't live".
- Port 8765 is shared by other chats' local test servers (three listening at once); use another port.
- `origin/dev` in the review-site clone is a fetch mapping of `claude/lantern-redesign-pass2`, not a GitHub branch:
  `git fetch origin +refs/heads/claude/lantern-redesign-pass2:refs/remotes/origin/dev`.
- A site push J approved in another chat (relayed) was blocked by the safety check; it needs his yes in this chat.
- `data/decisions.json` conflicts on rebase whenever a render lands: take theirs, then rerun `gen_decisions.py`.
