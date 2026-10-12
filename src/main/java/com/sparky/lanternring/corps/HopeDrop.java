package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.city.CityBlocks;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * The Blue Lantern's aerial drop (J, 2026-10-12): a big container or dome of blue hard light drops
 * from not far up (lower than the other corps' drops), lands, shows for a moment as hard-light glass
 * and bars in the construct colours, then sets from the bottom up into Hope Bricks (a dark polished
 * blue brick, the dome's bricks 1.25x denser), Hope Brick Walls and blue glass. It stays: a shelter,
 * or a prison.
 * <ul>
 * <li>Aimed at the ground: a dome, {@link #DOME} blocks round, with a window band and a door facing
 * whoever dropped it.</li>
 * <li>Aimed at a mob: a container comes down round it, a box with barred sides (brick-wall posts with
 * blue glass between) and a brick roof.</li>
 * </ul>
 * Blue villagers drop containers on Red raiders who land in their village (see {@link #villagers}).
 */
public final class HopeDrop {
	/** 15% of a full ring. */
	public static final int COST = 150;
	public static final int DOME = 6, CAGE = 3, CAGE_HEIGHT = 6;
	/** How far above its spot it drops from: lower than the other aerials. */
	static final int HEIGHT = 14;
	private static final int FLAGS = Block.UPDATE_ALL;

	enum Role { BRICK, POST, WINDOW }

	enum Stage { FALL, LIGHT, SET }

	private static final class Drop {
		final ServerLevel level;
		final BlockPos anchor;
		final Map<BlockPos, Role> plan;
		/** The plan in setting order: bottom up, then from the middle out. */
		final List<BlockPos> order;
		final List<Display.BlockDisplay> bodies = new ArrayList<>();
		final List<BlockPos> bodyAt = new ArrayList<>();
		Stage stage = Stage.FALL;
		long stageStart;
		int set;

		Drop(ServerLevel level, BlockPos anchor, Map<BlockPos, Role> plan) {
			this.level = level;
			this.anchor = anchor;
			this.plan = plan;
			this.order = new ArrayList<>(plan.keySet());
			order.sort(Comparator.<BlockPos>comparingInt(BlockPos::getY).thenComparingDouble(p -> p.distSqr(anchor)));
			this.stageStart = level.getGameTime();
		}
	}

	private static final List<Drop> DROPS = new ArrayList<>();
	/** When each Blue villager may next drop one. */
	private static final Map<UUID, Long> VILLAGER_NEXT = new HashMap<>();
	private static final DustParticleOptions BLUE = new DustParticleOptions(0x3AA8FF, 1.2f);

	private HopeDrop() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(HopeDrop::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			// Set whatever is still hard light, so nothing is left half-formed.
			for (Drop d : DROPS) {
				clearBodies(d);
				for (BlockPos p : d.order) setOne(d, p, false);
			}
			DROPS.clear();
			VILLAGER_NEXT.clear();
		});
	}

	// ---- shapes ---------------------------------------------------------------------------------------

	/** A dome over {@code anchor} (on the ground), its door facing {@code toward}. */
	static Map<BlockPos, Role> dome(BlockPos anchor, Vec3 toward) {
		Map<BlockPos, Role> m = new LinkedHashMap<>();
		Vec3 door = toward.subtract(Vec3.atBottomCenterOf(anchor)).multiply(1, 0, 1);
		door = door.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : door.normalize();
		int r = DOME;
		for (int x = -r - 1; x <= r + 1; x++) {
			for (int z = -r - 1; z <= r + 1; z++) {
				for (int y = 0; y <= r + 1; y++) {
					double d = Math.sqrt(x * x + y * y + z * z);
					if (d > r + 0.4 || d <= r - 0.75) continue;
					// The door: two high, one wide, facing whoever dropped it.
					double along = x * door.x + z * door.z, across = Math.abs(x * door.z - z * door.x);
					if (y <= 1 && along > 0 && across < 0.8) continue;
					int bucket = (int) Math.floor((Math.atan2(z, x) + Math.PI) / (Math.PI * 2) * 18);
					boolean window = (y == 2 || y == 3) && bucket % 3 != 0;
					m.put(anchor.offset(x, y, z), window ? Role.WINDOW : Role.BRICK);
				}
			}
		}
		return m;
	}

	/** A container round {@code anchor} (the caught mob's feet): barred sides, brick corners, base and roof. */
	static Map<BlockPos, Role> cage(BlockPos anchor) {
		Map<BlockPos, Role> m = new LinkedHashMap<>();
		int c = CAGE;
		for (int x = -c; x <= c; x++) {
			for (int z = -c; z <= c; z++) {
				boolean edgeX = Math.abs(x) == c, edgeZ = Math.abs(z) == c;
				for (int y = 0; y <= CAGE_HEIGHT; y++) {
					if (y == CAGE_HEIGHT) {
						m.put(anchor.offset(x, y, z), Role.BRICK);
						continue;
					}
					if (!edgeX && !edgeZ) continue;
					if ((edgeX && edgeZ) || y == 0 || y == CAGE_HEIGHT - 1) {
						m.put(anchor.offset(x, y, z), Role.BRICK);
						continue;
					}
					int along = edgeX ? z : x;
					m.put(anchor.offset(x, y, z), Math.floorMod(along, 2) == 0 ? Role.POST : Role.WINDOW);
				}
			}
		}
		return m;
	}

	private static boolean fillable(BlockState s) {
		return s.isAir() || s.canBeReplaced() || s.getBlock() instanceof LiquidBlock || s.is(ModRegistry.LIGHT_CONSTRUCT);
	}

	private static BlockState light(Role role) {
		return ModRegistry.LIGHT_CONSTRUCT.defaultBlockState().setValue(Corps.PROPERTY, Corps.BLUE)
				.setValue(LightConstructBlock.RIM, role != Role.BRICK);
	}

	private static BlockState finished(Role role) {
		return switch (role) {
			case BRICK -> CityBlocks.HOPE_BRICKS.defaultBlockState();
			case POST -> CityBlocks.HOPE_BRICK_WALL.defaultBlockState();
			case WINDOW -> Blocks.STAINED_GLASS_PANE.blue().defaultBlockState();
		};
	}

	// ---- dropping one -----------------------------------------------------------------------------

	/**
	 * Drops a container round {@code mark} (when {@code cage}) or a dome over it, dropped by {@code by}.
	 * Returns false, with a note to a player, if too much is in the way.
	 */
	public static boolean drop(ServerLevel level, Entity by, BlockPos mark, boolean cage) {
		Map<BlockPos, Role> plan = cage ? cage(mark) : dome(mark, by.position());
		int blocked = 0;
		for (BlockPos p : plan.keySet()) {
			if (!fillable(level.getBlockState(p))) blocked++;
		}
		if (blocked > plan.size() / 4) {
			if (by instanceof ServerPlayer player) {
				player.sendOverlayMessage(Component.translatable("message.lanternring.hope_drop_blocked").withStyle(ChatFormatting.AQUA));
			}
			return false;
		}
		for (Drop d : DROPS) {
			if (d.level == level && d.anchor.distSqr(mark) < 4) return false;
		}
		Drop d = new Drop(level, mark, plan);
		for (Map.Entry<BlockPos, Role> e : plan.entrySet()) {
			Display.BlockDisplay body = EntityTypes.BLOCK_DISPLAY.create(level, EntitySpawnReason.TRIGGERED);
			if (body == null) continue;
			body.setBlockState(light(e.getValue()));
			body.setBrightnessOverride(new Brightness(13, 15));
			body.setPosRotInterpolationDuration(2);
			BlockPos p = e.getKey();
			body.setPos(p.getX(), p.getY() + HEIGHT, p.getZ());
			level.addFreshEntity(body);
			d.bodies.add(body);
			d.bodyAt.add(p);
		}
		DROPS.add(d);
		level.playSound(null, mark.above(HEIGHT), SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 2f, 1.2f);
		level.playSound(null, mark.above(HEIGHT), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 2f, 0.8f);
		return true;
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Drop> it = DROPS.iterator(); it.hasNext(); ) {
			if (step(it.next())) it.remove();
		}
		if (server.getTickCount() % 20 == 10) {
			for (ServerLevel level : server.getAllLevels()) villagers(level);
		}
	}

	/** One tick of a drop. Returns true once it has all set. */
	private static boolean step(Drop d) {
		ServerLevel level = d.level;
		long t = level.getGameTime() - d.stageStart;
		switch (d.stage) {
			case FALL -> {
				int fall = Math.max(1, RingTuning.HOPE_DROP_FALL.ticks());
				double k = Math.min(1.0, (t + 1) / (double) fall);
				double up = HEIGHT * (1 - k * k);
				for (int i = 0; i < d.bodies.size(); i++) {
					BlockPos p = d.bodyAt.get(i);
					d.bodies.get(i).setPos(p.getX(), p.getY() + up, p.getZ());
				}
				if (k >= 1) {
					clearBodies(d);
					for (Map.Entry<BlockPos, Role> e : d.plan.entrySet()) {
						if (fillable(level.getBlockState(e.getKey()))) level.setBlock(e.getKey(), light(e.getValue()), Block.UPDATE_CLIENTS);
					}
					Vec3 c = Vec3.atBottomCenterOf(d.anchor);
					level.playSound(null, d.anchor, SoundEvents.ANVIL_LAND, SoundSource.BLOCKS, 2f, 0.6f);
					level.playSound(null, d.anchor, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 2f, 1.3f);
					level.sendParticles(ModParticles.of(ModParticles.SHARD, Corps.BLUE), c.x, c.y + 0.3, c.z, 60, DOME * 0.6, 0.2, DOME * 0.6, 0.15);
					d.stage = Stage.LIGHT;
					d.stageStart = level.getGameTime();
				}
			}
			case LIGHT -> {
				if (t % 4 == 0) {
					BlockPos p = d.order.get(level.getRandom().nextInt(d.order.size()));
					level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 3, 0.4, 0.4, 0.4, 0.01);
				}
				if (t >= RingTuning.HOPE_DROP_LIGHT.ticks()) {
					d.stage = Stage.SET;
					d.stageStart = level.getGameTime();
				}
			}
			case SET -> {
				int total = Math.max(1, RingTuning.HOPE_DROP_SET.ticks());
				int to = (int) Math.min(d.order.size(), Math.ceil(d.order.size() * (t + 1) / (double) total));
				while (d.set < to) setOne(d, d.order.get(d.set++), true);
				if (t % 5 == 0) level.playSound(null, d.order.get(Math.max(0, d.set - 1)), SoundEvents.DEEPSLATE_BRICKS_PLACE, SoundSource.BLOCKS, 1f, 0.8f);
				return d.set >= d.order.size();
			}
		}
		return false;
	}

	/** Sets one block of the drop into its finished block, if it's still hard light (or air it left). */
	private static void setOne(Drop d, BlockPos p, boolean fx) {
		BlockState there = d.level.getBlockState(p);
		if (!there.is(ModRegistry.LIGHT_CONSTRUCT) && !(there.isAir() || there.canBeReplaced())) return;
		BlockState want = Block.updateFromNeighbourShapes(finished(d.plan.get(p)), d.level, p);
		d.level.setBlock(p, want, FLAGS);
		if (fx && d.level.getRandom().nextInt(3) == 0) {
			d.level.sendParticles(BLUE, p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 2, 0.4, 0.4, 0.4, 0.01);
		}
	}

	private static void clearBodies(Drop d) {
		for (Entity e : d.bodies) e.discard();
		d.bodies.clear();
		d.bodyAt.clear();
	}

	// ---- Blue villagers ------------------------------------------------------------------------------

	/** Blue villagers drop a container on any Red raider standing on the ground near them. */
	static void villagers(ServerLevel level) {
		List<? extends SkyRaider> raiders = level.getEntities(CorpsMobs.SKY_RAIDER, r -> r.isAlive() && r.onGround());
		if (raiders.isEmpty()) return;
		long now = level.getGameTime();
		for (SkyRaider raider : raiders) {
			if (caught(level, raider)) continue;
			for (CorpsVillager blue : level.getEntitiesOfClass(CorpsVillager.class, raider.getBoundingBox().inflate(32),
					v -> v.isAlive() && v.corps() == Corps.BLUE && !v.isBaby())) {
				if (VILLAGER_NEXT.getOrDefault(blue.getUUID(), 0L) > now) continue;
				if (drop(level, blue, raider.blockPosition(), true)) {
					VILLAGER_NEXT.put(blue.getUUID(), now + RingTuning.HOPE_DROP_VILLAGER.ticks());
					blue.getLookControl().setLookAt(raider);
					break;
				}
			}
		}
	}

	/** Whether a drop is already coming down on (or has set round) this mob. */
	private static boolean caught(ServerLevel level, LivingEntity mob) {
		for (Drop d : DROPS) {
			if (d.level == level && d.anchor.distSqr(mob.blockPosition()) <= CAGE * CAGE) return true;
		}
		BlockPos above = mob.blockPosition().above(CAGE_HEIGHT);
		return level.getBlockState(above).is(CityBlocks.HOPE_BRICKS);
	}
}
