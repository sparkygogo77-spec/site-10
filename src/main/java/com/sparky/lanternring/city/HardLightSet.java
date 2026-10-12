package com.sparky.lanternring.city;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
import java.util.ArrayDeque;
import java.util.Deque;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * How Blue Lantern buildings go up (J, 2026-10-12): each block first forms as glowing blue hard
 * light (Sky Light), and {@link RingTuning#CITY_SET} later it "sets" into what it's meant to be,
 * so a hardening line climbs the building behind the glowing one. Used by the Blue villagers'
 * houses and islands and by Villager Spark; the sky city has its own saved version (CityBuilds).
 * <p>
 * Not saved, so nothing is left glowing for good: a block whose chunk is unloaded when it's due
 * waits until it loads again, and everything still pending sets at once when the world closes.
 */
public final class HardLightSet {
	private static final int FLAGS = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;

	private record Pending(ServerLevel level, BlockPos pos, BlockState want, long due) {
	}

	/** In the order they formed, which is also the order they're due. */
	private static final Deque<Pending> PENDING = new ArrayDeque<>();

	private HardLightSet() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(server -> tick());
		// Set what's left while the levels are still open, so a house half-set at quit isn't left as light.
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			while (!PENDING.isEmpty()) set(PENDING.poll(), false);
		});
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> PENDING.clear());
	}

	/** Forms {@code want} at pos as hard light now; it sets into {@code want} a moment later. Air is placed straight away. */
	public static void form(ServerLevel level, BlockPos pos, BlockState want) {
		if (want.isAir() || want.is(CityBlocks.SKY_LIGHT)) {
			level.setBlock(pos, want, FLAGS);
			return;
		}
		level.setBlock(pos, CityBlocks.SKY_LIGHT.defaultBlockState(), FLAGS);
		PENDING.add(new Pending(level, pos.immutable(), want, level.getGameTime() + RingTuning.CITY_SET.ticks()));
		if (level.getRandom().nextInt(12) == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5,
					3, 0.3, 0.3, 0.3, 0.02);
		}
		if (level.getRandom().nextInt(50) == 0) {
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1f, 1.5f);
		}
	}

	/** Whether any block is still waiting to set. */
	public static boolean busy() {
		return !PENDING.isEmpty();
	}

	/** Blocks whose chunk was unloaded when due are retried this often. */
	private static final int RETRY = 100;

	private static void tick() {
		java.util.List<Pending> later = null;
		while (!PENDING.isEmpty()) {
			Pending p = PENDING.peek();
			if (p.level.getGameTime() < p.due) break;
			PENDING.poll();
			if (!set(p, true)) {
				if (later == null) later = new java.util.ArrayList<>();
				later.add(new Pending(p.level, p.pos, p.want, p.level.getGameTime() + RETRY));
			}
		}
		if (later != null) PENDING.addAll(later);
	}

	/** Sets the block; false if its chunk isn't loaded (it should be tried again). */
	private static boolean set(Pending p, boolean effects) {
		ServerLevel level = p.level;
		if (!level.isLoaded(p.pos)) return false;
		// Only the light it formed sets; anything placed or broken meanwhile is left alone.
		if (!level.getBlockState(p.pos).is(CityBlocks.SKY_LIGHT)) return true;
		BlockState want = Block.updateFromNeighbourShapes(p.want, level, p.pos);
		if (want.isAir()) want = p.want;
		level.setBlock(p.pos, want, Block.UPDATE_ALL);
		if (!effects) return true;
		if (level.getRandom().nextInt(16) == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), p.pos.getX() + 0.5, p.pos.getY() + 1.0, p.pos.getZ() + 0.5,
					2, 0.4, 0.1, 0.4, 0.01);
		}
		if (level.getRandom().nextInt(60) == 0) {
			level.playSound(null, p.pos, want.getSoundType().getPlaceSound(), SoundSource.BLOCKS, 1f, 0.8f);
		}
		return true;
	}
}
