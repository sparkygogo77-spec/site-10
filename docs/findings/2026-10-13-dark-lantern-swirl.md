# Dark Lantern charge light: findings (branch claude/lantern-redesign-pass2, commit c087da5)

## What J asked for
- The glow was "just one pulse".
- He wants swirling light green in the centre, flaring through the lower levels in every direction from
  the centre, and a big green ball in the middle with some yellow.
- Iris shaders don't match Blender, so the light is baked into textures instead of being left to the shader pack.

## What changed
- tools/pixel_dark_bbmodel.py now writes a separate model, `dark_lantern_glow`:
  - 1554 boxes over the jade, ribs, plates, veins and socket.
  - 12 looping frames: `dark_lantern_glow.png` and `_1`..`_11.png`, one loop every 2.5 s.
- The baked light matches Blender update 35_swirl:
  - a ball of light at the bulge
  - a 3-arm swirl that twists with height
  - flares leaving the centre up and down
  - colours running through many greens to a yellow heart
- Each texel's alpha follows its brightness, so dark texels stay see-through under shader packs.
- `LanternFirstPerson.darkCharge` cross-fades two neighbouring frames (`renderPackSafe`), scaled by the
  Dark Lantern's squared charge curve. It is skipped at rest, so it costs no FPS when idle.
- The old `glow_charge` cubes are gone from `dark_lantern` (0 left), so nothing is drawn twice.

## Test and jar
- DarkLanternTest:
  - 33%: still dark.
  - 66%: green flares on the body.
  - Peak: bright, with a yellow heart.
- The jar is recompressed with oxipng to 31,347,350 bytes (29.9 MiB). That is right at the 30 MiB upload
  limit, so the next asset addition needs a size cut (for example fewer frames or a smaller glow atlas).
- J has the jar: `Documents\LanternLive\lantern-ring-dark-swirl.jar`.

## Still open
- The Blender 35_swirl preview: J's watcher was off.
- The underhand charge animation: the fist comes from below and the lantern is held closer.
- What J meant by "the lantern is not turned 90 degrees to the left of me".
