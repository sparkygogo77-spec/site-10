# Briefs for three more Blender chats (from the Blender designer chat, passes 400–499, 2026-10-14)

These are for **new Claude desktop chats** (Cowork-style, like the Blender designer chat: a cloud workspace linked to
J's computer, with the built-in browser), not for mc project threads. Paste one whole block as the first message of a
fresh desktop chat. It is self-contained: the chat attaches the repo itself, then reads this file.

### Starter for Chat C (combat, passes 500–599)

```
You're my Blender designer for my Lantern Ring Minecraft mod, working like my other Blender designer chats.
Setup, in this order:
1. Attach GitHub repo sparkygogo77-spec/site-10 with push access, and clone only branch claude/lantern-redesign-pass2
   (git clone --depth 1 --branch claude/lantern-redesign-pass2 ..., give it a 10-minute timeout).
2. Read docs/handoff/2026-10-14-blender-chat-briefs-2.md (the shared rules and the "Chat C" section) and
   docs/handoff/2026-10-14-blender-chat-brief.md. Load the lantern-ring-design skill. Read docs/blender/DESIGNS.md.
3. pip install bpy --break-system-packages.
4. Ask me to approve folder access, then request C:\Users\Josh\Documents\LanternLive. Also attach GitHub repo sparkygogo77-spec/lantern-blender with push access (sorted .blend files).
Your passes: 500-599. Your area: combat (P1-P6, K1-K5, R1-R5 are waiting on my picks).
Build headless here, deliver .blend files to my LanternLive folder, push review folders to the branch, and tell the mc
project chat (https://claude.ai/code/project/chan_01PxyDp7CugmGwF5sLv1ceR4) through the built-in browser. Only ask for
Blender access on my computer if I say "req access" or want to watch.
Start by asking me short multiple-choice questions about what to do first.
```

### Starter for Chat D (lanterns, charging, suit, passes 600–699)

Same block, with these lines changed:

```
2. ... the "Chat D" section ...
Your passes: 600-699. Your area: lanterns, charging and the suit (C1-C3 charging, H1-H3 hanging charge, suit round 3 are
waiting on my picks).
```

### Starter for Chat E (construct surfaces and corps looks, passes 700–799)

Same block, with these lines changed:

```
2. ... the "Chat E" section ...
Your passes: 700-799. Your area: construct surfaces, particle walls W1-W5 and corps looks (Orange not picked, Blue
B1-B3 to test).
```

## Who owns what (pass numbers)

| Chat | Passes | Owns |
|---|---|---|
| Super jump chat | under 100, 300–349 | super jump, smoke and light |
| Battery chat | 100–199 | red battery (done) |
| Lead Blender chat | 200–299 | splits work, sprint and ground flight |
| Chat B (textures, Red) | 350–399 | texture library, corps metals, Red Lantern islands |
| Blender designer chat | 400–499 | power landing (400, handed off), take-off and flight start (402+), flight air and landings |
| **Chat C** | **500–599** | combat |
| **Chat D** | **600–699** | lanterns, charging, suit |
| **Chat E** | **700–799** | construct surfaces, particle walls, corps looks |

Stay in your range and don't take on another chat's queue. If J asks you for something in another chat's area, do it
in your own range and say so in the INBOX entry.

## Shared rules (what worked in passes 400–401)

### Setup, once per session

1. Attach the repo (`add_repo`, push access), then clone just the branch with a 10-minute timeout:
   `git clone --depth 1 --branch claude/lantern-redesign-pass2 https://github.com/sparkygogo77-spec/site-10`.
   Add the refspec: `git config --add remote.origin.fetch "+refs/heads/claude/lantern-redesign-pass2:refs/remotes/origin/claude/lantern-redesign-pass2"`.
2. Install Blender: `pip install bpy --break-system-packages` (Blender 5.2 as a Python module).
3. Keep a working copy of LanternLive in your scratchpad (`$SCRATCH/LL/`, with `renders/`).
4. **J's folder:** ask J in chat to approve folder access, *then* call `device_request_folder_access` for
   `C:\Users\Josh\Documents\LanternLive`. A prompt nobody answers times out, and then you can only send files with
   `SendUserFile`.
5. **Blender access, only if J says "req access" or wants to watch:**
   - `computer_resolve_access` with `["Blender 5.2", "c:\\program files\\blender foundation\\blender 5.2\\blender.exe"]`.
     Both entries are needed: the launcher and the running `blender.exe` are separate apps.
   - Then `computer_request_access` with both.
   - Headless builds don't need it, and in 400–401 it was never used past setup.
   - Call `computer_release_lock` when you're done.

### Building a pass

- **Script:** `docs/blender/blender_updates/NNN_name.update.py` (globals `bpy`, `np`, `FOLDER`).
- **Rig:** copy lines 37–215 of `228_ground_flight.update.py`. They hold the knee rig, `solve`, `set_pose`, `cam`,
  `mixp` and the materials. Concatenate head + rig + body into the script.
- **Construct material, bloom and per-object animated properties:** copy from `400_power_slide.update.py`
  (`construct_nodes`, `fx_mat`, `obj_attr`, `key_prop`, `pixel_burst`, `pulse`, and the "PS Glow" compositor).
  - Animate per object with `o["fade"]` / `o["cx"]` keyframes, read in the shader by an OBJECT Attribute node. You
    don't need one material per object.
- **Follow cameras:** compute the camera from the mover's frame-1 position, then
  `c.parent = mover; c.matrix_parent_inverse = Matrix.Translation(start).inverted()`. Parenting with `matrix_world`
  kept leaves the camera offset by the mover's frame-1 travel; this bit pass 400.
- **Build and check:**
  `FRAME=.. SAMPLES=8-12 python3 tools/blender_pipeline/build_pass.py UPDATE.py $SCRATCH/LL "Cam A,Cam B"`.
  For contact sheets, run `render_frames.py` for 4–6 cameras in parallel, each in its own copy of LL. Look at the
  renders and fix what's wrong before J sees it; keep checks minimal.
- **Pack:** `pack_blend.py IN.blend /mnt/user-data/outputs/NAME.blend "Scene" "Cam X"`. Deliver to LanternLive with
  `device_commit_files`, or with `SendUserFile` if there's no folder access. Tell J the file and the camera to start on.

### Review, hand-off and git

- **Review:** `docs/blender/review/NNN_name/` (README, `sheet.png` quantized to 256 colours, poses JSON, under 5 MB),
  plus an entry at the top of `docs/blender/review/INBOX.md`.
- **Hand-off when J picks:** `docs/handoff/<date>-<topic>/README.md` with J's quotes and exact numbers, plus `poses/`
  and `assets/`. Mark the INBOX entry HANDED OFF and update `DESIGNS.md`.
- **Git:** commit, `git pull --rebase`, push. INBOX conflicts are common because every chat adds to the top. Keep both
  entries, newest first.

### Every finish: Blender folders, the blend repo, and tidying (J: "give me blender folders ... every finish, while pushing those folders to some repo and sorting and deleting redundant ones")

1. **Deliver to J's area folder.** Pack the `.blend` with `pack_blend.py`, then `device_commit_files` it to
   `C:\Users\Josh\Documents\LanternLive\<area>\<name>.blend`.
   - Areas: `lanterns`, `movement` (`movement\super_jump`), `combat`, `constructs`, `red`, `suit`.
   - A file over 30 MB once packed (texture-strip rounds) instead keeps its textures in a folder beside it, with
     relative paths. Videos always go in `<name>_media\`.
2. **Push to the blend repo.** Commit the same file at `sparkygogo77-spec/lantern-blender`, under `<area>/<name>.blend`
   (`add_repo` with push access first). Never commit `.blend1` files or anything over 95 MB.
3. **Tidy up when a design is superseded.**
   - `git rm` the old one in lantern-blender; history keeps it.
   - On J's computer, move it to `LanternLive\_to_delete\superseded\`. Never delete: the device tools can't, and J
     empties that folder himself.
   - Moving needs a script run in J's Blender Python Console (with computer access), e.g.
     `exec(open(r"C:\Users\Josh\Documents\LanternLive\sort_lantern_live.py").read())`. Copy the pattern: it
     writes `_to_delete\MOVED.txt` and an `undo_moves.py`.
   - Only move what DESIGNS.md marks OLD, or what J says to drop.
4. **Keep the root clean.** Leave in LanternLive's root only what Lantern Live and the scripts need:
   - `lantern_live.blend`, `lantern_live_link.py`, `*.update.py` (the watcher only reads the root);
   - `kl_assets`, `texture_library`, `hope_tex`, `metal_tex`, `red_tex`, `tool_tex`, `models_glb`, `ref`, `renders`;
   - `*.npz` model caches.
5. Name the area path in your message to J, e.g. "open `LanternLive\movement\takeoff_small.blend`, Cam S1".

### Notifying the mc project chat (built-in browser; this worked every time)

1. Load the built-in browser tools in one ToolSearch call:
   `ToolSearch {query: "mcp__remote-devices__Claude_Browser__", max_results: 64}`.
2. Open the chat: `preview_start` with `https://claude.ai/code/project/chan_01PxyDp7CugmGwF5sLv1ceR4`. Note the `tabId`.
3. Find the box: `find` "question or start a task" gives the box's ref.
4. Send, with one `browser_batch`:
   - `left_click` the ref;
   - `type` the message;
   - `key` Return.
5. Confirm: `find` the first words of your message. A "You said: …" heading means it posted. If it's missing, give J a
   one-line message to paste.
6. What to send: pass number, title, review folder, "review only" or "build from docs/handoff/... (J picked)", and the
   open questions. Notify only for real work.

### Working with J

- **Ask, then build:** short AskUserQuestion rounds, then build straight away. Always show 3 or more labelled takes.
- **Fixes mid-build:** he often sends a fix mid-build (a screenshot). Finish the step you're on, then fix it in the same
  turn.
- **KEEP / IMPROVE / DROP:** carry praise forward word for word, and change only what he criticised.
- **Replies:** keep status short. Spell out abbreviations on first use, name paths explicitly, and give one camera and a
  frame range to look at.
- **His rules (skill):**
  - every take opens on an over-the-shoulder camera;
  - knees, and the neck bends at most 57°;
  - the ring is on the right hand;
  - glow is saturated, never washed to white;
  - constructs are see-through (at most 99% opaque);
  - no copyrighted marks or names;
  - jar budget under 30 MB.

## Chat C: combat (500–599)

- **Queue (WAITING in `DESIGNS.md`):**

  | Round | Takes | File | Pass |
  |---|---|---|---|
  | Combat poses | P1–P6 (punch, blast, shield, beam, wall, slam) | `combat_poses.blend` | 221 |
  | Combos | K1–K5 | `combat_round2.blend` | 222 |
  | Round 3 | R1–R5 (grab-throw, hammer, dash afterimages, parry, flurry) | `combat_round3.blend` | 226 |

- **Start:** ask J to pick from each round (or say what's wrong), then refine round 4 from his picks.
- **Copy from:**
  - 221, 222 and 226 for the poses;
  - 223–225 for the omega-beam routing (SENT; E1–E4 are Ring Lab options);
  - 400 for construct pixels and dissolves.
- **Links:** combat interacts with the landing slide (400). Slam-landing variants should reuse the D0 crater rules in
  `docs/handoff/2026-10-14-power-landing/`.

## Chat D: lanterns, charging, suit (600–699)

- **Queue:**

  | Round | Takes | File | Pass |
  |---|---|---|---|
  | Charging at the lantern | C1 oath kneel, C2 raised, C3 both knees | `lantern_charge.blend` | 219 |
  | Hanging charge | H1 press, H2 punch, H3 steadied | `hanging_charge.blend` | 220 |
  | Lantern suit round 3 | 5×5 shell × accent, eye band, forms feet first, ring flare | `lantern_suit3.blend` | 215 |

- **Rules:** carry the G3 charge rules from the skill exactly:
  - 12 s to full;
  - 2 s overcharge;
  - 7.5 s fade;
  - spin one way;
  - gold cracks dim;
  - never white.
- **Copy from:**
  - 213 for the Dark Lantern import and the charge light (`kl_assets/dark_lantern*.glb`, staged from J's folder or from
    `docs/blender/models/`);
  - 219 and 220 for the poses.
- The Dark Lantern is the physics test model (hanging pendulum).

## Chat E: construct surfaces and corps looks (700–799)

- **Queue:**
  - Particle walls W1 curtain, W2 lattice, W3 swarm, W4 rising, W5 shards (`tools/blender_edits/particle_walls.py`);
    waiting on J.
  - Orange corps construct look (not picked yet).
  - Blue B1–B3 to test in game.
  - X3D1 glass aura is SENT (`docs/handoff/2026-10-14-x3d1-glass-aura.md`).
- **Rules (skill, construct textures):**
  - darker, smoother, slower: frametime 4–5, loops of 5–10 s;
  - every design built a different way (no recolours);
  - test every strip for loop jumps, tile seams and motion, and report the numbers;
  - quantize the PNG strips to stay under the 30 MB jar budget.
- **Coordinate with Chat B (350–399):** they own the texture library and the corps metals. Use their library; don't
  fork it.
