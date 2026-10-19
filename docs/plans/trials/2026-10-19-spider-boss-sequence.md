# Giant spider boss sequence: three parts (draft, 2026-10-19)

J, after the round 4 caves (`2026-10-19-spider-cave-size.md`): "I think W1 is not bad, but i think there should be a
sequence started thats parted in 3s that is at first big lantern construct spider, then when that retreats it runs
into a kind of web funnel trap where its a room small enough for you and the spider once you enter the room and start
fighting it triggers a destructive kind of webbed dirt disintegrating in the ground when that one dies or really at 30%
HP it falls into a net of cobweb like new animated webs (new animated spider model and animations should be soon) and
then you are taken to the BIG real spider wearing a construct thing armor on some of its arms as weapons or maybe
spiked web rock points on its hands for its strikes?"

Numbers below are first proposals (health in hit points, 2 = one heart; the player has 20). Nothing is built yet.

## Layout at real heights

Side by side, not stacked, so the lair keeps its full height:

| Part | Space | Size | Floor to roof |
|---|---|---|---|
| Entrance | crack and winding shaft from the surface | 3-5 wide | surface down to the cave roof |
| 1. The run | wild cave (round 3 recipe), burrows round the edge | about 150 × 100 | y -20 to 25 |
| Escape burrow | one burrow climbs from cave 1 to the trap | 11 wide | rises about 40 |
| 2. Funnel trap | funnel-web room, walls narrowing like a funnel spider's web | 24 across, 14 high | y 18 to 32 |
| The net | cobweb net hanging under the trap, inside the lair's roof | 20 across | about y 5 |
| 3. The lair | **W1** shape (J: "W1 is not bad") | 230 × 162 | y -50 to 10 |

The lair's floor and burrows go below the lava level (y -54), so the mod has to seal lava round it (the test
datapack already turns it to tuff).

## 1. The run: lantern construct spider

- A hard-light construct spider, about a 20-block leg span, health 200. It laps the cave fast and dives through the
  burrows to pop up behind you (the round 2-4 burrow system).
- At 50% health it stops coming back: it retreats up the escape burrow, and its light trail shows you the way.

## 2. Funnel trap

- A room just big enough for you and the construct spider (24 across), silk walls funnelling down to a floor of
  webbed dirt over the lair.
- The moment you hit it in here, the floor starts to come apart: one ring of webbed dirt crumbles every 3 s, from the
  walls inward, so the floor you can stand on keeps shrinking.
- At 30% health (or if it dies first) the rest of the floor gives way. You and the spider fall about 12 blocks into
  the cobweb net. The web is animated: it sags, catches you with no fall damage, then tears and lowers you about 50
  blocks into the lair over 4 s. The construct spider shatters on the way down.
- Needs the new animated spider model and animated web (J: "should be soon").

## 3. The lair: the big real spider

- A real (not construct) giant spider, about a 36-block leg span, health 400, in the W1-sized lair with its columns,
  side chambers and burrows.
- Its weapons, one of (J to pick):
  - **Construct armour on the front legs:** hard-light blade plates that stand off the leg (J's rule: armour
    "protrudes over them not on their skin"). Scythe strike about 14 damage. Each plate can be broken off
    (about 40 health) to disarm that leg.
  - **Spiked web-rock points:** each leg tip is stone bound in silk, sharpened to a spike. Stab about 12 damage and it
    pins you with web (Slowness for 3 s). A spike shatters if it strikes one of your construct Walls.
  - Both: armour on the two front legs, spikes on the rest.

## Decisions (J, 2026-10-19)

1. **Real spider's weapons: "Web-rock spikes".** Every leg tip is stone bound in silk, sharpened to a spike: stab about
   12 damage and pins you in web (Slowness 3 s); a spike shatters if it strikes one of your construct Walls. No
   construct armour on the real spider.
2. **Construct spider: "Yellow fear ★".** Yellow hard light with the Y1-Y3 fear textures.
3. **Where it lives:** "not sure you assume whats best, give me variations". Three variations below, ★ is my pick.

## Where it lives: variations

- **★ A. The Warren's true ending.** The Dread Warren plays as planned up to the Hollow (Z5), and the Brood Heart (Z6)
  becomes part 1. The Brood Matron is cut: the construct spider is what the fear-lantern made, and the real spider
  is what made the nest. One trial, one big finale, and the Warren's Dread meter carries into the fight.
- **B. A trial of its own, found from the Warren.** The Warren ends with the Matron as planned. Killing her opens a
  sealed burrow in the Brood Heart floor that leads down to this sequence (a second, harder trial). Players who stop
  after the Warren still get a full trial; the spider sequence is the reward for going deeper.
- **C. A wild lair anywhere in the world.** No trial around it: the crack and shaft spawn rarely under land (surface
  y 60+, not ocean or deep dark), and every lair is newly generated from the seed. Found by exploring, like an ancient
  city. Can be added on top of A or B later.

4. **Placement: "A, then C later ★".** The sequence is the Dread Warren's ending (Brood Heart + Matron cut); rare
   wild lairs (C) come later.
5. **Next: "Block-out of all 3 ★".** `tools/trials/spider_sequence.py` + `spider_sequence_blend.py`.

## Block-out (2026-10-19)

`tools/trials/spider_sequence.py` builds all three spaces on one grid at real heights; `spider_sequence_blend.py`
makes the Blender file.

| Part | Built |
|---|---|
| Cave 1 | 152 × 100, floor y -20, roof y 24, entrance shaft from the surface (seed 21) |
| Escape burrow | 11 wide, from cave 1's east end (y -10) up to the trap's west wall (y 21), about 175 long |
| Funnel trap | 24 across, 14 high, silk walls leaning in; webbed dirt floor 3 thick, top at y 18 |
| Drop and net | the drop is 20-25 wide; the cobweb net is at y 6 (12 below the trap floor) |
| Lair | W1 (seed 11), 221 × 162, floor y -44 under the trap, roof y -3 there (12 at the highest); no shaft of its own |

After the net, you're lowered 50 blocks to the lair floor.

- Blender: `LanternLive\trials\spider_sequence_blockout.blend` (4.7 MB). Cameras `01 overview cutaway`,
  `02 trap and net cutaway`, `03 cave 1 inside`, `04 funnel trap inside`, `05 down from the net`, `06 lair floor`.
  Viewport denoising is on, so the viewport no longer looks grainy while it samples.
- Datapack: `LanternLive\test-instances\stormies-spiders\lantern-spider-sequence-datapack.zip`,
  `/function lantern_seq:build` on land in a normal creative world (carves under you, coarse dirt floor and a cobweb
  net in the trap). Not run in game yet.

## Round 2: spikes, textures, spider and trap takes (2026-10-19)

J: "all 3, make the cavy spiky with driplets or even constructed tip ones that should be apart of the spiders arsenal,
they will hang from the ceiling".

- **Hanging spikes:** 546 in all (140 small + 26 big in cave 1, 320 small + 60 big in the lair), kept clear of the
  trap's drop. 86 are big (8-29 blocks long); 86 end in a yellow hard-light tip, part of the spider's arsenal (it can
  shake them loose onto you). The datapack places dripstone blocks, pointed dripstone on the tips, and yellow stained
  glass as a stand-in for the hard-light tips.
- **Textured caves:** 16-pixel-per-block noise textures: stone above y 4, deepslate below, dirt, dripstone, silk,
  webbed dirt; darker lighting. Camera `07 lair ceiling spikes` added.
- **Takes** (`LanternLive\trials\spider_takes.blend`, cameras 01-09), voxel-style stand-ins to rate:
  - Real spider (36-block legs, web-rock spikes: a silk band, then three stepped stone blocks): **R1 hunter** (thin
    banded legs), **R2 brute** (thick hairy legs, big abdomen), **R3 funnel-web** (glossy black, armour plate, long
    fangs, front legs raised).
  - Yellow construct spider (20-block legs): **C1 solid light** (see-through blocks with bright edges), **C2
    lattice** (glowing frames only), **C3 shards** (a cloud of separate cubes, legs of chained cubes).
  - Funnel trap, cut open mid-crumble (outer ring of floor gone, chunks falling to the net): **T1 silk funnel**,
    **T2 sheet webs** (web sheets strung across), **T3 earth funnel** (dirt walls with roots).
- The sequence file now uses R3 in the lair and C1 in cave 1 and the trap, until J picks.

J's next idea (2026-10-19): "maybe the original cave could be destroyed falling through a hollow funnel of spikes on
the sides into the dungeon?"

## Round 3: picks, cave collapse, construct rework (2026-10-19)

Picks: real spider **R2 brute**. Construct: "Discard the third one on the right unless you think itd look cool in game
which im not sure, massive improvements on the others needed" (C3 dropped; its shatter could still be the death
effect). The fall: **"Cave collapse ★"**, replacing the trap room.

**Cave collapse** (`spider_sequence.py --collapse`, `LanternLive\trials\spider_collapse.blend`, cameras 01-08):
- Cave 1 is now 30 high (174 × 105, y 24 to 57) and sits over the lair's west end. The grid runs to y 100: this
  version needs a surface of about y 85+ (hills, plateaus, mountains).
- Its floor over the drop is a 32-wide disc of webbed dirt (3 thick, top at y 42) over the tallest part of the lair.
- Under it, a 39-block hollow funnel narrowing from 32 to 18 across, with 70 spikes pointing in and down from its
  walls (30% with hard-light tips). Camera `08 inside the spike funnel`.
- The net sits at the lair roof (y 2), then it's 47 blocks down to the lair floor (y -45).
- 616 spikes in all, 105 with hard-light tips. Cave 1's own tunnels are kept 3+ blocks away from the lair.
- Datapack `LanternLive\test-instances\stormies-spiders\lantern-spider-collapse-datapack.zip`,
  `/function lantern_seq:build` under a hill. Not run in game yet.

**Construct spider rework** (`LanternLive\trials\spider_takes_r2.blend`, cameras 01-04, with R2 for scale):
- **C1a scale shell** (from C1): rows of overlapping see-through scale plates over a dark amber core, glowing seams,
  joints and claws (Y1 scales).
- **C1b dread armour** (from C1): a dark core with big plates standing off it, a spiked ridge down the back, guard
  plates on the legs (Y3 dread, the stand-off rule from 838 R4b).
- **C2a lightning lattice** (from C2): glowing frames with lightning zig-zagging through the body and down every leg
  (Y2 lightning).
- Every glow is kept at emission 1.5 or less so the yellow stays saturated (the 864 clipping lesson).
- The collapse sequence uses C1a until J picks.
