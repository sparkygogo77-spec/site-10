---
name: "lantern-ring-design"
description: "J's design philosophy and Blender workflow for Lantern Ring visuals: lanterns, charge light, construct textures, rings, constructs. Use for any Lantern Ring model, texture or animation work."
---

# Lantern Ring design: depth and philosophy

Lantern Ring is a Minecraft 26.3 Fabric mod: repo sparkygogo77-spec/site-10, Blender branch claude/lantern-redesign-pass2.
J judges everything by eye in Blender and in game, with Lunar Client and Complementary shaders.
This skill records what he has asked for and approved, so new work starts from it instead of from scratch.

## How to work with J

- **Show, don't describe.** Build every idea in Blender through Lantern Live, and render stills to check it yourself first.
- **Always give several options.** Use 3+ takes labelled (A1, A2, B1...), side by side, with a one-line note each.
- **Keep iterating until he says move on.**
  - He reads takes as "keep / improve / drop".
  - Carry what he praises into the next round word for word, and change only what he criticised.
- **Keep replies short.** Lead with what changed and where to look (full file path, camera, frames). Contact sheets are for your own checks and the review folder, not for J.
- **Always name the .blend file to open.** J often can't find the latest file.
- **Roles.**
  - You are the Blender / model / texture maker.
  - Game logic goes to the coordinator chat (the "mc" project) as a written brief file listing his picks, with exact tool commands.
  - A lead Blender chat may split the work between chats by LanternLive pass-number ranges (for example 100-199 for one chat, 200+ for the lead). Stay in your range, and don't take on another chat's queue.
- **Copyright.**
  - Never copy the Green Lantern emblem or other trademarked art, corps logos or character names (e.g. "Atrocitus"), even when J's reference images show them.
  - Use J's own concepts and original marks. The Red corps mark is three claw slashes in a ring.
  - Offer to raise a mark J draws himself: Image Editor > New 32x32 > Paint mode > save as `LanternLive\logo.png`.

## What J taught the Blender chats (2026-10-14)

- **Review format.**
  - No contact-sheet grids for J ("too difficult for me to see"). Give the file path, the camera and the frames.
  - Picture sheets are fine on Decisions cards and in-chat take grids; still no big contact sheet as a reply (J's pick 2026-10-19, "Yes, on cards").
  - One small file per decision (`LanternLive\picks\`), never one huge file.
  - Plain numbered camera names, e.g. "27 Dash strike R3a - 1st person".
  - A first-person and a third-person camera for every player animation.
  - End every reply with what is still waiting on him, and whether it is in the game yet.
- **Test once.** One check render per pass, then deliver; the visual review is his.
- **Feel.**
  - Fast and snappy: no wind-ups, mobs launched on contact, instant craters, the construct lingering briefly after.
  - Exception: swords are heavy and slow with a short pre-swing charge (see Tools and weapons).
  - Animations never take control from the player: short owned windows (3–6 ticks), steering always honoured.
  - Landings stop close: under 1 block of carry and under 0.3 s.
- **Body.**
  - The ring arm leads (by about 0.08 s in flight) and points where the player moves; the free hand is still or
    stabilising.
  - Weapons cut with the edge leading. A thrust draws back, then drives forward. Hammers are solid 3D constructs.
- **Variety.** Unpredictable, erratic shapes beat regular ones; 20–25 takes with no repeats when he asks for many.
- **Beams and glow.** Solid, readable lines in game (faint particles were rejected), darker cores, saturated, steady
  glow.
- **Ring Lab.**
  - His saved choices must never be overwritten by a new jar.
  - His in-game "To Claude" reports arrive as GitHub issues labelled `claude-inbox`; read them with
    `gh api "repos/sparkygogo77-spec/site-10/issues?labels=claude-inbox"`.
- **Files.** His LanternLive folder is sorted into `lanterns\`, `movement\`, `combat\`, `constructs\`,
  `red\` and `suit\`; superseded files go to `_to_delete\`. Shared rules and gotchas:
  `docs/handoff/2026-10-14-blender-chat-briefs-2.md`.

## Pages, cards and replies for J (2026-10-18/19)

- **Pictures to tap, not text to read:** "buttons dont lead anywhere just from looking at it i can tell ima have to read everything" (Control tab). Every action is a picture or one big button; anything a chat must do is copied as a ready prompt ("Copied: paste into your PC chat (Ctrl+V, Enter)").
- **Every open choice is a card:** what it is in plain words, why it matters (what it unblocks), a picture, options with a ★: "better descriptions and visuals" (decision manager).
- **His colours everywhere,** on cards and the first line of every turn-ending reply: 🟡 QUESTION = his answer, 🔴 PERMISSION = only he can do it (sign-in, token, approval, merge), 🔵 DONE. A 🔴 card stays open after he answers until the job is actually done.
- **Let him pick what's worth building:** "let me choose which one to start gib files seperately from the take variations because some arent worth buildign the file for yet" (catalogue .glb). Never bulk-generate per-model files; give him a click per model, separate from take variations.
- **Version and age on every pass:** "I need the age or I need a chronological v.# update for every website pass": the site shows `v# · age`.
- **Show what changed in his game,** newest first, with how to see it: "i need a better version on the site aswell for the jar showcase of recent updates" (Jar view).

## Trials and challenges (2026-10-19, docs/plans/trials/)

- "Need better ideas": a trial pitch is a one-sentence hook, one set-piece moment, a change to what the ring does, and
  why it's memorable; never just a meter, three zones and a boss. J picked the Fallen Titan after the Dread Warren.
- "show me the extent of stormies spiders before creating ceiling walking": when a mod might already do a hard system,
  show J it running in a test world before choosing the approach.

- **Dread Warren look (v2.0106-v2.0108):** webs stay hidden until danger, then glow ("I would prefer you only see the
  webs once youre in danger", W1d). Entrances are disguised and appealing, never a plain hole ("the entrances are too
  obvious or unappealing", W1a). Big caves have no columns; burrows and terrain are complex and spider-made ("remove the
  columns from the big caves, try to make the burrows and terrain more complex and maybe spider favored", v2.0107).
  Fear-construct spiders read as a black core first with yellow light only as accents (plates, edges, eyes); all-over
  yellow glow at small sizes failed until dimmed (v2.0107 -> v2.0108).
- **Show creatures in several poses, all turning:** "i want to see them in various positions to display as much as
  possible in these models" (v2.0107): walking, on a wall, dropped on a thread, rearing, dead on its back.
- **Big passes are rated on the site** ("RATED all of these on the site nearly", v2.0107): offer the site first, then
  pull ratings; small rounds get stills right above each in-chat question ("I need the images here").
- **Explain hand-offs in plain words** when offering one (J: "what is meant by game handoff", v2.0107).

## Movement and flight (approved, passes 400-407)

- **Take-offs are tiny and never hold you.** "maybe the take off should be a very small animation"; "allow me to fly
  once im flying". The standing take-off settles low: "Just 2.2" blocks of hover, never above the snap height (407).
- **Landings carry almost nothing.** L4: "0.3 carry blocks", under 0.3 s (405).
- **Moving counts too.** Descend and the double-tap landing must work while flying forward, not only standing: "when im
  moving forward i cant descend like when im standing still" (405).
- **Judge arms on the body the game uses at that speed.** Slow flight is upright (about 20 degree lean), the sprint is
  a flat glide; an arm that looks "above the head" on the glide may be right on the upright body (404 -> 406).
- **Free arm:** "angled about where the player's arm is"; A2 slightly forward is the dart's free arm, A1 the option (403).
- **First person only when the move has one:** "i shouldnt have 1st person renders for a third person animation".
- **Reviews:** an IMPROVE with no note means make 3 new variations of that take, labelled, and he picks (DECISIONS 2026-10-15; 839-862). He may answer "Drop it".

## Tools, weapons, mounts and enemies (passes 838-863)

- **Swords are heavy and slow** with a short pre-swing charge; the mob reacts on contact. 852 S2c1 is the speed floor: "no faster than this" (844, 852).
- **Pickaxes mine at the crosshair:** "should only mine in the crosshair" / "has to mine on center"; the tip strikes the block at screen centre (852 P1c2/P1c3).
- **Mining isn't instant:** blocks crack, then drop physical chunks with light particles (844 P1a note -> 853).
- **Axe hold:** default tipped 45 degrees forward toward the crosshair (844 A1c, picked from a picture).
- **Construct armour on mobs** "protrudes over them not on their skin": plates stand off the body; shells were rejected (828 -> 838, R4b KEEP).
- **Constructs form along their own action:** "in whatever way the catapult will launch it, not from me", not streamed from the ring (822 -> 857).
- **Mechs can carry construct weapons and have villager pilots:** "Give this bot the hammer and make it for the villagers" (843 MAa).
- **Shields:** "The shield in third person collides with arms": check arm/shield intersection numerically on every frame (842 H2b -> 850).

## Light in game (860)

- Block light like the beams' (lights the vicinity, fades) is right.
- Screen-space glow, rays on the arm and panes near the eye are not: "these light rays from blender are not it". Pass 860 G1-G6 replace the light rays.
- **First person never sees the ring's front.** The eye looks at the face's two back sides (measured in 864); ring glow
  must read on those sides. Front-only ideas were invisible until rebuilt (864 G1b, G1c).
- **Emission above about 1.5 on the glow green clips to pale mint** under Standard + bloom; 864 scales 860's strengths
  by 0.6 to stay saturated.

## Lantern Live (Blender link)

- **How updates run.** The add-on watches `C:\Users\Josh\Documents\LanternLive` and runs each new `NN_name.update.py` (globals: bpy, np, FOLDER).
  - Status goes to `live_status.txt`; renders go to `renders/`.
  - Test every update headless first: `/opt/bl/venv/bin/python` has bpy 5.0, `LL_NO_RENDER=1`, Cycles at 16-24 samples. Headless EEVEE renders can time out.
- **The watcher often stops.**
  - Check the last line of `live_status.txt`. If it is old, don't wait on the watcher.
  - Build the .blend headless here instead, with image paths relative (`//folder/...`) or packed.
  - Copy the .blend and its assets into LanternLive with device_commit_files, and tell J the file name.
- **Watching is a per-scene property.**
  - After `save_as_mainfile` into a new file, set `scene.lantern_live_watch = True` in a timer.
  - If the panel says Watching but nothing applies, reset `_state['timer']=False` and toggle watch.
- **Blender 5.2 video output.** Set `image_settings.media_type = "VIDEO"` before choosing FFMPEG, or the enum errors.
- **Listing LanternLive.** A recursive `device_list_dir` on the whole folder passes 2,000 entries and is truncated:
  list the area folders one by one.
- **PowerShell on J's PC.** A new window starts in the wrong folder: `cd C:\Users\Josh\Documents\LanternLive` first
  (or use the double-click `Render Lantern Review.cmd` there).
- **Delivery size.** SendUserFile caps at 30 MB. Unpack textures from big blends, keep the paths relative and copy the textures alongside.
- **Library files must be normal files.** A file written with `bpy.data.libraries.write` opens as an empty scene. Ship a real scene with a camera and bloom, and use `asset_mark()` for assets.
- **File switches.**
  - A switch can add `.001` to object names, so find objects by name prefix.
  - The add-on reloads `lantern_model.npz` after a switch; hide any stray non-prefixed meshes.
- **Drivers.**
  - Keep driver expressions "simple" (`min`, `max`, `pow`, ternary; no `**`), so they run without auto-run scripts.
  - Drive animations from keyframed scene properties (`scene["charge"]`, `["flight"]`, `["dissolve"]`) through SINGLE_PROP driver variables.
- **Animation.** Drive spin from an accumulated keyframed property that only grows, never from charge, or the swirl runs backwards when the charge falls.
- **Glow.** Use a compositor Bloom fed from a Render Layers node, with Standard view transform for saturated greens. AgX washes bright green to white.
- **Cameras.**
  - Give each option row its own camera.
  - Keep rows far apart, or facing away from each other. Translucent constructs nearer the camera hide the row behind.
- **Shaders can't be matched exactly.** Complementary can't run in Blender, so a Blender preview is only close. To calibrate, ask J for an in-game screenshot and match bloom and colour to it. The final check is always in game.

## The lantern charge (approved direction: G3)

- **Timing.** The ring flies in and physically seats in the port. The charge starts the instant it seats, and the light spreads out from the port in the lantern's own greens.
  - 12 s to full.
  - 2 s overcharge climax.
  - A slow 7.5 s fade with a let-go flash pulse; "the colour coming undone" is loved.
- **Centre.** A spinning ball in the middle, flaring with noise, spinning one way only.
  - Strands stay in the middle band.
  - It grows in brightness, not in reach.
  - Some yellow is in the green flow, and the hottest whites of the flare burn yellow.
  - At the climax it is a very bright saturated green, never white.
- **Ends.** The glass fades to near-black emerald at the very top and bottom; the blaze never reaches the ends.
- **Cracks.**
  - Gold-yellow lightning cracks fill from the centre outwards, reaching the edges a little before full.
  - They read as dark detailed lines with a dim gold glow, plus one flash as the light runs through.
  - They never get bright, they fade toward the ends like the glass, and the green swallows them late.
- **Stitches.** Very frequent dashes in the darkest green, down the middle of the front and down each side.
- **Gold frame (R4).**
  - Polished gold reflecting the green, with a glow only on the faces turned toward the glass: middle band, top and bottom collars, not the handle.
  - In game it has no emissive gold; use a LabPBR specular map instead.
- **Helix.** The pinched glass gets the slightest helix twist, about 3 degrees.
- **Ring light.** The light flowing into the ring is subtle and smooth; the lantern's brightness is the star.
- **In game it must match the render's light** (2026-10-16): "the blender model i chose had more lighting animation". The G3 renders bloom round the lantern; the game now adds a halo and stays lit while overcharged (Ring Lab > Lantern > Dark Lantern light, LIVE default), waiting on his check.
- **Always-on light.** The lantern gives off a low light at all times, and its glass is never fully dark (about 10-15% idle glow).
- **Reuse the flare.** Use the G3 flare for every corps' light source, recoloured: a noise ball spinning one way, with a breathing strength.

## Construct textures (approved direction)

- **Darker, smoother, slower.**
  - "They don't have to be so animated" and "never static, but not fast".
  - Frametime 4-5, loops of 5-10 s.
  - Smoothstep blends between five colour stops.
  - About 20-25% darker than first drafts, but still rich greens.
- **Motion.** Gliding in one direction beats churning.
- **Variety.** Every design must be built a different way. Recolouring one pattern is not variety. Hue shifts come out pink and were rejected; paint the pattern's own tones with a real palette instead.
- **When he does ask for a recolour** (BRJR, "Test with red"), Blender's Hue/Saturation node works in linear colour: reproduce it in linear, or crimson comes out brick orange (`tools/br1_red_strip.py`).
- **Translucency.**
  - Constructs stay see-through, at most 99% opaque; the blue hex Dome is the reference for how see-through.
  - Render only the outer shell, with no seams between blocks.
  - Keep texel density fixed in world space on scaled constructs.
- **His green picks.**
  - BR1 bricks (glowing mortar, bevelled lips, glint) in jade, emerald, lime and neon, and a blue for the Blue corps.
  - H1 neon hex.
  - D1 neon sparks.
  - W1 weave (emerald, neon). W1 neon's far look is the ideal for every face.
  - R2 K1 dark-jade fragments as the default construct look and the bull/army skin.
  - Pass 701 KEEPs: BRE and BRN bricks as construct looks, BRJR (BR1 jade in red) as a Red look, T9 barrier; BRD neon bricks BRDa carved, BRDb brushed alloy, BRDc dark gunmetal (703) not built yet.
  - Round 6: X5 quantum ripple (emerald and neon), X3 power aura emerald, X1 cosmic dust emerald.
  - The dissolve fill for constructs disappearing. The dissolve when a charge starts is loved.
- **Every corps gets its own construct look, lantern and ring.**
  - Red: R1 magma, R2 bloodfire.
  - Yellow: Y1 scales, Y2 lightning, Y3 dread; also G2 negative and N3 scales.
  - Violet: V1 crystal, V3 silk.
  - Blue: B1-B3 to test.
  - Orange: not picked yet.
- **Texture library.** R2 K1 is in `docs/texture_library/green/r2k1/` (its image is ~90% transparent: use a flat opacity); Yellow Y1-Y3 are in `docs/texture_library/yellow/y1..y3/` (from `tools/construct_designs7.py`).
- **Particle constructs.**
  - Pixels in the corps' shades live on any mesh's surface (a Blender particle system on the shape) over a faint shell.
  - For block clusters, delete the faces between blocks so only the outside shell remains.
- **Barrier surfaces.**
  - Soft, low-contrast marks moving in several directions; hard lines are rejected.
  - In game: T1 bands ×3, T2 warped bands, T3 radial bands, T5 radial glow, T6 light clouds, T7 soft veins, T9 bands + veins (`tools/construct_designs9.py`).
  - Waiting on J: particle walls W1 curtain, W2 lattice, W3 swarm, W4 rising, W5 shards (`tools/blender_edits/particle_walls.py`).
- **Covers.** A cover that disintegrates pixel by pixel into construct particles beats one that slides away.
- **Dislikes.** White lines on jade; dark, jade-blending lines are preferred.
- **Tests.** Test every strip: loop jump, tile seams against block edges, and motion > 0. Report as numbers. Use whole-number frequencies along the tile so strips stay seamless.
- **Tools.** The generators are `tools/construct_designs*.py` (rounds 1-9), `tools/construct_jade_game.py` and `tools/construct_texture_options.py`.

## Trials, caves and lairs (spider lair chat, 2026-10-19)

- **Caves are much bigger than first guesses.** "all too small, caves in the newest updates are way bigger than this":
  arenas for big creatures start at 200+ blocks across; tie them to real heights against biome surfaces.
- **Every generated place is new each time.** "I always need it in a differently generated (if it has to be limited
  multiple we can pick from a few designs of them)": build generators from the seed, not fixed layouts.
- **Hidden, deep, one way in.** "naturally no sign of the hollow dome ... plenty deep with dense overhead": a crack at
  the surface, a winding shaft, thick rock overhead.
- **A boss sequence is a set-piece chain** (J's design): construct form, a trap that destroys the floor, a fall, then
  the real creature. Falls end in water ("water in some way always in the center").
- **Fights need inputs, not just health bars.** "click 3 times then one right click rapidly to trigger the ejection".
- **Legs never collide; contact is real.** Strikes hit, except ranged construct attacks (the yellow construct's webs).
- **Construct glow at or under emission 1.5** or the yellow washes to white too (not only the green).
- **Concept rounds: J judges renders, not drawings,** and hands over his own creature ideas when pitches miss
  ("lets get a grizzly bear ..."): after a miss, ask for his direction instead of pitching blind again.

- **Entrances are ordinary world features** (Warren look 2): "as common as a certain rivine is mountain is, it should
  be random though", never a tell-tale sign; reuse what the game generates and attach ours ("natural mineshafts that
  have the additional portion of ours attached to it", "perfect utilization of existing generations").
- **Show the place itself, eye height, real-looking:** no CALM/DANGER pair pictures ("the DANGER below variations are
  worthless"), no doll's-house cutaways or islands ("these were all scrappable").
- **Webs never across the walkway** ("THE WEBBING ON THE INSIDE SHOULDNTBE HERE"); **the boss's eyes are the brightest
  thing in the dark** ("Cant see boss spiders eyes as well"); **less yellow** ("pure yellow i cant see the detail"):
  quiet stone, cool rim light on black-core constructs.

- **(spider lair notes r8-10)** **"Legs touching" means legs through the floor.** "When i meant legs touching i meant legs colliding through the
  floor" (round 9). Every creature take reports three measured numbers: legs through the floor/ceiling, legs touching
  each other or the body, and (strikes) spike-to-player distance on the hit frame. Burn them into the video label.
- **Strikes land unless it's a ranged construct attack.** "the strike is only okay making no contact if its using the
  yellow constructs and sending webs that way" (round 8): contact is measured as 0.0 blocks on every hit.
- **Movesets, not single strikes.** "all four as seperate moves but massively depending on distance and orientation"
  (round 9): give a chart of where the player is (distance, on the ground, flying, on a wall or ceiling, in a tunnel)
  against the move, and "more motion and points on each" (several contact points, body steps and turns).
- **Ground motion in real biology.** "then research spider leg movement" (round 9): research the real animal first
  and cite it (`docs/findings/2026-10-19-spider-leg-movement.md`: steps 4-2-3-1 per side, sides alternate, feet down
  about 70%, bob 0.05 body lengths twice a stride, roll and yaw about 6 degrees, front legs feel ahead).
- **Burrows join the network.** "make sure the burrows are accessing part of the pipeline instead of making short new
  ones" (round 9): digs break into existing tunnels; tunnels "all around" on a planned grid, T1 orb web picked.
- **Digs are quick but readable.** "the bury animation should be a quick one" (round 7) then "slower ... a digging arm
  animation ... smoothly settle into the blocks on all sides and ceilings" (round 9): about 1-2 s, digging leg strokes,
  feet settling onto tunnel walls and ceiling.
- **Size the spaces to the creature.** A 36-block-span spider needs tunnels and pits about 30 wide; at 9-24 wide its
  legs fold through its own body (round 10).
- **Ceiling capture.** "shoot slow projectile spreading web that captures me on the ceiling and it zips up and
  patrols upside down with the same leg rules all the time" (round 9): this lifted the climbing hold for R2's
  animations (not yet for game code).

- **(creatures refine, 2026-10-20) Creatures are mob-sized and animated:** "proper animations on a much smaller mob
  than these models" (v2.0112): bear 5 tall, enderman about 7, sharks 6-22 blocks. Polar bear: "skinner", "longer arms
  almost like a sloth with its claws", fur from a few hand-picked colours by patch and height plus a guard-hair fringe.
- **Lantern endermen:** no wings, crown or face; they carry the lantern and use it; acquired constructs float near them
  ("lava blocks, water casting", "faithful to minecraft frame time"); teleports animated with variations. The Orange
  Lantern charge is a vulnerability pause: "hugging the lantern extremely close ... in a prayer".
- **When J calls a model great, keep it and vary it** ("make smaller variations ... different types of shark").
- **Stills in the chat before rating:** "I dont see where this is" when they were only on a page.

- **Bosses move while they attack:** "we will need more extending or movement attacks from the spider to make it not
  just stationary" (spider lair round 10): lunges, charges and repositioning, not strikes from a standing spot.

## Models

- **Format.** Voxel pixel art at 1/4 or 1/2 model px, exported to Blockbench with greedy boxes and box UV (see `tools/pixel_rage_battery_bbmodel.py`).
  - Keep a model near 3 MB and about 2,500 boxes: merge kinds that share a colour, and fill hidden interior voxels.
- **Depth.** J likes depth: glassy ribs, darker undersides, gold lightning cracks, emissive cores.
- **Glow cubes.**
  - A glow cube in exactly the same place as its solid twin z-fights ("bleeds and flashes"). Inflate glow cubes 0.02 px.
  - Parts flush on glass also z-fight; inflate them 0.01 px.
- **Lit both sides.** Lit emblems and windows show on both sides, as on the blue lantern.
- **Lanterns are voxel pixel art, never smooth meshes** (604/605 all dropped): "the depth of the dark lantern is just the level of complexity and pixelated design, but of course i was expecting a more polished version of the gold on them" (606).
  - Build on the Dark Lantern's 0.25 px grid with its glass (glassy ribs, crazed middle, gold lightning, dark stitches); `tools/pixel_lanterns6.py` -> `7` -> `8` -> `9`.
  - Polished gold = shaded as metal: bright top lips, a mid tone that follows the light, one specular column, deep undersides, engraved bands (dots, zig-zags, rules).
  - "make these more complex" (607): layered frames, fins, studs, drips, glowing bowls, a sculpted port, see-through glass round a core carrying the G3 flare.
  - Keeper: 607 D1b molten vault ("this one is a keeper, i need more variation"); 608 leads D1b2 hex, D1b3 tall, D1b5 caged, D1b6 squat -> 609. Drip colour: "be creative, change it up".
  - Budget: curved glass on a 1/2 px grid, gold at 1/4 px, keeps a lantern near 1,000-2,400 boxes.
- **No see-through models.** "at a certain angle the lantern is transparent (every single model)": blended transparency writes no depth; use dithered (608).
- **Red Lantern.** A gold frame, with the claw mark on a lens brought out of its housing (`tools/fix_lantern_models.py`).
- **Red battery (final).**
  - The B2 build with the C1 arched handle, in smooth glossy crimson sRGB (188, 30, 47). J rejected tiled gem patterns: he wants smooth colour with diamond-like reflectivity.
  - But not everywhere (2026-10-16, in game): "it looks very weird with 100% of it being this way"; "lantern needs to be fully redesigned"; mix finishes by part. Takes M1 ruby + gold, M2 obsidian + ruby lens, M3 lacquer + black steel + gold neck, M4 matte + polished lens wait on his rating (Ring Lab > Corps > Red Lantern material).
  - At rest, blood falls as long thin pixel streaks, and wind lifts them while flying.
  - The charge lasts 8 s: the cover disintegrates, the hole is pure light, and pixel lightning plays round the port.
  - Hand-off: `docs/handoff/2026-10-13-red-battery-final/`.
- **Rings.** The square emblem ring (his concept) is the default; crown and signet takes exist.
- **Enemies.** Rougher enemy gear: Yellow fear-consumed mobs get Yellow armour A1-A4 and swords/axes/picks/bows (863, waiting on his pick).

## KEEPs built into the game (jar 2.1.1712) and still to build

- **Warden construct (838 R4b, default).** The real warden under W1 weave plates standing 1.5 px off the skin, forming feet first in 1 s.
- **Sword (844 S3b).** Stepping wide sweep pair, extruding from the ring fist behind a scan plate; the backswing hits again. The game's hand view is 70 degrees against Blender's 120, so wide sweeps leave the screen sooner.
- **Still to build:** 852 P1b3 pickaxe (strike, lever back, rip a chunk out); 816 X2 Oath ("fix the arm going into the body in third person"), X4 put the ring on, X4b with a ground wave; 602 set-down D1 default, D2 option (what triggers it in game: ask J).
- **Ring beams (840).** T1b hex collars + trailing sparks and T1c hex screw + impact fountain are Beam looks.

## Shaders (Complementary in Lunar)

- Reflections and glow come from the pack's material IDs.
- `ShaderPackIds.lookLike` gives a mod block a vanilla block's ID; for example, the battery uses DIAMOND_BLOCK. Skip glowing states, so they keep their light IDs.
- BbModel and entity parts can't get an ID that way; they need a LabPBR `_s.png` specular map.

## Delivering

- **Send the .blend, don't just name it:** "the threads gave me the blend file to open, chats like this should do the
  same" (SendUserFile after every build).
- **J's PC builds the .blend.** Chats push scripts and specs; `lantern_review.py` builds and saves each pass's `.blend`
  to its area folder when it renders (rebuilds when the script is newer). The PC chat (Claude Code in LanternLive,
  `docs/handoff/PC-CHAT-BRIEF.md`) builds, check-renders on the GPU and sends files: "I want you to do the work".
- **Jars.** The jar must stay under 30 MB. Quantize big PNG strips (FASTOCTREE 256), run oxipng, offer 32 px versions, and report MB for each hand-off.
- **Hand-off.** Commit to the branch and push. Write briefs to `docs/handoff/<date>-<topic>/README.md` (findings to `docs/findings/`).
- **Uploads to the coordinator chat.**
  - Inject the file into `input[type=file]` with a DataTransfer, type the message in the "Prompt" box and press Return.
  - Then check that the message really appears on the page: the project URL can redirect into a finished thread, where messages vanish.
  - If you can't confirm it, give J a one-line message to paste, and say the branch folder is the record.
- **Git.** Add the branch's remote-tracking refspec to `remote.origin.fetch`, so the stop hook stops reporting false unpushed commits.
- **Retiring a chat.** When J says "Retire this chat", follow `docs/handoff/RETIRING-A-CHAT.md`: a note in
  `docs/handoff/retired/` with open work, stray files, lessons (his words + pass) and gotchas; the coordinator folds the
  lessons into this skill.