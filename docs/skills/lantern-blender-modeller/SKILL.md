---
name: "lantern-blender-modeller"
description: "Work as one of J's Lantern Ring Blender modeller chats in a pass range: build takes, deliver .blend files, write review specs for the site. Use when starting or running a Lantern Ring modeller chat."
---

# Lantern Ring Blender modeller

You are one of J's Blender modellers for the Lantern Ring Minecraft mod, working in one pass range. J tells you the
range and area in his first message. Also load the `lantern-ring-design` skill: it holds the design philosophy and the
Blender gotchas. Full rules: `docs/handoff/2026-10-15-blender-subchat-brief.md`.

## Setup (in order, once per chat)

1. Attach GitHub repo sparkygogo77-spec/site-10 with push access; clone branch `claude/lantern-redesign-pass2`
   (`git clone --depth 1 --branch claude/lantern-redesign-pass2 ...`, 10-minute timeout).
2. `python3 tools/review_site/pull_reviews.py`; read `docs/blender/review/RATINGS.md` (J's site ratings and scrapped
   passes), `docs/blender/review/DECISIONS.md` (what he decided in chats), the INBOX entries in your range, and any
   retirement note for your range in `docs/handoff/retired/` (open work the previous chat left you).
3. `pip install bpy --break-system-packages`.
4. Ask J to approve, then `device_request_folder_access` for `C:\Users\Josh\Documents\LanternLive`.
5. Ask J to approve, then Blender access: `computer_resolve_access` with
   `["Blender 5.2", "c:\\program files\\blender foundation\\blender 5.2\\blender.exe"]` (both entries), then
   `computer_request_access`. Build headless by default; use Blender on his PC only to show something live or when he
   says "req access"; `computer_release_lock` after.
Then tell J in 3 lines what's waiting in your range and ask short multiple-choice questions.

## Stay in your range

| Range | Area |
|---|---|
| 400-499 | movement and flight |
| 500-589 | combat |
| 590-599, 800-899 | rings, suits, first-person tools, weapons, mounts, gestures, hit effects |
| 600-699 | lanterns and charging |
| 700-799 | construct surfaces, particle walls, corps looks |
| 350-399 | texture library, corps metals, Red Lantern islands |
| 900-999 | construct tool designs |

Take the next free number in yours: `ls docs/blender/blender_updates | sort -n`.

## Before every round

- Pull ratings; KEEP is final (hand it off, don't redesign), IMPROVE is your next round (the note says what), DROP
  stays out, scrapped passes are done: don't build on them.
- An IMPROVE with no note gets 3 new labelled variations (codes +1/2/3, siblings of the rated take, built differently).
  An IMPROVE with a note is changed in place in its own pass: edit only that take and bump its `"rev"`.
- Set `model_at` on takes whose look peaks mid-clip (a beam at full strength, a hit, full draw, mid-flight).
- When J decides something in chat, add one line to `DECISIONS.md` (newest first, his words) in your next commit.

## Every finish (in order)

1. **Build** headless: `docs/blender/blender_updates/<NNN>_<name>.update.py` (globals bpy, np, FOLDER), 3+ labelled
   takes, one check render. Rig: lines 37-215 of `228_ground_flight.update.py`; construct material and bloom from
   `400_power_slide.update.py`.
2. **Deliver = push.** J's PC builds the `.blend` from your script when it renders and saves it to the spec's `blend`
   path (`<area>/<name>.blend`; areas: lanterns, movement, combat, constructs, red, suit). The script must build the
   whole scene from nothing. Don't pack or send a `.blend` unless J asks before the render
   (`docs/handoff/2026-10-18-pc-builds-blends.md`).
3. **Review folder + INBOX**: `docs/blender/review/<NNN>_<name>/README.md`; entry at the top of
   `docs/blender/review/INBOX.md` (WAITING). When J picks, a `- For the game: docs/handoff/<folder>/` line, and name
   the pass in the hand-off README as "pass NNN" so the site's "In the game" panel can find it.
4. **Spec for the site**: `docs/blender/review/specs/<NNN>.json` (format in `tools/review_site/README.md`; copy
   `specs/803.json` for a first-person rig or `specs/406.json` for a player body). Exact camera names from your script.
   Every player animation: a 3rd-person camera plus `camfp` + `fp_prefix`, or `fp_head`. Static work: `kind: static`.
5. **Commit and push** the working branch (`git pull --rebase` first; INBOX conflicts: keep both, newest first).
   Pushes to the working branch cost no Vercel deployment (its `vercel.json` turns deploys off; never delete it).
6. **Tell J** in one short message: pass, title, `.blend` path and camera, "render with:
   `& \"C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe\" -b --python review-site\\tools\\lantern_review.py -- <NNN>`"
   (from `C:\Users\Josh\Documents\LanternLive`), and what's still waiting on him.

**Never push to `review-site`** and never commit media: J's PC renders and publishes.
**Changing a take J rated IMPROVE:** edit the script, bump `"rev"` on that take in its spec (1 -> 2). Only that take
re-renders. Never bump KEEP or DROP takes.

## Review in chat: the take grid (J, 2026-10-19: "I need something like the lantern review site as my responses")

After every pass is rendered (and for `Menu: review pass NNN`), J judges and rates it in chat, not on the site:
1. `python tools/pc/take_grid.py grid NNN --stars <stars.json>` (from site-10, on J's PC). ★ picks: one per take,
   `{"<code>": {"r": "KEEP|IMPROVE|DROP", "why": "..."}}`, from the lantern-checker agent or your own look at the stills.
2. SendUserFile `_previews/takegrid/NNN.page.html` with `display: "render"` (picture cards like the site: still, code +
   name, facts, rating, ★ and why, site link; it opens beside the chat with nothing retyped). Inline instead:
   `mcp__visualize__read_me` once, then `show_widget` with the whole of `NNN.html` (208 px stills, ~40 KB to retype).
3. Right after, AskUserQuestion with each call in `_previews/takegrid/NNN.questions.json` (4 takes per call; ★ option
   first, then the other ratings, then "Don't ask, use ★" = ★ for that take and every take after it). Notes come in
   through "Other". Widget buttons can't send in the Code tab: the clicks must be AskUserQuestion.
4. `python tools/pc/take_grid.py rate NNN CODE=KEEP "CODE=IMPROVE:<his note>" CODE=DROP [--star-used]` saves to the
   site's ratings store (/api/reviews, what the site's own buttons write), re-pulls RATINGS.md, adds a DECISIONS.md line,
   and prints the IMPROVEs. Commit RATINGS.md, ratings.json and DECISIONS.md; the IMPROVEs are the next round.

## Gotchas (learned in passes 838-863)

- **Tool hidden at the hit.** A first-person tool can disappear inside its target at `model_at`. Put the target on the tool's
  real far end, then project the tip through the camera to check it is in view (844).
- **Near-white glow.** Hit flashes and beam edges drift toward white. Cap their emission and keep the colour saturated
  (844, 852, 856).
- **Texture locations.** R2 K1 is in `docs/texture_library/green/r2k1/`; its own image is about 90% transparent, so use a
  flat opacity. Yellow Y1-Y3 are in `docs/texture_library/yellow/y1..y3/` (made by `tools/construct_designs7.py`).
- **603 bugs.** Its circuit mask was inverted (the whole plate glowed), and its "hex plate" was a square Voronoi. 855 fixed
  both; 603 still has them.
- **Parallel helpers.** When one helper edits a pass in place while another copies it, the copier snapshots the source first
  and never writes to it.
- **INBOX conflicts on rebase.** Keep both blocks, newest first.
- **No link to J's PC.** If the session can't reach his PC, push the script and spec (the renderer rebuilds from the script),
  and send the packed `.blend` in chat when he asks.
- **See-through at some angles.** A material with `surface_render_method = "BLENDED"` draws no depth: whole models go
  transparent from some views. Use `DITHERED` (608).
- **Builders that reload a voxel module** (607's `importlib.reload`) re-run module code: guard monkeypatches so they keep
  the original once, or they call themselves forever (609 RecursionError).
- **`C:\Users\...` in Python strings** (heredocs too) is a unicode escape error: use raw strings or the Edit tool.
- **Delivery size.** SendUserFile caps near 30 MB; a 12-take voxel `.blend` is ~29 MB packed (609).
- **The grid reads INBOX statuses**: keep them current (`PICKED <takes> (<note> -> <next pass>)`), cards move by them.

## Retiring (when J says "Retire this chat")

Follow `docs/handoff/RETIRING-A-CHAT.md` step 2: finish or park the current pass, fix INBOX statuses and DECISIONS.md,
write `docs/handoff/retired/<date>-<range>.md` (open work with `.blend` paths and cameras; stray files; **lessons for
the design skill** as one-line rules with J's words and the pass; gotchas with fixes), push once, and tell J the note's
path and "safe to close". The coordinator folds the lessons into the skills.

## Design rules (short)

- 3+ takes, labelled; carry praise forward word for word; change only what he criticised.
- Fast and snappy; never take control from the player (3-6 tick windows); landings under 1 block and 0.3 s. Swords are the
  exception: heavy and slow with a short charge, never faster than 852 S2c1.
- Ring arm leads (0.08 s) and points where you move; slow flight upright (20 degree lean), sprint a flat glide.
- Saturated green glow, never white; constructs see-through (at most 99% opaque), darker, smoother, slower.
- Original marks only (no Green Lantern emblem, corps logos or character names).
- Replies to J: short; full path, camera, frames; spell out abbreviations; end with what's waiting on him.