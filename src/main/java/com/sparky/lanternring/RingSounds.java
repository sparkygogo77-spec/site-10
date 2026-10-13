package com.sparky.lanternring;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * Each construct's own sound, layered from vanilla pieces so no two modes sound alike, plus the
 * ring's low and out-of-power warnings. BEACON_DEACTIVATE stays the "not enough charge" sound only.
 */
public final class RingSounds {
	private RingSounds() {
	}

	/** A slab of light slams up: a deep amethyst thud under a bright shimmer. */
	public static void wall(ServerLevel level, BlockPos at) {
		play(level, Vec3.atCenterOf(at), SoundEvents.AMETHYST_BLOCK_PLACE, 1.0f, 0.6f);
		play(level, Vec3.atCenterOf(at), SoundEvents.AMETHYST_BLOCK_RESONATE, 0.8f, 1.0f);
		play(level, Vec3.atCenterOf(at), SoundEvents.BEACON_POWER_SELECT, 0.4f, 1.8f);
	}

	/** The bridge unrolls ahead: a rising chime that runs away from you. */
	public static void bridge(ServerLevel level, BlockPos at) {
		play(level, Vec3.atCenterOf(at), SoundEvents.AMETHYST_CLUSTER_PLACE, 1.0f, 1.3f);
		play(level, Vec3.atCenterOf(at), SoundEvents.AMETHYST_BLOCK_RESONATE, 0.7f, 1.6f);
		play(level, Vec3.atCenterOf(at), SoundEvents.TRIAL_SPAWNER_OPEN_SHUTTER, 0.5f, 1.5f);
	}

	/** The Dome rises round you: a low swell with a glassy ring over it. */
	public static void domeUp(ServerLevel level, Player player) {
		play(level, player.position(), SoundEvents.CONDUIT_ACTIVATE, 0.6f, 1.4f);
		play(level, player.position(), SoundEvents.AMETHYST_BLOCK_RESONATE, 0.8f, 0.8f);
	}

	/** The Dome lets go: its light breaks up and goes back into the ring. */
	public static void domeDown(ServerLevel level, Player player) {
		play(level, player.position(), SoundEvents.AMETHYST_CLUSTER_BREAK, 0.8f, 1.2f);
		play(level, player.position(), SoundEvents.CONDUIT_DEACTIVATE, 0.4f, 1.6f);
	}

	/** The Shield snaps up on your arm: short and metallic. */
	public static void shieldUp(ServerLevel level, Player player) {
		play(level, player.position(), SoundEvents.TRIDENT_RETURN, 0.8f, 1.5f);
		play(level, player.position(), SoundEvents.AMETHYST_BLOCK_RESONATE, 0.6f, 1.8f);
	}

	/** The Shield folds away. */
	public static void shieldDown(ServerLevel level, Player player) {
		play(level, player.position(), SoundEvents.AMETHYST_BLOCK_HIT, 0.8f, 1.6f);
	}

	/** A Push: a burst of air with a deep hum under it. */
	public static void push(ServerLevel level, Vec3 at) {
		play(level, at, SoundEvents.WIND_CHARGE_BURST.value(), 1.0f, 0.8f);
		play(level, at, SoundEvents.AMETHYST_BLOCK_RESONATE, 0.8f, 0.6f);
	}

	/** The small wave where a Beam lands: a lighter burst. */
	public static void beamWave(ServerLevel level, Vec3 at) {
		play(level, at, SoundEvents.WIND_CHARGE_BURST.value(), 0.6f, 1.3f);
	}

	/** The ring has dropped to its low-charge mark: two soft bell notes. */
	public static void low(ServerLevel level, Player player) {
		play(level, player.position(), SoundEvents.NOTE_BLOCK_BELL.value(), 0.7f, 0.8f);
		play(level, player.position(), SoundEvents.NOTE_BLOCK_BELL.value(), 0.5f, 0.6f);
	}

	/** The ring is out of power: its light gutters out. */
	public static void depleted(ServerLevel level, Player player) {
		play(level, player.position(), SoundEvents.RESPAWN_ANCHOR_DEPLETE.value(), 0.8f, 1.2f);
		play(level, player.position(), SoundEvents.CONDUIT_DEACTIVATE, 0.7f, 0.8f);
	}

	private static void play(ServerLevel level, Vec3 at, SoundEvent sound, float volume, float pitch) {
		level.playSound(null, at.x, at.y, at.z, sound, SoundSource.PLAYERS, volume, pitch);
	}
}
