# Lantern Ring: notes for Claude

A Fabric mod for **Minecraft 26.3**: a green power ring with modes (Blast, Beam, Wall, Dome,
Bridge, Shockwave, Tether), flight, a 3D ring worn on the hand, and a Ring Lab test menu.
See README.md for the player-facing description.

## Build

- Needs **Java 25** (26.3's requirement). If `java -version` is older, unpack Temurin 25 to
  `/opt/jdk25` (`https://api.adoptium.net/v3/binary/latest/25/ga/linux/x64/jdk/hotspot/normal/eclipse`)
  and `export JAVA_HOME=/opt/jdk25 PATH=/opt/jdk25/bin:$PATH`.
- `./gradlew build` produces `build/libs/lantern-ring-<version>+26.3.jar`.
- Copy the jar into `modpack/lunar-client/mods/` and `modpack/vanilla-fabric/mods/` when releasing.

## 26.3 is unobfuscated

Minecraft 26.x ships with Mojang's own names and there are no Yarn mappings, so all code uses
Mojang names (`Level`, `ItemStack`, `InteractionResult`...). To check a signature, read the game
jar Loom extracts: `javap -cp .gradle/loom-cache/minecraftMaven/net/minecraft/minecraft-common-*/26.3/*.jar <class>`
(client classes are in `minecraft-clientOnly-*`). Many things moved since 1.21, for example:
- block codecs are gone; render layers come from the model (`force_translucent`, `light_emission`)
- `PoseStack.rotateDegrees(Axis, deg)` replaces `mulPose(Axis.rotationDegrees(...))`
- entity types are in `EntityTypes`, key types are `InputConstants.Type.KEYBOARD`
- `Screen` draws with `extractRenderState(GuiGraphicsExtractor, ...)`

## Layout

- `src/main`: common/server code. Ring powers in `RingPowers`, held Wall/Dome in
  `HeldConstructs`, flight in `RingFlight`. Effects are not spawned on the server: it sends
  `RingFxPayload` and each client draws it in that player's Ring Lab style.
- `src/client`: the Ring Lab (`LabSettings`, `RingLabScreen`, `LabFx`), custom particles
  (`ConstructParticle`), the 3D ring (`RingModels`, `RingHandLayer`, `RingFirstPerson`) and one
  mixin into `FirstPersonHandsAndItemsRenderer`.
- `src/gametest`: client game tests that boot the real game and take screenshots.
- `tools/`: Pillow scripts that generate the textures. `docs/screenshots/`: reference shots.

## Screenshot tests (seeing the game without a GPU)

The container can run the real client in software OpenGL:

```
apt-get update && apt-get install -y mesa-utils libegl1 libegl-mesa0   # once per container
export JAVA_HOME=/opt/jdk25 PATH=/opt/jdk25/bin:$PATH LIBGL_ALWAYS_SOFTWARE=1 \
  XDG_RUNTIME_DIR=/tmp/xdg SDL_VIDEODRIVER=x11 SDL_VIDEO_FORCE_EGL=1
mkdir -p /tmp/xdg && chmod 700 /tmp/xdg
xvfb-run -a -s "-screen 0 1280x720x24 +extension GLX +render -noreset" ./gradlew runClientGameTest --no-daemon
```

Screenshots land in `build/run/clientGameTest/screenshots/`. Without `SDL_VIDEO_FORCE_EGL=1` the
window fails with "Couldn't find matching GLX visual". A run takes 1-3 minutes.

Gotchas learned the hard way:
- Press the use key with `ctx.getInput().holdKey(o -> o.keyUse)`, not `holdMouse(1)`: mouse
  button numbers differ in 26.3 and `1` mines instead of using the item.
- Item code runs on both sides, and in singleplayer the client and server share one JVM. Never
  touch server state (like `HeldConstructs`) from the client side; `releaseUsing` doing that
  deadlocked the game.
- A component changed only on the server (e.g. the ring's mode from a test) isn't on the client's
  copy straight away; that's fine for the server-side logic.

## Working with the owner

The owner tests in their own game (often Lunar Client, which bundles Fabric API and Sodium) and
picks between versions in the Ring Lab. They paste its "Copy report" text back; treat KEEP as
final, IMPROVE as the next thing to iterate on, and DROP as safe to remove.
