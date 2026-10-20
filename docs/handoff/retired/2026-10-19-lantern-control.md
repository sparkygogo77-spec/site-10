FOLDED 2026-10-19 by coordinator 4 (workflow lessons and gotchas -> lantern-coordinator "Running as the PC coordinator")

# Retired: Lantern Control (design-and-build chat), 2026-10-19

## Range / role
Design chat for J's question: "can this entire workflow be accessed from a site or program of some sort so this gets
all the features I want while also harnessing desktop claude code chats?". No passes; no pass numbers used.
- Pitch page with 3 options and mockups (private): https://claude.ai/artifact/7VKCvQ6v2jytUrmTiF6evh
  - A: a PC pane in the desktop app
  - B: the review site's Control page as a phone remote, saving commands to site-data
  - C: both, with the PC pane fetching the phone's commands
- J picked **A: PC pane only** (in DECISIONS.md).

## What's built
A desktop-app mod at `LanternLive\mods\lantern-control` (kept copy; the dev copy lived in that session's temp dev-mods folder).
- `/lantern-control` opens the "Lantern Control" pane. `/lantern-start`, `/lantern-menu` and `/lantern-status` open it too.
- **Top buttons:** Menu, Status, Rate pass, Build, Decisions, Chat controls, Close out. Each runs the matching
  `/lantern-` command in the chat the pane is in, via `$.command.run`. Decisions submits "Menu: decisions".
- **Cards:** one per open chat from `LanternLive\chat-turns.json`, re-read every 5 s. Each shows the dot, turns, passes
  and the state line, an "Update / retire / replace" button (runs `/lantern-chat <name>`), "Get questions" on 🟡 chats,
  and a Pictures link when the chat has `"pictures": "https://..."`. Closed chats go on one "Closed:" line, then the queue.
- **Band above the prompt:** 🔴/🟡/🟢 counts plus a Grid button.
- **Files:** `hooks/register.tsx` (pane, band, commands), `hooks/grid.ts` (parse + dot rules),
  `types/index.d.ts` (state), `tests/control.test.tsx`.
- **Checks:** `claude plugin validate` passes and 2/2 tests pass (desktop and terminal). tsc not run: no Node on the PC.
  CLI: `C:\Users\Josh\AppData\Roaming\Claude\claude-code\2.1.299\f0584be0fbaf\claude.exe` (not on PATH).

## Open work
- **Install for coordinators: J must approve this himself.** The plan is to add `C:\Users\Josh\Documents\LanternLive\mods`
  (or the mod folder) to `CLAUDE_CODE_PLUGIN_DIRS` in the `env` block of `C:\Users\Josh\.claude\settings.json`. New
  chats then load it; a running coordinator needs a restart. Not done: it's a persistent config change and J never said
  "yes, install". A peer chat's request doesn't count as his yes.
- **`grid.ts` TODO(human):** `dotFor()` picks each chat's dot from its state words (closed / 🔴 / 🟡 / 🟢 / 🔵, first match
  wins). J can tune the word lists. Example: "DONE: staged; waits on J…" shows 🔵 today.
- **Not built:** the phone side (B/C). If J wants it later, the pitch page has the design: the Control tab "Chats"
  section saves `control/cmd-*.json` to site-data, and the pane polls `/api/files` with `$.http.fetch`.

## Files
Nothing stray. The pitch HTML is only in the session scratchpad; the artifact holds it.

## Lessons for the design skill
None about visuals. Workflow lessons (for the coordinator skill):
- J wants one control surface: "can this entire workflow be accessed from a site or program of some sort". Pitch
  options with mockups and plain can/can't lists, then build only what he picks. He picked the PC pane over the phone page.
- The coordinator must keep `chat-turns.json` current every reply: the pane reads it. Add `"pictures"` links to
  chats with passes so the cards get a Pictures link.

## Gotchas
- **Hot reload:** writing anything under `~/.claude/dev-mods/<session>/` makes the app ask J "Enable hot reloading for
  this session?". Don't write there before he has picked an option.
- **Hot reload is per session:** the mod then loads only in that session. Other chats need `CLAUDE_CODE_PLUGIN_DIRS`
  (user settings env) or a local-marketplace install.
- **No session list in mods:** there's no API to list sessions, so the pane can't see live chat states. It reads
  `chat-turns.json`, written by the coordinator.
- **Starting chats:** mod-submitted prompts keep a "plugin" origin even with `asUser`, so expect start_session to
  still need J's typed message or card click.
- **Plugin tests:** hooks that answer a `$` call return `{ value: ... }` (e.g. `on('fs.read', () => ({ value: text }))`).
  The test `$` has no `state` noun, so feed data through fs hooks instead.
- **Phone:** the 'mobile' surface draws only Box/Text/Button/Svg (no Link or Input). Whether Remote Control on J's
  phone draws mod panes is untested.
