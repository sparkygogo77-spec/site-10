# Briefs for two new Blender chats (from the super jump chat, 2026-10-14)

Both chats share these rules:

- **Repo:** sparkygogo77-spec/site-10. Commit to `claude/lantern-redesign-pass2` and put hand-offs in `docs/handoff/`.
- **Pass numbers:** the battery chat uses 100–199 and the lead chat 200–299.
- **J's files:** `C:\Users\Josh\Documents\LanternLive\`. Build each `.blend` headless (bpy 5.2.2), copy it and its textures there, then open it in J's Blender.
- **Lantern Live watcher:** the Folder box was found empty. It was set again, but the panel still says "Not watching", so check it.
- **Working style** (lantern-ring-design skill):
  - show 3 or more labelled takes;
  - keep replies short;
  - always name the `.blend` to open;
  - game code goes to the coordinator chat as a written brief;
  - no copyrighted marks;
  - Mojang textures are preview-only, recoloured at load time in game.

## Chat A: super jump, smoke and light (passes 304–349)

- **Read first:**
  - `docs/handoff/2026-10-13-super-jump-blender.md`;
  - `docs/handoff/2026-10-13-super-jump-ring-lab-brief.md` (J's picks, poses and timings);
  - the update scripts in `docs/blender/blender_updates/81`–`91` and `92`/`94`.
- **J's picks:**
  - Takes 1 and 2; fall arm D1a, D1b or D1c; landing E2; wall W2.
  - Rising arm G2+G3: 15° forward, follows the aim, square emblem ring.
  - Ribbon R1, short (1–2 blocks), also on the way down.
  - Craters by surface. A deeper fall uses E3 with rising guard walls.
  - All four landing coverages (P2, P4a, P4b, P3) are wanted, set per ring and swappable later.
  - Blocks crumble and drop rather than fly up.
- **Smoke and light (pass 94, `construct_smoke_rays2.blend`):** J picked "long rays". Every face of a construct glows, the glow fades over 4 blocks, and light beams leave every side.
- **Not in game yet:**
  - ribbon, rising arm and build-up;
  - P2/P3/P4 coverage; E2 as the default (E1 is still the default);
  - smoke rays.
- **Next:** refine the smoke rays, and keep briefing the coordinator.

## Chat B: textures, corps metals and Red towers (passes 350–399)

- **Read first:**
  - `docs/texture_library/README.md`;
  - `docs/handoff/2026-10-14-crimson-diamond-surface.md`;
  - the tools: `tools/texture_library.py`, `tools/corps_metal_recolour.py`, `tools/glowing_nether_bricks.py`, `tools/smooth_black_metal.py`;
  - the update scripts `93`, `95`–`99` and `300`–`303`.
- **Texture library:** J's good textures are BR1, W1, H1 (the only hex, for every colour), R1, R2, V1 and X3D1. Each comes in green, blue, crimson, yellow, violet and orange, in every format.
- **Crimson constructs:** use BR1, W1, H1 and R2. The classic textures are dropped. Blue uses BR1 jade in dark blue.
- **Corps metals:** vanilla diamond, emerald, iron, gold, netherite and copper, plus chiseled quartz, quartz bricks, quartz pillars and the red, chiseled and cracked nether bricks. Each comes in every corps hue plus black.
  - They keep their shader ID (`lookLike`) and get recoloured at load time.
  - Nether bricks are glowing metal with lit mortar, like BR1.
  - Smooth black metal is our own texture.
- **Red towers:** J said the old ones used too many block variations.
  - **Rule:** one design idea per tower, colours that blend, no pillars.
  - **Latest:** `red_tower_f.blend`. F1 is nearly all crimson diamond, F2 is construct brick, and F3 is smooth black metal. Waiting on J's pick.
- **Next:** iterate on the tower J picks, and brief the coordinator on the metals and towers.
