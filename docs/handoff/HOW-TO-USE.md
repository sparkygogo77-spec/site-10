# How J uses the Lantern chats (one page)

| You want | Use | Start it with |
|---|---|---|
| New Blender work, fast, checked on your graphics card | **PC chat** (Claude Code app, folder LanternLive) | `DESKTOP-KICKOFF.md` |
| Several jobs at once, or work while your PC is off | **Cloud thread** in the Site 10 project | `NEW-CHAT-PROMPT.md` (or ask the PC chat to post it) |
| Game code, jars, PRs, merges | Site 10 project coordinator / threads | the project's main box |
| Rate takes | https://lantern-review-j.vercel.app on your phone | KEEP / IMPROVE / DROP + a note |

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
