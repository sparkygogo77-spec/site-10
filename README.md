# Lantern Ring

A Fabric mod for Minecraft **26.3** inspired by the classic green power ring. Charge the ring at a
Power Battery, then fly, tunnel through mountains, and build constructs out of hard light.

## Install

1. Install [Fabric Loader](https://fabricmc.net/use/) for 26.3 and drop
   [Fabric API](https://modrinth.com/mod/fabric-api) into your `mods` folder.
2. Build the mod with `./gradlew build` (Java 25) and copy `build/libs/lantern-ring-2.0.0+26.3.jar` into `mods`.
   Or grab a ready-made jar from `modpack/`.

Version 1.0.0 (Minecraft 1.21.1) is in this repo's git history.

## The ring

| Control | What it does |
| --- | --- |
| Right-click | Use the current mode |
| Sneak + right-click | Switch to the next mode |
| **V** (rebindable) | Toggle flight on or off |

| Mode | Cost | What it does |
| --- | --- | --- |
| **Blast** | 100 | Bores a 3×3 tunnel 50 blocks long, starting right in front of you, in whatever direction you look (up, down, diagonal). Mobs in the tunnel take 10 damage. Bedrock and blocks with contents (chests, furnaces, spawners) are left alone. Cleared blocks don't drop. |
| **Beam** | 15 | Energy bolt: 8 damage and knockback, 48 block range |
| **Wall** | 40 | 5×3 hard-light shield two blocks in front of you |
| **Bridge** | 60 | 3-wide, 13-long hard-light bridge at your feet, heading where you face |
| **Shockwave** | 35 | Hurls every mob within 7 blocks away from you |
| **Tether** | 20 | Pulls a mob to you, or, aimed at a block, yanks you to it |

Hard-light constructs fade after 10 seconds.

**Flight:** with flight toggled on and charge left, double-tap jump to fly. It drains 1 charge every
half second (about 8 minutes on a full ring), and a charged ring also stops fall damage. When the
ring runs dry you drop out of the sky, so watch the charge bar.

**Charge:** 1000 when full, shown as the green bar under the item. Right-click a **Power Battery**
with the ring to refill it.

## Recipes

- **Power Ring:** emerald block on top, gold ingot / eye of ender / gold ingot across the middle, gold ingot at the bottom
- **Power Battery:** iron, emerald, iron / emerald, lantern, emerald / iron, glowstone, iron
