package com.sparky.lanternring;

import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Violet Lantern's Crystal Prison: aim at a creature and it is sealed in a shell of violet
 * crystal one block clear of it, held where it stands, for RingTuning.CRYSTAL_PRISON_TIME. Use it
 * again on a prisoner to shatter its prison early. Anything bigger than a ravager is too big to hold.
 * The shell is held hard light, so it never outlives the prison (even across a restart).
 */
public final class CrystalPrisons {
	private static final double RANGE = 32;
	private static final double MAX_WIDTH = 3.5;
	private static final double MAX_HEIGHT = 4.5;

	private static final List<Prison> PRISONS = new ArrayList<>();

	private static final class Prison {
		final ServerLevel level;
		final LivingEntity prisoner;
		final Vec3 at;
		final Set<BlockPos> blocks = new HashSet<>();
		final Corps corps;
		final long ends;

		Prison(ServerLevel level, LivingEntity prisoner, Corps corps, long ends) {
			this.level = level;
			this.prisoner = prisoner;
			this.at = prisoner.position();
			this.corps = corps;
			this.ends = ends;
		}
	}

	private CrystalPrisons() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(CrystalPrisons::tick);
		// Leaving the world: every prison opens, so none points at the closed world afterwards.
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Prison p : PRISONS) {
				for (BlockPos pos : p.blocks) {
					if (p.level.isLoaded(pos) && p.level.getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) p.level.removeBlock(pos, false);
				}
			}
			PRISONS.clear();
		});
	}

	public static boolean isLive(ServerLevel level, BlockPos pos) {
		for (Prison p : PRISONS) {
			if (p.level == level && p.blocks.contains(pos)) return true;
		}
		return false;
	}

	public static boolean activate(ServerLevel level, Player player) {
		RingPowers.Target target = RingPowers.trace(level, player, RANGE);
		// Aiming at a prison's crystal (or its prisoner) lets the prisoner out, for free.
		for (Iterator<Prison> it = PRISONS.iterator(); it.hasNext(); ) {
			Prison p = it.next();
			if (p.level == level && (p.prisoner == target.entity() || p.prisoner.getBoundingBox().inflate(1.6).contains(target.pos()))) {
				shatter(p);
				it.remove();
				return false;
			}
		}
		if (!(target.entity() instanceof LivingEntity mob) || !mob.isAlive()) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.crystal_prison_none").withStyle(ChatFormatting.LIGHT_PURPLE));
			return false;
		}
		if (mob.getBbWidth() > MAX_WIDTH || mob.getBbHeight() > MAX_HEIGHT) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.crystal_prison_big").withStyle(ChatFormatting.LIGHT_PURPLE));
			return false;
		}

		Prison prison = new Prison(level, mob, Corps.current(), level.getGameTime() + RingTuning.CRYSTAL_PRISON_TIME.ticks());
		AABB box = mob.getBoundingBox();
		int x0 = (int) Math.floor(box.minX) - 1, x1 = (int) Math.floor(box.maxX - 1e-3) + 1;
		int y0 = (int) Math.floor(box.minY + 1e-3) - 1, y1 = (int) Math.floor(box.maxY - 1e-3) + 1;
		int z0 = (int) Math.floor(box.minZ) - 1, z1 = (int) Math.floor(box.maxZ - 1e-3) + 1;
		BlockState base = Corps.state(ModRegistry.LIGHT_CONSTRUCT).setValue(LightConstructBlock.HELD, true);
		// Register the blocks before placing them, so their first check finds them live.
		PRISONS.add(prison);
		for (BlockPos pos : BlockPos.betweenClosed(x0, y0, z0, x1, y1, z1)) {
			int ends = (pos.getX() == x0 || pos.getX() == x1 ? 1 : 0) + (pos.getY() == y0 || pos.getY() == y1 ? 1 : 0)
					+ (pos.getZ() == z0 || pos.getZ() == z1 ? 1 : 0);
			if (ends == 0) continue;
			if (!level.getBlockState(pos).canBeReplaced() || !level.mayInteract(player, pos)) continue;
			BlockPos p = pos.immutable();
			prison.blocks.add(p);
			// The crystal's edges glow brightest.
			level.setBlockAndUpdate(p, base.setValue(LightConstructBlock.RIM, ends >= 2));
		}
		mob.setDeltaMovement(Vec3.ZERO);
		RingPowers.syncVelocity(mob);
		Vec3 c = box.getCenter();
		level.sendParticles(ModParticles.of(ModParticles.SHARD, prison.corps), c.x, c.y, c.z, 40, box.getXsize() / 2 + 0.6, box.getYsize() / 2 + 0.6, box.getZsize() / 2 + 0.6, 0.05);
		level.playSound(null, c.x, c.y, c.z, SoundEvents.AMETHYST_CLUSTER_PLACE, SoundSource.PLAYERS, 1.5f, 0.7f);
		level.playSound(null, c.x, c.y, c.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.2f, 1.0f);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), c);
		player.sendOverlayMessage(Component.translatable("message.lanternring.crystal_prison", mob.getDisplayName(),
				RingTuning.CRYSTAL_PRISON_TIME.ticks() / 20).withStyle(ChatFormatting.LIGHT_PURPLE));
		return true;
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Prison> it = PRISONS.iterator(); it.hasNext(); ) {
			Prison p = it.next();
			LivingEntity mob = p.prisoner;
			if (!mob.isAlive() || mob.isRemoved() || mob.level() != p.level || p.level.getGameTime() >= p.ends) {
				shatter(p);
				it.remove();
				continue;
			}
			// Held where it was caught: no walking, jumping, teleporting or being pushed.
			if (mob.position().distanceToSqr(p.at) > 0.01) mob.teleportTo(p.at.x, p.at.y, p.at.z);
			mob.setDeltaMovement(Vec3.ZERO);
			mob.fallDistance = 0;
			if (p.level.getGameTime() % 10 == 0) {
				Vec3 c = mob.getBoundingBox().getCenter();
				p.level.sendParticles(ModParticles.of(ModParticles.MOTE, p.corps), c.x, c.y, c.z, 3, 0.8, 0.8, 0.8, 0.01);
			}
		}
	}

	/** Breaks the shell with a burst of crystal shards. */
	private static void shatter(Prison p) {
		Corps before = Corps.enter(p.corps);
		try {
			for (BlockPos pos : p.blocks) {
				if (p.level.getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) p.level.removeBlock(pos, false);
			}
			Vec3 c = p.prisoner.getBoundingBox().getCenter();
			p.level.sendParticles(ModParticles.of(ModParticles.SHARD, p.corps), c.x, c.y, c.z, 60, 1.2, 1.2, 1.2, 0.25);
			p.level.playSound(null, c.x, c.y, c.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 1.5f, 0.8f);
			p.level.playSound(null, c.x, c.y, c.z, SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 1f, 1.3f);
		} finally {
			Corps.enter(before);
		}
		p.blocks.clear();
	}
}
