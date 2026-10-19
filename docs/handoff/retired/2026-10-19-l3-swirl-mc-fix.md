# Retired: "L3 core swirl in the game" chat (Claude Code on J's PC, side session), 2026-10-19

**Role:** mc build chat, one task: J said "I need L3 core swirl in the game" (pass 807 KEEP). Last pass used: none
(no new pass, no code change, no PR).

## What hid the swirl
- The code was already in main and in jar **2.1.1712** (commits 3104745, 69147f1, 7bf423c; the jar has
  `dark_lantern_swirl_*.png`). Two things on J's PC hid it:
  1. **Old jar.** Lunar's mods folder (`C:\Users\Josh\.lunarclient\profiles\26\mods\fabric-26.3`) held
     `lantern-ring-latest (29).jar` = **2.1.681** (2026-10-16). Installed 2.1.1712 there as `lantern-ring-latest.jar`;
     the old one is in `C:\Users\Josh\.lunarclient\profiles\26\mods-backup\lantern-ring-2.1.681.jar`.
  2. **Ring Lab Lantern model = Nebula** (`%APPDATA%\.minecraft\config\lanternring-lab.json`, a touched row, so no jar
     changes it). The L3 swirl only draws on the Dark Lantern. J chose "Just the jar": he switches it himself,
     K > Lantern > Lantern model > Dark Lantern.
- Charge style there is Floating (touched; the star is Hip carry); the swirl shows with either.

## Open work
- **The in-game check is still J's:** Dark Lantern picked, charge, the strands round the core should spin faster as it
  fills and the heart flare. DECISIONS has "chat-l3-swirl ... Haven't tried yet".

## Files
- `C:\Users\Josh\Documents\LanternLive\mc-l3`: empty leftover worktree folder (Windows refused the delete); safe to delete.
- `...\profiles\26\mods-backup\lantern-ring-2.1.681.jar`: old jar, safe to delete once J is happy.

## Lessons for the design skill
- None new (no design work in this chat).

## Gotchas
- **"It's not in the game" may be J's PC, not the code.** Before building, check on J's PC: the jar version inside
  Lunar's mods folder (`fabric.mod.json` in the jar) and his saved Ring Lab rows in
  `%APPDATA%\.minecraft\config\lanternring-lab.json` (`touched` rows never move to a new star pick, and a row picked
  before the star moved there shows no "new pick" badge).
- **The jar link never changes:** https://github.com/sparkygogo77-spec/site-10/blob/builds/lantern-ring-latest.jar
  (`latest.json` beside it gives the version). Browser downloads pile up as `lantern-ring-latest (N).jar`; only one
  Lantern Ring jar may sit in the mods folder.
- **`gh` is not installed on J's PC.** Take the jar from git instead:
  `git -C site-10 cat-file blob origin/builds:lantern-ring-latest.jar > jar` (run through `cmd /c` so the bytes stay intact).
