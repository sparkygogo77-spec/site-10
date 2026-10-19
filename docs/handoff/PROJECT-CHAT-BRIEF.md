# Brief: a Blender thread in the Site 10 project

J starts every new Blender thread in the Site 10 project
(https://claude.ai/code/project/chan_01Nh3k9VYj9ScKTPZ7pDFFDu) by pasting `docs/handoff/NEW-CHAT-PROMPT.md`. This file is
the whole brief: do what it says, in order, and keep replies short.

**Who manages you:** the **PC chat**, a Claude Code session running on J's PC (`C:\Users\Josh\Documents\LanternLive`).
It has J's graphics card (RTX 5070 Ti, Blender 5.2), his files and the review renderer, and it reads and posts in this
project through its built-in browser. It may post here as J's messages (they start with "From the PC chat:"). Treat
those as J's instructions relayed. You can't message it directly: write to the repo (below) and it picks that up
within about 10 minutes.

## 1. Setup (silent, before your first reply)

1. Clone: `git clone --depth 1 --branch claude/lantern-redesign-pass2 https://github.com/sparkygogo77-spec/site-10`
   (10-minute timeout).
2. **Skills.** If the skills `lantern-ring-design` and `lantern-blender-modeller` are available to you, load them.
   Either way, read `docs/skills/lantern-ring-design/SKILL.md` and `docs/skills/lantern-blender-modeller/SKILL.md`
   (repo copies of the same skills; the account version wins if they differ). Skip the modeller skill's PC-access setup
   steps (folder access, computer access): the PC chat does that work now.
3. `python3 tools/review_site/pull_reviews.py`, then `python3 tools/gen_asset_library.py`.
4. Read `docs/handoff/STATE.md`, `docs/blender/review/DECISIONS.md` (top 20 lines) and
   `docs/handoff/2026-10-18-pc-builds-blends.md`.

## 2. First reply (always this shape)

```
Loading skills: lantern-ring-design, lantern-blender-modeller (account skills | repo copies in docs/skills/).
Asset library: docs/library/LIBRARY.md (<N> waiting passes, <N> jar models, <N> textures, PC files listed <date>).

Start here (waiting on you):
  P:863 Fear-consumed mobs: Yellow armour and tools · suit\fear_gear.blend
  ... (the 8 lines under "Start here" in LIBRARY.md)
Also: J: jar models (lanterns, rings, tools, mobs) · T: textures · B: base models · F: your .blend files

1. What should I make? Answer with an id and a note (e.g. "P:860 improve the glow", "J:dark_lantern new lens"),
   or describe something new.
2. Pass range for this thread? (★ <the first free range from the table, see below>)
3. Build route: ★ A here / B PC chat on your graphics card / C live in your Blender (see below)
```

Fill the numbers and the 8 lines from the generated `LIBRARY.md`, nothing else. Nothing longer than this.

## 3. The three build routes (J picks per job)

| Route | Who builds | Best for | J gets |
|---|---|---|---|
| **A ★ Here** | this thread writes the script and spec and pushes | most passes: new takes, variations, IMPROVEs with a note | clips on the review site; the PC builds the `.blend` into his area folder when it renders (about 15 min after the push) |
| **B PC chat** | the PC chat, on J's graphics card | look-dev that needs many fast renders (glow, bloom, colour, translucency), matching the game's shaders, fixing a pass that fails on the PC | the same, plus in-game comparison; slower to start (one chat, one job at a time) |
| **C Live** | the script runs in J's open Blender via Lantern Live | J wants to watch it build and tweak by hand | the scene in his Blender; review clips only if a spec is pushed too |

- **Route A:** follow the modeller skill's "Every finish", with the change in `2026-10-18-pc-builds-blends.md`: push
  the script and spec; don't pack or send a `.blend`. The script must build the whole scene from nothing.
- **Route B:** write `docs/pc_requests/<YYYY-MM-DD>-<pass>-<slug>.md` (format in `docs/pc_requests/README.md`), push,
  and tell J "sent to the PC chat". Don't build the same pass here. When the PC chat finishes it moves the file to
  `docs/pc_requests/done/` with what it made, and posts here.
- **Route C:** write the script as for A, then a request with `route: C`. The PC chat copies it into the LanternLive root
  as `NN_name.update.py`, which Lantern Live runs in J's open Blender.

## 4. Pass ranges

Take a range J names; otherwise offer the first one with no open thread in `STATE.md`:

| Range | Area |
|---|---|
| 400-499 | movement and flight |
| 500-589 | combat |
| 590-599, 800-899 | rings, suits, first-person tools, weapons, mounts, gestures, hit effects |
| 600-699 | lanterns and charging |
| 700-799 | construct surfaces, particle walls, corps looks |
| 350-399 | texture library, corps metals, Red Lantern islands |
| 900-999 | construct tool designs |

Name the thread "Blender: <area> <range>" and add a line to `STATE.md`'s thread table when you start.

## 5. Rules that matter most (the skills have the rest)

- 3+ labelled takes; carry J's praise forward word for word; change only what he criticised.
- KEEP is final (hand off), IMPROVE is your next round, DROP stays out. Scrapped passes are done.
- Saturated green glow, never white; constructs see-through (at most 99% opaque), darker, smoother, slower.
- Original marks only: no Green Lantern emblem, corps logos or character names.
- Never push to `review-site`, never commit media: J's PC renders and publishes.
- Replies: full path (`C:\Users\Josh\Documents\LanternLive\<area>\<name>.blend`), camera, frames; spell out
  abbreviations; end with what's waiting on J and whether it's in the game yet.
- Re-run `python3 tools/gen_asset_library.py` and commit `docs/library/` with each finish, so the next thread's menu is
  current.
