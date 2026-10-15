# J's decisions log

Every chat J talks to appends here when he decides something in conversation (not on the review site; site ratings
are in `RATINGS.md`). Newest first. One line per decision: date, pass/area, his words in quotes, what it means.
Read this and `RATINGS.md` before starting any round.

## 2026-10-15: Blender chat C (passes 800–899)

### Rings and lanterns
- **807 lantern charge:** "L3 Core swirl wins this one" (KEEP; hand-off `docs/handoff/2026-10-15-keeps-charge-hits/`).
- **804 → 825 icon rings:** "ripple should cover the key, get rid of 12, make 13 extend the ripple to the black sides, no
  black on the ring, delete 14 and revise design of face on R19d, then give me 7 more rings". No black on rings.
- **825 icon rings:** "R19f 11b only not completely boring ring faces" (I1b and R19f kept; the rest dropped) → 832.
- **Ring placement:** the jar now places the ring on the fist's punching face, over the middle finger (RingModels
  `placement()`); Blender first-person rigs should match it (831 on).

### Beams
- **Naming:** "omega beams are the zig zag eye beams not this". The beam from the ring is the ring beam (B1 picked:
  "B1 wins this one"); the eye beams are separate (820 → 829).
- **819 ring beam:** "O4 looks better (different texture is necessary,) O2 might be good if its a real glow in game ...
  O3 sparks are good too ... find a way to apply my construct textures" → 830.
- **829 eye beam chain:** C1 is "the best looking"; "the lines shouldnt go around corners so predictably"; "we need
  better textures for the omega beams i dont think i saw them much in game" → 833.
- **Laser:** "we absolutely need a better laser than the one that shoots right now" → 834.
- **820 eye beams:** Z1 corner hunter; "the pattern should continue ... through each target to the last, if it hits a
  player it does not continue through them" → 829.

### Gestures, worn ring, first person
- **First-person view:** "i should see the arm relative to the crosshair at about 120 degree FOV"; crosshair in every
  first-person camera.
- **816 X1 cast:** knuckles down at rest, ring worn like a bracelet, the fist turns up 100° "slowly over the course of
  .4s very smoothly", not far out.
- **816 X4 put the ring on:** "looks good"; no light ring, "a wave of bright light out like 80 blocks" (third person);
  then "ring going on has to be smoother", no hand collision, no snap back, the left hand "should pull away quickly",
  "a light glowing effect that is perfect and optimized for my game".
- **816 X2 oath:** okay only as the ultimate build: look up, beam up 2–3 s, a ~150-block dome forming top first over
  10 s, lasting 2.5 minutes → 826. Then "the construct of the dome also builds behind the blocks a little too laggy" → 835.
- **818 worn ring:** W3 scrapped ("the arm never goes up like that" except while holding space in flight). **W4b rise
  at 135° is good**; turn the hand more, ring on the fist's top as in the jar, an angle that shows the ring while
  flying up. W2 light rays and smoke "look bad" → 831.

### Weapons, constructs, mounts
- **808 construct weapons:** scrapped; "there is also already a spear in the game we should just use that new one";
  bow and shield redone (823): "VERY in depth bow and arrow models, think modern day", "the shield is too small".
- **809 mounts:** "horse is the only flying construct i want right now"; a flying baby dragon and a ghast that fits the
  real model (824).
- **810 big constructs:** giant fist and cage bubble "not sure"; the game's bubble "isnt bad the physics and controls are
  just broken currently" (mc chat); catapult + ram → snap launcher (822); mech suit → designs, a second size, animations,
  for villagers or any mob (821).
- **815 hit effects:** "the outline flash is good the construct break is good" (F3, F1 KEEP; handed off).

### Suits
- **817:** "C4 C3 C2 are all good", "hex suits are good"; C1 "good but shoulders on c4 i think are better" (827).
- **817 → 827:** C8 no cape, not brick, new materials, a full helmet over head and eyes; C6 no shoulder shield, the
  gauntlet on both hands; C5 brick with C8's shoulders, nothing on the neck.
- **Animals:** "stretch the textures over some animals too, just the construct textures", more designs on a warden and
  a pig (828).

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
