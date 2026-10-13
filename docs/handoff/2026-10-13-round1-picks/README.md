# J's round-1 Blender picks (2026-10-13), for the coordinator

J picked these on the picks board. The lead Blender chat produced them in passes 200-207 on this branch.

| Item | Pick | Source | What's here for the game |
|---|---|---|---|
| Hope sanctuary | **A3 Lotus tiers** | `docs/blender/blender_updates/200_hope_sanctuary.update.py`, `take_a3` | `hope_sanctuary_A3.json`: block plan (12,259 blocks) and the spinning turbine (804 + 68 blocks, marked `moving`) |
| Squad armour + ravager | **B2 Hard-light shell + R2** | `201_squad_armour.update.py`, `armour(v, "B2")`, `ravager("B2")` | Voxel layout at 1 voxel per model px on BlueVillagerModel boxes. Lead Blender chat to export textures/bbmodels next. |
| Red Lantern tower | **C3 Split claw** | `202_red_tower.update.py`, `take_c3` | `red_tower_C3.json`: block plan (21,039 blocks) plus the two steak farms (336 blocks); the chained-mob field is code (posts every ~16°, 31-44 blocks out) |
| Lean on a lantern | **L3 Shoulder lean** | `203_kneel_lean.update.py` | `lean_L3_poses.json`: key poses in the super jump format, `charge_ticks`, `body_yaw_rad` |
| Kneel | none yet | `203` | J: "revise what the legs are doing, needs work". Round 2 is pass 208. |
| Construct tools, Green | **T3 Pure light** | `204_construct_tools.update.py` | Voxel designs (sword, pickaxe, axe, shovel, hoe, hammer); lead chat to export bbmodels next |
| Construct tools, Blue | **U3 Pure hope** | `207_construct_tools_blue.update.py` | Same, in Blue |
| Lantern suit | none yet | `205` | J: "better attempts at S2". Round 2 is pass 209. |
| Suit helmet | **H3, "mask only maybe"** | `205`, `helmet(v, "H3")` | Round 2 shows mask-only variants on the new S2 suits |
| Deluge water, Green | **G1 Clear emerald** | `206_deluge_water.update.py`, `water(..., "G1")` | Clear green-tinted water, glassy, strong reflections: base (0.05, 0.55, 0.25), very low roughness, mostly transmissive. For the fluid textures and fog colour. |
| Deluge water, Red | **R2 Clotted** | `206`, `water(..., "R2")` | Opaque, satin (not mirror) deep blood red (0.24, 0, 0.01) with slow darker swirls (0.07, 0, 0.004) drifting through it |

## Notes for building them
- **Block plans.** Entries are `[x, y, z, name]` in Minecraft axes, centred on the structure:
  - y = 0 is its floor;
  - negative y hangs below the floor (the sanctuary's underside);
  - names are the Blender texture names, which are the mod's block ids for mod blocks and the vanilla ids for vanilla blocks.
  - Glass rails two blocks high run around every paddock, so animals can't jump off (J's 18 c).
- **The sanctuary floats.** In the renders it sits about 34 blocks above the rescue dome.
  - The turbine spins once every 20 s.
  - J's 19 b+c: it powers the lanterns and slowly charges Blue rings nearby.
- **The tower.** The tower stands on its plinth with the stairs facing north.
  - The field posts are spread around the plinth. Each one has an enraged mob chained to it that lunges and snaps back.
- **The Hope mark is original.** It is an open ring with a four-point star rising out of its gap (`MARK` in pass 200). Do not swap in a published emblem.

## Models exported (B2/R2, T3, U3)
`python tools/export_round1_models.py src/main/resources/assets/lanternring` wrote these, read straight from the Blender designs:
- **Tools:** `bbmodel/construct_{sword,pickaxe,axe,shovel,hoe,hammer}_{green,blue}.bbmodel` (T3 and U3).
  - They stand upright, pommel down, at half a pixel per voxel.
- **Armour:** `bbmodel/blue_squad_armour_{flyer,flyer_lasso,warrior,rider}.bbmodel` (B2).
  - The pieces sit on BlueVillagerModel's boxes, feet at y = 0.
  - Each role carries its gear: wings, lasso, hammer, lance.
- **Ravager:** `bbmodel/blue_ravager_r2.bbmodel` (R2), facing north, feet at y = 0.

How the cubes draw, by name prefix in BbModel:
- `glass_hardlight_*` cubes are translucent and full-bright: the hard light. These broad faces are where J wants the animated construct texture.
- `glow_*` cubes are the bright rims, inlays, gems and lance.
- The tool handles are solid.

All the textures together come to 84 KB.
