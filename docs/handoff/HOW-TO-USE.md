# How J uses the Lantern chats (one page)

| You want | Use | Start it with |
|---|---|---|
| New Blender work, fast, checked on your graphics card | **PC chat** (Claude Code app, folder LanternLive) | `DESKTOP-KICKOFF.md` |
| Several jobs at once, or work while your PC is off | **Cloud thread** in the Site 10 project | `NEW-CHAT-PROMPT.md` (or ask the PC chat to post it) |
| Game code, jars, PRs, merges | Site 10 project coordinator / threads | the project's main box |
| Rate takes | https://lantern-review-j.vercel.app on your phone | KEEP / IMPROVE / DROP + a note |
| Answer everything waiting on you (passes, next rounds, game questions, chats) | **Decisions**: menu > Decisions in a PC chat, or Control > Decisions on the site | click the ★ or another option; the PC chat records it in `DECISIONS.md` and acts on it |
| See where everything stands | **The grid**: every PC chat reply that finishes a job ends with it (cards move from Waiting on you to Your picks to In the game), then the menu | links on the cards open the site and the jar; the menu below it opens a `.blend` in Blender |
| Finish chats, start fresh | menu > **Wrap up**: Close out this chat / Retire all chats (they write notes, the skills get the lessons) / New coordinator | `NEW-COORDINATOR-PROMPT.md` (the chat fills it in and sends it as a file) |

**Terminal commands** (Claude's Terminal panel or any terminal, in `C:\Users\Josh\Documents\LanternLive`; type `lr`
in cmd or `.\lr` in PowerShell for the list): `lr status` · `lr render` (everything missing) · `lr pass 864` (one pass,
`force` to redo) · `lr stop` · `lr open 864` (its .blend in Blender) · `lr waiting` · `lr ratings` · `lr library` ·
`lr watch` · `lr site`. If they go missing: copy `site-10\tools\pc\lr.cmd` and `lr.ps1` into LanternLive.

**Picking things to work on:** `docs/library/LIBRARY.md` gives everything a short id: `P:` waiting passes, `J:` models in
your jar, `T:` textures, `B:` Blender base models, `F:` your `.blend` files. Answer any chat with an id and a note, e.g.
`J:dark_lantern new lens, 3 takes`.

**Settings:**
- Model: Opus for the PC chat (fewer, careful steps; it checks renders); Sonnet for cloud threads (cheaper, parallel).
- Skills: `lantern-ring-design` (your taste), `lantern-blender-modeller`, `lantern-coordinator`. Copies live in
  `docs/skills/` so every chat reads the same rules. When a retired chat's lessons get folded in, save the skill card
  the coordinator proposes; then ask the PC chat to re-copy them into `docs/skills/`.

**Documents every chat reads:** `docs/handoff/STATE.md` (where everything stands), `RATINGS.md` / `DECISIONS.md` (your
picks), `docs/blender/review/INBOX.md` (passes waiting on you), `docs/library/LIBRARY.md` (the menu).

**When to retire a chat:** after a few passes, or when you switch area (e.g. rings -> lanterns). Not after every fix:
each new chat spends a pass's worth of reading to catch up. Say "Retire this chat"; it writes a note the next one reads.
