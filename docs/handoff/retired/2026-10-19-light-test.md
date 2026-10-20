FOLDED 2026-10-19 by coordinator 4 (written by coordinator: the chat was archived before it wrote a note; Lunar
loader gotcha -> lantern-coordinator "Research chats")

# Retired: LambDynamicLights test world (Claude Code on J's PC), 2026-10-19

**Role:** research/test chat, session `local_442ddcc8-56b1-4bbb-bf0c-ae1a8df4370b`, 5 turns, no passes. Started by
coordinator 3; retired on J's pick "Retire the light test" in coordinator 4. Source: its hand-over in the shared notes
folder and its last report.

## What it did

- Test instance `LanternLive\test-instances\lambdynamiclights` (official launcher, Fabric Loader 0.19.5): Fabric API
  0.164.0, lantern-ring 2.1.1712, LambDynamicLights 4.13.0, Sodium 0.9.3-beta.1, Iris 1.11.7 (sha512-checked, J
  approved each download).
- J's run: no clash with the patched Complementary pack, torch works, Black Hole looks better, held ring only "a little
  warmly lit beside me".
- Found our jar already gives a held ring green light 12 under the patched shader (PowerRingItem
  getLightEmission/getLightColor + ShaderPackPatcher TINT_UNIFORMS); it is just small. Brief for the code chat:
  `docs/handoff/2026-10-19-ring-held-light-brief.md` (e1cba0a7). Research doc sections b58b4b32, e1cba0a7, 1fc74fc3. The brief asks for light 15 and a wider
  reach (LambDynamicLights' light is uncoloured, so the shader paints it orange and small).

## Open work (for J, no chat owns it)

- J's Lunar try of CreeperMeyt Dynamic Lights ("test later"), all staged in the test folder: untick LambDynamicLights
  in Lunar, drop the dynamic-lights-creepermeyt jar (MIT, datapack-based, real light blocks) into Lunar's mods, new
  world with it and `lantern-ring-creepermeyt-lights.zip` (ring 14, batteries 15, construct weapons 7), hold the ring in
  the dark cave. Then pick card 1 / card 2 / the shader brief for the code chat.

## Gotchas

- Lunar runs Fabric Loader 0.19.3: mods that need 0.19.5 (LambDynamicLights 4.13.0) won't load there; test them in the
  official launcher instance instead.
- LambDynamicLights' light is uncoloured: the green has to come from our shader patch.
