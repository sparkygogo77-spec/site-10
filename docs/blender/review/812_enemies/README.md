# Pass 812: enemies — WAITING

**Script:** `docs/blender/blender_updates/812_enemies.update.py`
**Open in Blender:** `C:\Users\Josh\Documents\LanternLive\combat\enemies.blend` (Cam E1, press play; 130 frames)
**Files here:** `sheet.png` (check render, Cam all, tick 63: the Wisp's fear cone on the player, the Brute mid-slam behind
its player, the Mite on its player's back)

All three are original designs. Each plays three clips in a row, at 20 ticks a second:

- **Idle:** ticks 1–40.
- **Attack:** ticks 41–80, against a player stand-in.
- **Death:** ticks 81–130. The player fires a construct shot and the enemy comes apart.

| Take | Enemy | Idle | Attack | Death |
|---|---|---|---|---|
| E1 | Dread Wisp (fear): gaunt shade, dark rib plates, a halo of six floating eye-plates (sickly yellow), four 5-link tendrils, long clawed arms | hovers ±0.12, the eyes orbit | the eyes snap forward and stare, a cone of yellow light washes the player (who turns away, arm over the eyes), the tendrils lash at 2.5× | the eyes go out one by one (3 ticks apart), then it unravels into dark pixels from the bottom up |
| E2 | Ember Brute (rage): hunched, huge forearms, two horns, red cracks on the chest, brow and arms | breathes, and the cracks pulse with the breath | rears back, both fists slam (tick 63), a red ground ring to 6 blocks; the player is knocked back | staggers twice, the cracks flare, bursts to pixels |
| E3 | Leech Mite (parasite): a 4-segment crawler, mandibles, 6 hooked legs, a violet glowing sac | skitters in a small circle | leaps onto the player's back and latches; the sac pulses while it drains, and the player staggers and claws at it | shaken off, lands on its back, legs curl, pops into pixels |

**For J:** KEEP / IMPROVE / DROP per enemy. The kept ones go to the mc chat as entity models with these clips.
