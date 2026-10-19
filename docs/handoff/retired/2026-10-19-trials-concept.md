# Retired: trials concept chat (2026-10-19)

FOLDED 2026-10-19 (lessons in lantern-ring-design "Trials and challenges").

## Range / role

- **Role:** a concept and design chat for trials and challenges. It used no pass numbers, built no Blender files and
  wrote no code.
- **Output:** `docs/plans/trials/2026-10-19-trials-concept.md`, with `docs/plans/trials/cave_map.png` (made by
  `tools/trials_cave_map.py`, Pillow).
- **What the doc covers:**
  - the Dread Warren fear spider cave in full;
  - six round-2 trial pitches;
  - how trials fit the mod;
  - the build plan and risks.

## Open work

- **J's picks (all in DECISIONS.md):**
  - Any corps can enter the Warren.
  - The next trial is the **Fallen Titan**.
  - Climbing is "Watch it first": the research chat sets up a Stormie's Spiders test world.
- **Waiting on:**
  - the Stormie's Spiders test world (research chat), and then J's Stage A/B climbing choice;
  - the mods-physics survey (`docs/research/2026-10-19-mods-physics.md`). It wasn't in the repo when this chat ran.
    Fold its picks into Part 4 of the concept doc.
- **Not started:** the Blender passes in Part 4 of the doc. The coordinator numbers them v2.01xx when J wants them:
  - spider bodies (legs as separate segments for IK);
  - the motion reference;
  - the Matron;
  - the cave kit;
  - a greybox mood fly-through;
  - the Will Flare;
  - the Fallen Titan.
- **No promises to J are outstanding.**

## Files

- There are no files on J's PC. Everything is in the repo.

## Lessons for the design skill

- **Trial pitches need a set piece and a ring twist, not a meter.** J: "Need better ideas" on six trials that were
  each a meter, three zones and a boss. Round 2 (accepted, ★ Fallen Titan picked) gave each trial:
  - a one-sentence hook;
  - one memorable set-piece moment;
  - a change to what the ring does;
  - why it's memorable.
- **Ask to see a mod before designing around it.** J: "show me the extent of stormies spiders before creating ceiling
  walking". When an existing mod might already do a hard system, J wants to watch it in a test world before the
  approach is chosen.

## Gotchas

- **`git pull` in site-10 fails** with "Cannot rebase onto multiple branches" because of the extra fetch refspec. Use
  `git pull --rebase origin claude/lantern-redesign-pass2`.
- **Other chats leave unstaged edits** (for example in `DECISIONS.md`), so `pull --rebase` refuses to run, and stash
  is off limits. Fix:
  - `git fetch`, then check `git rev-list --left-right --count HEAD...FETCH_HEAD`. If the remote isn't ahead, push
    straight.
  - To commit only your own lines in a shared file: build HEAD's version plus your insert, then
    `git hash-object -w` + `git update-index --cacheinfo`. Make the same insert in the working copy.
- **On J's PC the Python has Pillow but no matplotlib.** `python -I` hides the user site-packages, so Pillow
  disappears with it. Run your own scripts without `-I`.
