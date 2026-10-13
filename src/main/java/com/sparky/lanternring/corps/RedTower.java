package com.sparky.lanternring.corps;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.designs.BlockPlan;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.decoration.LeashFenceKnotEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Red Lantern tower (J's C3 "Split claw" from the lead Blender chat, 2026-10-13): where the Red
 * Lanterns live, and where recruited Blue Lanterns lead a raging player (BlueRecruits). The first
 * time a player is enraged by a Red Lantern with no tower in reach, one is marked out a couple of
 * hundred blocks away; it rises when someone comes near enough for its ground to be loaded.
 * <p>
 * The tower and its two steak farms (cows penned on the terraces, smokers and campfires) are J's
 * Blender block plan (data/lanternring/plans/red_tower.plan), standing on a blackstone footing. Round
 * the plinth is a field of posts, one every 16 degrees, 31 to 44 blocks out, each with an enraged
 * monster chained to it (leashed to the post) that lunges at anything that comes in reach and is
 * snapped back by its chain. Emptied posts get a new prisoner after a while.
 */
public final class RedTower {
	public static final String PLAN = "red_tower";
	/** Every chained field mob carries this tag. */
	public static final String CHAINED = "lanternring.chained";
	/** A new tower is marked out this far from the enraged player... */
	private static final int FROM = 180, TO = 260;
	/** ...unless there's one this close already. */
	private static final double REACH = 700;
	/** It rises once someone is this close (its ground is loaded by then). */
	private static final double RISE = 110;
	/** How far round the marked spot it looks for the flattest ground. */
	private static final int SHIFT = 24, CANDIDATES = 16;
	/** The plinth's half-width; the field's posts. */
	private static final int HALF = 29;
	private static final double POST_STEP = 16, POST_IN = 31, POST_OUT = 44;
	/** Blocks set per tick while it rises (21,375 in all: about 9 s). */
	private static final int PER_TICK = 120;
	/** How far a chained mob may roam from its post, how far it notices prey, and how often posts refill. */
	private static final double CHAIN = 5.5, PREY = 9;
	private static final int PULSE = 20, REFILL = 1200;
	private static final int FLAGS = Block.UPDATE_CLIENTS;
	private static final DustParticleOptions RAGE = new DustParticleOptions(0x9A0A0A, 1.4f);
	private static final List<EntityType<? extends Mob>> PRISONERS = List.of(EntityTypes.ZOMBIE, EntityTypes.HUSK,
			EntityTypes.VINDICATOR, EntityTypes.ZOMBIFIED_PIGLIN, EntityTypes.SKELETON, EntityTypes.PILLAGER);

	private RedTower() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(RedTower::tick);
	}

	/** Every tower in this level (marked out or standing). */
	public static List<Site> sites(ServerLevel level) {
		return Collections.unmodifiableList(Data.get(level).sites);
	}

	/** True for a monster chained to a post in a tower's field. */
	public static boolean chained(Mob mob) {
		return mob.entityTags().contains(CHAINED);
	}

	/** A Red Lantern has just enraged this player: mark out a tower within reach if there's none. */
	public static void enraged(ServerPlayer p) {
		ServerLevel level = p.level();
		if (level.dimension() != Level.OVERWORLD) return;
		Data data = Data.get(level);
		for (Site s : data.sites) {
			if (horizontal(s.anchor, p.blockPosition()) < REACH) return;
		}
		RandomSource r = p.getRandom();
		double a = r.nextDouble() * Math.PI * 2, d = FROM + r.nextDouble() * (TO - FROM);
		BlockPos at = BlockPos.containing(p.getX() + Math.cos(a) * d, p.getY(), p.getZ() + Math.sin(a) * d);
		data.sites.add(new Site(at, false, 0, 0L));
		data.setDirty();
	}

	/** Marks out (and starts raising) a tower right here: for tests and commands. */
	public static Site raiseAt(ServerLevel level, BlockPos ground) {
		Data data = Data.get(level);
		Site s = new Site(ground, true, 0, 0L);
		data.sites.add(s);
		data.setDirty();
		return s;
	}

	private static void tick(MinecraftServer server) {
		ServerLevel level = server.overworld();
		Data data = Data.get(level);
		if (data.sites.isEmpty()) return;
		long now = level.getGameTime();
		for (Site s : data.sites) {
			if (!s.settled) {
				if (now % 20 == 0 && someoneNear(level, s.anchor)) settle(level, s);
				if (s.settled) data.setDirty();
				continue;
			}
			if (!level.isLoaded(s.anchor)) continue;
			if (!s.built()) {
				build(level, s);
				data.setDirty();
				if (s.built()) {
					farms(level, s);
					s.refilled = now - REFILL;
				}
			} else {
				if (now - s.refilled >= REFILL) {
					fillPosts(level, s);
					s.refilled = now;
					data.setDirty();
				}
				if (now % PULSE == 0) rage(level, s);
			}
		}
	}

	private static boolean someoneNear(ServerLevel level, BlockPos at) {
		for (ServerPlayer p : level.players()) {
			if (!p.isSpectator() && horizontal(p.blockPosition(), at) < RISE) return true;
		}
		return false;
	}

	/** Picks the flattest dry ground round the marked spot and sets the tower's floor on it. */
	private static void settle(ServerLevel level, Site s) {
		RandomSource r = level.getRandom();
		BlockPos best = null;
		double bestScore = Double.MAX_VALUE;
		for (int i = 0; i < CANDIDATES; i++) {
			int x = s.anchor.getX() + (i == 0 ? 0 : r.nextInt(SHIFT * 2 + 1) - SHIFT);
			int z = s.anchor.getZ() + (i == 0 ? 0 : r.nextInt(SHIFT * 2 + 1) - SHIFT);
			int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE, wet = 0;
			long sum = 0;
			int n = 0;
			for (int dx = -HALF; dx <= HALF; dx += 4) {
				for (int dz = -HALF; dz <= HALF; dz += 4) {
					if (!level.isLoaded(new BlockPos(x + dx, 0, z + dz))) return;
					int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x + dx, z + dz) - 1;
					if (!level.getFluidState(new BlockPos(x + dx, top, z + dz)).isEmpty()) wet++;
					lo = Math.min(lo, top);
					hi = Math.max(hi, top);
					sum += top;
					n++;
				}
			}
			double score = (hi - lo) + wet * 4.0;
			if (score < bestScore) {
				bestScore = score;
				best = new BlockPos(x, (int) Math.round(sum / (double) n) + 1, z);
			}
		}
		if (best == null) return;
		s.anchor = best;
		s.settled = true;
		level.playSound(null, best, SoundEvents.WARDEN_EMERGE, SoundSource.HOSTILE, 6f, 0.6f);
	}

	/** The next blocks, bottom layer first; the floor gets a blackstone footing down to the ground. */
	private static void build(ServerLevel level, Site s) {
		List<BlockPlan.Entry> blocks = BlockPlan.get(PLAN).part(TOWER).blocks();
		int end = Math.min(blocks.size(), s.placed + PER_TICK);
		for (int i = s.placed; i < end; i++) {
			BlockPlan.Entry e = blocks.get(i);
			BlockPos p = s.anchor.offset(e.x(), e.y(), e.z());
			if (e.y() == 0) footing(level, p.below());
			level.setBlock(p, e.state(), FLAGS);
			// Whatever ground was in the rooms above the floor goes.
			if (e.y() == 0) clearAbove(level, p.above(), s.anchor.getY() + 6);
			if (i % 40 == 0) {
				level.sendParticles(RAGE, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 3, 0.5, 0.5, 0.5, 0.0);
			}
		}
		s.placed = end;
		if (s.placed % 2400 < PER_TICK) {
			level.playSound(null, s.anchor, SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.BLOCKS, 4f, 0.5f);
		}
	}

	private static void footing(ServerLevel level, BlockPos from) {
		BlockPos.MutableBlockPos p = from.mutable();
		for (int i = 0; i < 16; i++) {
			BlockState there = level.getBlockState(p);
			if (!there.isAir() && !there.canBeReplaced() && there.getFluidState().isEmpty()) return;
			level.setBlock(p, Blocks.BLACKSTONE.defaultBlockState(), FLAGS);
			p.move(0, -1, 0);
		}
	}

	private static void clearAbove(ServerLevel level, BlockPos from, int toY) {
		for (BlockPos p = from; p.getY() <= toY; p = p.above()) {
			BlockState there = level.getBlockState(p);
			if (!there.isAir() && BlueClearing.natural(there)) level.setBlock(p, Blocks.AIR.defaultBlockState(), FLAGS);
		}
	}

	/** The steak farms on the terraces, and their cows. */
	private static void farms(ServerLevel level, Site s) {
		List<BlockPos> dirt = new ArrayList<>();
		for (BlockPlan.Entry e : BlockPlan.get(PLAN).part(FARMS).blocks()) {
			BlockPos p = s.anchor.offset(e.x(), e.y(), e.z());
			level.setBlock(p, e.state(), FLAGS);
			if (e.state().is(Blocks.COARSE_DIRT)) dirt.add(p);
		}
		dirt.sort(Comparator.comparingInt((BlockPos p) -> p.getY()).reversed());
		int top = dirt.isEmpty() ? 0 : dirt.get(0).getY();
		List<BlockPos> floor = dirt.stream().filter(p -> p.getY() == top && level.getBlockState(p.above()).isAir()).toList();
		RandomSource r = level.getRandom();
		for (int side = -1; side <= 1; side += 2) {
			final int sign = side;
			List<BlockPos> pen = floor.stream().filter(p -> Integer.signum(p.getX() - s.anchor.getX()) == sign).toList();
			for (int i = 0; i < 4 && !pen.isEmpty(); i++) {
				BlockPos p = pen.get(r.nextInt(pen.size())).above();
				var cow = EntityTypes.COW.create(level, EntitySpawnReason.STRUCTURE);
				if (cow == null) continue;
				cow.snapTo(p.getX() + 0.5, p.getY(), p.getZ() + 0.5, r.nextFloat() * 360f, 0f);
				cow.setPersistenceRequired();
				level.addFreshEntity(cow);
			}
		}
	}

	/** Where the field's posts stand: one every 16 degrees, alternately nearer and farther out. */
	public static List<BlockPos> posts(ServerLevel level, Site s) {
		List<BlockPos> out = new ArrayList<>();
		int n = (int) Math.round(360 / POST_STEP);
		for (int i = 0; i < n; i++) {
			double a = Math.toRadians(i * POST_STEP);
			double d = POST_IN + (POST_OUT - POST_IN) * ((i * 7) % 4) / 3.0;
			int x = s.anchor.getX() + (int) Math.round(Math.cos(a) * d), z = s.anchor.getZ() + (int) Math.round(Math.sin(a) * d);
			int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
			out.add(new BlockPos(x, y, z));
		}
		return out;
	}

	/** Every post without a prisoner gets one: a monster in a rage, chained to the post. */
	private static void fillPosts(ServerLevel level, Site s) {
		RandomSource r = level.getRandom();
		List<BlockPos> posts = s.posts == null ? (s.posts = posts(level, s)) : s.posts;
		for (BlockPos base : posts) {
			if (!level.isLoaded(base)) continue;
			BlockPos fence = base.above();
			if (!level.getBlockState(fence).is(Blocks.NETHER_BRICK_FENCE)) {
				level.setBlock(base, Blocks.POLISHED_BLACKSTONE_BRICKS.defaultBlockState(), Block.UPDATE_ALL);
				level.setBlock(fence, Blocks.NETHER_BRICK_FENCE.defaultBlockState(), Block.UPDATE_ALL);
				level.setBlock(fence.above(), Blocks.NETHER_BRICK_FENCE.defaultBlockState(), Block.UPDATE_ALL);
			}
			if (!level.getEntitiesOfClass(Mob.class, new AABB(fence).inflate(CHAIN + 3), m -> m.isAlive() && chained(m)).isEmpty()) continue;
			Mob mob = PRISONERS.get(r.nextInt(PRISONERS.size())).create(level, EntitySpawnReason.STRUCTURE);
			if (mob == null) continue;
			double a = r.nextDouble() * Math.PI * 2;
			mob.snapTo(fence.getX() + 0.5 + Math.cos(a) * 2, base.getY() + 1, fence.getZ() + 0.5 + Math.sin(a) * 2, r.nextFloat() * 360f, 0f);
			mob.addTag(CHAINED);
			mob.setPersistenceRequired();
			mob.addEffect(new MobEffectInstance(ModEffects.RAGE, MobEffectInstance.INFINITE_DURATION, 0, false, false, true));
			level.addFreshEntity(mob);
			mob.setLeashedTo(LeashFenceKnotEntity.getOrCreateKnot(level, fence.above()), true);
		}
	}

	/** The prisoners strain at their chains and go for anything in reach; a chain that came loose is put back. */
	private static void rage(ServerLevel level, Site s) {
		if (s.posts == null) s.posts = posts(level, s);
		Vec3 c = Vec3.atBottomCenterOf(s.anchor);
		AABB field = new AABB(c, c).inflate(POST_OUT + 8, 24, POST_OUT + 8);
		for (Mob mob : level.getEntitiesOfClass(Mob.class, field, m -> m.isAlive() && chained(m))) {
			BlockPos post = nearestPost(s, mob.blockPosition());
			if (post == null) continue;
			BlockPos top = post.above(2);
			if (!mob.isLeashed()) mob.setLeashedTo(LeashFenceKnotEntity.getOrCreateKnot(level, top), true);
			Vec3 anchor = Vec3.atBottomCenterOf(post.above());
			if (mob.position().distanceTo(anchor) > CHAIN * 1.8) mob.teleportTo(anchor.x + 1, anchor.y, anchor.z);
			LivingEntity prey = level.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().inflate(PREY),
					e -> e != mob && e.isAlive() && !(e instanceof Mob m && chained(m)) && !RedRage.red(e)
							&& !(e instanceof net.minecraft.world.entity.player.Player p && (p.isCreative() || p.isSpectator())))
					.stream().min(Comparator.comparingDouble(e -> e.distanceToSqr(mob))).orElse(null);
			if (prey != null && mob.getTarget() != prey) mob.setTarget(prey);
			if (level.getRandom().nextInt(4) == 0) {
				level.sendParticles(RAGE, mob.getX(), mob.getEyeY(), mob.getZ(), 2, 0.2, 0.1, 0.2, 0.0);
			}
		}
	}

	private static @Nullable BlockPos nearestPost(Site s, BlockPos at) {
		BlockPos best = null;
		double bestD = Double.MAX_VALUE;
		for (BlockPos p : s.posts) {
			double d = p.distSqr(at);
			if (d < bestD) {
				bestD = d;
				best = p;
			}
		}
		return best;
	}

	private static double horizontal(BlockPos a, BlockPos b) {
		double dx = a.getX() - b.getX(), dz = a.getZ() - b.getZ();
		return Math.sqrt(dx * dx + dz * dz);
	}

	private static final String TOWER = "C3_claw", FARMS = "farms";

	// ---- saved -------------------------------------------------------------------------------

	/** One tower: where (the plinth's centre at floor level once settled), how far it has risen, and the last refill. */
	public static final class Site {
		BlockPos anchor;
		boolean settled;
		int placed;
		long refilled;
		@Nullable List<BlockPos> posts;

		Site(BlockPos anchor, boolean settled, int placed, long refilled) {
			this.anchor = anchor;
			this.settled = settled;
			this.placed = placed;
			this.refilled = refilled;
		}

		public BlockPos anchor() {
			return anchor;
		}

		public boolean built() {
			return settled && placed >= BlockPlan.get(PLAN).part(TOWER).blocks().size();
		}

		private static final Codec<Site> CODEC = RecordCodecBuilder.create(i -> i.group(
				BlockPos.CODEC.fieldOf("anchor").forGetter(s -> s.anchor),
				Codec.BOOL.optionalFieldOf("settled", false).forGetter(s -> s.settled),
				Codec.INT.optionalFieldOf("placed", 0).forGetter(s -> s.placed),
				Codec.LONG.optionalFieldOf("refilled", 0L).forGetter(s -> s.refilled)
		).apply(i, Site::new));
	}

	static final class Data extends SavedData {
		final List<Site> sites = new ArrayList<>();

		private static final Codec<Data> CODEC = RecordCodecBuilder.create(i -> i.group(
				Site.CODEC.listOf().optionalFieldOf("sites", List.of()).forGetter(d -> d.sites)
		).apply(i, sites -> {
			Data d = new Data();
			d.sites.addAll(sites);
			return d;
		}));

		static final SavedDataType<Data> TYPE = new SavedDataType<>(LanternRing.id("red_towers"), Data::new, CODEC,
				DataFixTypes.SAVED_DATA_COMMAND_STORAGE);

		static Data get(ServerLevel level) {
			return level.getDataStorage().computeIfAbsent(TYPE);
		}
	}
}
