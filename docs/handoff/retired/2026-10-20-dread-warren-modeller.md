# Retired: Dread Warren modeller chat (PC, Trials), 2026-10-20

## Range / role

Blender modeller on J's PC for the Dread Warren trial look (area "Trials"), started by coordinator 3. Passes
v2.0106, v2.0107, v2.0108. Last pass number used: **v2.0108**.

## Open work

- **v2.0108, 12 IMPROVE with no notes** (3 new versions each = the next round, suggested v2.01NN):
  W2a3c broodling mane; W2d2a-c phantom wire (heavy, faint fill, dashed); W3a2c Matron gold-rimmed chitin; W3a3a
  Matron dimmed hourglass; W3c1a-c Lights out: the scream (sound rings, true dark, the brood answers); W3c3a and
  W3c3c the shell opens (heavy beam, close-up); W4ba funnel hollow, deep.
  Open: `C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r3.blend`, cameras "Cam <code> <name>", frames
  1-120. Script `docs/blender/blender_updates/v2.0108_dread_warren_r3.update.py` (options per take through `CUR`
  for spiders and `MOPT` for the Matron; `build_W4b(X, code, v)` takes a variant dict).
- **J re-rated v2.0106 later in coordinator 3's chat** (commits 656db3d1, cde99cea; after v2.0107/v2.0108 were built): W1a The Maw IMPROVE ("the entrances are too obvious or unappealing"), W1b, W1c and W3b IMPROVE, W1d DROP ("I dont like this system, I would prefer you only see the webs once youre in danger"), W3c DROP. New rule: webs stay hidden or near-invisible and only glow when the player is in danger; show calm vs danger as a before/after. So the next round should also try the caves again (W1a-c, W3b) under that rule. Its creature IMPROVEs (W2a-W3a) are superseded by the v2.0107/v2.0108 KEEPs. Before each rating question, put the take stills right above it: J: "I need the images here".
- **Unrated:** v2.0108 W2a1a, W2a1b, W2a2c; v2.0107 W3a1 (Matron, lantern cage). J answered "No preference".
- **Handed off** (game chat): `docs/handoff/2026-10-19-dread-warren-spiders/` (Hunter and Weaver from v2.0107,
  Broodlings and Phantom shells from v2.0108). Not in a jar yet.
- **Dropped, don't rebuild:** every cave scene of v2.0106 (Maw, Weave Gallery, Hatchery, four corps counters) and
  the Brood Heart arena; v2.0107 burrow warren, reignite, split phantom; v2.0108 all three crevices, funnel deep lips
  and sheet webs, four Matron versions, green core, two shard broodlings.
- **Still on hold:** ceiling walking, until J watches the Stormie's Spiders test world (DECISIONS 2026-10-19).
- **Site area:** specs say `"area": "Trials"`, but `review-site/tools/gen_site.py` AREAS has no "Trials", so the site
  files these passes under "Combat & powers". A review-site change, not for a modeller chat.

## Files

- `LanternLive\trials\dread_warren.blend` (v2.0106, every take rated): can go to `_to_delete\` once J is done.
- Delivery copies made only to fit SendUserFile: `trials\dread_warren_r2_*.blend` (5 files) and
  `trials\dread_warren_r3_*.blend` (10 files). The full pass files are `dread_warren_r2.blend` and `dread_warren_r3.blend`.
- Other `trials\` files (spider_cave*, spider_sequence*, renders*) belong to other chats; not mine.

## Lessons for the design skill

- Show every creature in several poses, all turning: J: "i want to see them in various positions to display as much
  as possible in these models" (v2.0107). For spiders: walking, on a wall, dropped on a thread, rearing, dead on its
  back (no ceiling walking while that is on hold).
- Caves have no columns; burrows and terrain should be complex and spider-made: J: "remove the columns from the big
  caves, try to make the burrows and terrain more complex and maybe spider favored" (v2.0107).
- Fear-construct spiders that J kept read as a black core first, with yellow light as accents (plates, edges, eyes);
  all-over yellow glow at small sizes was rated IMPROVE until dimmed (v2.0107 -> v2.0108).
- For big passes J rates on the site, not in chat questions: "RATED all of these on the site nearly" (v2.0107).
  Offer the site first, then pull_reviews.py.
- Say what a hand-off is in plain words when offering one: J asked "what is meant by game handoff" (v2.0107).

## Gotchas

- **SendUserFile cap (30 MB):** a voxel Matron row is 11-13 MB, so whole passes ran 64-108 MB, and saving with
  compression didn't shrink them. Split them per take with `tools/trials/split_blend_by_take.py`.
- **Git Bash heredocs halve backslashes** in Python string literals (`\U` became `\U`: unicode error; `\v` became
  a vertical tab, so a spec was written to the wrong path and overwrote v2.0106's, restored from git). Build Windows
  paths with `chr(92)`, or use the Edit tool.
- **Box helpers out of the grid:** a tunnel random walk leaving the voxel grid gave "negative dimensions" in
  `ellip`; guard `if np.any(hi <= lo): return`.
- **Blender 5 turntables:** `action.fcurves` is gone; spin with a driver, expression `frame*0.05236` (one turn per
  120 frames, no keyframes).
- **Cameras inside closed caves** see only stone: build caves as open-top dioramas or cut the front wall away.
- **The site's "re-rendered since rated"** flag showed on takes J rated after the render; looks like a clock or
  time-zone mismatch in the site, not a real re-render.
