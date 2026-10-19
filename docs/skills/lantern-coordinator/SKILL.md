---
name: "lantern-coordinator"
description: "Coordinate J's Lantern Ring chats: review site, PC render loop, Blender modeller chats and the mc project chat. Use when starting or running a Lantern Ring coordinator chat."
---

# Lantern Ring coordinator

You coordinate J's Lantern Ring Minecraft mod work: the Blender modeller chats on his desktop, the mc project Code
threads (https://claude.ai/code/project/chan_01YLUFj9KADvqrGT75FUzG27), and the review site
https://lantern-review-j.vercel.app. You also own passes 400-499 (movement and flight) unless J has given them to a
modeller. Also load the `lantern-ring-design` skill: it holds the design philosophy.

## Setup (in order, once per chat)

1. Attach GitHub repo sparkygogo77-spec/site-10 with push access; clone branch `claude/lantern-redesign-pass2`
   (`git clone --depth 1 --branch claude/lantern-redesign-pass2 ...`, 10-minute timeout).
2. Read `docs/handoff/2026-10-15-START-HERE.md` (its "where this chat left off"), `docs/handoff/2026-10-14-coordinator-brief.md`
   and `tools/review_site/README.md`.
3. `python3 tools/review_site/pull_reviews.py`; read `docs/blender/review/RATINGS.md` (site ratings + scrapped passes),
   `docs/blender/review/DECISIONS.md` (what J decided in chats) and the top of `docs/blender/review/INBOX.md`.
4. Check `docs/handoff/retired/` for notes not marked FOLDED; fold them in (see "Retiring chats").
5. Ask J to approve, then `device_request_folder_access` for `C:\Users\Josh\Documents\LanternLive`.
6. Ask J to approve, then Blender access: `computer_resolve_access` with
   `["Blender 5.2", "c:\\program files\\blender foundation\\blender 5.2\\blender.exe"]` (both entries), then
   `computer_request_access`. Use it only to show something live or when J says "req access"; `computer_release_lock` after.
7. `pip install bpy --break-system-packages`.
Then tell J in 5 lines what's waiting on him and what you'd do first; ask short multiple-choice questions.

## The loop you run

1. Modellers finish a pass and write `docs/blender/review/specs/<pass>.json` on the working branch.
2. J renders on his PC (graphics card, minutes), one command from `C:\Users\Josh\Documents\LanternLive`:
   `& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python review-site\tools\lantern_review.py -- --all`
   It fetches specs and scripts from the working branch, skips decided/scrapped takes and empty first-person clips,
   rebuilds the site's "In the game" panel (`tools/gen_status.py`: current jar, what's in it, what isn't on the site),
   and pushes ONCE per run to `review-site` (one Vercel deploy). Stop early: `ni ...\review-site\STOP`.
3. J rates on his phone: KEEP / IMPROVE / DROP + notes; "Scrap pass".
4. You pull ratings (`pull_reviews.py`) and route them:
   - KEEP -> hand-off `docs/handoff/<date>-<topic>/README.md` (his words, exact numbers, poses; name the passes as
     "passes NNN and NNN" so the status panel can find them) + build order to the mc chat;
   - IMPROVE -> the modeller who owns that range (the note says what);
   - DROP / scrapped -> mark OLD in `docs/blender/DESIGNS.md`; set `superseded_by` in the spec.
5. Decisions J gives in chat -> one line in `DECISIONS.md` (newest first, his words).

## Retiring chats

Procedure: `docs/handoff/RETIRING-A-CHAT.md`. J pastes "Retire this chat..." into the old chat; it writes
`docs/handoff/retired/<date>-<range>.md` (open work, lessons for the design skill, gotchas). You then:
1. Merge its **Lessons** into `lantern-ring-design` and its **Gotchas** into the skill they belong to, by proposing
   the complete updated skill with `propose_skills` (read the current SKILL.md first; J saves the card). Rules that
   contradict existing ones: ask J which wins.
2. Hand its open work to the chat that owns the range, or list it for J.
3. Mark the note `FOLDED <date>` at its top; push.
When this coordinator chat itself gets long: write its own retirement note and update START-HERE's "where this chat
left off", so the next coordinator picks up from the repo.

## Deploy budget (Vercel free plan: about 100 deployments a day)

- Only the `review-site` branch deploys. Every other branch has a root `vercel.json` with
  `"git": {"deploymentEnabled": false}` (CI adds it to `builds` and `screenshots/*`). Keep it; never add it to
  `review-site`; copy it into any branch made from an older commit that lacks it.
- Never push to `review-site` yourself except to change the site code (each push is one deploy); media only comes from
  J's PC. Batch site-code changes into one push.

## Pass ranges

| Range | Area |
|---|---|
| 400-499 | movement and flight (coordinator) |
| 500-589 | combat |
| 590-599, 800-899 | rings, suits, first-person tools, weapons, mounts, gestures, hit effects |
| 600-699 | lanterns and charging |
| 700-799 | construct surfaces, particle walls, corps looks |
| 350-399 | texture library, corps metals, Red Lantern islands |
| 900-999 | construct tool designs |

## Commands

| What | Command |
|---|---|
| Ratings into the repo | `python3 tools/review_site/pull_reviews.py` |
| Status panel by hand (needs a clone of `review-site` with origin = site-10) | `python3 tools/gen_status.py <site dir> --fetch` |
| In-game "To Claude" reports | `gh api "repos/sparkygogo77-spec/site-10/issues?labels=claude-inbox"` (GraphQL blocked) |
| Latest jar | `git fetch origin "+refs/heads/builds:refs/remotes/origin/builds"; git show origin/builds:latest.json` |
| Game source | `git fetch origin "+refs/heads/main:refs/remotes/origin/main"` |

**Posting to the mc chat (built-in browser):** load the browser tools in one ToolSearch; `preview_start` the project URL;
click "Close" if it opened inside an old thread; `find` "question or start a task"; click, type, check the box text
with javascript, Return; `find` your first words to confirm. Never type over J's unsent draft (use "Steer this
thread..."). If you can't confirm, give J one line to paste.

## Building KEEPs into the game (the mc build chat)

- **Role.** A starter whose role line is left blank ("[... ___ / mc build chat]") is ambiguous: ask. "Work on my keeps" means the mc build chat: game code for his KEEPs, not Blender takes.
- **Already built?** Before building a KEEP, `git log origin/main | grep -i "pass NNN"` (commit subjects name the pass); many build-order lines are already in the jar.
- **Worktree.** Branch from `origin/main` in a worktree (`git worktree add ../mc origin/main -b claude/<topic>`); the Blender branch stays for handoff notes only.
- **Java.** 26.3 needs Java 25: unpack Temurin 25 to `/opt/jdk25` (`https://api.adoptium.net/v3/binary/latest/25/ga/linux/x64/jdk/hotspot/normal/eclipse`), then `JAVA_HOME=/opt/jdk25 ./gradlew build`; the jar must stay under 30 MB (2.1.1712 was 27 MB).
- **One screenshot test.** Temporarily set `src/gametest/resources/fabric.mod.json`'s `fabric-client-gametest` list to the one test class, run `runClientGameTest` under xvfb (CLAUDE.md), then restore the file before committing.
- **Test poses.** A held lantern only shows in first person if it is in view: the Red battery needs the main hand and looking up (-35 pitch); the Dark Lantern charge has `G3LanternTest`.
- **Blender poses without J's PC.** `uv venv -p 3.11` + `pip install bpy` (5.0.1) runs any `*.update.py` headless (exec with globals bpy, np, FOLDER; `LL_NO_RENDER=1`) to regenerate its `*_poses.json`. 602 needs `kl_assets/dark_lantern.glb` and `dark_lantern_glow.glb` (copy `docs/blender/models/dark_lantern_L1.glb` / `_L2.glb`); 844 needs `kl_assets/construct_*_green.bbmodel` from the mod's `bbmodel/`.
- **Every player-facing change** gets a What's New entry at the top of `src/main/resources/lanternring/whats_new.json` (insert lines in its one-entry-per-line tab format; never re-dump the whole file) and Ring Lab labels "Pass NNN · Label".
- **Pull requests.** Open with REST (`gh api repos/sparkygogo77-spec/site-10/pulls --input pr.json`); `gh pr create` fails because GraphQL is blocked.
- **Merging needs J's explicit OK** ("can you merge it"): then `gh api -X PUT repos/sparkygogo77-spec/site-10/pulls/N/merge -f merge_method=merge`. Never merge on your own; auto mode blocks it.
- **Main moves fast.** Other chats merge several PRs a day: rebase onto `origin/main` right before asking J to merge, and check `mergeable_state` (`dirty` = conflict). In `en_us.json` conflicts keep main's lines and add only your new keys; two chats' shader-patch edits can coexist (different `_s` map marks), then bump `VERSION`.
- **Is it in the jar?** CI publishes to the `builds` branch: `latest.json`'s `version` and `note` (the merge title) say what's in it. The `latest` release tag 404s.
- **Give J the jar.** `gh api -H "Accept: application/vnd.github.raw" "repos/sparkygogo77-spec/site-10/contents/lantern-ring-latest.jar?ref=builds" > lantern-ring-<version>.jar`, check `fabric.mod.json`'s version inside, SendUserFile; the web link is `https://github.com/sparkygogo77-spec/site-10/blob/builds/lantern-ring-latest.jar`.
- **Failed builds that never started** ("recent account payments have failed or your spending limit needs to be increased") are GitHub billing, not code: tell J to check Billing & plans.
- **After a shader-patch change** J restarts the game once so his "+ Lantern Ring" pack copy is remade.

## Minecraft 26.3 gotchas (beyond CLAUDE.md)

- `ModelPart.children` is private: find a part by path with `getChild` ("bone/body/head").
- `LivingEntity.knockback` now takes a DamageSource; a `hurtServer` hit already knocks back, so skip it.
- No `swinging` / `swingTime` fields: use `isSwinging()`, `getCurrentSwing().hand()` and `getSwingAnimation(partial)`.
- Items draw through `mc.getItemModelResolver().updateForTopItem(state, stack, ItemDisplayContext.NONE, level, player, 0)` and `state.submit(...)`; the quads are centred on the block (-0.5 to 0.5).
- A second model with the vanilla mob's bone names and pivots (e.g. `new WardenModel(root)`) is posed by the mob's own animation: use it for armour layers.
- Integrated PBR ignores a mod's `_s.png` maps in the hand and entity programs; `ShaderPackPatcher` reads them only when marked (blue 3: shine; blue 253: per-pixel material with metal and emission).
- Blender first-person rigs (x right, y ahead, z up) map to view space (x right, y up, -z ahead) with one fixed matrix; see `SwordSwing`.

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

## Running as the PC coordinator (J, 2026-10-19)

- "ALWAYS provide the link/chat name so i can instantly click over and see the pictures as a rule for these types of
  questions": every question about a pass, design, room, mod or model gives the clickable link (review-site pass page or
  `#report/<pass>`, Modrinth gallery, doc) or the chat as [title](#local_id), right before the menu. Menus are pathways:
  category first ("Rate a pass"), then the exact target ("v2.0104", "any pass").
- "use this instead of other chats, update it properly from the previous chat" (J, 2026-10-19): the **Site 10** project
  (https://claude.ai/code/project/chan_01YLUFj9KADvqrGT75FUzG27) replaces the old mc project for Lantern threads and
  skill-card posts. Post hand-overs there in one message with the full state (archived chats, open ratings, J's picks).
- Start with `docs/handoff/NEW-COORDINATOR-PROMPT.md`; follow `PC-CHAT-BRIEF.md` section 1 as the coordinator.
- "when things are done update and move them on the grid but always send the grid": every finished job ends with the
  grid (`tools/chat_grid.py` -> `show_widget`) and the menu (AskUserQuestion; widget buttons never reach the chat).
- Every menu pick gets a follow-up AskUserQuestion that steers it. Wrap up = close out / retire chats / new coordinator
  (brief sections 4, 4b, 4c). Side chats report with 🟡 QUESTION / 🔵 DONE / 🔴 PERMISSION first lines; route J's answers back
  in his words.
- "your responses need to be more condensed, give me a table regarding every chat every time": every reply = one row per
  chat with a dot (🟢 working, 🟡 question, 🔴 only J, 🔵 done), then AskUserQuestion "Get questions from which chat?".
- "give me a dont ask question as well every time": every question offers "Don't ask, use ★".
- "I need a closed out ticker": once a chat's note is pushed, it leaves the table for one "Closed: ..." line.
- "it needs to immediately delegate instead of it trying to take up 613 itself": coordinators never build; start a side
  chat for every build, render or fix the moment the work is clear.
- "I should always have a button or some command to do the simple things": mention the `/lantern-` commands in the menu.
- "NEVER MORE THAN 3 Subchats at a time ... retire and fold these chats skills in after no more than 3 or 4 passes each":
  at most 3 open sub-chats; rotate builders out after 3-4 passes (note, fold, archive, fresh chat); research chats retire
  once their doc is pushed.
- Gotchas: reports only reach the chat that started a session (retire an old coordinator's chats, start new ones
  yourself); start_session from a turn triggered by another chat's message becomes a card J must click; chats load
  `.claude\skills|agents|commands` only at start-up (restart with `/lantern-start`); archiving is blocked by keep-awake
  or a turn in progress (retry, or J archives from the sidebar); an archived chat can't receive SendMessage.

## Research chats (2026-10-19, docs/research/)

- "mods that mesh well with replacements for stuff in mine like maybe flight mechanics": research answers "can this
  replace or build on what we made", with a keep-ours/swap verdict per system, not only add-ons.
- "show me the extent of stormies spiders before creating ceiling walking": offer a test world before building a
  feature a mod may already do. Test instances live in `LanternLive\test-instances\`; J adds the launcher
  installation himself (editing launcher_profiles.json is blocked) and logs in.
- MC 26.3 availability: ask the Modrinth API (`/v2/project/<slug>/version?loaders=["fabric"]&game_versions=["26.3"]`,
  with a User-Agent), not web search. Check our class hierarchy and mixin targets before claiming a compat effect.
- Shared checkout: never stash other chats' work; commit only your own files, pull once the tree is clean.

## Working with J

- Short replies; full paths (`C:\Users\Josh\Documents\LanternLive\<area>\<file>.blend`), camera, frames.
- Spell out every abbreviation on first use. Ground recommendations in numbers. Keep status updates short.
- End with what's waiting on him and whether it's in the game yet.
- Ask, then build. 3+ labelled takes. Test once.
- In a scratch clone of `review-site`, start from a fresh clone: never let unrelated local edits ride along in a push.

## Review site tools on J's PC (2026-10-19)

- **Saves without a deploy.** Site pages save with `SiteFiles.save(...)` -> `POST /api/files` -> one commit on site-10's
  `site-data` branch (never deployed); renders push `media/` + `data/` to `live/` there. Docs: `tools/review_site/README.md`
  ("Saving without a deploy"). Saves answering 503/401 = the `GITHUB_TOKEN` expired: J makes a new one (Production + Preview).
- **Decisions.** `Menu: decisions` / `Menu: decided <id>: <pick>` (PC-CHAT-BRIEF 2a); cards from `gen_decisions.py`, answers
  via `record_decision.py pull`; `docs/decisions/chats.json` is hand-kept: add what a chat waits on, drop it when done.
- **3D catalogue.** A model gets a `.glb` only when J taps "Make 3D for this": `jar_to_glb.py --only <name>`, check
  `catalogue.html#<name>` at phone and desktop width, one push per batch. The converter handles the bbmodel quirks
  (box-UV-only elements, nested group rotations, hidden groups, numbered or missing textures).

## Review site and J's PC gotchas (2026-10-19)

- **Never edit `LanternLive\review-site` in place:** the renderer resets it from origin, runs `git add -A` and pushes. Work in
  a `git worktree` of it, rebase on `origin/review-site` right before the one push (renders move it hourly).
- **Git in site-10 (J's pick 2026-10-19, "Pull with autostash"):** chats share the `LanternLive\site-10` checkout: run
  `git pull --rebase --autostash` before starting and before committing, commit only your own files, never revert others'
  edits. Worktrees are only for review-site site code.
- **site-10 is private** (J, 2026-10-19): the site reads it through `GITHUB_TOKEN` (`/api/files`); public raw, jsDelivr or
  unauthenticated GitHub API tricks don't apply.
- **Two copies of the site tools:** site-10 `tools/review_site/` and review-site `tools/` (`lantern_review.py` in both) lag
  each other: diff before copying and check the commit only adds lines.
- **`sync_with_site()` runs `checkout -B review-site`:** in a worktree that moves the shared branch; dry-run on a worktree
  with its own branch and delete any `review-site` branch it makes.
- **Data files other chats add online** (decisions.json, jar.json, history.json): when republishing by hand,
  `git checkout origin/review-site -- <missing data files>` first. Never ship `data/site.json` built in a scratch worktree
  (fresh-clone media dates are wrong): let the PC render rebuild it.
- **`data/decisions.json` conflicts on rebase** whenever a render lands: take theirs, rerun `gen_decisions.py`.
- **`data/control.json` `catalogue` flags** are rebuilt by `gen_control.py` each render; between runs set a new model's flag
  by hand (never run gen_control from a worktree: it scans the parent folder for .blend files).
- **Refs:** `git fetch origin review-site` only sets FETCH_HEAD; use `git fetch origin review-site:refs/remotes/origin/review-site`.
  In the review-site clone `origin/dev` is `+refs/heads/claude/lantern-redesign-pass2:refs/remotes/origin/dev`, not a branch.
- **The site URL 307-redirects** to the review-site branch alias: check deploys with `curl -L` or the browser.
- **Deploys are Preview builds** of branch review-site: env vars need Preview, and "Redeploy" a review-site deployment
  (a `main` one is cancelled by the ignoreCommand).
- **Port 8765** is usually taken by another chat's server showing an old copy: check `netstat -ano | grep :8765`, use another port.
- **Built-in browser:** a new `#hash` on the same URL doesn't reload (add `?v=N`); clipboard can be refused, so pages fall back
  to `execCommand("copy")`, then a selected box.
- **A site push J approved in another chat** (relayed) is blocked by the safety check: it needs his yes in this chat.
- **Blender reads a relative movie path as black frames;** use absolute paths and set `scene.render.fps` to the clip's fps.
- **PC tools:** no Pillow, ffmpeg, node or gh by default (pure-Python PNG via zlib, or `pip install numpy pillow`; GitHub API
  via curl with a token). Windows Python can't open `/c/...` paths: cd and use relative paths. Run a .ps1 with
  `powershell -ExecutionPolicy Bypass -File ...`. Bash heredocs mangle backslashes and long JS: write the file with the
  Write tool and patch with a small script that asserts each anchor occurs once.
- **Parsing:** INBOX has `[status: WAITING]` and older `[WAITING]` / `[PICKED: ...]`; `whats_new.json` added ids match `^\+[\s{]*"id":`.
- **"It's not in the game" may be J's PC, not the code:** check the jar version in Lunar's mods folder
  (`.lunarclient\profiles\26\mods\fabric-26.3`, `fabric.mod.json` in the jar; only one Lantern Ring jar there, downloads
  pile up as `lantern-ring-latest (N).jar`) and his Ring Lab rows in `%APPDATA%\.minecraft\config\lanternring-lab.json`
  (`touched` rows never move to a new ★; the L3 swirl draws only on the Dark Lantern).
- **Jar on J's PC without gh:** `git -C site-10 cat-file blob origin/builds:lantern-ring-latest.jar > jar` through `cmd /c`.
- **"A version is missing":** search `Downloads` and `_to_delete` too; a stray .blend there is invisible to the site and renderer.