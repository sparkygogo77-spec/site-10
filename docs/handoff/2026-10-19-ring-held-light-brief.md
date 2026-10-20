# Brief: a bigger green held light for the ring under the Lantern Ring shader (2026-10-19)

**For:** the mod-code chat. **From:** the LambDynamicLights test chat. **J's pick:** "C, both" (route 2: a green
shader light that works in Lunar with no extra mod).

## What J saw
In the LambDynamicLights test instance (`test-instances/lambdynamiclights`, ComplementaryUnbound r5.8.1 + Lantern
Ring on), the held Power Ring only lit "the ground a little, warmly, beside me". The Black Hole's area looked better,
but J said "not the ring glow". LambDynamicLights can't fix this in Lunar: Lunar's Fabric Loader is 0.19.3 and
LambDynamicLights 4.13.0 needs 0.19.5. Its light also has no colour, so the shader paints it warm orange.

## What's already there (don't rebuild it)
- `PowerRingItem#getLightEmission` returns `shaderHeldLight` = 12 when `ShaderGlow.patchedPackOn()`, else 0
  (`LanternRingClient` line ~79). `PowerRingItem#getLightColor` hands Iris the corps colour (with SunDim riding in
  its length).
- `ShaderPackPatcher.TINT_UNIFORMS` adds `heldBlockLightColor(2)` and `LanternCorpsColor()`. `heldLighting.glsl`
  already swaps `heldLightCol` to the corps colour for item 44085 (`item.properties`: power_ring and the batteries).
- So the held ring already gives green light 12 under the patched pack. That's the small patch J saw.

## Why it's small
Complementary's falloff in `lib/lighting/heldLighting.glsl`:
`heldLight = pow2(pow2(heldLight * 0.47 / (dist + 6)))`. For light 12 that's about 0.78 at your feet, 0.1 at 4 blocks
and almost nothing at 8. Iris also only asks for the light of items **in your hands**, so a worn ring gives none.

## Asks (smallest first; J judges each in game)
1. **Brighter:** `shaderHeldLight` 12 → 15 (the most Iris passes). One number.
2. **Wider, ring only:** a `ShaderPackPatcher` edit in `heldLighting.glsl` right after the `LANTERN_RING_TINT` block:
   for `heldItemId == 44085` (and `heldItemId2`), scale `lViewPosL` down (try `*= 0.6`) so the ring reaches about
   8 blocks instead of 4. Guard it with `#ifdef LANTERN_RING_TINT` like the others.
3. **Worn ring and charging:** feed the same light when the ring is worn (not held) or charging. Iris only reads
   hand items, so this needs a ring-specific uniform. For example, put a "ring on" bit into `heldBlockLightColor`'s
   length the way SunDim already does, and have the patch add held light for 44085 even when `heldItemId` isn't 44085.
   Bigger job: say so before starting.
4. **Not this brief:** constructs, Beam and other players' rings. Shader held light is only your own hands. That's
   card 2 (real light blocks following you, built on ChargeLight), or ship `assets/lanternring/dynamiclights/*.json`
   (card 1, LambDynamicLights users only). A working card-1 sample is in
   `test-instances/lambdynamiclights/resourcepacks/lantern-dynamic-lights-test/`.

## How J checks it
Lunar, 26.3, Complementary + Lantern Ring on, Held Lighting on (Shader Settings → Lighting), the dark cave from
`lantern-light-test-datapack.zip` (`/function lantern_light:build`). Hold the ring. Pass: a clear **green** pool round
you, reaching about 8 blocks, in each corps colour.
