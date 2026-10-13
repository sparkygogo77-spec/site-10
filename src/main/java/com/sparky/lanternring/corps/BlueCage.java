package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.block.LightConstructBlock;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Blue Lantern squad's ground cage (J, 2026-10-13): a monster a flyer has lassoed and slammed
 * into the ground is pinned there by a hard-light press. Four posts rise round it and a heavy
 * plate with a weight on top drops down onto it a block at a time, so it can't get up. A caged
 * monster is no longer a threat (ConstructAlly.isBadMob skips it, so nothing keeps shooting it);
 * the cage holds it until everything round the lantern is safe, when it's lifted into a prison
 * capsule (next step).
 *
 * <p>The cage is construct blocks, re-formed as they fade. The monster is frozen (no AI) and held
 * on its spot. After a restart a caged monster (tagged) gets its cage back where it lies.
 */
public final class BlueCage {
	/** On a caged monster: it's pinned and no threat to anyone. */
	public static final String CAGED = "lanternring.blue_caged";
	/** How high above its resting place the press plate starts, and ticks per block it drops. */
	private static final int DROP_FROM = 4, DROP_TICKS = 3;
	private static final int REPAIR = 100;
	private static final float SLAM_HIT = 6f;
	/** A slammed monster that hasn't landed after this long is caged where it is. */
	private static final int LAND_WAIT = 60;

	static final class Cage {
		final ServerLevel level;
		final Mob mob;
		final Vec3 at;
		final BlockPos floor;
		final int half, height;
		int drop;
		long lastRepair;
		final List<BlockPos> blocks = new ArrayList<>();

		Cage(ServerLevel level, Mob mob) {
			this.level = level;
			this.mob = mob;
			this.at = mob.position();
			this.floor = mob.blockPosition();
			this.half = Mth.ceil(mob.getBbWidth() / 2) + 1;
			this.height = Mth.ceil(mob.getBbHeight()) + 1;
			this.drop = DROP_FROM;
		}
	}

	private record Pending(ServerLevel level, Mob mob, long since) {
	}

	private static final Map<UUID, Cage> CAGES = new HashMap<>();
	private static final List<Pending> SLAMMED = new ArrayList<>();

	private BlueCage() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(BlueCage::tick);
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			CAGES.clear();
			SLAMMED.clear();
		});
		// The slam's fall is taken as the fixed slam hit when it lands (close), never more.
		net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
				!((caged(entity) || BluePrison.prisoner(entity)) && source.is(net.minecraft.tags.DamageTypeTags.IS_FALL)));
		// A monster caged before the game closed gets its cage back.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof Mob mob && mob.entityTags().contains(CAGED) && !CAGES.containsKey(mob.getUUID())) {
				Cage c = new Cage(level, mob);
				c.drop = 0;
				CAGES.put(mob.getUUID(), c);
			}
		});
	}

	public static boolean caged(LivingEntity e) {
		return e.entityTags().contains(CAGED);
	}

	/** Locked in a Blue Lantern prison capsule (BluePrison). */
	public static boolean prisoner(LivingEntity e) {
		return BluePrison.prisoner(e);
	}

	/**
	 * A flyer just slammed this monster down: from now on it's no threat (nobody shoots it), the
	 * fall can't kill it (the slam's own hit is fixed), and it's caged as soon as it lands.
	 */
	static void slammed(ServerLevel level, LivingEntity e) {
		if (!(e instanceof Mob mob) || caged(mob)) return;
		mob.addTag(CAGED);
		SLAMMED.add(new Pending(level, mob, level.getGameTime()));
	}

	/** All the monsters caged round a spot (for the prison to collect). */
	static List<Mob> cagedNear(Vec3 c, double r) {
		List<Mob> out = new ArrayList<>();
		for (Cage cage : CAGES.values()) {
			if (cage.mob.isAlive() && cage.at.distanceToSqr(c) < r * r) out.add(cage.mob);
		}
		return out;
	}

	/** Takes the cage away (the prison collects the monster, or it died): the monster keeps its no-AI hold. */
	static void open(Mob mob) {
		Cage c = CAGES.remove(mob.getUUID());
		if (c != null) clear(c);
	}

	private static void tick(MinecraftServer server) {
		if (!SLAMMED.isEmpty()) {
			for (Iterator<Pending> it = SLAMMED.iterator(); it.hasNext(); ) {
				Pending p = it.next();
				if (!p.mob.isAlive()) {
					it.remove();
					continue;
				}
				boolean landed = !com.sparky.lanternring.Lasso.isCaught(p.mob) && p.mob.onGround();
				if (landed || p.level.getGameTime() - p.since > LAND_WAIT) {
					it.remove();
					close(p.level, p.mob);
				}
			}
		}
		if (CAGES.isEmpty()) return;
		for (Iterator<Cage> it = CAGES.values().iterator(); it.hasNext(); ) {
			Cage c = it.next();
			if (!c.mob.isAlive() || c.mob.isRemoved()) {
				it.remove();
				clear(c);
				continue;
			}
			// Held on its spot.
			if (c.mob.position().distanceToSqr(c.at) > 0.04) c.mob.teleportTo(c.at.x, c.at.y, c.at.z);
			c.mob.setDeltaMovement(Vec3.ZERO);
			long now = c.level.getGameTime();
			if (c.drop > 0 && now % DROP_TICKS == 0) {
				c.drop--;
				build(c);
				if (c.drop == 0) thud(c);
			} else if (now - c.lastRepair >= REPAIR) {
				build(c);
			}
		}
	}

	/** A monster the prison couldn't take after all goes back under a press where it is (no second slam hit). */
	static void recage(ServerLevel level, Mob mob) {
		if (CAGES.containsKey(mob.getUUID())) return;
		mob.setNoAi(true);
		mob.setTarget(null);
		mob.addTag(CAGED);
		Cage c = new Cage(level, mob);
		c.drop = 1;
		CAGES.put(mob.getUUID(), c);
		build(c);
	}

	/** The press closes on a slammed monster. */
	private static void close(ServerLevel level, Mob mob) {
		// The slam's hit: hurts, never kills.
		mob.setHealth(Math.max(1f, mob.getHealth() - SLAM_HIT));
		mob.setNoAi(true);
		mob.setTarget(null);
		mob.addTag(CAGED);
		Cage c = new Cage(level, mob);
		CAGES.put(mob.getUUID(), c);
		build(c);
		level.playSound(null, mob.blockPosition(), SoundEvents.ANVIL_PLACE, SoundSource.NEUTRAL, 0.6f, 1.6f);
	}

	/** Posts, the press plate (at its current drop) and the weight on top. */
	private static void build(Cage c) {
		c.lastRepair = c.level.getGameTime();
		clear(c);
		Corps before = Corps.enter(Corps.BLUE);
		try {
			BlockState shell = Corps.state(ModRegistry.LIGHT_CONSTRUCT);
			BlockState rim = shell.setValue(LightConstructBlock.RIM, true);
			int h = c.half, top = c.height + c.drop;
			for (int dx = -h; dx <= h; dx++) {
				for (int dz = -h; dz <= h; dz++) {
					boolean edgeX = Math.abs(dx) == h, edgeZ = Math.abs(dz) == h;
					// Corner posts the full height, bars along the sides at the bottom.
					if (edgeX && edgeZ) {
						for (int y = 0; y <= top; y++) put(c, c.floor.offset(dx, y, dz), rim);
					} else if (edgeX || edgeZ) {
						put(c, c.floor.offset(dx, 0, dz), rim);
					}
					// The press plate.
					put(c, c.floor.offset(dx, top, dz), edgeX || edgeZ ? rim : shell);
				}
			}
			// The weight: a smaller block stacked on the plate's middle.
			for (int dx = -1; dx <= 1; dx++) {
				for (int dz = -1; dz <= 1; dz++) put(c, c.floor.offset(dx, top + 1, dz), Math.abs(dx) + Math.abs(dz) == 0 ? rim : shell);
			}
		} finally {
			Corps.restore(before);
		}
	}

	private static void put(Cage c, BlockPos p, BlockState state) {
		BlockState now = c.level.getBlockState(p);
		if (!now.canBeReplaced() || !now.getFluidState().isEmpty()) return;
		c.level.setBlockAndUpdate(p, state);
		c.blocks.add(p.immutable());
	}

	private static void clear(Cage c) {
		for (BlockPos p : c.blocks) {
			if (c.level.getBlockState(p).is(ModRegistry.LIGHT_CONSTRUCT)) c.level.removeBlock(p, false);
		}
		c.blocks.clear();
	}

	/** The plate lands: a heavy thud and dust from the ground round it. */
	private static void thud(Cage c) {
		Vec3 at = c.at;
		c.level.playSound(null, c.floor, SoundEvents.ANVIL_LAND, SoundSource.NEUTRAL, 0.9f, 0.7f);
		c.level.playSound(null, c.floor, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.NEUTRAL, 1f, 0.8f);
		BlockState ground = c.level.getBlockState(c.floor.below());
		if (!ground.isAir()) {
			c.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), at.x, at.y + 0.1, at.z, 30, c.half, 0.1, c.half, 0.15);
		}
		c.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), at.x, at.y + c.height, at.z, 12, c.half, 0.2, c.half, 0.03);
	}

	static @Nullable Vec3 cagedAt(Mob mob) {
		Cage c = CAGES.get(mob.getUUID());
		return c == null ? null : c.at;
	}
}
