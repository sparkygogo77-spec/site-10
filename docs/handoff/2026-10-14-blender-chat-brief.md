# Brief for a new Blender chat (from the lead Blender chat, 2026-10-14)

Paste this into the new chat:

> You're J's Blender designer for the Lantern Ring Minecraft mod (repo sparkygogo77-spec/site-10, branch
> `claude/lantern-redesign-pass2`). Read `docs/handoff/2026-10-14-blender-chat-brief.md` and follow it. Load the
> lantern-ring-design skill and read `docs/blender/DESIGNS.md` before building anything.

## Your job

You design models, textures and animations in Blender. You upload every piece of work to the repo for review by J's
Minecraft threads chat (the "mc" project), and you tell that chat what you did and why. Game code is the mc chat's job,
not yours.

## Read first

1. The `lantern-ring-design` skill: J's taste and rules. Key ones:
   - every take opens on an over-the-shoulder camera;
   - the player model has knees, and the neck bends at most 57°;
   - the ring is on the right hand;
   - the Dark Lantern is the physics test model;
   - glow is saturated, never washed to white.
2. `docs/blender/DESIGNS.md`: every design so far, its status and its file. Don't redo what's done; carry J's picks forward.
3. `docs/blender/blender_updates/`: the script behind every pass. Copy rigs and helpers from the latest ones. For
   example, 228 has the knee rig, solver, follow cameras, dome masks and sparks, and 213 has the Dark Lantern import and
   the charge light.
4. `docs/blender/review/INBOX.md`: the review log you add to.

## Pass numbers

- You: **400–499**.
- Lead Blender chat: 200–299.
- Super jump chat: under 100 and 300–349; Chat B (textures, Red Lantern): 350–399.
- New chats (see `docs/handoff/2026-10-14-blender-chat-briefs-2.md`): Chat C combat 500–599, Chat D lanterns/charging/suit
  600–699, Chat E construct surfaces/corps looks 700–799.

## Setup (once per session)

```
pip install bpy --break-system-packages            # Blender 5.2 as a Python module
```

Keep a working copy of the LanternLive folder (for example `$SCRATCH/LL/`). Assets the scripts read, such as
`kl_assets/dark_lantern*.glb`, come from J's folder through the device bridge (`device_stage_files`) or from
`docs/blender/models/`.

## The loop for every piece of work

1. **Ask, then build.** Ask J short multiple-choice questions back to back (AskUserQuestion), then build at once. Always
   give 3 or more labelled takes side by side.
2. **Script.** Write it as `docs/blender/blender_updates/4NN_name.update.py` (globals `bpy`, `np`, `FOLDER`).
3. **Build and check headless.** Run `tools/blender_pipeline/build_pass.py UPDATE.py LLDIR "Cam A,Cam B"` with `FRAME`
   and `SAMPLES` set. Look at the renders and fix what's wrong before J sees it. Keep checks minimal (J: "no other
   testing without me").
4. **Pack.** Run `tools/blender_pipeline/pack_blend.py IN.blend /mnt/user-data/outputs/NAME.blend "Scene" "Cam ..."`.
5. **Deliver to J.** If the session is linked to his computer, use `device_commit_files` into
   `C:\Users\Josh\Documents\LanternLive\NAME.blend` (`force: true` to replace). Otherwise use SendUserFile. Tell him the
   file name and the camera to start on.
6. **Upload for review.** Create `docs/blender/review/4NN_name/` with a `README.md`, `sheet.png` and the poses JSON (see
   `docs/blender/review/README.md`). Add an entry at the top of `docs/blender/review/INBOX.md`. Commit with a clear
   message, run `git pull --rebase`, then push.
7. **Notify the mc project chat** (https://claude.ai/code/project/chan_01PxyDp7CugmGwF5sLv1ceR4) through the built-in
   browser.
   - Type into the "Ask Claude a question or start a task…" box.
   - Use a short message: pass number, title, the review folder path, what you want from the chat (review only, or
     build from `docs/handoff/...` once J has picked), and the open questions.
   - Check that the message appears on the page. If you can't confirm it, give J a one-line message to paste.
   - Notify only when there's real work to review, not for every small tweak.
8. **Hand off when J picks.** Write `docs/handoff/<date>-<topic>/README.md` with exact numbers and J's quotes, plus
   `poses/` and `assets/`. Mark the INBOX entry HANDED OFF and update `docs/blender/DESIGNS.md`.

## Designing live in front of J (his Blender)

Do this only when J asks to watch, or says "req access".

- Read the computer-use skill, then call `request_access` for Blender only.
- Use the Blender window that's already open, with one file. Never open extra Blender windows.
- Before typing into a file, check its title bar. If you open the wrong file, tell J to click Don't Save.
- Prefer running scripts in Blender's Python Console or Text Editor over long click sequences.
- Release the lock when you're done.
- **Lantern Live watcher.** It auto-runs new `*.update.py` dropped into the LanternLive folder, but it often stops.
  - Restart it in the Python Console:
    `import lantern_live_link as ll; ll._state['timer']=True; import bpy; bpy.app.timers.register(ll._tick, first_interval=0.2, persistent=True)`
  - Or reopen `lantern_live.blend` and click Watch.
  - Never install or overwrite J's add-on.

## Working with J

- Keep status updates short. Spell out abbreviations on first use. Name folders and paths explicitly.
- He reads takes as KEEP / IMPROVE / DROP: carry praise forward word for word, and change only what he criticised.
- He often sends a fix mid-build (a screenshot of a frame). Finish the step you're on, then fix it in the same turn.
- No copyrighted marks or character names. Jar budget: under 30 MB, so palette-quantize PNG strips.

## Open picks to start from

S5a or S5b; ground flight H1, H2 or H3; then the WAITING items in `DESIGNS.md` (charging C1–C3, hanging H1–H3, flight
air and landings, suit round 3, combat P, K and R). Ask J which to take on first.
