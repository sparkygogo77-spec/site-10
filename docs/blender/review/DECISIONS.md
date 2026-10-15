# J's decisions log

Every chat J talks to appends here when he decides something in conversation (not on the review site; site ratings
are in `RATINGS.md`). Newest first. One line per decision: date, pass/area, his words in quotes, what it means.
Read this and `RATINGS.md` before starting any round.

## 2026-10-14/15: Blender chat for combat, lanterns and constructs (passes 500–799, 519–521, 601–602)

### Catalogue and first person
- **519 catalogue:** "some third person animations dont have 1st person and vice versa, i need them all in a blender
  file" -> "All picked so far". Cameras renamed: "I need the cameras named for each properly" (`NN <name> - 3rd person`
  / `- 1st person`).
- **520 first person:** wanted for all four groups (flurries, slams, take-off and double jump, sprint and flight),
  "Show me both" styles (vanilla and bigger). Waiting on his pick.

### Combat
- **521 grab and throw:** construct hand, throws "where you look" (G1–G3 waiting). From 503: "grab-throw later".
- **518 primed slam:** "if im flying fast and i hold shift and fly into the ground it should be a primed slam ... crater
  happen instantly ... left click and rebuild the blocks"; crouch on a super-jump fall = the larger primed slam; "shift
  while flying should also make me go hyper speed"; "crouch should be the hyper speed activation from flying".
- **505 dash strike:** "R3a is better but the animation should maybe be way faster"; "R3c ... the end animation of the
  hand coming up is unnecessary". Speed (6/4/3-tick dash) still open.
- **503:** R4b absorb "is good"; hammer "should swing from the side if hitting a wall but over head most of the time"
  (R2a + R2b handed off).
- **517 omega beams final:** E2 wild, "damage on contact when the line makes another angle", K1 snap strike, U3 "1.6x
  speed, snap", W2 bubble sleeve (handed off).
- **507/509 flurry:** F2 jab-cross-spinning backfist; "i need these flurrys while flying" (in game).
- **508/510 slams:** "locked .7s"; mobs "sent away as soon as i make contact"; S3 M3, big and medium as two tiers.

### Lanterns
- **602 set-down:** "Kneel and place" (D1–D3 waiting).
- **L1c / set-down in game:** "model when set down is huge"; the L1c problem is "Lantern too big": the Dark Lantern
  stands 16 px (one block) with the handle.
- **601:** "much shorter charge animation maybe 6 seconds" (C6a–C6c waiting). "hip carry charge style still held in third
  person" (game bug, mc chat).

## 2026-10-14/15: Blender designer chat (passes 400–499) and coordinator

### Process (applies to every chat)
- Review happens on the site, https://lantern-review-j.vercel.app: "build a site i can access from my phone and review
  the models and images myself". KEEP / IMPROVE / DROP + notes; "Scrap pass" for whole passes.
- Renders run on J's PC (graphics card), not in the cloud: "we'll need the pipeline to render on my pc". Optimise:
  skip empty first-person clips, half rate for long clips, never re-render decided takes ("do 1 2 3 4").
- First person only where the animation has one: "i shouldnt have 1st person renders for a third person animation".
- Chats talk through GitHub (the working branch), never by pushing to `review-site`: "the most optimal way to
  communicate through github or any way it wont cost deployments".
- Older rounds replaced by newer passes are off the site: "Cut the older rounds".
- New chats get the briefs: coordinator `docs/handoff/2026-10-14-coordinator-brief.md`, modellers
  `docs/handoff/2026-10-15-blender-subchat-brief.md`.

### Movement and flight
- **405 landing:** "land much closer than a few blocks from where i started ... should be faster too". Site: **L4 KEEP
  with 0.3 blocks of carry**; L5, L6, L2 DROP. Bug to fix in game: "when im moving forward i cant descend like when im
  standing still to stop flying and land".
- **404 arm lead:** "arm should be animated in the directions a player could move with the arm leading the body by
  like .08s". Site: **D1 KEEP, D3 KEEP** (bank as an option), D2 DROP. J asked whether the arm "above the head" is
  right: it's the flat sprint glide; 406 shows the same rule on the upright slow-flight body (waiting).
- **403 take-off:** "the snap to hover is great, the spring may be better on the way up but it should slow down no
  higher than snap goes, make it faster for both"; "Running dart seems to be the most accurate"; the free arm "should
  be angled about where the player's arm is". Site: **S2a IMPROVE ("Maybe settles at 2.2")**, R3A3 IMPROVE (no note
  yet). In-game picks: S2b, A2.
- **403 R1** "is backwards in sequence? its a landing?": reversed, it works as a double-tap soft landing.
- **401/402:** "maybe the take off should be a very small animation": standing puff to 3+ blocks with a little shake;
  running = a super-fast arc, flat at 5 blocks. Animations must never drag: "allow me to fly once im flying".
- **400 power slide:** "A3 dissolve ... make the dissolve the 25 28 threshold, B2 for plough" (Ring Lab option),
  plus D0. Handed off.

### Game build
- "build it all, fix up ring lab too": everything picked in one jar (bundle, PR #314 → 2.1.647).
- Ring Lab must keep his settings: "I need the next jar to consider this and for this to save for me"
  (`docs/handoff/2026-10-14-j-ring-lab-settings/`). His Send-to-Claude notes went missing.

### Still open
- 403–405 site picks have not been sent to the mc chat as a build order yet.
- R3A3: ask J what's wrong. 406: waiting on his rating.
