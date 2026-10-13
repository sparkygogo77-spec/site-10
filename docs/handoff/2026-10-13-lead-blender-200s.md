# Lead Blender chat: passes 200-202 (Hope sanctuary, squad armour, Red tower)

This is the lead Blender chat. It owns the coordinator's Blender queue. Pass numbers:
- lead chat: 200-299;
- battery chat: 100-199 (it retires after the battery);
- super jump chat: under 100, then 300-399.

## Round 1 is in J's Blender; waiting on his picks

| Pass | File | Takes | Cameras |
|---|---|---|---|
| 200 | `hope_sanctuary.blend` | A1 Hourglass funnel, A2 Turbine drum, A3 Lotus tiers | Cam A1/A2/A3/all, A1 inside, A2 inside, A3 halo |
| 201 | `squad_armour.blend` | B1 Pearl plate + R1 barding, B2 Hard-light shell + R2 all-hard-light ravager, B3 Night guard + R3 seamed ravager | Cam B1/B2/B3/squads/backs |
| 202 | `red_tower.blend` | C1 Fang spire, C2 Rage furnace, C3 Split claw | Cam C1/C2/C3/field/all |

**Pass 200, Hope sanctuary.**
- J's answers built in: 12, 17 b, 18 c and 19 b+c.
- **Layout:**
  - herds sit in bubbles at the bottom;
  - the flyers' deck is on top;
  - the turbine spins in the middle, one turn every 20 s;
  - there are two-high glass rails everywhere, so no animal can jump off;
  - it's wide, not tall: about 50 blocks across and 30-35 blocks high.
- **Blocks:** whole blocks only, in Skystone, Hope Quartz, Hope Bricks, Hope Lamp, blue construct brick and nebula glass. A pick converts straight to a block plan.
- **The mark is original:** an open ring with a four-point star rising out of its gap (`MARK` in the update file). It is not a published emblem.

**Pass 201, squad armour.**
- It is on BlueVillagerModel's boxes, one voxel per model pixel, with the armour 1 px proud of the suit.
- **Roles:**
  - flyer: light wings;
  - flyer: lasso coil;
  - warrior: slam hammer;
  - rider: lance.
- The ravager is close to vanilla proportions, reskinned per take.

**Pass 202, Red tower.**
- J's answer 31: a cooler tower, steak farms, and enraged mobs chained to spaced posts in a field below.
- **Steak farms:** each take has two fenced cattle pens on the plinth, with hay, a smoker, a campfire and magma.
- **The field:**
  - 22 posts around the plinth on scorched netherrack and coarse dirt;
  - each post has a chained zombie, skeleton, spider, hoglin or pillager with glowing red eyes;
  - they lunge on the chain and snap back.
- **The rage orb:** it floats at the top and beats like a heart. There is no emblem.
- The vanilla textures are only in J's LanternLive folder, for previews. They are not in the repo.

## Still in the queue (specs needed)

- **Kneel and lean:** the next Blender pass.
  - Kneel to pick up a lantern on the ground.
  - Lean on a lantern standing one block higher to charge faster (J's answer 16).
- **Construct tools, the Lantern suit, the kill animation and the Deluge:** these were asked for in other threads, and their specs haven't reached this chat. The coordinator should paste J's descriptions, or point to the files.

## Round 1, passes 203-206 (in J's Blender, waiting on picks)

| Pass | File | Takes |
|---|---|---|
| 203 | `kneel_lean.blend` + `kneel_lean_poses.json` | K1 one knee, K2 squat, K3 vow (ring flare); L1 fist in the port, L2 palm down, L3 shoulder lean (ring brightens all hold) |
| 204 | `construct_tools.blend` | Green set: sword, pickaxe, axe, shovel (mace), hoe (scythe), hammer, each as T1 Jade relic / T2 Gilded edge / T3 Pure light |
| 205 | `lantern_suit.blend` | S1 Corps uniform / S2 Hard-light shell / S3 Jade plate; helmets H1 lantern cap / H2 glass dome / H3 mask + hood / H4 none; forms feet-up in 1.5 s |
| 206 | `deluge_water.blend` | Green G1 clear emerald / G2 hard-light water / G3 deep jade; Red R1 blood / R2 clotted / R3 black blood; level-3 event at the game's timing |

**Pass 203, kneel and lean.**
- The poses use the super jump format: per part `rot` (xRot, yRot, zRot, in radians) and `offset_px` from the vanilla pivot.
- The ring is the right arm. Mirror it for left-handed.
- In the kneels the lantern follows the ring hand from `carry_from_tick`.
- The leans list their `charge_ticks`.

**Pass 204, construct tools.**
- Voxels are half a model pixel, built from J's reference pack (`docs/blender/reference/tools_abdulka/`).
- The broad faces carry the construct texture.

**Pass 205, Lantern suit.**
- It is one pixel proud of the skin boxes.
- The chest mark is J's own lantern as a 5x6 pixel mark. It is not a published emblem.

**Pass 206, Deluge water.**
- It follows Deluges.java: globe, geyser, flood and rolling rings.
- Green waves are about 4 blocks apart and Red about 3.2, with Red rolling slower.

## Still open

- **The Dread Runner kill animation:** the coordinator says its spec lives in the Dread Runner thread. It needs pulling from there.
- **The other corps:** the Blue tool set and the other corps' suits come after J's Green picks.
