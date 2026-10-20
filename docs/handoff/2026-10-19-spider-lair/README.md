# Hand-off: the giant spider lair (the Dread Warren's ending)

For the mc chat. Design and every number: `docs/plans/trials/2026-10-19-spider-boss-sequence.md` (rounds 1-6) and
`docs/plans/trials/2026-10-19-spider-cave-size.md` (cave sizes). Everything below is a block-out J has picked from;
nothing is in the game yet. J asked for this brief on 2026-10-19 ("do all and one more").

## What it is

The Dread Warren's ending, replacing the Brood Heart room and the Brood Matron (J: "A, then C later ★"). Rare wild lairs
anywhere under the mountains come later (C).

1. **Cave 1, the run.** A natural-shaped cave about 160 × 100 and 30 high, its ceiling full of dripstone spikes. The
   yellow fear construct spider fights you here.
2. **The collapse.** At 30% health a 32-wide disc of webbed dirt in the middle of cave 1's floor crumbles from the
   outside in. You both drop down a hollow funnel (32 narrowing to 20 across) lined with spikes pointing in, then
   through the open middle of the lair, and land in a pool (water: no fall damage).
3. **The fight in the fall.** Halfway down the funnel the construct spider grabs you from below. Three attack clicks
   then one use (right click), fast, eject it: a ring blast throws it into the funnel spikes and it shatters.
4. **The lair.** The W1 cave J liked (about 230 × 160, 60 high), with columns, side chambers, 600+ hanging spikes and
   a 5-den burrow web round it. The real spider, R2 brute, waits there.

## J's picks

| What | Pick |
|---|---|
| Real spider | **R2 brute**, 36-block leg span, 400 health (first proposal), "Web-rock spikes" on every leg tip: a silk band, then stepped stone narrowing to a point. Stab about 12 damage and pins you in web (Slowness 3 s); a spike breaks if it hits one of your construct Walls. |
| Construct spider | Yellow fear, 20-block leg span, 200 health; C3 shards dropped (its shatter kept as the death); "[No preference]" between C1a / C1b / C2a, so **C1b dread armour** (stand-off plates, spiked ridge, leg guards) is in the block-out. |
| The fall | "Cave collapse ★", then "it should be straight over the larger one and the funnel should be a great distance ... water ... in the center", then "Both, by terrain". |
| Fall fight | "fight during the fall but you need to click 3 times then one right click rapidly to trigger the ejection animation"; tuning "Keep it ★". |
| Burrows | "bigger dens and denser spokes ... 5 is cool but with much more spokes for connectivity". |
| Hanging spikes | "driplets or even constructed tip ones that should be apart of the spiders arsenal, they will hang from the ceiling". |

## Build it in game

### 1. The layout generator (worldgen)

- Port the recipe in `tools/trials/spider_cave_wild.py` (`build()`) and `tools/trials/spider_sequence.py`
  (`layout_stack()`, `burrow_web()`, `add_spikes()`) to a feature or structure that runs from the world seed: J wants
  every lair generated fresh ("I always need it in a differently generated").
- **Heights by terrain** ("Both, by terrain"): where the surface above is about y 125+ use the long version (cave 1
  floor about y 60, 105-block fall); where it's about y 100-125 the short one (floor about y 35, 82-block fall). The
  lair floor sits at about y -45 in both; seal any lava or water around it (the test datapack turns them to tuff).
- Never under oceans, rivers or the deep dark.
- The only way in is a 3-wide crack at the surface that winds down to cave 1's roof (no other sign of the lair).
- **Burrow web:** 5 den rooms (about 30 × 24 × 14) round the lair in the rock between the caves; each den has 3
  burrows down to the lair's ring tunnel, 2 up to cave 1's, and links to every other den: 35 tunnels, 9 wide.
- **Spikes:** dripstone from both ceilings (lots of small, about 90 big ones 8-29 long); about a quarter end in a
  yellow hard-light tip. The test datapack uses yellow stained glass for those tips: the mod needs its own
  construct-spike block.

### 2. The hard-light spikes as a weapon

The spiders can shake hard-light tips loose: the tip breaks off and falls (a falling block entity, about 8 damage, a
little splash damage). Only hard-light tips drop; plain dripstone stays.

### 3. The collapse and the fall fight

- The disc: 4 rings of webbed dirt crumble from the outside in, about 0.5 s apart once the construct spider is at 30%;
  the last ring goes under you both.
- Grab: when you've fallen about half the funnel. While held you fall at the same speed, can't fly, and take 2 damage
  every 0.5 s.
- Input: 3 attack clicks, then 1 use, within 2 s of the grab, each press within 0.6 s of the last; a wrong order
  restarts the count while the window runs. Show LMB, LMB, LMB, RMB prompts.
- Success: the ejection (a ring blast), the construct spider is thrown into the funnel spikes and shatters into
  hard-light shards; no splash damage.
- Failure: it rides you into the pool (8 damage, it slams you), then fights on in the lair at 30% beside R2.

### 4. Spider movement

- **Ceiling and wall walking is still ON HOLD** (DECISIONS 2026-10-19: J watches the Stormie's Spiders test world
  first). The walk test below shows R2 climbing a column only because J asked to see legs on slopes and columns;
  don't build climbing code until J has picked the climbing approach.
- Legs plant on the blocks: each foot target is ray-cast onto the surface and a two-bone solve finds the knee
  (`Spider.leg()` in `tools/trials/spider_anim_tests.py`); tetrapod gait (half the legs swing while half stay planted).
- Burrows: R2 dives into a hole with its legs tucked, scuttles through the tunnel, bursts out of another hole in a spray
  of dirt (take A2).
- Strike: rears up, the other front leg lifts, the right front spike stabs (take A3).

## Models still to make

The Blender spiders are stand-ins built from boxes. Real models: voxel pixel art in Blockbench (greedy boxes, box UV,
about 2,500 boxes; `tools/pixel_rage_battery_bbmodel.py`), glow cubes inflated 0.02 px, yellow glow kept saturated
(emission at or under about 1.5). The Dread Warren's own Hunter and Weaver spiders are a separate hand-off
(`docs/handoff/2026-10-19-dread-warren-spiders/`).

## Files (J's PC, `C:\Users\Josh\Documents\LanternLive\`)

| What | Where |
|---|---|
| Stacked lair (long), animated fall frames 1-170 | `trials\spider_stack.blend`; videos `trials\renders_stack\10_fall_pov.mp4`, `11_fall_side.mp4` |
| Animation tests A1 walk, A2 burrow pop-up, A3 spike strike | `trials\spider_anims.blend`; videos `trials\renders_anim\` |
| Spider takes | `trials\spider_takes.blend` (R1-R3, C1-C3), `trials\spider_takes_r2.blend` (R2, C1a, C1b, C2a) |
| Test datapacks (not run in game yet) | `test-instances\stormies-spiders\lantern-spider-stack-datapack.zip` and `-stack-short-datapack.zip`: `/function lantern_seq:build` in a creative world, on a mountain (long) or hill (short) |
| Picture pages | https://claude.ai/artifact/Li4BpncsnWgGpg86XC4EBL (sequence), https://claude.ai/artifact/ALyPbB365wv42KA6qN25vn (cave sizes) |


## J's notes on the R2 animation tests (2026-10-19), still to do

J: "the legs should never collide, the bury animation should be a quick one instead of that one that isnt animated,
the strike is only okay making no contact if its using the yellow constructs and sending webs that way, otherwise i
want a contacting strike, and a more maybe organized or natural grid system for the tunnels all around".

1. **Legs never collide:** no leg segment may pass through another leg or the body, on any frame. Check it
   numerically per frame (as with the 842 shield-and-arm check) and adjust the gait / foot targets until it's zero.
2. **The burrow dive is quick and animated:** a fast dig-in (legs scrabbling, dirt flying), not the slow glide with
   legs frozen tucked (A2). The pop-up out of the far hole stays.
3. **The strike makes contact:** the real spider's spike has to hit you. A strike that stops short is only right for
   the yellow construct spider, and then it fires webs at you from range.
4. **Tunnels on a more organized or natural grid all around:** the burrow web should read as a planned network (or a
   natural one) round the whole lair, not scattered spokes.

J then asked to send everything to Lantern coordinator 3.

## Open

- Health and damage numbers are first proposals; J hasn't rated them.
- Nobody has walked the datapacks in game yet.
- Ceiling and wall climbing waits on the Stormie's Spiders decision.
