package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileSystem;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;

/**
 * Makes a Lantern Ring copy of each Complementary shader pack in the shaderpacks folder, next to
 * the original: "ComplementaryUnbound_r5.8.1 + Lantern Ring.zip". The copy gives every corps its
 * exact light colour, makes the constructs and lanterns glow, and lets the green Deluge give green
 * light while still drawn as the pack's water. Pick it in Video Settings > Shader Packs.
 *
 * <p>It is made on the player's own computer from their own copy of the pack, because
 * Complementary's licence doesn't allow sharing a changed pack. If an edit no longer fits a newer
 * pack version, no copy is made and the mod falls back to {@link ShaderPackIds}.
 *
 * <p>IDs it adds: blocks 19000 (green), 19004 (red), 19008 (violet), 19012 (orange), 19016 (blue), 19019 (the
 * Blue Lantern itself: blue light, but only its glass glows),
 * 19020 (yellow, for later), 32002 (green Deluge) and 32003 (Red Deluge, thick opaque blood), both treated as water; held items 44085 (green)
 * and 44086 (red). Light colour slots 85 to 90 follow the same order.
 *
 * <p>It also makes the mod's own glow (the ring, its charge, its particles, the lasso) real light:
 * anything drawn with {@link ShaderGlow}'s marker light gets emission in the hand, entity and
 * particle programs, so it blooms instead of looking like flat green paint.
 */
final class ShaderPackPatcher {
	/** Bump when the edits change, so existing copies are made again. */
	private static final String VERSION = "11";
	private static final String MARKER = "lanternring-patch.txt";
	private static final String SUFFIX = " + Lantern Ring";
	private static final String MATERIALS = "shaders/lib/materials/materialHandling/";

	private record Edit(String find, String replace) {
	}

	private static final Map<String, List<Edit>> EDITS = Map.of(
			// Glow on solid ring blocks (lanterns, fonts, the forge), like the pack's modded lights.
			// The sky city's Hope Lamp (19017) glows only in its pane, not its Skystone frame.
			MATERIALS + "terrainIPBR.glsl", List.of(new Edit("", """
					if (mat == 19019) { // Lantern Ring: Blue Lantern, its stone lit as stone and only the glass glowing
					    float glass = smoothstep(0.66, 0.80, color.b) * smoothstep(0.05, 0.15, color.b - color.r);
					    emission = glass * 3.0;
					} else if (mat == 19018) { // Lantern Ring: Hope Inlay, only its blue channels of light glow
					    noSmoothLighting = true; noDirectionalShading = true;
					    emission = smoothstep(0.3, 0.7, color.b - color.r) * 3.0;
					} else if (mat == 19017) { // Lantern Ring: Hope Lamp
					    noSmoothLighting = true; noDirectionalShading = true;
					    float lum = dot(color.rgb, vec3(0.2125, 0.7154, 0.0721));
					    emission = pow(max(lum - 0.62, 0.0) * 2.6, 1.5) * 4.0;
					} else if (mat >= 19000 && mat < 19024) { // Lantern Ring lights
					    noSmoothLighting = true; noDirectionalShading = true;
					    emission = dot(color.rgb, vec3(0.2125, 0.7154, 0.0721)) * 2.5;
					} else
					""")),
			// Glow on the see-through constructs.
			MATERIALS + "translucentIPBR.glsl", List.of(new Edit("", """
					if (mat >= 19000 && mat < 19024) { // Lantern Ring constructs
					    emission = dot(color.rgb, vec3(0.2125, 0.7154, 0.0721)) * 1.6;
					    materialMask = OSIEBCA * 245.0; // Lantern Ring haze (see HAZE)
					} else
					""")),
			// Which light colour slot each ring ID uses.
			"shaders/lib/voxelization/lightVoxelization.glsl", List.of(new Edit("The returning IDs matter. */", """
					The returning IDs matter. */
					        if (mat >= 19000 && mat < 19024) return 85 + (mat - 19000) / 4; // Lantern Ring
					        if (mat == 32002) return 85; // Lantern Ring: green Deluge
					        if (mat == 32003) return 86; // Lantern Ring: Red Deluge""")),
			// The corps colours, in the pack's empty slots.
			"shaders/lib/colors/blocklightColors.glsl", List.of(
					slot(85, "0.5, 1.6, 0.55", "4.0", "green"),
					slot(86, "2.0, 0.25, 0.15", "3.5", "red"),
					slot(87, "1.2, 0.4, 2.0", "3.5", "violet"),
					slot(88, "2.2, 0.9, 0.15", "3.5", "orange"),
					slot(89, "0.3, 0.9, 2.2", "3.5", "blue"),
					slot(90, "1.9, 1.6, 0.3", "3.5", "yellow")),
			"shaders/block.properties", List.of(new Edit(null, """

					# Lantern Ring
					block.19000=%s
					block.19004=%s lanternring:lava_font:filled=true
					block.19008=%s
					block.19012=%s
					block.19016=%s lanternring:sky_light lanternring:hope_crystal
					block.19019=lanternring:power_battery:corps=blue
					block.19017=lanternring:hope_lamp
					block.19018=lanternring:hope_inlay
					block.32002=lanternring:hard_light_liquid
					block.32003=lanternring:ember_liquid
					""".formatted(green(), corps("red"), corps("violet"), corps("orange"), corps("blue").replace(" lanternring:power_battery:corps=blue", "")))),
			"shaders/item.properties", List.of(new Edit(null, """

					# Lantern Ring
					item.44085=lanternring:power_battery lanternring:great_battery lanternring:ring_forge lanternring:power_ring
					item.44086=lanternring:lava_font
					""")),
			// The Red Deluge is the pack's water too, but thick blood (J, 2026-10-12): deep red, opaque
			// whatever the Water Opacity setting (you can't see the bottom), a calm smooth surface and only a
			// faint glow, and no green floor on its tint.
			"shaders/lib/materials/specificMaterials/translucents/water.glsl", List.of(
					new Edit("glColorM.g = max(glColorM.g, 0.39);", "if (mat != 32003) glColorM.g = max(glColorM.g, 0.39);"),
					new Edit(null, """

					if (mat == 32003) { // Lantern Ring: Red Deluge, thick blood
					    color.rgb = vec3(0.30, 0.012, 0.02);
					    color.a = 0.985;
					    emission = max(emission, 0.2);
					    #ifdef GBUFFERS_WATER
					        normalM = normalize(mix(normalM, dot(normalM, normal) < 0.0 ? -normal : normal, 0.75));
					    #endif
					}
					""")),
			// Its surface doesn't bob with Waving Water Height: on uneven levels that made sharp facets.
			"shaders/lib/materials/materialMethods/wavingBlocks.glsl", List.of(new Edit("if (mat == 32000) { // Water",
					"if (mat == 32000 || mat == 32002) { // Water (not the Red Deluge)")),
			"shaders/entity.properties", List.of(new Edit("entity.50048=glow_squid",
					"entity.50048=glow_squid lanternring:warden_construct lanternring:dragon_construct lanternring:sentry_construct")));
	/**
	 * The glow marker ({@link ShaderGlow}) in the hand, entity and particle programs. The vertex
	 * shader spots sky light above vanilla's 240 before the pack clamps it, and passes the block
	 * light on as the glow's strength; the fragment shader turns that into emission (brighter on
	 * brighter pixels, so a gem's core blooms more than its rim). Each file takes all of these or
	 * none: if a pack version doesn't fit, that program is left as it was and the rest still works.
	 */
	private static final List<Edit> GLOW = List.of(
			new Edit("in vec2 lmCoord;", "in vec2 lmCoord;\nflat in float lanternGlow; // Lantern Ring"),
			new Edit("out vec2 lmCoord;", "out vec2 lmCoord;\nflat out float lanternGlow; // Lantern Ring"),
			new Edit("lmCoord  = GetLightMapCoordinates();", """
					lmCoord  = GetLightMapCoordinates();
					    // Lantern Ring: its glow comes with sky light past vanilla's 240; block light is how strong.
					    lanternGlow = (gl_TextureMatrix[1] * gl_MultiTexCoord1).y * 256.0 - 8.0 > 243.5 ? max(lmCoord.x, 0.05) : 0.0;"""),
			new Edit("DoLighting(color, shadowMult,", """
					if (lanternGlow > 0.0) { // Lantern Ring glow
					        emission = max(emission, 2.6 * lanternGlow * sqrt(max(dot(color.rgb, vec3(0.2125, 0.7154, 0.0721)), 0.0)));
					        #ifdef GBUFFERS_ENTITIES_TRANSLUCENT
					            materialMask = OSIEBCA * 245.0; // Lantern Ring haze (see HAZE)
					        #endif
					    }
					    DoLighting(color, shadowMult,"""));
	/**
	 * A held ring's corps colour, which the mod hands Iris as the ring's held-light colour
	 * (PowerRingItem#getLightColor, uniform heldBlockLightColor). With it: the held ring lights the
	 * world in its corps colour, and bloom and fog take a little of that colour while you hold it.
	 * Everything that uses it checks LANTERN_RING_TINT, so a pack where the uniforms edit doesn't fit
	 * just goes without.
	 */
	private static final List<Edit> TINT_UNIFORMS = List.of(new Edit(null, """

			// Lantern Ring: a held ring's corps colour comes as its held light colour.
			#ifndef LANTERN_RING_TINT
			#define LANTERN_RING_TINT
			uniform vec3 heldBlockLightColor;
			uniform vec3 heldBlockLightColor2;
			vec3 LanternCorpsColor() {
			    if (heldItemId == 44085 && heldBlockLightValue > 0 && dot(heldBlockLightColor, vec3(1.0)) > 0.01) return normalize(heldBlockLightColor);
			    if (heldItemId2 == 44085 && heldBlockLightValue2 > 0 && dot(heldBlockLightColor2, vec3(1.0)) > 0.01) return normalize(heldBlockLightColor2);
			    return vec3(0.0);
			}
			vec3 LanternTint(vec3 c, float amount) {
			    vec3 corps = LanternCorpsColor();
			    if (corps == vec3(0.0)) return c;
			    return mix(c, corps * length(c), amount);
			}
			#endif
			"""));
	private static final List<Edit> HELD_LIGHT = List.of(new Edit("    vec3 playerPosLightM = playerPos + relativeEyePosition;", """
			    #ifdef LANTERN_RING_TINT // Lantern Ring: a held ring lights things in its corps colour, as bright as the green slot
			        if (heldItemId == 44085 && dot(heldBlockLightColor, vec3(1.0)) > 0.01) heldLightCol = normalize(heldBlockLightColor) * max(length(heldLightCol), 0.3);
			        if (heldItemId2 == 44085 && dot(heldBlockLightColor2, vec3(1.0)) > 0.01) heldLightCol2 = normalize(heldBlockLightColor2) * max(length(heldLightCol2), 0.3);
			    #endif
			    vec3 playerPosLightM = playerPos + relativeEyePosition;"""));
	private static final List<Edit> BLOOM_TINT = List.of(new Edit(
			"vec3 blur = (blur1 + blur2 + blur3 + blur4 + blur5 + blur6 + blur7) * 0.14;", """
			vec3 blur = (blur1 + blur2 + blur3 + blur4 + blur5 + blur6 + blur7) * 0.14;
			        #ifdef LANTERN_RING_TINT
			            blur = LanternTint(blur, 0.3); // Lantern Ring: bloom takes the corps colour
			        #endif"""));
	private static final List<Edit> FOG_TINT = List.of(new Edit("color = mix(color, vec4(fogColorM, 0.0), fog);", """
			#ifdef LANTERN_RING_TINT
			                fogColorM = LanternTint(fogColorM, 0.12); // Lantern Ring: fog takes a little of the corps colour
			            #endif
			            color = mix(color, vec4(fogColorM, 0.0), fog);"""));
	/**
	 * Energy haze: the constructs and the mod's see-through glow (materialMask 245, an unused value)
	 * shimmer what's behind them, like heat. It rides on the pack's water refraction pass, so it
	 * shows at the pack's High detail and up.
	 */
	private static final List<Edit> HAZE = List.of(
			new Edit("vec2 DoRefraction(", """
					vec2 LanternHaze(inout vec3 color, inout float z0, inout float z1, vec3 viewPos, float lViewPos) { // Lantern Ring
					    vec3 hazePos = ViewToPlayer(viewPos) + cameraPosition;
					    vec2 haze = texture2DLod(noisetex, hazePos.xz * 0.05 + hazePos.y * 0.07 + vec2(0.0, frameTimeCounter * 0.09), 0.0).rb - vec2(0.5);
					    haze *= 0.03 * gbufferProjection[1][1] / (2.0 + lViewPos);
					    haze *= clamp(GetApproxDistance(z1) - GetApproxDistance(z0), 0.0, 1.0);
					    vec2 hazeCoord = texCoord.xy + haze;
					    if (int(texture2D(colortex6, hazeCoord).g * 255.1) != 245) return texCoord.xy;
					    color = texture2D(colortex0, hazeCoord).rgb;
					    z0 = texture2D(depthtex0, hazeCoord).r;
					    z1 = texture2D(depthtex1, hazeCoord).r;
					    return hazeCoord;
					}

					vec2 DoRefraction("""),
			new Edit("    if (int(texelFetch(colortex6, texelCoord, 0).g * 255.1) != 241) return texCoord.xy;", """
					    if (int(texelFetch(colortex6, texelCoord, 0).g * 255.1) == 245) return LanternHaze(color, z0, z1, viewPos, lViewPos); // Lantern Ring
					    if (int(texelFetch(colortex6, texelCoord, 0).g * 255.1) != 241) return texCoord.xy;"""));
	/**
	 * Extras that a pack version may not fit: each group of edits goes in whole or not at all, and
	 * the rest of the copy is made either way.
	 */
	private static final Map<String, List<List<Edit>>> EXTRAS = Map.of(
			"shaders/program/gbuffers_hand.glsl", List.of(GLOW),
			"shaders/program/gbuffers_entities.glsl", List.of(GLOW),
			"shaders/program/gbuffers_textured.glsl", List.of(GLOW),
			"shaders/lib/uniforms.glsl", List.of(TINT_UNIFORMS),
			"shaders/lib/lighting/heldLighting.glsl", List.of(HELD_LIGHT),
			"shaders/program/composite5.glsl", List.of(BLOOM_TINT),
			"shaders/lib/atmospherics/fog/mainFog.glsl", List.of(FOG_TINT),
			"shaders/lib/materials/materialMethods/refraction.glsl", List.of(HAZE));
	/** Both Deluges are water everywhere the pack checks for real water. */
	private static final Edit WATER = new Edit("if (mat == 32000)", "if (mat == 32000 || mat == 32002 || mat == 32003)");

	private static volatile String notice;

	private ShaderPackPatcher() {
	}

	private static Edit slot(int slot, String rgb, String strength, String name) {
		return new Edit("if (mat == " + slot + ") return vec4(0.0);",
				"if (mat == " + slot + ") return vec4(vec3(" + rgb + ") * " + strength + ", 0.0); // Lantern Ring " + name);
	}

	private static String corps(String colour) {
		return ("lanternring:light_construct:corps=%1$s lanternring:construct_brick:corps=%1$s lanternring:power_battery:corps=%1$s"
				+ " lanternring:blast_glow:corps=%1$s lanternring:beam_glow:corps=%1$s").formatted(colour);
	}

	private static String green() {
		StringBuilder names = new StringBuilder(corps("green"));
		names.append(" lanternring:ring_forge lanternring:great_battery:filled=true");
		for (String ghost : "stairs slab fence pane wall door trapdoor gate carpet ladder lantern leaves plant".split(" ")) {
			names.append(" lanternring:ghost_").append(ghost);
		}
		return names.toString();
	}

	/** Starts making copies in the background; any news goes to chat on joining a world. */
	static void init() {
		Thread thread = new Thread(ShaderPackPatcher::run, "Lantern Ring shader pack patcher");
		thread.setDaemon(true);
		thread.start();
	}

	static void onJoin() {
		String text = notice;
		if (text == null) return;
		notice = null;
		Minecraft mc = Minecraft.getInstance();
		if (mc.player != null) {
			mc.gui.chatListener().handleSystemMessage(Component.literal("[Lantern Ring] " + text).withStyle(ChatFormatting.GREEN), false);
		}
	}

	private static void run() {
		Path dir = FabricLoader.getInstance().getGameDir().resolve("shaderpacks");
		if (!Files.isDirectory(dir)) return;
		List<String> made = new ArrayList<>();
		try (Stream<Path> packs = Files.list(dir)) {
			for (Path pack : packs.toList()) {
				String name = pack.getFileName().toString();
				String lower = name.toLowerCase(Locale.ROOT);
				if (!lower.startsWith("complementary") || lower.contains("lantern ring")) continue;
				boolean zip = lower.endsWith(".zip");
				if (!zip && !Files.isDirectory(pack)) continue;
				Path out = dir.resolve((zip ? name.substring(0, name.length() - 4) : name) + SUFFIX + ".zip");
				try {
					if (upToDate(pack, out)) continue;
					if (patch(pack, zip, out)) made.add(out.getFileName().toString());
				} catch (IOException | RuntimeException e) {
					LanternRing.LOGGER.warn("Couldn't make a Lantern Ring copy of shader pack {}", name, e);
				}
			}
		} catch (IOException e) {
			LanternRing.LOGGER.warn("Couldn't read the shaderpacks folder", e);
		}
		if (!made.isEmpty()) {
			notice = "Made the shader pack \"" + String.join("\", \"", made)
					+ "\" with each corps' own light colour. Pick it in Video Settings > Shader Packs.";
		}
	}

	private static boolean upToDate(Path pack, Path out) throws IOException {
		if (!Files.exists(out) || Files.getLastModifiedTime(out).compareTo(Files.getLastModifiedTime(pack)) < 0) return false;
		try (FileSystem fs = FileSystems.newFileSystem(out)) {
			Path marker = fs.getPath(MARKER);
			return Files.exists(marker) && Files.readString(marker).strip().equals(VERSION);
		} catch (IOException | RuntimeException e) {
			return false;
		}
	}

	/** Copies the pack into out with the edits; writes nothing if any edit doesn't fit this pack version. */
	private static boolean patch(Path pack, boolean zip, Path out) throws IOException {
		try (FileSystem fs = zip ? FileSystems.newFileSystem(URI.create("jar:" + pack.toUri()), Map.of()) : null) {
			Path root = zip ? fs.getPath("/") : pack;
			List<Path> files;
			try (Stream<Path> walk = Files.walk(root)) {
				files = walk.filter(Files::isRegularFile).toList();
			}
			int waterEdits = 0;
			Map<String, byte[]> changed = new java.util.HashMap<>();
			for (Path file : files) {
				String path = root.relativize(file).toString().replace('\\', '/');
				List<Edit> edits = EDITS.get(path);
				boolean glsl = path.startsWith("shaders/") && path.endsWith(".glsl");
				if (edits == null && !glsl) continue;
				String text = Files.readString(file, StandardCharsets.ISO_8859_1);
				String before = text;
				if (edits != null) {
					for (Edit edit : edits) {
						if (edit.find == null) text = text + edit.replace;
						else if (edit.find.isEmpty()) text = edit.replace + text;
						else if (text.contains(edit.find)) text = text.replace(edit.find, edit.replace);
						else return gaveUp(pack, path + " has no \"" + edit.find + "\"");
					}
				}
				for (List<Edit> group : EXTRAS.getOrDefault(path, List.of())) {
					String extra = text;
					for (Edit edit : group) {
						if (extra == null) break;
						if (edit.find == null) extra = extra + edit.replace;
						else extra = extra.contains(edit.find) ? extra.replace(edit.find, edit.replace) : null;
					}
					if (extra != null) text = extra;
					else LanternRing.LOGGER.warn("A Lantern Ring extra doesn't fit {} in {}; it stays as it was", path, pack.getFileName());
				}
				if (glsl && text.contains(WATER.find)) {
					text = text.replace(WATER.find, WATER.replace);
					waterEdits++;
				}
				if (!text.equals(before)) changed.put(path, text.getBytes(StandardCharsets.ISO_8859_1));
			}
			for (String path : EDITS.keySet()) {
				if (!changed.containsKey(path)) return gaveUp(pack, "it has no " + path);
			}
			if (waterEdits == 0) return gaveUp(pack, "no water checks found");

			Path temp = out.resolveSibling(out.getFileName() + ".tmp");
			try (OutputStream stream = Files.newOutputStream(temp); ZipOutputStream zipOut = new ZipOutputStream(stream)) {
				for (Path file : files) {
					String path = root.relativize(file).toString().replace('\\', '/');
					zipOut.putNextEntry(new ZipEntry(path));
					byte[] data = changed.get(path);
					if (data != null) zipOut.write(data);
					else Files.copy(file, zipOut);
					zipOut.closeEntry();
				}
				zipOut.putNextEntry(new ZipEntry(MARKER));
				zipOut.write(VERSION.getBytes(StandardCharsets.UTF_8));
				zipOut.closeEntry();
			}
			Files.move(temp, out, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
			LanternRing.LOGGER.info("Made Lantern Ring shader pack {}", out.getFileName());
			return true;
		}
	}

	private static boolean gaveUp(Path pack, String why) {
		LanternRing.LOGGER.warn("Didn't make a Lantern Ring copy of {}: {}", pack.getFileName(), why);
		return false;
	}
}
