# Rays "game breaking", and two hammer types (J, 2026-10-15 ~23:00 UTC)

Screenshots `2026-10-15-rays-*.png` (first person, Complementary Unbound 5.81 patched). J: "the rays are game breaking and theres
two hammer types".

## 1. Rays
- Shot 97303d3c: after/while charging, big streaked shafts and sheared planes fill the whole view; the sky goes dark purple and
  everything is smeared. Shot 05d0e3a0 (Wall 15x15): large translucent streak planes radiate across the upper left of the view.
- Suspects: `BeamChargeGlow` "the ring is a sun": shafts of pure light round the ring (lines ~242-310) and the crowns of thin rays
  (~184-221): in first person the ring sits at the eye, so 1-block shafts become screen-wide streaks; plus the charge's world dimming
  ("Charge light round 2: darkness plunges as the ring fills", "Sun dims round a charging ring"). Same family as the glow bugs.
- Fix: keep the rays off the camera in first person (clamp length near the eye, or draw them only in third person / on the lantern),
  cut their alpha under the patched pack, and limit the dimming. Screenshot test in first person at full charge and overcharge.

## 2. Two hammer types
- There are two hammers: **Hammer mode** (10-13: "a solid hard-light hammer in your hand", aimed leap and smash, `HammerSlams`,
  `HammerHold`) and the **construct hammer** (10-14: "tap in Hammer mode, R2a overhead, R2b from the side on walls",
  `ConstructHammers`, `ConstructHammerFx`, plus the Tools-mode hotbar hammer). J wants one.
- Ask J which to keep as the one hammer (or merge: the construct hammer's look and R2a/R2b swings, with the leap and smash on a
  charged use), then remove the other and update the What's New book.
