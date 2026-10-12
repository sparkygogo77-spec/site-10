# Lantern Ring mod pack (Minecraft 1.21.1, Fabric)

There are two folders. Pick the one that matches how you play.

## `lunar-client/` (use this for Lunar Client)

Contains only `lantern-ring-1.0.0.jar`. Lunar Client already ships Fabric API (and Sodium, Iris and
others) and keeps them updated, so you don't add those yourself. Adding a second copy can make
Lunar refuse to start.

1. Open Lunar Client and pick **1.21.1** in the version selector. Fabric mods need 1.16.5 or newer.
2. Click the **⚙** button at the bottom right and open the **Mods** tab (📁).
3. Drag `lantern-ring-1.0.0.jar` into it, then launch.

If Lunar shows a mod error screen, switch to Lunar's **Vanilla** addon (Vanilla icon at the bottom
right of the version selector), then add both jars from `vanilla-fabric/mods/` the same way.

## `vanilla-fabric/` (any normal Fabric setup)

For the official launcher, Prism, MultiMC, CurseForge or Modrinth App, or Lunar's Vanilla addon.

1. Install [Fabric Loader](https://fabricmc.net/use/) for **1.21.1**.
2. Copy both jars in `vanilla-fabric/mods/` into your `mods` folder (`%appdata%\.minecraft\mods`
   on Windows, `~/Library/Application Support/minecraft/mods` on macOS).

## In game

Find the **Power Ring** and **Power Battery** in the Tools creative tab, or craft them (see the
main README). Sneak + right-click switches the ring's mode. Right-click uses it. **V** toggles flight.
