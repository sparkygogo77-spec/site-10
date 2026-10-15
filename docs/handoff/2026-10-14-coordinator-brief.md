# Coordinator brief: Lantern Ring (Blender desktop chats + mc project threads)

For a **new coordinator chat**: a Claude desktop chat (cloud workspace linked to J's PC, with the built-in browser)
that oversees the Blender modeller chats on the desktop and the mc project Code threads. Read this whole file first;
it is meant to be enough on its own. Last updated 2026-10-14 by the Blender designer chat (passes 400–499).

## Starter (J pastes this into a fresh desktop chat)

```
You're the coordinator for my Lantern Ring Minecraft mod. You oversee my Blender chats on the desktop and the mc
project Code threads (https://claude.ai/code/project/chan_01PxyDp7CugmGwF5sLv1ceR4).
Setup, in order:
1. Attach GitHub repo sparkygogo77-spec/site-10 with push access; clone branch claude/lantern-redesign-pass2
   (git clone --depth 1 --branch claude/lantern-redesign-pass2 ..., 10-minute timeout).
2. Read docs/handoff/2026-10-14-coordinator-brief.md, then load the lantern-ring-design skill.
3. Run python3 tools/review_site/pull_reviews.py and read docs/blender/review/RATINGS.md and the top of
   docs/blender/review/INBOX.md.
4. Ask me to approve folder access, then request C:\Users\Josh\Documents\LanternLive.
Then tell me in 5 lines what's waiting on me and what you'd do first, and ask short multiple-choice questions.
```

## 1. The setup in one picture

| Who | Where | Does |
|---|---|---|
| **J** | phone + PC (Lunar Client, Blender 5.2) | judges by eye: rates takes on the review site, tests jars in game |
| **Coordinator (you)** | desktop chat, linked to J's PC | routes work, keeps the loop moving, writes briefs, tells chats what J picked |
| **Blender chats** | desktop chats, each with a pass range | build takes (models, textures, animations) as `.update.py` scripts + packed `.blend` |
| **mc project chat / Code threads** | claude.ai/code project "mc" | the Java mod: builds what J picked into the jar, Ring Lab options |

Pass ranges (take the next free number in your own range: `ls docs/blender/blender_updates | sort -n`):

| Range | Chat | Area |
|---|---|---|
| <100, 300–349 | super jump chat | super jump, smoke, light |
| 200–299 | lead Blender chat | sprint, ground flight, splits work |
| 350–399 | Chat B | texture library, corps metals, Red Lantern islands |
| 400–499 | Blender designer chat | take-off, flight, landings, arm lead (403–406) |
| 500–589, 600s, 700s | combat chat | combat, slams, omega beams, flurry; lanterns/charge; particle walls, corps looks |
| 590–599, 800s | rings and suits chat | suit armour, skin workshop, rings, first-person tools |

## 2. The review loop (the main thing you run)

**Site:** https://lantern-review-j.vercel.app: per take, a looping 3rd-person clip, a 1st-person (eye camera) clip, a
spinnable 3D pose, KEEP / IMPROVE / DROP and a note. It's the `review-site` branch, deployed by Vercel project
`lantern-review` on every push. Full how-to: `tools/review_site/README.md`.

1. A Blender chat finishes a pass and writes `docs/blender/review/specs/<key>.json` on the working branch (no deploy;
   chats never push to `review-site`). Sub-chat starter and rules: `docs/handoff/2026-10-15-blender-subchat-brief.md`.
2. J's PC renders it: `blender -b --python review-site\tools\lantern_review.py -- <key>` (graphics card, minutes),
   which pushes the clips; Vercel redeploys in about a minute. Cloud fallback: Cycles on CPU, about 1.5 s a frame.
3. J rates on his phone.
4. `python3 tools/review_site/pull_reviews.py` writes `docs/blender/review/RATINGS.md`. KEEP = final,
   IMPROVE = next round (the note says what), DROP = safe to remove. "Re-rendered since" = he rated an older render.
5. Scrapped passes (J's "Scrap pass" button) are listed at the top of `RATINGS.md`; the renderer skips them.
6. You route it: KEEP → a hand-off in `docs/handoff/<date>-<topic>/` and a message to the mc chat;
   IMPROVE → the Blender chat that owns the range; DROP → mark OLD in `docs/blender/DESIGNS.md`.

## 3. Design philosophy (condensed; the lantern-ring-design skill has the detail)

**Working with J**
- Show, don't describe. Always 3+ labelled takes (A1, A2…). Iterate until he says move on.
- Carry his praise forward word for word; change only what he criticised.
- Short replies: what changed and where to look. Always give the full path
  (`C:\Users\Josh\Documents\LanternLive\<area>\<file>.blend`), the camera and the frames. No contact-sheet grids for him.
- Spell out every abbreviation on first use. Keep status updates short. Ground recommendations in numbers.
- End with what's still waiting on him, and whether it's in the game yet.
- Test once: one check render per pass; the visual review is his.
- Ask short multiple-choice questions, then build straight away.

**Feel**
- Fast and snappy. No wind-ups; mobs launched on contact; instant craters; the construct lingers briefly after.
- Never take control from the player: owned windows of 3–6 ticks, steering always honoured, any input cancels.
- Landings stop close: under 1 block of carry, under 0.3 s (he just asked for 0.3 blocks on L4).
- The ring arm leads (0.08 s in flight) and points where you move; the free hand is still or stabilising.
  Slow flight is upright (20° lean), sprint flight is a flat glide: judge arm poses on the body the game will use.
- Every player animation needs both a 1st-person and a 3rd-person view.

**Look**
- Glow: saturated green, never washed to white (Standard view transform, compositor Bloom), steady, solid enough to
  read in game; darker cores.
- Constructs: see-through (at most 99% opaque), outer shell only, darker, smoother, slower (frametime 4–5, loops
  of 5–10 s), every design built a different way (no recolours), dark jade lines not white.
- Unpredictable beats regular; when he asks for many, 20–25 takes with no repeats.
- Lantern charge G3: 12 s to full, 2 s overcharge, 7.5 s fade, spin one way, gold cracks dim, never white.
- Models: voxel pixel art, Blockbench export, about 2,500 boxes / 3 MB; inflate glow cubes 0.02 px.
- Original marks only: never the Green Lantern emblem, corps logos or character names, even from his references.
- Jar under 30 MB. His saved Ring Lab choices must never be overwritten by a new jar.

## 4. Skills and when to load them

| Skill | Load when |
|---|---|
| `lantern-ring-design` | any model, texture, animation or design decision (always, at start) |
| `artifact-design` / `artifact-capabilities` | building or changing a page for J (the review site itself is on Vercel, not an Artifact) |
| `built-in-browser` | before posting to the mc chat through the browser |
| `computer-use` | only if J says "req access" or wants to watch Blender |
| `docs` | J asks for a document to keep or share (repo briefs like this one stay markdown in the repo) |

## 5. Commands you'll use

| What | Command |
|---|---|
| J's ratings into the repo | `python3 tools/review_site/pull_reviews.py` |
| Raw ratings | `curl https://lantern-review-j.vercel.app/api/reviews` |
| In-game "To Claude" reports | `gh api "repos/sparkygogo77-spec/site-10/issues?labels=claude-inbox"` (GraphQL is blocked) |
| Latest jar | `git fetch origin "+refs/heads/builds:refs/remotes/origin/builds"; git show origin/builds:latest.json` |
| Game source | `git fetch origin "+refs/heads/main:refs/remotes/origin/main"` |
| Site branch | `git clone -b review-site --single-branch https://github.com/sparkygogo77-spec/site-10 review-site` |
| Deliver a file to J | `device_commit_files` into `LanternLive\<area>\` (needs folder access) |
| Blender headless | `pip install bpy --break-system-packages`; build with `tools/blender_pipeline/build_pass.py` |

**Posting to the mc chat (built-in browser):** load the tools in one ToolSearch
(`mcp__remote-devices__Claude_Browser__`), `preview_start` the project URL, click "Close" if it opened inside an old
thread, `find` "question or start a task", click, type, check the box text with javascript, Return, then `find` your
first words to confirm. Never type over J's unsent draft; use the thread's "Steer this thread…" box instead. If you
can't confirm, give J one line to paste.

## 6. Repo map

| Path | What |
|---|---|
| `docs/blender/review/INBOX.md` | one entry per Blender delivery, newest first, with status WAITING / PICKED / HANDED OFF |
| `docs/blender/review/RATINGS.md` | J's latest site ratings (pulled) |
| `docs/blender/review/<NNN>_*/` | per pass: README, sheet, poses JSON |
| `docs/blender/DESIGNS.md` | every design and its state (OLD = superseded) |
| `docs/blender/blender_updates/` | every pass's build script |
| `docs/handoff/` | briefs for the mc chat (J's picks, exact numbers); `2026-10-14-blender-chat-briefs-2.md` has the Blender rules and gotchas |
| `tools/review_site/` | the review loop: PC renderer, site generator, ratings puller |
| `CLAUDE.md` | how to build the mod (Java 25, Minecraft 26.3, Mojang names) |

## 7. Open as of 2026-10-14

- J's site ratings (also in `RATINGS.md`):
  - **404:** D1 and D3 KEEP, D2 DROP.
  - **405:** L4 KEEP with 0.3 blocks of carry; L5, L6 and L2 DROP.
  - **403:** S2a IMPROVE ("maybe settles at 2.2"); R3A3 IMPROVE (no note yet: ask what's wrong).
  - None of these has gone to the mc chat yet.
- 406 (upright slow-flight arm lead) is rendering, so J can judge the arm on the upright body.
- The review site is still filling with every waiting pass (803 tools, 519 catalogue, rings, suits, combat, walls,
  Red, smoke). Older rounds that newer passes replaced were cut.
- Ring Lab settings fix for the mc chat: `docs/handoff/2026-10-14-j-ring-lab-settings/` (stop overwriting his picks,
  his notes went missing). J was on jar 2.1.647; the latest seen was 2.1.655.
- `sparkygogo77-spec/lantern-blender` (a repo for the sorted .blend files) doesn't exist yet; J has to create it.
