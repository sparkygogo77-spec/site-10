package com.sparky.lanternring.designs;

import com.sparky.lanternring.LanternRing;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.function.Supplier;
import java.util.regex.Pattern;
import java.util.stream.Stream;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Vec3i;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtAccounter;
import net.minecraft.nbt.NbtIo;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

/**
 * The library of builds the Build mode cycles through, and which of them fit a chosen area. Three
 * sources: whole buildings from the game's own structures (village houses for every biome, camps,
 * igloos, outposts, shipwrecks, ruins, fossils...), BuildGen's generated builds in many materials,
 * and structure files the player adds: anything saved with a structure block in the world, or
 * .nbt files dropped in config/lanternring/builds/.
 */
public final class BuildDesigns {
	/** The game's structures that are whole buildings by themselves (not jigsaw pieces). */
	private static final Pattern VANILLA = Pattern.compile(
			"^(village/(plains|desert|savanna|snowy|taiga)/(houses|town_centers)/.*"
					+ "|igloo/top|pillager_outpost/(watchtower|watchtower_overgrown|feature_.*)|shipwreck/.*|end_city/ship"
					+ "|fossil/.*|nether_fossils/.*|ruined_portal/.*|underwater_ruin/.*|desert_well/.*|abandoned_camp/(tent|camp)/.*)$");
	/** The biggest build footprint, a little over the biggest area. */
	private static final int MAX_SIDE = 72;

	/** The chosen area: a set of ground columns, flattened to groundY. */
	public static final class Area {
		public final Set<Long> cols;
		public final int groundY;
		/** From the area toward the bearer: builds face this way. */
		public final Direction toward;
		public final int minX, minZ, maxX, maxZ;
		public final double cx, cz;
		private final int[][] prefix;

		public Area(Set<Long> cols, int groundY, Direction toward) {
			this.cols = cols;
			this.groundY = groundY;
			this.toward = toward;
			int x0 = Integer.MAX_VALUE, z0 = Integer.MAX_VALUE, x1 = Integer.MIN_VALUE, z1 = Integer.MIN_VALUE;
			double sx = 0, sz = 0;
			for (long c : cols) {
				int x = colX(c), z = colZ(c);
				x0 = Math.min(x0, x);
				z0 = Math.min(z0, z);
				x1 = Math.max(x1, x);
				z1 = Math.max(z1, z);
				sx += x;
				sz += z;
			}
			minX = x0;
			minZ = z0;
			maxX = x1;
			maxZ = z1;
			cx = sx / Math.max(1, cols.size());
			cz = sz / Math.max(1, cols.size());
			int w = maxX - minX + 1, d = maxZ - minZ + 1;
			prefix = new int[w + 1][d + 1];
			for (int x = 0; x < w; x++) {
				for (int z = 0; z < d; z++) {
					prefix[x + 1][z + 1] = prefix[x][z + 1] + prefix[x + 1][z] - prefix[x][z] + (has(minX + x, minZ + z) ? 1 : 0);
				}
			}
		}

		public boolean has(int x, int z) {
			return cols.contains(col(x, z));
		}

		public int width() {
			return maxX - minX + 1;
		}

		public int depth() {
			return maxZ - minZ + 1;
		}

		/** Whether a w by d rectangle with its low corner at (x, z) lies wholly in the area. */
		boolean fits(int x, int z, int w, int d) {
			int ax = x - minX, az = z - minZ;
			if (ax < 0 || az < 0 || ax + w > width() || az + d > depth()) return false;
			int n = prefix[ax + w][az + d] - prefix[ax][az + d] - prefix[ax + w][az] + prefix[ax][az];
			return n == w * d;
		}

		/** The low corner of the w by d spot nearest the middle of the area, or null if it doesn't fit. */
		int[] spot(int w, int d) {
			int[] best = null;
			double bestDist = Double.MAX_VALUE;
			for (int x = minX; x + w - 1 <= maxX; x++) {
				for (int z = minZ; z + d - 1 <= maxZ; z++) {
					double dist = Math.pow(x + (w - 1) / 2.0 - cx, 2) + Math.pow(z + (d - 1) / 2.0 - cz, 2);
					if (dist < bestDist && fits(x, z, w, d)) {
						bestDist = dist;
						best = new int[] {x, z};
					}
				}
			}
			return best;
		}

		/** The biggest square that fits anywhere in the area. */
		int biggestSquare() {
			int lo = 0, hi = Math.min(width(), depth());
			while (lo < hi) {
				int mid = (lo + hi + 1) / 2;
				if (spot(mid, mid) != null) lo = mid;
				else hi = mid - 1;
			}
			return lo;
		}
	}

	public static long col(int x, int z) {
		return ((long) x << 32) | (z & 0xFFFFFFFFL);
	}

	public static int colX(long c) {
		return (int) (c >> 32);
	}

	public static int colZ(long c) {
		return (int) c;
	}

	/** One build in the list: what it is, and where and which way round it goes in the area. */
	public static final class Design {
		public final String name;
		public final String category;
		/** Its materials (a palette or a village biome), or "" if it comes in only one. */
		public final String material;
		private final Supplier<Blueprint> source;
		private Blueprint blueprint;
		/** Its footprint before turning. */
		final int w, d;
		Rotation rotation = Rotation.NONE;
		int x, z;
		double fill;

		Design(String name, String category, String material, int w, int d, Supplier<Blueprint> source) {
			this.name = name;
			this.category = category;
			this.material = material;
			this.w = w;
			this.d = d;
			this.source = source;
		}

		public Blueprint blueprint() {
			if (blueprint == null) blueprint = source.get();
			return blueprint;
		}

		/** Forgets the blocks (they're made again if it's shown again), to keep memory down. */
		public void release() {
			blueprint = null;
		}

		public int footprintW() {
			return rotation == Rotation.CLOCKWISE_90 || rotation == Rotation.COUNTERCLOCKWISE_90 ? d : w;
		}

		public int footprintD() {
			return rotation == Rotation.CLOCKWISE_90 || rotation == Rotation.COUNTERCLOCKWISE_90 ? w : d;
		}

		/** Each block of the build in the world, turned to face the bearer. Air in the bottom layer is left out. */
		public Map<BlockPos, BlockState> place(int groundY) {
			Blueprint b = blueprint();
			Map<BlockPos, BlockState> out = new LinkedHashMap<>();
			for (Map.Entry<Long, BlockState> e : b.blocks.entrySet()) {
				int lx = BlockPos.getX(e.getKey()), ly = BlockPos.getY(e.getKey()), lz = BlockPos.getZ(e.getKey());
				if (ly == 0 && e.getValue().isAir()) continue;
				int rx, rz;
				switch (rotation) {
					case CLOCKWISE_90 -> {
						rx = b.d - 1 - lz;
						rz = lx;
					}
					case CLOCKWISE_180 -> {
						rx = b.w - 1 - lx;
						rz = b.d - 1 - lz;
					}
					case COUNTERCLOCKWISE_90 -> {
						rx = lz;
						rz = b.w - 1 - lx;
					}
					default -> {
						rx = lx;
						rz = lz;
					}
				}
				out.put(new BlockPos(x + rx, groundY + ly, z + rz), e.getValue().rotate(rotation));
			}
			return out;
		}

		public String size() {
			Blueprint b = blueprint;
			return footprintW() + "x" + footprintD() + (b != null ? ", " + b.h + " high" : "");
		}
	}

	/**
	 * One build in the list with all the materials it comes in: scrolling moves between groups,
	 * crouch + scroll between the versions of one.
	 */
	public static final class Group {
		public final List<Design> variants = new ArrayList<>();
		final String rank;
		double fill;

		Group(String rank) {
			this.rank = rank;
		}

		void add(Design d) {
			variants.add(d);
			fill = Math.max(fill, d.fill);
		}
	}

	/**
	 * The order builds come in, best first (my own pick of what looks most impressive raised
	 * from nothing). The player's own builds lead; anything not named goes last.
	 */
	private static final List<String> RANK = List.of("My Builds", "Castle", "Manor", "Skyscraper", "Village House", "Lighthouse",
			"Spire Tower", "Temple", "Pyramid", "Glass Dome", "Arena", "House", "Fort Wall", "Village Square", "Power Battery", "Tower",
			"Outpost", "Farm", "Garden", "Gazebo", "End Ship", "Shipwrecks", "Igloo", "Ruined Portals", "Plaza", "Obelisk", "Wells",
			"Tents", "Campsites", "Ruins", "Fossils");

	private static int rank(String key) {
		int i = RANK.indexOf(key);
		return i < 0 ? RANK.size() : i;
	}

	/** Which way to turn a build so its front (+z) faces {@code toward}. */
	static Rotation facing(Direction toward) {
		return switch (toward) {
			case NORTH -> Rotation.CLOCKWISE_180;
			case WEST -> Rotation.CLOCKWISE_90;
			case EAST -> Rotation.COUNTERCLOCKWISE_90;
			default -> Rotation.NONE;
		};
	}

	// ---- the structure library -------------------------------------------------------------------

	/** group: templates with the same group are one build in different materials (village biomes). */
	private record Template(String name, String category, String group, String material, int w, int h, int d, Supplier<CompoundTag> data) {
	}

	private static List<Template> catalog;
	private static MinecraftServer catalogServer;

	/** Every structure in the library, loaded once per server (the files are only read for their size here). */
	private static synchronized List<Template> catalog(MinecraftServer server) {
		if (catalog != null && catalogServer == server) return catalog;
		List<Template> out = new ArrayList<>();
		var manager = server.getStructureTemplateManager();
		List<Identifier> ids;
		try (Stream<Identifier> stream = manager.listTemplates()) {
			ids = stream.toList();
		} catch (RuntimeException e) {
			LanternRing.LOGGER.warn("Couldn't list structures for the Build mode", e);
			ids = List.of();
		}
		for (Identifier id : ids) {
			String path = id.getPath();
			boolean vanilla = id.getNamespace().equals("minecraft") && VANILLA.matcher(path).matches();
			// Saved with a structure block in this world: no folder in the name.
			boolean own = !path.contains("/") && !path.equals("empty");
			if (!vanilla && !own) continue;
			try {
				StructureTemplate t = manager.get(id).orElse(null);
				if (t == null) continue;
				Vec3i size = t.getSize();
				if (size.getX() < 1 || size.getZ() < 1 || size.getX() > MAX_SIDE || size.getZ() > MAX_SIDE) continue;
				String group = own ? "own:" + path : groupOf(path);
				out.add(new Template(nice(own ? path : strip(last(path))), own ? "My Builds" : category(path), group, own ? "" : materialOf(path),
						size.getX(), size.getY(), size.getZ(), () -> t.save(new CompoundTag())));
			} catch (RuntimeException e) {
				LanternRing.LOGGER.debug("Skipping structure {}", id, e);
			}
		}
		// Files dropped in config/lanternring/builds/.
		Path dir = FabricLoader.getInstance().getConfigDir().resolve("lanternring").resolve("builds");
		try {
			Files.createDirectories(dir);
			try (Stream<Path> files = Files.walk(dir)) {
				for (Path file : files.filter(f -> f.toString().endsWith(".nbt")).toList()) {
					try {
						CompoundTag tag = NbtIo.readCompressed(file, NbtAccounter.unlimitedHeap());
						CompoundTag fixed = DataFixTypes.STRUCTURE.updateToCurrentVersion(server.getFixerUpper(), tag, NbtUtils.getDataVersion(tag, 500));
						ListTag size = fixed.getListOrEmpty("size");
						int w = size.getIntOr(0, 0), h = size.getIntOr(1, 0), d = size.getIntOr(2, 0);
						if (w < 1 || d < 1 || w > MAX_SIDE || d > MAX_SIDE) continue;
						String name = file.getFileName().toString().replaceAll("\\.nbt$", "");
						out.add(new Template(nice(name), "My Builds", "file:" + file, "", w, h, d, () -> fixed));
					} catch (IOException | RuntimeException e) {
						LanternRing.LOGGER.warn("Couldn't read build {}", file, e);
					}
				}
			}
		} catch (IOException e) {
			LanternRing.LOGGER.warn("Couldn't read {}", dir, e);
		}
		LanternRing.LOGGER.info("Build mode library: {} structures", out.size());
		catalog = out;
		catalogServer = server;
		return out;
	}

	/** Sends the library to be read again next time (after a /reload or new files). */
	public static synchronized void forget() {
		catalog = null;
		catalogServer = null;
	}

	private static final Pattern BIOME = Pattern.compile("(plains|desert|savanna|snowy|taiga)_");

	/** A village building's name without its biome, so the biomes' versions of it group together. */
	private static String strip(String name) {
		return BIOME.matcher(name).replaceAll("").replaceAll("_degraded$", "");
	}

	private static String groupOf(String path) {
		String[] parts = path.split("/");
		if (parts[0].equals("village")) return "village/" + parts[2] + "/" + strip(last(path));
		if (parts[0].equals("shipwreck")) return "shipwreck/" + strip(last(path));
		return path;
	}

	private static String materialOf(String path) {
		String[] parts = path.split("/");
		if (parts[0].equals("village")) return nice(parts[1]);
		if (parts[0].equals("shipwreck")) return path.endsWith("_degraded") ? "Weathered" : "Intact";
		return "";
	}

	/** Where a build's category sits in RANK. */
	private static String rankKey(String category) {
		if (category.endsWith("Village Square")) return "Village Square";
		if (category.endsWith("Village")) return "Village House";
		return category;
	}

	private static String last(String path) {
		return path.substring(path.lastIndexOf('/') + 1);
	}

	static String nice(String name) {
		StringBuilder out = new StringBuilder();
		for (String word : name.replace('-', '_').split("_")) {
			if (word.isEmpty()) continue;
			if (!out.isEmpty()) out.append(' ');
			out.append(Character.toUpperCase(word.charAt(0))).append(word.substring(1));
		}
		return out.toString();
	}

	private static String category(String path) {
		String[] parts = path.split("/");
		return switch (parts[0]) {
			case "village" -> nice(parts[1]) + (parts[2].equals("town_centers") ? " Village Square" : " Village");
			case "abandoned_camp" -> parts[1].equals("tent") ? "Tents" : "Campsites";
			case "shipwreck" -> "Shipwrecks";
			case "fossil", "nether_fossils" -> "Fossils";
			case "ruined_portal" -> "Ruined Portals";
			case "underwater_ruin" -> "Ruins";
			case "igloo" -> "Igloo";
			case "pillager_outpost" -> "Outpost";
			case "end_city" -> "End Ship";
			case "desert_well" -> "Wells";
			default -> nice(parts[0]);
		};
	}

	/** A structure's blocks as a blueprint. Jigsaw and structure blocks become air. */
	private static Blueprint fromTemplate(Template t) {
		CompoundTag tag = t.data().get();
		Blueprint b = new Blueprint(t.w(), t.d());
		ListTag palette = tag.getListOrEmpty("palette");
		if (palette.size() == 0) {
			ListTag palettes = tag.getListOrEmpty("palettes");
			if (palettes.size() > 0) palette = palettes.getListOrEmpty(0);
		}
		List<BlockState> states = new ArrayList<>();
		for (int i = 0; i < palette.size(); i++) {
			BlockState s = NbtUtils.readBlockState(BuiltInRegistries.BLOCK, palette.getCompoundOrEmpty(i));
			if (s.is(Blocks.JIGSAW) || s.is(Blocks.STRUCTURE_BLOCK)) s = Blocks.AIR.defaultBlockState();
			states.add(s);
		}
		ListTag blocks = tag.getListOrEmpty("blocks");
		for (int i = 0; i < blocks.size(); i++) {
			CompoundTag block = blocks.getCompoundOrEmpty(i);
			ListTag pos = block.getListOrEmpty("pos");
			int si = block.getIntOr("state", -1);
			if (si < 0 || si >= states.size()) continue;
			BlockState s = states.get(si);
			if (s.is(Blocks.STRUCTURE_VOID)) continue;
			b.set(pos.getIntOr(0, 0), pos.getIntOr(1, 0), pos.getIntOr(2, 0), s);
		}
		b.h = Math.max(b.h, t.h());
		return b;
	}

	// ---- builds that follow the area's own shape ------------------------------------------------

	/** Distance in steps from each column to the nearest column outside the area (0 = the rim). */
	private static Map<Long, Integer> rim(Area a) {
		Map<Long, Integer> dist = new HashMap<>();
		ArrayDeque<Long> queue = new ArrayDeque<>();
		for (long c : a.cols) {
			int x = colX(c), z = colZ(c);
			if (!a.has(x + 1, z) || !a.has(x - 1, z) || !a.has(x, z + 1) || !a.has(x, z - 1)) {
				dist.put(c, 0);
				queue.add(c);
			}
		}
		while (!queue.isEmpty()) {
			long c = queue.poll();
			int x = colX(c), z = colZ(c), n = dist.get(c) + 1;
			for (long next : new long[] {col(x + 1, z), col(x - 1, z), col(x, z + 1), col(x, z - 1)}) {
				if (a.cols.contains(next) && !dist.containsKey(next)) {
					dist.put(next, n);
					queue.add(next);
				}
			}
		}
		return dist;
	}

	/** True for rim columns close to the front of the area (where gates go). */
	private static Set<Long> gate(Area a, Map<Long, Integer> rim, int width) {
		double best = -Double.MAX_VALUE;
		long front = 0;
		for (Map.Entry<Long, Integer> e : rim.entrySet()) {
			if (e.getValue() != 0) continue;
			double dot = (colX(e.getKey()) - a.cx) * a.toward.getStepX() + (colZ(e.getKey()) - a.cz) * a.toward.getStepZ();
			if (dot > best) {
				best = dot;
				front = e.getKey();
			}
		}
		Set<Long> out = new java.util.HashSet<>();
		for (long c : a.cols) {
			if (Math.abs(colX(c) - colX(front)) <= width && Math.abs(colZ(c) - colZ(front)) <= width && rim.get(c) <= 2) out.add(c);
		}
		return out;
	}

	private interface AreaGen {
		Blueprint make(Area a, Palette p, Random r);
	}

	private static Blueprint fort(Area a, Palette p, Random r) {
		Blueprint b = new Blueprint(a.width(), a.depth());
		Map<Long, Integer> rim = rim(a);
		Set<Long> gate = gate(a, rim, 1);
		int h = 5 + r.nextInt(3);
		for (Map.Entry<Long, Integer> e : rim.entrySet()) {
			int x = colX(e.getKey()) - a.minX, z = colZ(e.getKey()) - a.minZ;
			int dist = e.getValue();
			if (dist > 1) continue;
			if (gate.contains(e.getKey())) {
				b.set(x, 0, z, p.floor());
				for (int y = h - 1; y <= h; y++) b.set(x, y, z, p.wall());
				continue;
			}
			for (int y = 0; y <= h; y++) b.set(x, y, z, (x + z) % 9 == 0 && dist == 0 ? p.frame() : p.wall());
			if (dist == 0 && (x + z) % 2 == 0) b.set(x, h + 1, z, p.wall());
			if (dist == 0 && Math.floorMod(x * 31 + z * 17, 23) == 0) b.set(x, h + 2, z, p.light());
		}
		return b;
	}

	private static Blueprint garden(Area a, Palette p, Random r) {
		Blueprint b = new Blueprint(a.width(), a.depth());
		Map<Long, Integer> rim = rim(a);
		Set<Long> gate = gate(a, rim, 1);
		Block[][] trees = {{Blocks.OAK_LOG, Blocks.OAK_LEAVES}, {Blocks.BIRCH_LOG, Blocks.BIRCH_LEAVES}, {Blocks.CHERRY_LOG, Blocks.CHERRY_LEAVES},
				{Blocks.OAK_LOG, Blocks.AZALEA_LEAVES}, {Blocks.SPRUCE_LOG, Blocks.SPRUCE_LEAVES}};
		Block[] tree = trees[r.nextInt(trees.length)];
		Block[] flowers = {Blocks.POPPY, Blocks.DANDELION, Blocks.CORNFLOWER, Blocks.ALLIUM, Blocks.OXEYE_DAISY, Blocks.AZURE_BLUET,
				Blocks.RED_TULIP, Blocks.ORANGE_TULIP, Blocks.WHITE_TULIP, Blocks.PINK_TULIP, Blocks.LILY_OF_THE_VALLEY, Blocks.SHORT_GRASS};
		int px = (int) Math.round(a.cx) - a.minX, pz = (int) Math.round(a.cz) - a.minZ;
		double pond = Math.max(1.5, Math.min(a.width(), a.depth()) / 7.0);
		BlockState hedge = Blocks.OAK_LEAVES.defaultBlockState().setValue(BlockStateProperties.PERSISTENT, true);
		List<int[]> treeSpots = new ArrayList<>();
		for (Map.Entry<Long, Integer> e : rim.entrySet()) {
			int x = colX(e.getKey()) - a.minX, z = colZ(e.getKey()) - a.minZ;
			int dist = e.getValue();
			boolean path = x == px || z == pz || gate.contains(e.getKey()) && dist <= 1;
			double fromMiddle = Math.hypot(x - px, z - pz);
			if (fromMiddle <= pond) {
				b.set(x, 0, z, Blocks.WATER.defaultBlockState());
				continue;
			}
			if (fromMiddle <= pond + 1) {
				b.set(x, 0, z, Blocks.STONE_BRICKS.defaultBlockState());
				continue;
			}
			if (path) {
				b.set(x, 0, z, Blocks.DIRT_PATH.defaultBlockState());
				continue;
			}
			b.set(x, 0, z, Blocks.GRASS_BLOCK.defaultBlockState());
			if (dist == 0) {
				b.set(x, 1, z, hedge);
				b.set(x, 2, z, hedge);
			} else if (dist >= 3 && Math.floorMod(x * 7 + z * 13, 41) == 0) {
				treeSpots.add(new int[] {x, z});
			} else if (r.nextFloat() < 0.22f) {
				b.set(x, 1, z, flowers[r.nextInt(flowers.length)].defaultBlockState());
			}
		}
		for (int[] t : treeSpots) BuildGen.tree(b, t[0], 1, t[1], tree[0], tree[1], r);
		return b;
	}

	private static Blueprint plaza(Area a, Palette p, Random r) {
		Blueprint b = new Blueprint(a.width(), a.depth());
		Map<Long, Integer> rim = rim(a);
		int px = (int) Math.round(a.cx) - a.minX, pz = (int) Math.round(a.cz) - a.minZ;
		int pattern = r.nextInt(3);
		for (Map.Entry<Long, Integer> e : rim.entrySet()) {
			int x = colX(e.getKey()) - a.minX, z = colZ(e.getKey()) - a.minZ;
			int dist = e.getValue();
			double fromMiddle = Math.hypot(x - px, z - pz);
			boolean alt = switch (pattern) {
				case 0 -> ((int) fromMiddle) % 3 == 0;
				case 1 -> (x + z) % 2 == 0;
				default -> (x / 2 + z / 2) % 2 == 0;
			};
			b.set(x, 0, z, dist == 0 ? p.base() : alt ? p.wall() : p.floor());
			if (dist == 0 && Math.floorMod(x * 31 + z * 17, 11) == 0) {
				for (int y = 1; y <= 3; y++) b.set(x, y, z, p.fence());
				b.set(x, 4, z, p.light());
			}
			if (fromMiddle <= 3.4 && fromMiddle > 2.4) b.set(x, 1, z, p.wall());
			else if (fromMiddle <= 2.4) b.set(x, 1, z, Blocks.WATER.defaultBlockState());
		}
		for (int y = 1; y <= 3; y++) b.set(px, y, pz, p.frame());
		b.set(px, 4, pz, BuildGen.lamp(p));
		return b;
	}

	private static Blueprint farm(Area a, Palette p, Random r) {
		Blueprint b = new Blueprint(a.width(), a.depth());
		Map<Long, Integer> rim = rim(a);
		Set<Long> gate = gate(a, rim, 1);
		Block[] crops = {Blocks.WHEAT, Blocks.CARROTS, Blocks.POTATOES, Blocks.BEETROOTS};
		int offset = r.nextInt(5);
		for (Map.Entry<Long, Integer> e : rim.entrySet()) {
			int x = colX(e.getKey()) - a.minX, z = colZ(e.getKey()) - a.minZ;
			int dist = e.getValue();
			if (dist == 0) {
				b.set(x, 0, z, Blocks.GRASS_BLOCK.defaultBlockState());
				if (!gate.contains(e.getKey())) b.set(x, 1, z, p.fence());
				continue;
			}
			if (dist == 1) {
				b.set(x, 0, z, Blocks.DIRT_PATH.defaultBlockState());
				continue;
			}
			int row = Math.floorMod(z + offset, 5);
			if (row == 2) {
				b.set(x, 0, z, Blocks.WATER.defaultBlockState());
				continue;
			}
			b.set(x, 0, z, Blocks.FARMLAND.defaultBlockState().setValue(BlockStateProperties.MOISTURE, 7));
			Block crop = crops[Math.floorMod((z + offset) / 5, crops.length)];
			BlockState plant = crop.defaultBlockState();
			if (plant.hasProperty(BlockStateProperties.AGE_7)) plant = plant.setValue(BlockStateProperties.AGE_7, 7);
			else if (plant.hasProperty(BlockStateProperties.AGE_3)) plant = plant.setValue(BlockStateProperties.AGE_3, 3);
			b.set(x, 1, z, plant);
		}
		return b;
	}

	// ---- the list for an area -------------------------------------------------------------------

	/**
	 * Every build that fits the area, turned to face the bearer, each with the materials it comes
	 * in, in the order scrolling shows them: the biggest of each kind in RANK order, then the next
	 * size of each, and so on.
	 */
	public static List<Group> forArea(MinecraftServer server, Area area, long seed) {
		Rotation rot = facing(area.toward);
		Map<String, Group> groups = new LinkedHashMap<>();
		Random rng = new Random(seed);
		double areaSize = area.cols.size();

		// Generated builds at a few sizes up to the biggest square that fits; one group per size.
		int square = area.biggestSquare();
		for (BuildGen.Kind kind : BuildGen.KINDS) {
			List<Integer> sizes = new ArrayList<>();
			for (double scale : new double[] {1.0, 0.8, 0.6, 0.45}) {
				int w = Math.min(kind.max(), (int) Math.floor(square * scale));
				if (w < kind.min()) continue;
				int d = Math.max(kind.min(), (int) Math.round(w * kind.aspect()));
				// Turned sideways the footprint swaps; shrink until it fits.
				while (w >= kind.min()) {
					d = Math.max(Math.min(kind.min(), w), (int) Math.round(w * kind.aspect()));
					boolean side = rot == Rotation.CLOCKWISE_90 || rot == Rotation.COUNTERCLOCKWISE_90;
					if (area.spot(side ? d : w, side ? w : d) != null) break;
					w--;
				}
				if (w >= kind.min() && !sizes.contains(w)) sizes.add(w);
			}
			for (int w : sizes) {
				int d = Math.max(Math.min(kind.min(), w), (int) Math.round(w * kind.aspect()));
				// The kind's first palette is its best look, so it's the one shown first.
				for (Palette p : kind.palettes()) {
					long s = rng.nextLong();
					int fw = w, fd = d;
					Design design = new Design(p.name() + " " + kind.name(), kind.name(), p.name(), fw, fd,
							() -> kind.gen().make(fw, fd, p, new Random(s)));
					if (place(design, area, rot, areaSize)) groups.computeIfAbsent(kind.name() + "/" + w, k -> new Group(kind.name())).add(design);
				}
			}
		}

		// The game's buildings and the player's own.
		for (Template t : catalog(server)) {
			Design design = new Design(t.name(), t.category(), t.material(), t.w(), t.d(), () -> fromTemplate(t));
			if (place(design, area, rot, areaSize)) groups.computeIfAbsent(t.group(), k -> new Group(rankKey(t.category()))).add(design);
		}

		// Builds that follow the area's own outline.
		addShaped(groups, area, "Fort Wall", Palette.MASONRY, BuildDesigns::fort, rng);
		addShaped(groups, area, "Garden", List.of(Palette.OAK, Palette.BIRCH, Palette.CHERRY), BuildDesigns::garden, rng);
		addShaped(groups, area, "Plaza", Palette.MASONRY, BuildDesigns::plaza, rng);
		addShaped(groups, area, "Farm", List.of(Palette.OAK, Palette.SPRUCE, Palette.DARK_OAK), BuildDesigns::farm, rng);

		// Within a kind, the ones that fill the area best first; kinds take turns in RANK order.
		Map<String, List<Group>> byRank = new LinkedHashMap<>();
		for (Group g : groups.values()) byRank.computeIfAbsent(g.rank, k -> new ArrayList<>()).add(g);
		List<List<Group>> lists = new ArrayList<>(byRank.values());
		for (List<Group> list : lists) list.sort(Comparator.comparingDouble((Group g) -> -g.fill));
		lists.sort(Comparator.comparingInt((List<Group> l) -> rank(l.get(0).rank)).thenComparingDouble(l -> -l.get(0).fill));
		List<Group> out = new ArrayList<>();
		for (int i = 0; ; i++) {
			boolean any = false;
			for (List<Group> list : lists) {
				if (i < list.size()) {
					out.add(list.get(i));
					any = true;
				}
			}
			if (!any) break;
		}
		return out;
	}

	private static void addShaped(Map<String, Group> groups, Area area, String name, List<Palette> palettes, AreaGen gen, Random rng) {
		if (area.cols.size() < 20) return;
		for (Palette p : palettes) {
			long s = rng.nextLong();
			Design design = new Design(p.name() + " " + name, name, p.name(), area.width(), area.depth(), () -> gen.make(area, p, new Random(s)));
			design.x = area.minX;
			design.z = area.minZ;
			// Shown after the first round of buildings.
			design.fill = 0.3;
			groups.computeIfAbsent("shaped/" + name, k -> new Group(name)).add(design);
		}
	}

	/** Finds the design a spot in the area, turned to face the bearer (or sideways if only that fits). */
	private static boolean place(Design design, Area area, Rotation rot, double areaSize) {
		Rotation[] tries = {rot, rot.getRotated(Rotation.CLOCKWISE_90), rot.getRotated(Rotation.COUNTERCLOCKWISE_90)};
		for (Rotation r : tries) {
			design.rotation = r;
			int[] spot = area.spot(design.footprintW(), design.footprintD());
			if (spot != null) {
				design.x = spot[0];
				design.z = spot[1];
				design.fill = design.w * (double) design.d / areaSize;
				return true;
			}
			// Square footprints look the same sideways: no point trying.
			if (design.w == design.d) return false;
		}
		return false;
	}

}
