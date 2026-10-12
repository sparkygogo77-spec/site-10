package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;
import java.util.function.BiFunction;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import com.sparky.lanternring.city.BlueCity;
import com.sparky.lanternring.city.CityData;
import org.jspecify.annotations.Nullable;

/**
 * The Blue Lantern flier highway: once a Blue corps village is floating, its villagers raise a
 * network of sky lanes between the city's districts, marked by glowing hoops to fly through, with a
 * landing pad and perch at every district. Armored diving hawks (see {@link DivingHawk}) hatch on
 * the pads, live along the lanes and are what fliers ride there instead of elytras.
 *
 * <p>The network is planned from the city's anchor alone, so it is the same after a restart:
 * <ul>
 * <li>districts come from {@link #setDistricts} (the city thread plugs in its ports and towers);
 * until then, four ports round the island,</li>
 * <li>lanes join every district to its nearest neighbours (a minimum spanning tree) and the outer
 * districts in a loop, so there is always a way round and a short way across,</li>
 * <li>each lane arches gently and climbs over anything solid in its way,</li>
 * <li>hawks route along it with Dijkstra's shortest path, flying hoop to hoop.</li>
 * </ul>
 */
public final class FlierHighway {
	public static final EntityType<DivingHawk> DIVING_HAWK = register("diving_hawk",
			EntityType.Builder.<DivingHawk>of(DivingHawk::new, MobCategory.MISC).sized(1.4f, 1.3f).eyeHeight(1.35f)
					.passengerAttachments(1.45f).clientTrackingRange(10));
	public static final Item DIVING_HAWK_EGG = egg("diving_hawk_spawn_egg", DIVING_HAWK);
	/** Calls your tamed hawk to you (sold by Blue villagers in a city with flier ports). */
	public static final Item HAWK_WHISTLE = whistle();

	/** Lanes fly this high over the island top, hoops stand this far apart and are this wide. */
	static final int LANE_HEIGHT = 14, HOOP_STEP = 9, HOOP_RADIUS = 3, PORT_RADIUS = 26, PAD_RADIUS = 3;
	/** Lanes stay this far out from a sky city's middle, clear of its towers, except coming in to a pad. */
	static final int CITY_KEEP_OUT = 34;
	/** Hawks living on one highway, at most. */
	static final int HAWKS = 4;

	/** Where a city's districts are, given its anchor (the island top); empty to use the default ports. */
	private static BiFunction<ServerLevel, BlockPos, List<BlockPos>> districts = (level, anchor) -> BlueCity.ports(anchor);
	private static final Map<BlockPos, Network> PLANS = new HashMap<>();
	/** Anchors whose highway is being built right now, by the builder doing it. */
	private static final Map<BlockPos, Builder> BUILDING = new HashMap<>();

	private static <T extends net.minecraft.world.entity.Entity> EntityType<T> register(String name, EntityType.Builder<T> builder) {
		ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
	}

	private static Item whistle() {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LanternRing.id("hawk_whistle"));
		return Registry.register(BuiltInRegistries.ITEM, key, new com.sparky.lanternring.item.HawkWhistleItem(new Item.Properties()
				.stacksTo(1).rarity(net.minecraft.world.item.Rarity.RARE).setId(key)));
	}

	private static Item egg(String name, EntityType<? extends net.minecraft.world.entity.Mob> type) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, new SpawnEggItem(new Item.Properties().spawnEgg(type).setId(key)));
	}

	public static void init() {
		FabricDefaultAttributeRegistry.register(DIVING_HAWK, DivingHawk.createAttributes());
		CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.SPAWN_EGGS).register(output -> output.accept(DIVING_HAWK_EGG));
		CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.TOOLS_AND_UTILITIES).register(output -> output.accept(HAWK_WHISTLE));
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 10 == 0) {
				for (ServerLevel level : server.getAllLevels()) rides(level);
			}
			if (server.getTickCount() % 40 != 0) return;
			for (ServerLevel level : server.getAllLevels()) tick(level);
		});
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			CROUCHING.clear();
			PLANS.clear();
			BUILDING.clear();
		});
	}

	/** The city thread's hook: where the districts of the city anchored at a point are. */
	public static void setDistricts(BiFunction<ServerLevel, BlockPos, List<BlockPos>> source) {
		districts = source;
		PLANS.clear();
	}

	// ---- the plan -------------------------------------------------------------------------------

	/** A district's landing pad: hawks sit on top of {@code perch} (its lamp), riders land round it. */
	public record Pad(BlockPos centre, BlockPos perch) {
	}

	/** A lane between two pads: the points to fly through, from pad a to pad b. */
	public record Lane(int a, int b, List<Vec3> points, double length) {
		List<Vec3> from(int pad) {
			if (pad == a) return points;
			List<Vec3> back = new ArrayList<>(points);
			java.util.Collections.reverse(back);
			return back;
		}
	}

	public static final class Network {
		public final BlockPos anchor;
		public final List<Pad> pads;
		public final List<Lane> lanes;
		/** Whether the highway raises its own pads (false when the city built them, as its ports). */
		public final boolean ownPads;

		Network(BlockPos anchor, List<Pad> pads, List<Lane> lanes, boolean ownPads) {
			this.anchor = anchor;
			this.pads = pads;
			this.lanes = lanes;
			this.ownPads = ownPads;
		}

		public int nearestPad(Vec3 at) {
			int best = 0;
			double bestD = Double.MAX_VALUE;
			for (int i = 0; i < pads.size(); i++) {
				double d = Vec3.atCenterOf(pads.get(i).perch).distanceToSqr(at);
				if (d < bestD) {
					bestD = d;
					best = i;
				}
			}
			return best;
		}

		/**
		 * The shortest way along the lanes from one pad to another (Dijkstra), as the points to fly
		 * through in order, ending over the destination's perch.
		 */
		public List<Vec3> route(int from, int to) {
			int n = pads.size();
			double[] dist = new double[n];
			int[] via = new int[n];
			Arrays.fill(dist, Double.MAX_VALUE);
			Arrays.fill(via, -1);
			dist[from] = 0;
			PriorityQueue<double[]> queue = new PriorityQueue<>((x, y) -> Double.compare(x[0], y[0]));
			queue.add(new double[] {0, from});
			while (!queue.isEmpty()) {
				double[] top = queue.poll();
				int at = (int) top[1];
				if (top[0] > dist[at]) continue;
				for (int i = 0; i < lanes.size(); i++) {
					Lane l = lanes.get(i);
					if (l.a != at && l.b != at) continue;
					int next = l.a == at ? l.b : l.a;
					double d = dist[at] + l.length;
					if (d < dist[next]) {
						dist[next] = d;
						via[next] = i;
						queue.add(new double[] {d, next});
					}
				}
			}
			List<Vec3> path = new ArrayList<>();
			if (from == to || via[to] < 0) {
				path.add(Vec3.atCenterOf(pads.get(to).perch).add(0, 1, 0));
				return path;
			}
			List<Integer> chain = new ArrayList<>();
			for (int at = to; at != from; ) {
				Lane l = lanes.get(via[at]);
				chain.add(0, via[at]);
				at = l.a == at ? l.b : l.a;
			}
			int at = from;
			for (int i : chain) {
				Lane l = lanes.get(i);
				path.addAll(l.from(at));
				at = l.a == at ? l.b : l.a;
			}
			path.add(Vec3.atCenterOf(pads.get(to).perch).add(0, 1, 0));
			return path;
		}
	}

	/** The highway of the city anchored at {@code anchor} (worked out once, then remembered). */
	public static Network network(ServerLevel level, BlockPos anchor) {
		return PLANS.computeIfAbsent(anchor.immutable(), a -> plan(level, a));
	}

	private static Network plan(ServerLevel level, BlockPos anchor) {
		List<BlockPos> spots = new ArrayList<>(districts.apply(level, anchor));
		boolean ownPads = spots.isEmpty();
		if (ownPads) {
			// Four ports round the island, a little higher than it, turned 45 degrees from its
			// houses so lanes cross over the gaps between them.
			for (int i = 0; i < 4; i++) {
				double a = Math.PI / 4 + i * Math.PI / 2;
				spots.add(anchor.offset((int) Math.round(Math.cos(a) * PORT_RADIUS), 6 + 2 * i, (int) Math.round(Math.sin(a) * PORT_RADIUS)));
			}
			// And one over the middle, above the lantern: the hub.
			spots.add(anchor.above(LANE_HEIGHT + 6));
		}
		List<Pad> pads = new ArrayList<>();
		for (BlockPos s : spots) pads.add(new Pad(s, s));
		List<int[]> edges = linkUp(spots, anchor);
		List<Lane> lanes = new ArrayList<>();
		for (int[] e : edges) lanes.add(lane(level, e[0], e[1], pads, anchor, ownPads ? 0 : CITY_KEEP_OUT));
		return new Network(anchor, pads, lanes, ownPads);
	}

	/**
	 * Which districts get a lane: a minimum spanning tree (Prim's) so every district is reachable
	 * the short way, plus a loop through the outer districts in order round the centre, so hawks
	 * can circle the city and there's a second way to everywhere.
	 */
	static List<int[]> linkUp(List<BlockPos> spots, BlockPos centre) {
		int n = spots.size();
		List<int[]> edges = new ArrayList<>();
		if (n < 2) return edges;
		Set<Long> seen = new HashSet<>();
		boolean[] in = new boolean[n];
		double[] best = new double[n];
		int[] link = new int[n];
		Arrays.fill(best, Double.MAX_VALUE);
		best[0] = 0;
		link[0] = -1;
		for (int k = 0; k < n; k++) {
			int u = -1;
			for (int i = 0; i < n; i++) if (!in[i] && (u < 0 || best[i] < best[u])) u = i;
			in[u] = true;
			if (link[u] >= 0) add(edges, seen, link[u], u);
			for (int v = 0; v < n; v++) {
				double d = Math.sqrt(spots.get(u).distSqr(spots.get(v)));
				if (!in[v] && d < best[v]) {
					best[v] = d;
					link[v] = u;
				}
			}
		}
		// The outer loop: districts well away from the centre, in order of their angle round it.
		List<Integer> outer = new ArrayList<>();
		for (int i = 0; i < n; i++) {
			BlockPos p = spots.get(i);
			if (Math.hypot(p.getX() - centre.getX(), p.getZ() - centre.getZ()) > 8) outer.add(i);
		}
		outer.sort((x, y) -> Double.compare(angle(spots.get(x), centre), angle(spots.get(y), centre)));
		if (outer.size() >= 3) {
			for (int i = 0; i < outer.size(); i++) add(edges, seen, outer.get(i), outer.get((i + 1) % outer.size()));
		}
		return edges;
	}

	private static void add(List<int[]> edges, Set<Long> seen, int a, int b) {
		long key = (long) Math.min(a, b) << 32 | Math.max(a, b);
		if (seen.add(key)) edges.add(new int[] {a, b});
	}

	private static double angle(BlockPos p, BlockPos c) {
		return Math.atan2(p.getZ() - c.getZ(), p.getX() - c.getX());
	}

	/**
	 * The points of a lane from pad a to pad b, one per hoop: a gentle arch between the pads that
	 * rises over anything solid in the way (it looks a little ahead and behind too, so it climbs
	 * before a tower, not into it).
	 */
	private static Lane lane(ServerLevel level, int a, int b, List<Pad> pads, BlockPos anchor, int keepOut) {
		Vec3 from = Vec3.atCenterOf(pads.get(a).perch).add(0, 3, 0);
		Vec3 to = Vec3.atCenterOf(pads.get(b).perch).add(0, 3, 0);
		List<Vec3> guide = guide(from, to, Vec3.atCenterOf(anchor), keepOut);
		double length = 0;
		for (int i = 1; i < guide.size(); i++) length += guide.get(i).distanceTo(guide.get(i - 1));
		int steps = Math.max(2, (int) Math.round(length / HOOP_STEP));
		List<Vec3> points = new ArrayList<>();
		for (int i = 1; i < steps; i++) {
			double t = i / (double) steps;
			// No hoop right by a pad, where several lanes meet: the pad marks the spot.
			if (t * length < PAD_RADIUS + 4 || (1 - t) * length < PAD_RADIUS + 4) continue;
			Vec3 p = along(guide, t * length).add(0, Math.sin(t * Math.PI) * Math.min(6, length * 0.08), 0);
			int lift = 0;
			while (lift < 16 && !clear(level, p.add(0, lift, 0))) lift += 2;
			points.add(p.add(0, lift, 0));
		}
		// Smooth out sudden climbs so the lane is flyable.
		for (int pass = 0; pass < 2; pass++) {
			for (int i = 1; i < points.size() - 1; i++) {
				double y = Math.max(points.get(i).y, (points.get(i - 1).y + points.get(i + 1).y) / 2);
				points.set(i, new Vec3(points.get(i).x, y, points.get(i).z));
			}
		}
		double len = 0;
		Vec3 prev = from;
		for (Vec3 p : points) {
			len += p.distanceTo(prev);
			prev = p;
		}
		len += prev.distanceTo(to);
		return new Lane(a, b, points, len);
	}

	/**
	 * The line a lane follows: straight from pad to pad, unless that would cut through the city
	 * (closer than {@code keepOut} to its middle). Then it heads straight out from the pad, swings
	 * round the city just outside that radius the short way, and comes straight in to the other pad.
	 */
	static List<Vec3> guide(Vec3 from, Vec3 to, Vec3 centre, int keepOut) {
		List<Vec3> out = new ArrayList<>();
		out.add(from);
		if (keepOut > 0 && closest(from, to, centre) < keepOut) {
			double r = keepOut + 2;
			double a0 = Math.atan2(from.z - centre.z, from.x - centre.x);
			double a1 = Math.atan2(to.z - centre.z, to.x - centre.x);
			double sweep = Mth.wrapDegrees((a1 - a0) * Mth.RAD_TO_DEG) * Mth.DEG_TO_RAD;
			int n = Math.max(2, (int) Math.ceil(Math.abs(sweep) * r / 3));
			for (int i = 0; i <= n; i++) {
				double t = i / (double) n;
				double ang = a0 + sweep * t;
				out.add(new Vec3(centre.x + Math.cos(ang) * r, Mth.lerp(t, from.y, to.y), centre.z + Math.sin(ang) * r));
			}
		}
		out.add(to);
		return out;
	}

	/** How close a straight line between two points passes to a point, across the ground. */
	private static double closest(Vec3 a, Vec3 b, Vec3 c) {
		double dx = b.x - a.x, dz = b.z - a.z;
		double len2 = dx * dx + dz * dz;
		double t = len2 < 1e-6 ? 0 : Mth.clamp(((c.x - a.x) * dx + (c.z - a.z) * dz) / len2, 0, 1);
		return Math.hypot(a.x + dx * t - c.x, a.z + dz * t - c.z);
	}

	/** The point a distance {@code d} along a polyline. */
	private static Vec3 along(List<Vec3> line, double d) {
		for (int i = 1; i < line.size(); i++) {
			double seg = line.get(i).distanceTo(line.get(i - 1));
			if (d <= seg || i == line.size() - 1) return line.get(i - 1).lerp(line.get(i), seg < 1e-6 ? 0 : Math.min(1, d / seg));
			d -= seg;
		}
		return line.getLast();
	}

	/** Whether a hoop's worth of air (and a hawk) fits round a point. */
	private static boolean clear(ServerLevel level, Vec3 p) {
		BlockPos c = BlockPos.containing(p);
		for (int dx = -HOOP_RADIUS; dx <= HOOP_RADIUS; dx += HOOP_RADIUS) {
			for (int dy = -HOOP_RADIUS; dy <= HOOP_RADIUS; dy += HOOP_RADIUS) {
				for (int dz = -HOOP_RADIUS; dz <= HOOP_RADIUS; dz += HOOP_RADIUS) {
					if (!level.getBlockState(c.offset(dx, dy, dz)).getCollisionShape(level, c).isEmpty()) return false;
				}
			}
		}
		return true;
	}

	// ---- the blocks -----------------------------------------------------------------------------

	private static final BlockState HOOP = Blocks.STAINED_GLASS.lightBlue().defaultBlockState();
	private static final BlockState HOOP_LIGHT = Blocks.SEA_LANTERN.defaultBlockState();
	private static final BlockState PAD = Blocks.PRISMARINE_BRICKS.defaultBlockState();
	private static final BlockState PAD_RIM = Blocks.DARK_PRISMARINE.defaultBlockState();
	private static final BlockState PAD_LIGHT = Blocks.SEA_LANTERN.defaultBlockState();

	/** A ring of glass standing across the lane at a point, with lights at its four quarters. */
	static Map<BlockPos, BlockState> hoop(Vec3 at, Vec3 along) {
		Map<BlockPos, BlockState> out = new LinkedHashMap<>();
		Vec3 dir = along.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : along.normalize();
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		if (side.lengthSqr() < 1e-6) side = new Vec3(1, 0, 0);
		side = side.normalize();
		Vec3 up = side.cross(dir).normalize();
		if (up.y < 0) up = up.scale(-1);
		int steps = 40;
		for (int i = 0; i < steps; i++) {
			double a = i * Math.PI * 2 / steps;
			Vec3 p = at.add(side.scale(Math.cos(a) * HOOP_RADIUS)).add(up.scale(Math.sin(a) * HOOP_RADIUS));
			boolean light = i % (steps / 4) == 0;
			BlockPos pos = BlockPos.containing(p);
			if (light || !out.containsKey(pos)) out.put(pos, light ? HOOP_LIGHT : HOOP);
		}
		return out;
	}

	/** A round floating landing pad with a lit rim and a lamp in the middle, where the hawk sits. */
	static Map<BlockPos, BlockState> pad(Pad pad) {
		Map<BlockPos, BlockState> out = new LinkedHashMap<>();
		BlockPos c = pad.centre;
		for (int dx = -PAD_RADIUS; dx <= PAD_RADIUS; dx++) {
			for (int dz = -PAD_RADIUS; dz <= PAD_RADIUS; dz++) {
				double d = Math.sqrt(dx * dx + dz * dz);
				if (d > PAD_RADIUS + 0.4) continue;
				boolean rim = d > PAD_RADIUS - 0.6;
				out.put(c.offset(dx, 0, dz), rim ? (Math.abs(dx) == 0 || Math.abs(dz) == 0 ? PAD_LIGHT : PAD_RIM) : PAD);
				if (d < PAD_RADIUS - 1) out.put(c.offset(dx, -1, dz), PAD_RIM);
			}
		}
		out.put(c, PAD_LIGHT);
		return out;
	}

	/** Whether the highway of a city is standing: the lights of its first hoop are there. */
	public static boolean built(ServerLevel level, Network net) {
		if (net.lanes.isEmpty() || net.lanes.getFirst().points.isEmpty()) return true;
		Map<BlockPos, BlockState> first = laneBlocks(net, net.lanes.getFirst(), 1);
		for (Map.Entry<BlockPos, BlockState> e : first.entrySet()) {
			if (e.getValue() == HOOP_LIGHT && !level.getBlockState(e.getKey()).is(Blocks.SEA_LANTERN)) return false;
		}
		return true;
	}

	/** The hoops of a lane (the first {@code max} of them), each standing square across the lane. */
	static Map<BlockPos, BlockState> laneBlocks(Network net, Lane lane, int max) {
		Map<BlockPos, BlockState> blocks = new LinkedHashMap<>();
		List<Vec3> pts = lane.points;
		Vec3 start = Vec3.atCenterOf(net.pads.get(lane.a).perch).add(0, 3, 0);
		Vec3 end = Vec3.atCenterOf(net.pads.get(lane.b).perch).add(0, 3, 0);
		for (int i = 0; i < Math.min(max, pts.size()); i++) {
			Vec3 before = i == 0 ? start : pts.get(i - 1);
			Vec3 after = i == pts.size() - 1 ? end : pts.get(i + 1);
			blocks.putAll(hoop(pts.get(i), after.subtract(before)));
		}
		return blocks;
	}

	// ---- building it ----------------------------------------------------------------------------

	/** Who is building a highway and which piece is next: pads first, then one lane at a time. */
	private static final class Builder {
		final CorpsVillager villager;
		final Network net;
		int piece;
		SkyBuilds.@Nullable Job job;

		Builder(CorpsVillager villager, Network net) {
			this.villager = villager;
			this.net = net;
		}
	}

	private static void tick(ServerLevel level) {
		// Finished or abandoned builds.
		for (var it = BUILDING.entrySet().iterator(); it.hasNext(); ) {
			Builder b = it.next().getValue();
			if (b.villager.level() != level) continue;
			if (!b.villager.isAlive()) {
				it.remove();
				continue;
			}
			if (SkyBuilds.running(b.job)) {
				Vec3 at = Vec3.atCenterOf(b.job.current());
				b.villager.flyTo(at.add(2, 3, 0), false);
				continue;
			}
			int pads = b.net.ownPads ? b.net.pads.size() : 0;
			if (b.piece < pads) {
				b.job = SkyBuilds.start(level, pad(b.net.pads.get(b.piece)), 60, Corps.BLUE, false, b.villager);
			} else if (b.piece < pads + b.net.lanes.size()) {
				Lane lane = b.net.lanes.get(b.piece - pads);
				Map<BlockPos, BlockState> blocks = laneBlocks(b.net, lane, Integer.MAX_VALUE);
				List<Vec3> pts = lane.points;
				b.job = SkyBuilds.start(level, blocks, 40 + 10 * pts.size(), Corps.BLUE, false, b.villager);
			} else {
				it.remove();
				finish(level, b);
				continue;
			}
			b.piece++;
		}
		if (level.getGameTime() % 200 != 0) return;
		// Once a sky city's flier ports stand, its Blue villagers raise the lanes between them.
		for (CityData.City city : CityData.get(level).all()) {
			BlockPos anchor = city.anchor;
			if (!city.has(BlueCity.Piece.PORTS) || BUILDING.containsKey(anchor) || !level.isLoaded(anchor)) continue;
			Network net = network(level, anchor);
			if (built(level, net)) {
				hatch(level, net);
				continue;
			}
			// Someone free: not out with a building crew (the city crew would keep pulling it back).
			List<CorpsVillager> crew = level.getEntitiesOfClass(CorpsVillager.class, new AABB(anchor).inflate(80),
					v -> v.isAlive() && v.corps() == Corps.BLUE && !v.isBaby() && !v.crewBusy());
			if (crew.isEmpty()) continue;
			crew.sort(java.util.Comparator.comparingDouble(v -> v.distanceToSqr(Vec3.atCenterOf(anchor))));
			BUILDING.put(anchor, new Builder(crew.getFirst(), net));
			announce(level, anchor, Component.translatable("message.lanternring.highway_start"));
		}
	}

	/** Whether this villager is raising a highway right now (crews leave it be). */
	static boolean isBuilding(CorpsVillager v) {
		for (Builder b : BUILDING.values()) {
			if (b.villager == v) return true;
		}
		return false;
	}

	// ---- autopilot: a hawk flies you along the highway ---------------------------------------------

	/** Ticks each player has crouched on a port pad (-1: already asked, waiting for them to stand). */
	private static final Map<java.util.UUID, Integer> CROUCHING = new HashMap<>();
	/** How long to crouch on a pad to call a hawk, and how far a ride to another city may be. */
	static final int CALL_TICKS = 20, CITY_RANGE = 2000;

	/** Players crouching on a port pad call a city hawk to fly them where they're looking. */
	private static void rides(ServerLevel level) {
		for (ServerPlayer p : level.players()) {
			if (!p.isShiftKeyDown() || !p.onGround() || p.isPassenger() || p.isSpectator()) {
				CROUCHING.remove(p.getUUID());
				continue;
			}
			int t = CROUCHING.getOrDefault(p.getUUID(), 0);
			if (t < 0) continue;
			CityData.City city = padCity(level, p);
			if (city == null) {
				CROUCHING.remove(p.getUUID());
				continue;
			}
			t += 10;
			if (t < CALL_TICKS) {
				CROUCHING.put(p.getUUID(), t);
				continue;
			}
			CROUCHING.put(p.getUUID(), -1);
			requestRide(level, p, city);
		}
	}

	/** The city whose port pad the player is standing on, if any. */
	private static CityData.@Nullable City padCity(ServerLevel level, ServerPlayer p) {
		for (CityData.City c : CityData.get(level).all()) {
			if (!c.has(BlueCity.Piece.PORTS)) continue;
			for (BlockPos port : BlueCity.ports(c.anchor)) {
				double dx = p.getX() - (port.getX() + 0.5), dz = p.getZ() - (port.getZ() + 0.5), dy = p.getY() - (port.getY() + 1);
				if (Math.abs(dx) <= 3 && Math.abs(dz) <= 3 && dy > -0.5 && dy < 3) return c;
			}
		}
		return null;
	}

	/**
	 * Sends one of the city's hawks to carry the player, on autopilot, to the port they're looking
	 * toward: another pad of this city, or the nearest pad of another sky city.
	 */
	public static boolean requestRide(ServerLevel level, ServerPlayer p, CityData.City city) {
		Network net = network(level, city.anchor);
		int from = net.nearestPad(p.position());
		Vec3 look = p.getLookAngle().multiply(1, 0, 1);
		look = look.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : look.normalize();
		List<Vec3> route = null;
		Component where = null;
		double best = -2;
		for (int i = 0; i < net.pads.size(); i++) {
			if (i == from) continue;
			double score = facing(look, p.position(), Vec3.atCenterOf(net.pads.get(i).perch));
			if (score > best) {
				best = score;
				route = net.route(from, i);
				where = Component.translatable("message.lanternring.ride_port", direction(city.anchor, net.pads.get(i).perch));
			}
		}
		for (CityData.City other : CityData.get(level).all()) {
			if (other == city || !other.has(BlueCity.Piece.PORTS) || other.anchor.distSqr(city.anchor) > (double) CITY_RANGE * CITY_RANGE) continue;
			BlockPos to = null;
			for (BlockPos port : BlueCity.ports(other.anchor)) {
				if (to == null || port.distSqr(p.blockPosition()) < to.distSqr(p.blockPosition())) to = port;
			}
			// Another city counts a little extra, so looking its way picks it over a pad nearby.
			double score = facing(look, p.position(), Vec3.atCenterOf(to)) + 0.15;
			if (score > best) {
				best = score;
				Vec3 start = Vec3.atCenterOf(net.pads.get(from).perch);
				Vec3 end = Vec3.atCenterOf(to).add(0, 1, 0);
				double cruise = Math.max(start.y, end.y) + 20;
				route = new ArrayList<>(List.of(new Vec3(start.x, cruise, start.z), new Vec3(end.x, cruise, end.z), end));
				where = Component.translatable("message.lanternring.ride_city", to.getX(), to.getZ());
			}
		}
		if (route == null) {
			p.sendOverlayMessage(Component.translatable("message.lanternring.ride_nowhere").withStyle(ChatFormatting.AQUA));
			return false;
		}
		DivingHawk hawk = null;
		double near = 120 * 120;
		for (DivingHawk h : level.getEntitiesOfClass(DivingHawk.class, new AABB(city.anchor).inflate(120), DivingHawk::isAlive)) {
			if (!h.freeForFare() || !city.anchor.equals(h.cityAnchor())) continue;
			double d = h.distanceToSqr(p);
			if (d < near) {
				near = d;
				hawk = h;
			}
		}
		if (hawk == null) {
			p.sendOverlayMessage(Component.translatable("message.lanternring.ride_no_hawk").withStyle(ChatFormatting.AQUA));
			return false;
		}
		hawk.fetch(p, route);
		p.sendOverlayMessage(Component.translatable("message.lanternring.ride_coming", where).withStyle(ChatFormatting.AQUA));
		return true;
	}

	/** How well {@code to} lines up with where the player looks (1 straight ahead, -1 behind). */
	private static double facing(Vec3 look, Vec3 from, Vec3 to) {
		Vec3 d = to.subtract(from).multiply(1, 0, 1);
		return d.lengthSqr() < 1e-4 ? -1 : look.dot(d.normalize());
	}

	private static Component direction(BlockPos anchor, BlockPos pad) {
		int dx = pad.getX() - anchor.getX(), dz = pad.getZ() - anchor.getZ();
		String d = Math.abs(dx) >= Math.abs(dz) ? (dx > 0 ? "east" : "west") : (dz > 0 ? "south" : "north");
		return Component.translatable("direction.lanternring." + d);
	}

	private static void finish(ServerLevel level, Builder b) {
		Pad home = b.net.pads.getFirst();
		b.villager.flyTo(Vec3.atBottomCenterOf(home.perch).add(1.5, 1, 0), true);
		hatch(level, b.net);
		announce(level, b.net.anchor, Component.translatable("message.lanternring.highway_done"));
	}

	/** Hawks hatch on the pads until the highway has its flock. */
	private static void hatch(ServerLevel level, Network net) {
		AABB area = new AABB(net.anchor).inflate(PORT_RADIUS + 48);
		int have = level.getEntitiesOfClass(DivingHawk.class, area, h -> h.isAlive()).size();
		for (int i = 0; have < Math.min(HAWKS, net.pads.size()) && i < net.pads.size(); i++) {
			Pad pad = net.pads.get(i);
			if (!level.getEntitiesOfClass(DivingHawk.class, new AABB(pad.perch).inflate(2)).isEmpty()) continue;
			DivingHawk hawk = DIVING_HAWK.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (hawk == null) return;
			hawk.snapTo(pad.perch.getX() + 0.5, pad.perch.getY() + 1, pad.perch.getZ() + 0.5, level.getRandom().nextFloat() * 360f, 0f);
			hawk.settle(net.anchor, i);
			level.addFreshEntity(hawk);
			CorpsShots.summon(level, hawk.position(), hawk.getBbHeight(), hawk.getBbWidth(), Corps.BLUE);
			level.playSound(null, pad.perch, SoundEvents.PARROT_IMITATE_PHANTOM, SoundSource.NEUTRAL, 1f, 0.6f);
			have++;
		}
	}

	private static void announce(ServerLevel level, BlockPos at, Component text) {
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(Vec3.atCenterOf(at)) < 128 * 128) p.sendSystemMessage(text.copy().withStyle(ChatFormatting.ITALIC, ChatFormatting.AQUA));
		}
	}

	/** Builds a city's highway straight away (tests and the Ring Lab): every piece at once. */
	public static Network buildNow(ServerLevel level, BlockPos anchor) {
		Network net = network(level, anchor);
		if (net.ownPads) for (Pad p : net.pads) place(level, pad(p));
		for (Lane lane : net.lanes) place(level, laneBlocks(net, lane, Integer.MAX_VALUE));
		hatch(level, net);
		return net;
	}

	private static void place(ServerLevel level, Map<BlockPos, BlockState> blocks) {
		blocks.forEach((pos, state) -> {
			if (level.getBlockState(pos).canBeReplaced()) level.setBlock(pos, state, 3);
		});
	}

	private FlierHighway() {
	}
}
