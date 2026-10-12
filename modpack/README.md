# Lantern Ring mod pack (Minecraft 26.3, Fabric)

There are two folders. Pick the one that matches how you play.

**Updating:** every build has the same file name, so delete the old `lantern-ring` jar from your
mods folder before adding the new one, then restart the game. The newest build is always at
https://github.com/sparkygogo77-spec/site-10/releases/download/latest/lantern-ring-latest.jar

## `lunar-client/` (use this for Lunar Client)

Contains only `lantern-ring-2.0.0+26.3.jar`. A Fabric mod is a single `.jar`; you don't unzip it. Lunar Client already ships Fabric API (and Sodium, Iris and
others) and keeps them updated, so you don't add those yourself. Adding a second copy can make
Lunar refuse to start.

1. Open Lunar Client and pick **26.3** in the version selector.
2. Click the **⚙** button at the bottom right and open the **Mods** tab (📁).
3. Drag `lantern-ring-2.0.0+26.3.jar` into it, then launch.

If Lunar shows a mod error screen, switch to Lunar's **Vanilla** addon (Vanilla icon at the bottom
right of the version selector), then add both jars from `vanilla-fabric/mods/` the same way.

## `vanilla-fabric/` (any normal Fabric setup)

If your launcher already has Fabric API installed (most do), you only need the Lantern Ring jar.

For the official launcher, Prism, MultiMC, CurseForge or Modrinth App, or Lunar's Vanilla addon.

1. Install [Fabric Loader](https://fabricmc.net/use/) for **26.3** (needs Java 25; the launchers bundle it).
2. Copy both jars in `vanilla-fabric/mods/` into your `mods` folder (`%appdata%\.minecraft\mods`
   on Windows, `~/Library/Application Support/minecraft/mods` on macOS).

## In game

Find the **Power Ring** and **Power Battery** in the Tools creative tab, or craft them (see the
main README). Sneak + right-click switches the ring's mode. Right-click uses it. **V** toggles flight.
