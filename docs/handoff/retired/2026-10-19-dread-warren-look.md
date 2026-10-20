FOLDED 2026-10-19 by coordinator 3 (lessons -> lantern-ring-design "Trials"; gotchas -> lantern-blender-modeller). Note: the spider-lair hand-over (placement A) cuts the Matron, so the Matron items below wait on J.

# Retired: Dread Warren look, modeller chat (PC, Trials), 2026-10-19/20

J (coordinator 3's Chat controls): "Retire + replace"; the new chat does "Its open work". **Next free pass: v2.0109**
(area "Trials").

## Range / role

Blender modeller on J's PC for the Dread Warren trial look (area "Trials"), started by coordinator 3. Passes
v2.0106, v2.0107, v2.0108. Last pass number used: **v2.0108**.

## Open work

**Round 2 is parked: nothing of it is built.** The coordinator's request (build from J's later v2.0106 ratings, plus
4+ Matron designs) came after this chat had already built v2.0107 and v2.0108 and J had said "Hand off, then retire".
No v2.0109 script exists. Everything below is for the fresh chat.

### Round 2 brief (from J's later v2.0106 ratings, coordinator 3, commits 656db3d1 + cde99cea)

Rule for every take: **J: "I would prefer you only see the webs once youre in danger"**. Webs stay hidden or
near-invisible and glow only when the player is in danger. Show it as a calm/danger before-and-after wherever webs appear.

| v2.0106 take | Rating | Note (J's words, or the reason he accepted) |
|---|---|---|
| W1a The Maw | IMPROVE | "the entrances are too obvious or unappealing": hide or disguise the entrance, make it appealing, not a plain hole |
| W1b Weave Gallery | IMPROVE | plain |
| W1c Hatchery | IMPROVE | the egg sacs glow nicely, but the room is too dark to read its shape |
| W1d Four corps counters | DROP | "I dont like this system, I would prefer you only see the webs once youre in danger" |
| W2a Broodlings | IMPROVE | they blur into one glowing blob; give them separate small bodies (v2.0108 KEEPs W2a1c/W2a3a/W2a3b already do this) |
| W2b Hunter | IMPROVE | plain (v2.0107 W2b1-3 are KEEP and handed off) |
| W2c Weaver | IMPROVE | the body is hard to see from this angle (v2.0107 W2c1-3 are KEEP and handed off) |
| W2d Dread Phantom | IMPROVE | mostly particles; give it a body inside the cloud (v2.0108 W2d1a-c are KEEP and handed off) |
| W3a The Matron | IMPROVE | reads as a round ball; needs a head, legs and the glass abdomen showing |
| W3b Brood Heart arena | IMPROVE | pillars and web roof good; the Brood Heart is small in frame |
| W3c Lights out | DROP | (v2.0108 still has 5 Lights out IMPROVEs; ask J whether those stay) |

**Big spider boss:** J: "I also need more spider designs for the big spider boss". At least 4 labelled Matron takes
with different silhouettes, leg styles and abdomen shapes, each with a readable head, legs and the glass abdomen
showing; webs only in danger.

**Rating:** before each rating question, put the take stills right above it (SendUserFile the jpgs). J: "I need the
images here".

**Pictures to start from:** v2.0106 `C:\Users\Josh\Documents\LanternLive\trials\dread_warren.blend` (cameras "Cam W1a Maw",
"Cam W1b Weave Gallery", "Cam W1c Hatchery", "Cam W3a Matron", "Cam W3b Brood Heart", frame 60); review
https://lantern-review-j.vercel.app/#report/v2.0106 . Script `docs/blender/blender_updates/v2.0106_dread_warren.update.py`.

### Earlier rounds (built, rated)

- **v2.0108, 12 IMPROVE with no notes** (3 new versions each = the next round, suggested v2.01NN):
  W2a3c broodling mane; W2d2a-c phantom wire (heavy, faint fill, dashed); W3a2c Matron gold-rimmed chitin; W3a3a
  Matron dimmed hourglass; W3c1a-c Lights out: the scream (sound rings, true dark, the brood answers); W3c3a and
  W3c3c the shell opens (heavy beam, close-up); W4ba funnel hollow, deep.
  Open: `C:\Users\Josh\Documents\LanternLive\trials\dread_warren_r3.blend`, cameras "Cam <code> <name>", frames
  1-120. Script `docs/blender/blender_updates/v2.0108_dread_warren_r3.update.py` (options per take through `CUR`
  for spiders and `MOPT` for the Matron; `build_W4b(X, code, v)` takes a variant dict).
- **Unrated:** v2.0108 W2a1a, W2a1b, W2a2c; v2.0107 W3a1 (Matron, lantern cage). J answered "No preference".
- **Handed off** (game chat): `docs/handoff/2026-10-19-dread-warren-spiders/` (Hunter and Weaver from v2.0107,
  Broodlings and Phantom shells from v2.0108). Not in a jar yet.
- **Dropped, don't rebuild:** v2.0106 four corps counters and Lights out (J's later rating; his first rating here
  also dropped the Maw, Gallery, Hatchery and arena, but the later one brings those back as IMPROVE, above); v2.0107 burrow warren, reignite, split phantom; v2.0108 all three crevices, funnel deep lips
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

- Webs are hidden until danger: J: "I would prefer you only see the webs once youre in danger" (v2.0106 W1d).
- Cave entrances must be disguised and appealing, never a plain hole: J: "the entrances are too obvious or unappealing" (v2.0106 W1a).
- Put the stills right above every rating question: J: "I need the images here" (coordinator 3, v2.0106).

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
- **Voxel mesher:** `grid_mesh(name, G, labels, s, trans=...)` draws a face only where the neighbour is empty or a
  *different see-through* label, so glass shows what is inside it with no hidden faces. Size one numpy int16 label grid
  per model; capsule/ellip/octa helpers fill it.
- **Pixel-snapped textures:** object coordinates snapped to 1/16 (Vector Math SNAP) before Noise make procedural veins
  read as pixel art. Keep the vein emission low (0.2-0.45) at block scale or the cave looks like marble.
- **Cameras inside closed caves** see only stone: build caves as open-top dioramas or cut the front wall away.
- **The site's "re-rendered since rated"** flag showed on takes J rated after the render; looks like a clock or
  time-zone mismatch in the site, not a real re-render.
