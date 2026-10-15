# START HERE: starting new Lantern Ring chats (J's copy-paste sheet)

Three kinds of chat, all **Claude desktop chats linked to J's PC** (so they can reach LanternLive, Blender and the
built-in browser). Each starter below is self-contained: paste it as the first message of a fresh chat.

## The order to start them

1. **Coordinator first.** It owns the review site and the loop, knows who's doing what, and tells the others.
   Only one coordinator at a time; when one gets long, start a new one with the same starter (it picks up from the
   repo, nothing is lost).
2. **Then the modellers**, one per pass range (table below). Start only the ranges you're working on right now.
3. **The mc project chat already exists** (https://claude.ai/code/project/chan_01PxyDp7CugmGwF5sLv1ceR4). Don't
   recreate it. The coordinator sends it build orders.
4. **Render on your PC** whenever a modeller says a pass is ready (one command, below). Rate on your phone.

Already-running chats: paste the one-line note at the bottom instead of a starter.

## Starter: coordinator (also: the successor to the Blender designer chat 400–499)

```
You're the coordinator for my Lantern Ring Minecraft mod. You oversee my Blender modeller chats on the desktop and the
mc project Code threads (https://claude.ai/code/project/chan_01PxyDp7CugmGwF5sLv1ceR4), and you own the review site
https://lantern-review-j.vercel.app and its render loop. You also take over passes 400-499 (movement and flight).
Setup, in order:
1. Attach GitHub repo sparkygogo77-spec/site-10 with push access; clone branch claude/lantern-redesign-pass2
   (git clone --depth 1 --branch claude/lantern-redesign-pass2 ..., 10-minute timeout).
2. Read docs/handoff/2026-10-15-START-HERE.md, then docs/handoff/2026-10-14-coordinator-brief.md, then
   tools/review_site/README.md. Load the lantern-ring-design skill.
3. Run python3 tools/review_site/pull_reviews.py; read docs/blender/review/RATINGS.md, docs/blender/review/DECISIONS.md
   and the top of docs/blender/review/INBOX.md.
4. Ask me to approve, then request folder access to C:\Users\Josh\Documents\LanternLive.
5. Ask me to approve, then request Blender access on my PC (steps in START-HERE "Blender access").
6. pip install bpy --break-system-packages.
Then tell me in 5 lines what's waiting on me and what you'd do first, and ask short multiple-choice questions.
```

## Starter: Blender modeller (one per range; change the two lines in <>)

```
You're one of my Blender modellers for my Lantern Ring Minecraft mod.
Your passes: <e.g. 500-589>. Your area: <e.g. combat>. Stay in your range.
Setup, in order:
1. Attach GitHub repo sparkygogo77-spec/site-10 with push access; clone branch claude/lantern-redesign-pass2
   (git clone --depth 1 --branch claude/lantern-redesign-pass2 ..., 10-minute timeout).
2. Read docs/handoff/2026-10-15-blender-subchat-brief.md and docs/handoff/2026-10-15-START-HERE.md
   ("Blender access"). Load the lantern-ring-design skill.
3. Run python3 tools/review_site/pull_reviews.py; read docs/blender/review/RATINGS.md, docs/blender/review/DECISIONS.md
   and the INBOX entries in your range.
4. pip install bpy --break-system-packages.
5. Ask me to approve, then request folder access to C:\Users\Josh\Documents\LanternLive.
6. Ask me to approve, then request Blender access on my PC.
Then tell me in 3 lines what's waiting in your range and ask short multiple-choice questions.
```

### Pass ranges (take the next free number inside yours: `ls docs/blender/blender_updates | sort -n`)

| Range | Area |
|---|---|
| 400–499 | movement and flight: take-off, arm lead, landings (coordinator, or a modeller if you split it off) |
| 500–589 | combat: slams, omega beams, flurry, grab and throw |
| 590–599, 800–899 | rings, suits, first-person tools, construct weapons, mounts, gestures, hit effects |
| 600–699 | lanterns and charging |
| 700–799 | construct surfaces, particle walls, corps looks |
| 350–399 | texture library, corps metals, Red Lantern islands |
| 900–999 | construct tool designs (950 exists) |

## Blender access (any chat, after J approves)

1. Load the computer tools (ToolSearch `computer`), then
   `computer_resolve_access` with `["Blender 5.2", "c:\\program files\\blender foundation\\blender 5.2\\blender.exe"]`.
   Both entries are needed: the launcher and the running `blender.exe` are separate apps.
2. `computer_request_access` with both resolved apps; give the reason ("build and show takes in your Blender").
3. Use it only to show J something live or when he says "req access"; build headless otherwise (faster, no clicks).
4. `computer_release_lock` when you're done, so J gets his mouse back.

Folder access the same way: ask in chat first, then `device_request_folder_access` for
`C:\Users\Josh\Documents\LanternLive`. A prompt nobody answers times out; then only `SendUserFile` works.

## Render on J's PC (when a modeller says a pass is ready)

```
cd C:\Users\Josh\Documents\LanternLive
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python review-site\tools\lantern_review.py -- --all
```

To stop early: `ni C:\Users\Josh\Documents\LanternLive\review-site\STOP` in a second window (it uploads what's done).

## Retiring a chat (when it gets long or its range is done)

Paste into the old chat:

```
Retire this chat. Follow docs/handoff/RETIRING-A-CHAT.md on claude/lantern-redesign-pass2 (pull first), step 2.
```

It writes `docs/handoff/retired/<date>-<range>.md` (open work, lessons, gotchas). The coordinator folds the lessons into
the `lantern-ring-design` skill for you to save, then start the replacement with the normal starter.

## One-line note for chats already running

```
New rule for every finish: read docs/handoff/2026-10-15-blender-subchat-brief.md on claude/lantern-redesign-pass2 (pull first) and follow its "Every finish" steps: write a review spec to docs/blender/review/specs/<pass>.json, and check RATINGS.md and DECISIONS.md before you start anything; when I decide something in chat, add it to DECISIONS.md.
```

## Where this chat (Blender designer 400–499 + first coordinator) left off, 2026-10-15

- **Built:** passes 400–406; the review site (Vercel project `lantern-review`, branch `review-site`, ratings in a
  private Blob); the PC renderer `tools/review_site/lantern_review.py`; `pull_reviews.py`; specs for every waiting
  pass in `docs/blender/review/specs/`; the briefs; `DECISIONS.md`.
- **J's picks not yet sent to the mc chat** (send as a build order from `docs/handoff/`):
  405 L4 as the landing with 0.3 blocks of carry (L5/L6/L2 dropped); 404 D1 default + D3 option (D2 dropped);
  403 S2a "maybe settles at 2.2" (IMPROVE, a new round); the forward-descend bug from DECISIONS.md.
- **Waiting on J:** 406 (upright arm lead), R3A3 (ask what's wrong), everything new on the site.
- **Not done:** the `sparkygogo77-spec/lantern-blender` repo (J has to create it); moving the stray rebuilt `.blend`
  files from the LanternLive root (smoke_long_rays, smoke_rays_detail, red_halo9...) to `_to_delete\`.
