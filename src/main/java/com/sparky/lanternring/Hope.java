package com.sparky.lanternring;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.sparky.lanternring.designs.Blueprint;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Random;
import java.util.UUID;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.ProblemReporter;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.BonemealSource;
import net.minecraft.world.level.block.BonemealableBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.GrassBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.TagValueInput;
import net.minecraft.world.level.storage.TagValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Blue Lantern's powers of hope. Everything here runs on the server.
 * <ul>
 * <li><b>Renew</b>: a wave of blue light heals every friendly thing near you and regrows the land
 * (grass on bare dirt, flowers, crops ripen, saplings grow, dead coral comes back).
 * <li><b>Restore</b>: brings the last villager or tamed pet that died near you back to life (or
 * your own pet, wherever in this world it died).
 * <li><b>Villager Spark</b>: two blue builder villagers appear where you aim and build a house
 * with a bed and a workstation. While they're still blue, the village grows a house at a time
 * (RingTuning.HOPE_GROW) and each new house brings another builder. They fade to normal colours
 * over RingTuning.HOPE_FADE and stop building then.
 * <li><b>Hope Golem</b>: a strong blue iron golem that guards the place for RingTuning.HOPE_GOLEM_LIFETIME.
 * </ul>
 * Blue villagers and golems carry a {@link Mark} (saved and synced); the client tints them blue by it.
 */
public final class Hope {
	/** Who the Blue Lantern made: when, whether it's a Hope Golem, and the village a builder belongs to. */
	public record Mark(long since, boolean golem, BlockPos village) {
		public static final Codec<Mark> CODEC = RecordCodecBuilder.create(i -> i.group(
				Codec.LONG.fieldOf("since").forGetter(Mark::since),
				Codec.BOOL.fieldOf("golem").forGetter(Mark::golem),
				BlockPos.CODEC.fieldOf("village").forGetter(Mark::village)).apply(i, Mark::new));
		public static final StreamCodec<io.netty.buffer.ByteBuf, Mark> STREAM_CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_LONG, Mark::since,
				ByteBufCodecs.BOOL, Mark::golem,
				BlockPos.STREAM_CODEC, Mark::village,
				Mark::new);

		/** How blue it still is: 1 when new, down to 0 once faded (golems stay blue). */
		public float blue(long gameTime) {
			if (golem) return 1f;
			return Math.max(0f, 1f - (gameTime - since) / (float) Math.max(1, RingTuning.HOPE_FADE.ticks()));
		}
	}

	public static final AttachmentType<Mark> MARK = AttachmentRegistry.create(LanternRing.id("hope"),
			b -> b.persistent(Mark.CODEC).syncWith(Mark.STREAM_CODEC, AttachmentSyncPredicate.all()));

	private static final double HEAL_RADIUS = 12;
	private static final int RENEW_RADIUS = 12;
	private static final double RESTORE_NEAR = 48;
	private static final int MAX_DEATHS = 32;
	private static final int VILLAGE_REACH = 64;
	private static final int MAX_HOUSES = 9;
	private static final float GOLEM_HEALTH = 300f;
	private static final float GOLEM_DAMAGE = 30f;

	private Hope() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Hope::tick);
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> remember(entity));
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			Mark mark = entity.getAttached(MARK);
			if (mark == null) return;
			if (!mark.golem() && entity instanceof Villager) village(level, mark.village());
			if (mark.golem() && entity instanceof IronGolem g && !GOLEMS.contains(g)) GOLEMS.add(g);
		});
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			RENEWS.clear();
			JOBS.clear();
			VILLAGES.clear();
			DEATHS.clear();
			GOLEMS.clear();
		});
	}

	private static void tick(MinecraftServer server) {
		RENEWS.removeIf(Renew::step);
		JOBS.removeIf(HouseJob::step);
		if (server.getTickCount() % 20 == 0) {
			for (ServerLevel level : server.getAllLevels()) {
				Map<BlockPos, Long> villages = VILLAGES.get(level.dimension());
				if (villages != null) growVillages(level, villages);
			}
			GOLEMS.removeIf(Hope::golemTick);
		}
	}

	private static void sparkle(ServerLevel level, double x, double y, double z, int count, double spread) {
		level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), x, y, z, count, spread, spread, spread, 0.02);
	}

	private static void fail(Player player, String key) {
		player.sendOverlayMessage(Component.translatable(key).withStyle(ChatFormatting.AQUA));
	}

	// ---- Renew ------------------------------------------------------------------------------

	private static final List<Renew> RENEWS = new ArrayList<>();

	public static boolean renew(ServerLevel level, Player player) {
		AABB area = player.getBoundingBox().inflate(HEAL_RADIUS);
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, area, e -> e.isAlive() && !(e instanceof Enemy))) {
			e.heal(10f);
			e.clearFire();
			e.removeEffect(MobEffects.POISON);
			e.removeEffect(MobEffects.WITHER);
			e.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 1));
			sparkle(level, e.getX(), e.getY() + e.getBbHeight() * 0.6, e.getZ(), 14, 0.4);
		}
		RENEWS.add(new Renew(level, player.blockPosition()));
		RingFx.send(level, Kind.PUSH, RingPowers.handPos(player), player.position());
		level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.5f, 0.8f);
		level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1f, 1.5f);
		return true;
	}

	/** The regrowing wave, running out from where Renew was used. */
	private static final class Renew {
		final ServerLevel level;
		final BlockPos center;
		int age;
		double done = -1;

		Renew(ServerLevel level, BlockPos center) {
			this.level = level;
			this.center = center;
		}

		/** Regrows the next ring of ground; true once it reaches its edge. */
		boolean step() {
			age++;
			double r = Math.min(RENEW_RADIUS, RENEW_RADIUS * age / (double) Math.max(1, RingTuning.RENEW_SPREAD.ticks()));
			for (int dx = -RENEW_RADIUS; dx <= RENEW_RADIUS; dx++) {
				for (int dz = -RENEW_RADIUS; dz <= RENEW_RADIUS; dz++) {
					double d = Math.sqrt(dx * dx + dz * dz);
					if (d <= done || d > r) continue;
					for (int dy = -6; dy <= 6; dy++) regrow(level, center.offset(dx, dy, dz));
				}
			}
			done = r;
			return r >= RENEW_RADIUS;
		}
	}

	private static final Block[] FLOWERS = {Blocks.CORNFLOWER, Blocks.CORNFLOWER, Blocks.BLUE_ORCHID, Blocks.AZURE_BLUET,
			Blocks.DANDELION, Blocks.POPPY, Blocks.OXEYE_DAISY, Blocks.ALLIUM, Blocks.LILY_OF_THE_VALLEY};

	private static void regrow(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		if (state.isAir()) return;
		BlockPos above = pos.above();
		BlockState up = level.getBlockState(above);
		Block block = state.getBlock();
		boolean changed = false;
		if ((block == Blocks.DIRT || block == Blocks.COARSE_DIRT || block == Blocks.ROOTED_DIRT || block == Blocks.PODZOL)
				&& up.isAir()) {
			level.setBlockAndUpdate(pos, Blocks.GRASS_BLOCK.defaultBlockState());
			changed = true;
		} else if (block instanceof GrassBlock && up.isAir()) {
			float roll = level.getRandom().nextFloat();
			if (roll < 0.07f) {
				level.setBlockAndUpdate(above, FLOWERS[level.getRandom().nextInt(FLOWERS.length)].defaultBlockState());
				changed = true;
			} else if (roll < 0.16f) {
				level.setBlockAndUpdate(above, Blocks.SHORT_GRASS.defaultBlockState());
				changed = true;
			}
		} else if (block instanceof CropBlock crop) {
			if (!crop.isMaxAge(state)) {
				level.setBlockAndUpdate(pos, crop.getStateForAge(crop.getMaxAge()));
				changed = true;
			}
		} else if (block == Blocks.DEAD_BUSH) {
			level.setBlockAndUpdate(pos, Blocks.FERN.defaultBlockState());
			changed = true;
		} else if (block instanceof BonemealableBlock grow && !(block instanceof GrassBlock) && (state.is(BlockTags.SAPLINGS)
				|| state.is(BlockTags.CROPS) || block == Blocks.SWEET_BERRY_BUSH || block == Blocks.COCOA)) {
			for (int i = 0; i < 4 && level.getBlockState(pos).getBlock() == block; i++) {
				BlockState now = level.getBlockState(pos);
				if (grow.isValidBonemealTarget(level, pos, now, BonemealSource.INTERACTION)) {
					grow.performBonemeal(level, level.getRandom(), pos, now, BonemealSource.INTERACTION);
				}
			}
			changed = true;
		} else {
			String path = BuiltInRegistries.BLOCK.getKey(block).getPath();
			if (path.startsWith("dead_") && path.contains("coral")) {
				Block alive = BuiltInRegistries.BLOCK.getValue(BuiltInRegistries.BLOCK.getKey(block).withPath(path.substring(5)));
				if (alive != Blocks.AIR) {
					level.setBlockAndUpdate(pos, alive.withPropertiesOf(state));
					changed = true;
				}
			}
		}
		if (changed && level.getRandom().nextInt(3) == 0) sparkle(level, pos.getX() + 0.5, pos.getY() + 1.1, pos.getZ() + 0.5, 2, 0.3);
	}

	// ---- Restore ----------------------------------------------------------------------------

	/** A villager or pet that died, saved as it was. */
	private record Death(EntityType<?> type, CompoundTag data, Vec3 pos, UUID owner) {
	}

	private static final Map<ResourceKey<Level>, Deque<Death>> DEATHS = new HashMap<>();

	private static void remember(LivingEntity entity) {
		if (!(entity.level() instanceof ServerLevel level)) return;
		UUID owner = null;
		if (entity instanceof OwnableEntity pet) {
			if (pet.getOwnerReference() == null) return;
			owner = pet.getOwnerReference().getUUID();
		} else if (!(entity instanceof Villager)) {
			return;
		}
		TagValueOutput out = TagValueOutput.createWithContext(ProblemReporter.DISCARDING, level.registryAccess());
		entity.saveWithoutId(out);
		Deque<Death> deaths = DEATHS.computeIfAbsent(level.dimension(), k -> new ArrayDeque<>());
		deaths.addFirst(new Death(entity.getType(), out.buildResult(), entity.position(), owner));
		while (deaths.size() > MAX_DEATHS) deaths.removeLast();
	}

	public static boolean restore(ServerLevel level, Player player) {
		Deque<Death> deaths = DEATHS.get(level.dimension());
		Death pick = null;
		if (deaths != null) {
			for (Death d : deaths) {
				if (d.pos.distanceTo(player.position()) <= RESTORE_NEAR) {
					pick = d;
					break;
				}
			}
			if (pick == null) {
				for (Death d : deaths) {
					if (player.getUUID().equals(d.owner)) {
						pick = d;
						break;
					}
				}
			}
		}
		if (pick == null) {
			fail(player, "message.lanternring.restore_none");
			return false;
		}
		Optional<Entity> made = EntityType.create(pick.type, TagValueInput.create(ProblemReporter.DISCARDING, level.registryAccess(), pick.data),
				level, EntitySpawnReason.LOAD);
		if (made.isEmpty() || !(made.get() instanceof LivingEntity alive)) {
			deaths.remove(pick);
			fail(player, "message.lanternring.restore_none");
			return false;
		}
		deaths.remove(pick);
		Vec3 at = pick.pos.distanceTo(player.position()) <= RESTORE_NEAR ? pick.pos
				: player.position().add(player.getLookAngle().multiply(1, 0, 1).normalize().scale(2));
		alive.setUUID(UUID.randomUUID());
		alive.snapTo(at.x, at.y, at.z, alive.getYRot(), 0);
		alive.removeAllEffects();
		alive.clearFire();
		alive.deathTime = 0;
		alive.setHealth(alive.getMaxHealth());
		alive.fallDistance = 0;
		if (!level.addFreshEntity(alive)) {
			fail(player, "message.lanternring.restore_none");
			return false;
		}
		alive.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 1));
		for (int i = 0; i < 6; i++) sparkle(level, at.x, at.y + i * 0.4, at.z, 8, 0.35);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), at.add(0, 1, 0));
		level.playSound(null, at.x, at.y, at.z, SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.7f, 1.3f);
		player.sendOverlayMessage(Component.translatable("message.lanternring.restored", alive.getDisplayName()).withStyle(ChatFormatting.AQUA));
		return true;
	}

	// ---- Villager Spark and the blue villages -----------------------------------------------

	/** Each blue village (by its centre) and the game time it may next grow a house. */
	private static final Map<ResourceKey<Level>, Map<BlockPos, Long>> VILLAGES = new HashMap<>();
	private static final List<HouseJob> JOBS = new ArrayList<>();

	private static void village(ServerLevel level, BlockPos center) {
		VILLAGES.computeIfAbsent(level.dimension(), k -> new HashMap<>())
				.putIfAbsent(center.immutable(), level.getGameTime() + RingTuning.HOPE_GROW.ticks());
	}

	public static boolean spark(ServerLevel level, Player player) {
		RingPowers.Target target = RingPowers.trace(level, player, 40);
		if (!target.hitBlock() && target.entity() == null) {
			fail(player, "message.lanternring.spark_aim");
			return false;
		}
		BlockPos aim = BlockPos.containing(target.pos());
		int groundY = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, aim.getX(), aim.getZ());
		BlockPos ground = new BlockPos(aim.getX(), groundY, aim.getZ());

		// Join the nearest blue village, or start one here.
		BlockPos center = null;
		Map<BlockPos, Long> villages = VILLAGES.get(level.dimension());
		if (villages != null) {
			double best = VILLAGE_REACH * VILLAGE_REACH;
			for (BlockPos c : villages.keySet()) {
				double d = c.distSqr(ground);
				if (d < best) {
					best = d;
					center = c;
				}
			}
		}
		boolean fresh = center == null;
		if (fresh) center = ground;
		Plot plot = fresh ? plotAt(level, ground, new Random(level.getRandom().nextLong())) : nextPlot(level, center);
		if (plot == null) {
			fail(player, "message.lanternring.spark_full");
			return false;
		}
		List<UUID> builders = new ArrayList<>();
		for (int i = 0; i < 2; i++) builders.add(spawnBuilder(level, center, Vec3.atBottomCenterOf(plot.front().offset(i * 2 - 1, 0, 2))).getUUID());
		village(level, center);
		JOBS.add(new HouseJob(level, plot, builders, fresh));
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), Vec3.atCenterOf(plot.front().above()));
		level.playSound(null, ground, SoundEvents.VILLAGER_CELEBRATE, SoundSource.NEUTRAL, 1f, 1.2f);
		level.playSound(null, ground, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 1.2f);
		player.sendOverlayMessage(Component.translatable(fresh ? "message.lanternring.spark_new" : "message.lanternring.spark_join")
				.withStyle(ChatFormatting.AQUA));
		return true;
	}

	private static Villager spawnBuilder(ServerLevel level, BlockPos village, Vec3 at) {
		Villager v = EntityTypes.VILLAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
		v.snapTo(at.x, at.y, at.z, level.getRandom().nextFloat() * 360, 0);
		v.setAttached(MARK, new Mark(level.getGameTime(), false, village.immutable()));
		level.addFreshEntity(v);
		for (int i = 0; i < 5; i++) sparkle(level, at.x, at.y + i * 0.4, at.z, 6, 0.3);
		return v;
	}

	/** Where a house goes: its blueprint and the corner its (0, 0, 0) sits on. Its door faces +z. */
	private record Plot(Blueprint blueprint, BlockPos origin) {
		BlockPos front() {
			return origin.offset(blueprint.w / 2, 1, blueprint.d);
		}
	}

	private static Plot plotAt(ServerLevel level, BlockPos center, Random rng) {
		int w = 7 + rng.nextInt(3) * 2;
		// The Blue Lantern's own hard-light designs, set into Hope Quartz (J, 2026-10-12).
		Blueprint bp = com.sparky.lanternring.designs.HopeArchitecture.house(w, rng);
		return new Plot(bp, center.offset(-bp.w / 2, -1, -bp.d / 2));
	}

	/** A free spot for the village's next house, on rings around its centre. */
	private static Plot nextPlot(ServerLevel level, BlockPos center) {
		Random rng = new Random(level.getRandom().nextLong());
		for (int ring = 1; ring <= 3; ring++) {
			int n = ring * 6;
			double dist = 12 + (ring - 1) * 11;
			int start = rng.nextInt(n);
			for (int k = 0; k < n; k++) {
				double a = Math.PI * 2 * (start + k) / n;
				int x = center.getX() + (int) Math.round(Math.cos(a) * dist);
				int z = center.getZ() + (int) Math.round(Math.sin(a) * dist);
				BlockPos g = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
				Plot plot = plotAt(level, g, rng);
				if (free(level, plot)) return plot;
			}
		}
		return null;
	}

	/** Natural ground that's fairly flat, dry and has nothing built on it. */
	private static boolean free(ServerLevel level, Plot plot) {
		int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE;
		Blueprint bp = plot.blueprint();
		for (int x = -1; x <= bp.w; x++) {
			for (int z = -1; z <= bp.d + 2; z++) {
				int gx = plot.origin().getX() + x, gz = plot.origin().getZ() + z;
				int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, gx, gz) - 1;
				lo = Math.min(lo, top);
				hi = Math.max(hi, top);
				BlockState surface = level.getBlockState(new BlockPos(gx, top, gz));
				if (!surface.getFluidState().isEmpty()) return false;
				for (int y = top; y <= top + 4; y++) {
					if (built(level.getBlockState(new BlockPos(gx, y, gz)))) return false;
				}
			}
		}
		return hi - lo <= 4 && Math.abs(lo - plot.origin().getY()) <= 6;
	}

	private static boolean built(BlockState s) {
		return s.is(BlockTags.PLANKS) || s.is(BlockTags.DOORS) || s.is(BlockTags.BEDS) || s.is(BlockTags.WOODEN_STAIRS)
				|| s.is(BlockTags.WOODEN_SLABS) || s.is(BlockTags.FENCES) || s.is(Blocks.COBBLESTONE) || s.is(Blocks.STONE_BRICKS)
				|| s.is(Blocks.GLASS_PANE) || s.is(Blocks.GLASS) || s.is(Blocks.BELL) || s.is(Blocks.DIRT_PATH)
				|| s.is(ModRegistry.LIGHT_CONSTRUCT) || com.sparky.lanternring.city.CityBlocks.isCity(s);
	}

	private static final Block[] WORKSTATIONS = {Blocks.COMPOSTER, Blocks.LECTERN, Blocks.BARREL, Blocks.SMOKER, Blocks.BLAST_FURNACE,
			Blocks.CARTOGRAPHY_TABLE, Blocks.FLETCHING_TABLE, Blocks.LOOM, Blocks.SMITHING_TABLE, Blocks.STONECUTTER,
			Blocks.GRINDSTONE, Blocks.BREWING_STAND, Blocks.CAULDRON};
	private static final Block[] BEDS = {Blocks.BED.blue(), Blocks.BED.lightBlue(), Blocks.BED.cyan(), Blocks.BED.white()};

	/** Builder villagers raising one house, a few blocks a tick, bottom up. */
	private static final class HouseJob {
		final ServerLevel level;
		final Plot plot;
		final List<UUID> builders;
		final boolean first;
		final List<Map.Entry<BlockPos, BlockState>> blocks = new ArrayList<>();
		final int perTick;
		int clearRow = -1;
		int next;
		int age;

		HouseJob(ServerLevel level, Plot plot, List<UUID> builders, boolean first) {
			this.level = level;
			this.plot = plot;
			this.builders = builders;
			this.first = first;
			plot.blueprint().blocks.forEach((key, state) -> blocks.add(Map.entry(plot.origin().offset(BlockPos.of(key)), state)));
			// Bottom up, then row by row, so it rises like it's being built.
			blocks.sort((a, b) -> a.getKey().getY() != b.getKey().getY() ? Integer.compare(a.getKey().getY(), b.getKey().getY())
					: a.getKey().getZ() != b.getKey().getZ() ? Integer.compare(a.getKey().getZ(), b.getKey().getZ())
					: Integer.compare(a.getKey().getX(), b.getKey().getX()));
			perTick = Math.max(1, (int) Math.ceil(blocks.size() / (double) Math.max(1, RingTuning.HOPE_BUILD.ticks())));
		}

		/** True once the house is finished. */
		boolean step() {
			age++;
			Blueprint bp = plot.blueprint();
			BlockPos o = plot.origin();
			// First level the ground: fill under the footprint and clear above it, a row per tick.
			if (clearRow < bp.d + 3) {
				clearRow++;
				int z = clearRow - 1;
				for (int x = -1; x <= bp.w; x++) {
					BlockPos col = o.offset(x, 0, z);
					for (int y = -1; y >= -6; y--) {
						BlockPos p = col.offset(0, y, 0);
						if (level.getBlockState(p).canBeReplaced()) level.setBlock(p, Blocks.DIRT.defaultBlockState(), 2);
					}
					if (level.getBlockState(col).canBeReplaced() || level.getBlockState(col).is(BlockTags.LOGS)
							|| level.getBlockState(col).is(BlockTags.LEAVES)) level.setBlock(col, Blocks.GRASS_BLOCK.defaultBlockState(), 2);
					for (int y = 1; y <= bp.h + 3; y++) {
						BlockPos p = col.offset(0, y, 0);
						BlockState s = level.getBlockState(p);
						if (!s.isAir() && !s.is(Blocks.BEDROCK)) level.setBlock(p, Blocks.AIR.defaultBlockState(), 2);
					}
				}
				return false;
			}
			for (int i = 0; i < perTick && next < blocks.size(); i++, next++) {
				Map.Entry<BlockPos, BlockState> e = blocks.get(next);
				com.sparky.lanternring.city.HardLightSet.form(level, e.getKey(), e.getValue());
				if (next % 4 == 0) sparkle(level, e.getKey().getX() + 0.5, e.getKey().getY() + 0.5, e.getKey().getZ() + 0.5, 2, 0.3);
			}
			if (age % 20 == 0 && next < blocks.size()) {
				BlockPos at = blocks.get(next).getKey();
				for (UUID id : builders) {
					if (level.getEntity(id) instanceof Villager v) {
						v.getBrain().setMemory(MemoryModuleType.WALK_TARGET, new WalkTarget(at, 0.6f, 3));
						sparkle(level, v.getX(), v.getY() + 1.4, v.getZ(), 3, 0.2);
					}
				}
				level.playSound(null, at, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 0.8f, 0.9f + level.getRandom().nextFloat() * 0.3f);
			}
			if (next < blocks.size()) return false;
			furnish();
			return true;
		}

		/** A bed and a workstation inside (so the villagers move in and take jobs), and a bell for the first. */
		private void furnish() {
			Blueprint bp = plot.blueprint();
			BlockPos o = plot.origin();
			List<BlockPos> floor = new ArrayList<>();
			for (int x = 1; x < bp.w - 1; x++) {
				for (int z = 1; z < bp.d - 1; z++) {
					BlockPos p = o.offset(x, 1, z);
					if (level.getBlockState(p).isAir() && level.getBlockState(p.above()).isAir() && !level.getBlockState(p.below()).isAir()) floor.add(p);
				}
			}
			Random rng = new Random(o.asLong());
			boolean bed = false;
			for (BlockPos p : floor) {
				BlockPos head = p.relative(Direction.NORTH);
				if (floor.contains(head) && Math.abs(p.getZ() - plot.front().getZ()) > 2) {
					BlockState foot = BEDS[rng.nextInt(BEDS.length)].defaultBlockState()
							.setValue(BlockStateProperties.HORIZONTAL_FACING, Direction.NORTH);
					level.setBlock(p, foot.setValue(BlockStateProperties.BED_PART, BedPart.FOOT), 3);
					level.setBlock(head, foot.setValue(BlockStateProperties.BED_PART, BedPart.HEAD), 3);
					floor.remove(head);
					floor.remove(p);
					bed = true;
					break;
				}
			}
			for (int i = floor.size() - 1; i >= 0; i--) {
				BlockPos p = floor.get(i);
				if (p.getX() != plot.front().getX()) {
					level.setBlock(p, WORKSTATIONS[rng.nextInt(WORKSTATIONS.length)].defaultBlockState(), 3);
					break;
				}
			}
			if (first) {
				BlockPos bell = plot.front().offset(2, 0, 3);
				int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, bell.getX(), bell.getZ());
				level.setBlock(new BlockPos(bell.getX(), y, bell.getZ()), Blocks.BELL.defaultBlockState(), 3);
			}
			BlockPos f = plot.front();
			for (int i = 0; i < 8; i++) sparkle(level, f.getX() + 0.5, f.getY() + i * 0.5, f.getZ() + 0.5, 6, 0.6);
			level.playSound(null, f, SoundEvents.VILLAGER_CELEBRATE, SoundSource.NEUTRAL, 1f, 1f);
			level.playSound(null, f, SoundEvents.PLAYER_LEVELUP, SoundSource.NEUTRAL, 0.6f, 1.4f);
			if (!bed) LanternRing.LOGGER.debug("Blue house at {} had no room for a bed", o);
		}
	}

	/** Villages whose builders are still blue grow another house (with another builder) every so often. */
	private static void growVillages(ServerLevel level, Map<BlockPos, Long> villages) {
		long now = level.getGameTime();
		Iterator<Map.Entry<BlockPos, Long>> it = villages.entrySet().iterator();
		while (it.hasNext()) {
			Map.Entry<BlockPos, Long> e = it.next();
			if (now < e.getValue()) continue;
			BlockPos center = e.getKey();
			if (!level.isLoaded(center)) continue;
			e.setValue(now + RingTuning.HOPE_GROW.ticks());
			if (JOBS.stream().anyMatch(j -> j.level == level && center.equals(villageOf(j)))) continue;
			List<Villager> builders = level.getEntitiesOfClass(Villager.class, new AABB(center).inflate(VILLAGE_REACH), v -> {
				Mark m = v.getAttached(MARK);
				return m != null && center.equals(m.village()) && m.blue(now) > 0;
			});
			if (builders.isEmpty()) {
				// Everyone has faded (or gone): the village is finished.
				it.remove();
				continue;
			}
			if (houses(level, center) >= MAX_HOUSES) continue;
			Plot plot = nextPlot(level, center);
			if (plot == null) continue;
			List<UUID> ids = new ArrayList<>();
			for (int i = 0; i < Math.min(2, builders.size()); i++) ids.add(builders.get(i).getUUID());
			ids.add(spawnBuilder(level, center, Vec3.atBottomCenterOf(plot.front().offset(0, 0, 2))).getUUID());
			JOBS.add(new HouseJob(level, plot, ids, false));
		}
	}

	private static BlockPos villageOf(HouseJob job) {
		for (UUID id : job.builders) {
			if (job.level.getEntity(id) instanceof Villager v && v.getAttached(MARK) != null) return v.getAttached(MARK).village();
		}
		return null;
	}

	/** Roughly how many houses the village has: its beds, two blocks each. */
	private static int houses(ServerLevel level, BlockPos center) {
		int beds = 0;
		int r = 40;
		for (BlockPos p : BlockPos.betweenClosed(center.offset(-r, -6, -r), center.offset(r, 8, r))) {
			if (level.getBlockState(p).is(BlockTags.BEDS)) beds++;
		}
		return beds / 2;
	}

	// ---- Hope Golem -------------------------------------------------------------------------

	private static final List<IronGolem> GOLEMS = new ArrayList<>();

	public static boolean golem(ServerLevel level, Player player) {
		RingPowers.Target target = RingPowers.trace(level, player, 16);
		Vec3 at = target.hitBlock() ? target.pos() : player.position().add(player.getLookAngle().multiply(1, 0, 1).normalize().scale(3));
		IronGolem g = EntityTypes.IRON_GOLEM.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (g == null) return false;
		g.snapTo(at.x, at.y, at.z, player.getYRot() + 180, 0);
		g.setPlayerCreated(true);
		g.getAttribute(Attributes.MAX_HEALTH).setBaseValue(GOLEM_HEALTH);
		g.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(GOLEM_DAMAGE);
		g.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(0.35);
		g.setHealth(GOLEM_HEALTH);
		g.setCustomName(Component.translatable("entity.lanternring.hope_golem").withStyle(ChatFormatting.AQUA));
		g.setAttached(MARK, new Mark(level.getGameTime(), true, BlockPos.containing(at)));
		level.addFreshEntity(g);
		GOLEMS.add(g);
		for (int i = 0; i < 8; i++) sparkle(level, at.x, at.y + i * 0.4, at.z, 10, 0.6);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), at.add(0, 1.4, 0));
		level.playSound(null, at.x, at.y, at.z, SoundEvents.IRON_GOLEM_REPAIR, SoundSource.PLAYERS, 1f, 0.8f);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.9f);
		return true;
	}

	/** Once a second: heals the golem a little; true when it has faded or is gone. */
	private static boolean golemTick(IronGolem g) {
		if (g.isRemoved() || !g.isAlive()) return true;
		Mark m = g.getAttached(MARK);
		if (m == null) return true;
		if (!(g.level() instanceof ServerLevel level)) return true;
		if (level.getGameTime() - m.since() > RingTuning.HOPE_GOLEM_LIFETIME.ticks()) {
			for (int i = 0; i < 8; i++) sparkle(level, g.getX(), g.getY() + i * 0.35, g.getZ(), 10, 0.6);
			level.playSound(null, g.blockPosition(), SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.NEUTRAL, 1f, 0.8f);
			g.discard();
			return true;
		}
		g.heal(2f);
		if (level.getRandom().nextInt(3) == 0) sparkle(level, g.getX(), g.getY() + 2.2, g.getZ(), 3, 0.5);
		return false;
	}
}
