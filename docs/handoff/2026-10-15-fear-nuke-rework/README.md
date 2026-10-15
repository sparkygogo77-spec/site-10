# Hand-off: Fear Nuke rework and a missile barrage (J, 2026-10-15 ~23:05 UTC)

J, in game (screenshot `nuke-now.png`: Yellow ring, "Fear Nuke built, let go to send it, 22/30 blocks", the bomb hanging in the sky):
"nuke physics and timing needs work, I want missile barrage next from angles in above that do the same explosions but small and
multiple one after another. The nuke also should drop where i begin to hold right click instead of forming there, then where i let go
it throws it in that direction, and it seemingly floats above the ground right before it explodes when i dont want control over it,
but it should explode on contact or about 5 blocks above the ground, the bottom most of the nuke."

## 1. Fear Nuke: new flow
- **Hold right-click:** the nuke drops into place at the spot you're aiming at when you start holding, instead of forming in the sky
  over you (today: "Fear Nuke forms in the sky, tethered to the raised ring"). *Coordinator's reading; confirm with J if unsure.*
- **Let go:** it's thrown in the direction you're looking when you release, with real physics (a heavy arc: gravity, no hovering).
- **No control after release:** today it seems to float above the ground just before it blows. It must not hang or steer.
- **Detonation:** on contact with anything, or when the **bottom of the nuke is about 5 blocks above the ground** (an airburst),
  whichever comes first. Keep the existing airburst, crater and Fear Frenzy.
- "Physics and timing needs work": tighten the build-up and the fall so it reads fast and heavy (J's rule: fast and snappy, no long
  wind-ups, never takes control from the player).

## 2. Missile barrage (new power, next after the nuke)
- Missiles come in **from angles above** (not straight down), several, **one after another**.
- Each does **the same explosion as the nuke, but small**.
- Suggested shape (confirm with J): hold to paint the target area, release to call the barrage; 5-8 missiles staggered 3-5 ticks apart,
  each from a different high angle. Same Fear-yellow look as the nuke.
- If the missile model needs designing, say so and the coordinator routes a Blender pass to the combat chat (500s).

## Test
Client game test: hold, release, throw arc, detonation height (bottom 5 blocks above ground) and on-contact, with screenshots; a
barrage test that counts the explosions and their spacing.
