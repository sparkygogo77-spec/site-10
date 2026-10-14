package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * The bearer becomes a sun while charging (J, 2026-10-14): the lantern is the light source, and
 * the ground, walls and caves round the bearer grow brighter and brighter in the corps' colour as
 * the ring fills, then flashes out wider, to {@link #BURST_REACH} blocks, at the burst. Everyone sees it, since it is
 * real block light (the Blast's invisible light, coloured by corps under the patched pack), while
 * the daylight round the charger drains away for everyone near (client SunDim).
 *
 * <p>The lights are kept at full while the charge is live and pulled back in once it stops: they
 * dim step by step and go. Each one is also a Blast light, so it would go out by itself anyway.
 */
public final class ChargeLight {
	/** Blocks lit round the lantern as the ring meets the lens, and at the burst. */
	private static final int START_REACH = 4;
	private static final int FULL_REACH = 16;
	public static final int BURST_REACH = 30;
	/** Blocks between lights on the grid round the lantern. */
	private static final int STEP = 5;
	/** How far down a light looks for the floor, and how far above the lantern it starts. */
	private static final int DOWN = 24;
	private static final int UP = 4;
	/** Ticks the light holds after the last refresh (longer after the burst), then ticks per fade step. */
	private static final int HOLD = 6;
	private static final int BURST_HOLD = 24;
	private static final int FADE_EVERY = 2;
	private static final int FADE_STEP = 2;
	/** The lantern's own light as the charge starts. */
	private static final int CORE_IDLE = 7;

	private static final class Glow {
		ServerLevel level;
		final Set<BlockPos> lights = new HashSet<>();
		long last;
		int hold;
		int brightness = BlastGlowBlock.START_LEVEL;
	}

	private static final Map<UUID, Glow> GLOWS = new HashMap<>();

	private ChargeLight() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(ChargeLight::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Glow g : GLOWS.values()) clear(g);
			GLOWS.clear();
		});
	}

	/**
	 * Lights the area round {@code bearer}'s lantern, {@code x} of the way (0..1) from the ring
	 * meeting the lens to the ring filling, or at the burst.
	 */
	public static void light(ServerLevel level, ServerPlayer bearer, float x, boolean burst) {
		Glow g = GLOWS.computeIfAbsent(bearer.getUUID(), k -> new Glow());
		if (g.level != null && g.level != level) clear(g);
		g.level = level;
		g.last = level.getGameTime();
		g.hold = burst ? BURST_HOLD : HOLD;
		g.brightness = BlastGlowBlock.START_LEVEL;
		int reach = burst ? BURST_REACH : Math.round(START_REACH + (FULL_REACH - START_REACH) * (float) Math.pow(Mth.clamp(x, 0f, 1f), 0.8));
		// The lantern is held up in front of the chest.
		Vec3 lantern = bearer.getEyePosition().add(bearer.getViewVector(1f).multiply(1, 0, 1).scale(0.8)).add(0, -0.5, 0);
		BlockPos core = BlockPos.containing(lantern);
		Corps before = Corps.enter(Corps.of(bearer.getMainHandItem()));
		try {
			BlockState glow = Corps.state(ModRegistry.BLAST_GLOW).setValue(BlastGlowBlock.LEVEL, BlastGlowBlock.START_LEVEL);
			// The light inside the lantern itself lights the block and you, rising with the charge (J's charge
			// hand-off, 2026-10-14): level 7 as the ring meets the port, up to 15 when full.
			int inside = burst ? BlastGlowBlock.START_LEVEL : Math.round(CORE_IDLE + (BlastGlowBlock.START_LEVEL - CORE_IDLE) * Mth.clamp(x, 0f, 1f));
			place(g, bearer, glow.setValue(BlastGlowBlock.LEVEL, inside), core);
			for (int dx = -reach; dx <= reach; dx += STEP) {
				for (int dz = -reach; dz <= reach; dz += STEP) {
					if (dx * dx + dz * dz > reach * reach || dx == 0 && dz == 0) continue;
					// On the floor (or a cave floor) below each grid point.
					BlockPos pos = core.offset(dx, UP, dz);
					for (int i = 0; i < UP + DOWN && pos.getY() > level.getMinY(); i++, pos = pos.below()) {
						if (!level.getBlockState(pos).isAir()) continue;
						BlockPos below = pos.below();
						if (!level.getBlockState(below).getCollisionShape(level, below).isEmpty()) {
							place(g, bearer, glow, pos);
							break;
						}
					}
				}
			}
		} finally {
			Corps.restore(before);
		}
	}

	private static void place(Glow g, ServerPlayer bearer, BlockState glow, BlockPos pos) {
		BlockState there = g.level.getBlockState(pos);
		if (there.is(ModRegistry.BLAST_GLOW)) {
			int level = glow.getValue(BlastGlowBlock.LEVEL);
			if (there.getValue(BlastGlowBlock.LEVEL) != level) g.level.setBlock(pos, there.setValue(BlastGlowBlock.LEVEL, level), 2);
			g.lights.add(pos.immutable());
		} else if (there.isAir() && g.level.mayInteract(bearer, pos)) {
			g.level.setBlock(pos, glow, 3);
			g.lights.add(pos.immutable());
		}
	}

	/** Every server tick: once a charge stops, its light is pulled back in step by step. */
	private static void tick(MinecraftServer server) {
		for (Iterator<Glow> it = GLOWS.values().iterator(); it.hasNext(); ) {
			Glow g = it.next();
			if (g.level == null) {
				it.remove();
				continue;
			}
			long since = g.level.getGameTime() - g.last;
			if (since <= g.hold || (since - g.hold) % FADE_EVERY != 0) continue;
			g.brightness -= FADE_STEP;
			if (g.brightness <= 0) {
				clear(g);
				it.remove();
				continue;
			}
			for (BlockPos pos : g.lights) {
				BlockState there = g.level.getBlockState(pos);
				if (there.is(ModRegistry.BLAST_GLOW) && there.getValue(BlastGlowBlock.LEVEL) > g.brightness) {
					g.level.setBlock(pos, there.setValue(BlastGlowBlock.LEVEL, g.brightness), 2);
				}
			}
		}
	}

	private static void clear(Glow g) {
		for (BlockPos pos : g.lights) {
			BlockState there = g.level.getBlockState(pos);
			if (!there.is(ModRegistry.BLAST_GLOW)) continue;
			g.level.setBlock(pos, there.getValue(BlastGlowBlock.WATERLOGGED) ? Blocks.WATER.defaultBlockState() : Blocks.AIR.defaultBlockState(), 3);
		}
		g.lights.clear();
	}

	/** Test hook: how many lights a bearer's charge has lit right now. */
	public static int lit(UUID bearer) {
		Glow g = GLOWS.get(bearer);
		return g == null ? 0 : g.lights.size();
	}
}
