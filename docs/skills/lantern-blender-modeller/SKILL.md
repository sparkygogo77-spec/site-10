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

## Response style (J, 2026-10-19: "more appealing answers and explanations and visualizations")

Every turn-ending reply, in this order:
1. First line: 🟡 QUESTION / 🔵 DONE / 🔴 PERMISSION, then the clickable link to the pictures (review-site `#report/<pass>`,
   an Artifact page, or the chat as [title](#local_id)).
2. A visual: `show_widget` (take grid, status board, before/after, diagram) in the chat; anything J must look at on his
   phone goes on a private Artifact page with the pictures embedded (widgets don't reach Remote Control).
3. 2-4 plain sentences: what was made or found, why it matters for the mod, what is still open. No jargon; numbers
   in his units (blocks, hearts, seconds).
4. The question (AskUserQuestion): pathway style (category, then target); each option says what he will see or get,
   names its picture ("card 2 on the Titan bosses page"), and one option is "Don't ask, use ★".

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

- **(take grid chat, 2026-10-19)** Rate in chat by default ("I need something like the lantern review site as my
  responses"); send J to the site only when he picks it (he did for v2.0111). ★ is a starting point: J overruled most
  ★ picks on 609 (dropped the whole hex line), so lean IMPROVE when unsure.
- Picture grids: SendUserFile `NNN.page.html` with display "render" (show_widget can't load local files and retypes
  every base64 byte). Never hand-edit ratings.json: `take_grid.py rate` / `flush` (pull_reviews.py overwrites it); don't
  commit an empty MARKUPS.md after /api/markups fails. The site's rating button toggles: clicking a take's current
  rating clears it.

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

- **SendUserFile cap (30 MB):** voxel creature passes run 64-108 MB; split per take with
  `tools/trials/split_blend_by_take.py`.
- **Git Bash heredocs halve backslashes** in Python literals (`` became a vertical tab and overwrote another spec):
  build Windows paths with `chr(92)` or use the Edit tool.
- **Voxel helpers:** guard boxes that leave the grid (`if np.any(hi <= lo): return`); `grid_mesh` draws a face only
  where the neighbour is empty or a different see-through label, so glass shows its insides with no hidden faces.
- **Blender 5 turntables:** `action.fcurves` is gone; spin with a driver `frame*0.05236` (one turn per 120 frames).
- **Pixel-snapped veins:** snap object coords to 1/16 (Vector Math SNAP) before Noise; keep vein emission 0.2-0.45.
- **Cameras inside closed caves see only stone:** build open-top dioramas or cut the front wall away.

- **(spider lair, 2026-10-19)** Git Bash heredocs mangle Python (`\\n`, nested quotes): write scripts with the Write
  tool; open text files with `encoding="utf-8"`. `"LanternLive\trials"` in a Python string is a tab: use raw strings.
- **Blender 5.2:** `sc.cycles.use_preview_denoising` (not `preview_denoising`); render paths must be absolute.
- **Parenting in scripts:** `child.parent = root` without touching `matrix_parent_inverse`, or parts land at the origin.
- **Big voxel meshes:** `remove_doubles` then `dissolve_limit(delimit={"MATERIAL"})` (54 MB .blend -> 5.5 MB).
- **numpy room masks** from broadcast axes are (1, Y, Z): `np.broadcast_to(m, (X, Y, Z)).copy()` before in-place `&=`.
- **Datapacks:** `fill` caps at 32,768 blocks (split slabs in x too); force-load tiles at 200 blocks; a function chain
  caps at 65,536 commands (split into scheduled parts run `execute at` a marker). Stacked caves: "lowest air in the
  column" finds the cave below, so restrict the search by y.

- **(Warren look 2, 2026-10-20)** A SUN light lights every take in the file: use AREA lights with a cutoff per take.
  Area light `rot=(radians(-40), 0, ..)` points away (-y); +X rotation points +y at the scene.
- **Eye-height cameras into pits:** stand at the rim (2-3 blocks) and aim at the far wall. Carve walk-in corridors 5
  wide, 4 tall (1-block frames in 3x3 read as doorways). Calm webs: alpha 0.0 (0.03 still shows up close).
- **Site renders come out darker than quick tests:** light calm scenes brighter than looks right in a test.
- **BLENDER.lock can be held by another chat's non-review Blender job:** wait, never break it.
- **One take at a time with J:** build one, still above an AskUserQuestion, steer the next from his answer; every pick
  question gets a "New iterations" option ("give me a new iterations button").

- **(spider lair r8-10) Leg IK that never clips:** foot rays hit only the ground (BVH trees of the course meshes,
  never the spider's own boxes); aim each foot within 36-88% of the leg's reach; reject spots behind the creature's
  back plane; pull a foot back onto a ledge rather than down a drop; take a catch-up step when a planted foot is
  stretched past 88% of reach or 9 blocks off its spot; then a per-frame knee search (knee out / fore-aft / up grid,
  foot kept planted, small cost for change) clears whatever still touches. Same sample count in the fixer and the check.
- **Paths:** never turn a body 90 degrees in one frame (feet cross); level the body again at the top of a slope.
- **Cutaway scenes:** cast feet and run the floor check against the whole ground; only the picture is cut open.
- **Course edges:** pad walk courses 30 blocks past both ends, or back feet hang off the edge.
- **Render lock:** wrap every headless render in a script that refuses if `review-site\BLENDER.lock` or `RENDERING`
  exists, writes its own PID to BLENDER.lock and removes it after; when locked, queue a background wait-then-render.
- **Check before render:** a `--check` mode that builds without rendering (5-20 s) for every iteration; render once.
- **Versioned outputs:** a new .blend, render folder and page per round (overwriting round N's stills broke its page).

- **(creatures refine, 2026-10-20) Two-bone IK on a rolling body:** solve in the limb parent's frame and swing the
  limb plane through the target (`atan2(-dx, -dz)`), or planted feet drift. Raise limbs by blending the direction
  (normalised lerp), not Euler angles. Hugging arms: roll the arm about the shoulder-to-hand line to point elbows out.
- **Checks:** split tapered limbs into two capsules (one max-radius capsule reports false floor clips); leave
  scaled-to-nothing frames (teleports) out of collision checks.
- **Hurt flash:** an Attribute node (OBJECT, "hurt") mixing base colour to red, keyed per part; works in EEVEE.
- **Cameras:** `clip_end` about 2.5x the camera distance so neighbouring takes don't show; throws go across the view.
- **PowerShell 5.1:** commit with `git commit -F <file>`; never pipe a here-string into `python -`; `Set-Content
  -Encoding utf8` adds a BOM (read with `utf-8-sig`).

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