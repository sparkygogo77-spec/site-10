package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * SAW: hold right-click on a block to pick it, then drag the crosshair away along the ground: the
 * saw forms there, a big disc of hard light standing upright and half sunk into the ground, facing
 * the way you dragged. Hold left-click as well and it spins and rolls forward, tearing a trench a
 * single block wide through everything in its disc (RADIUS blocks round its middle) and cutting
 * up any mob it catches. It rolls a block every RingTuning.SAW_BLOCK while left-click is held, for
 * STEP_COST a block, and stands still (but stays) when it is let go. Letting go of right-click
 * dissolves it. Clients draw it from the SAW effect re-sent every tick (client SawFx).
 */
public final class Saws {
	/** How far away the starting block can be picked. */
	private static final double REACH = 48;
	/** The disc's radius in blocks: it stands this high above the ground and sinks as deep. */
	public static final double RADIUS = 4.0;
	/** How far the crosshair has to be dragged from the picked block before the saw forms. */
	private static final double DRAG = 1.2;
	/** Charge per block rolled (0.3% of a full ring); forming costs RingMode.SAW.cost (3%). */
	public static final int STEP_COST = 3;
	/** The furthest one saw rolls. */
	private static final double MAX_DISTANCE = 128;
	/** Damage to a mob in the disc, every HIT_INTERVAL ticks it stays there. */
	private static final float DAMAGE = 7.0f;
	private static final int HIT_INTERVAL = 8;
	/** Left-click counts as held this many ticks after its last message (sent every tick). */
	private static final int SPIN_GRACE = 2;

	private static final class Saw {
		final ServerLevel level;
		final BlockPos picked;
		/** The disc's middle, on the ground's surface; null until it has formed. */
		Vec3 center;
		Vec3 dir = new Vec3(0, 0, 1);
		double rolled;
		/** Blocks rolled that have been paid for. */
		int paid;
		long lastSpin = -100;
		boolean spinning;
		final Map<UUID, Long> hits = new HashMap<>();

		Saw(ServerLevel level, BlockPos picked) {
			this.level = level;
			this.picked = picked;
		}
	}

	private static final Map<UUID, Saw> SAWS = new HashMap<>();

	private Saws() {
	}

	static void register() {
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> SAWS.clear());
	}

	/** Right-click in Saw mode: picks the block aimed at (or the one underfoot). */
	public static void begin(ServerPlayer player) {
		cancel(player);
		ServerLevel level = player.level();
		Vec3 eye = player.getEyePosition();
		BlockHitResult hit = level.clip(new ClipContext(eye, eye.add(player.getLookAngle().scale(REACH)),
				ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		BlockPos picked = hit.getType() == HitResult.Type.MISS ? player.blockPosition().below() : hit.getBlockPos();
		Saw saw = new Saw(level, picked);
		SAWS.put(player.getUUID(), saw);
		mark(saw, player, Vec3.atCenterOf(picked));
		level.playSound(null, picked, SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.PLAYERS, 1.0f, 1.2f);
	}

	/** Every tick right-click is held: before it forms, follows the drag; after, spins and rolls while left-click is held. */
	public static void tick(ServerPlayer player, ItemStack ring) {
		Saw saw = SAWS.get(player.getUUID());
		if (saw == null || saw.level != player.level()) return;
		long now = saw.level.getGameTime();
		if (saw.center == null) {
			Vec3 drag = dragPoint(saw, player);
			Vec3 start = Vec3.atBottomCenterOf(saw.picked).add(0, 1, 0);
			Vec3 d = new Vec3(drag.x - start.x, 0, drag.z - start.z);
			if (d.length() < DRAG) {
				if (now % 2 == 0) mark(saw, player, drag);
				return;
			}
			if (!player.isCreative() && PowerRingItem.getCharge(ring) < RingMode.SAW.cost) {
				player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
				return;
			}
			if (!player.isCreative()) PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - RingMode.SAW.cost);
			saw.dir = d.normalize();
			saw.center = start;
			RingFx.send(saw.level, Kind.CONSTRUCT, RingPowers.handPos(player), start);
			saw.level.playSound(null, start.x, start.y, start.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.2f, 0.7f);
		}

		boolean spin = now - saw.lastSpin <= SPIN_GRACE;
		if (spin && !saw.spinning) saw.level.playSound(null, saw.center.x, saw.center.y, saw.center.z, SoundEvents.GRINDSTONE_USE, SoundSource.PLAYERS, 1.2f, 0.6f);
		saw.spinning = spin;
		if (spin) roll(saw, player, ring);
		RingFx.send(saw.level, Kind.SAW, saw.center, saw.center.add(saw.dir), saw.spinning ? 1f : 0.001f, player.getId(), null);
	}

	/** Left-click is held (sent each tick) while right-click is: the saw spins. */
	public static void spin(ServerPlayer player) {
		Saw saw = SAWS.get(player.getUUID());
		if (saw == null || saw.level != player.level() || !player.isUsingItem()) return;
		saw.lastSpin = saw.level.getGameTime();
	}

	/** Right-click let go: the saw dissolves. */
	public static void release(Player player) {
		Saw saw = SAWS.remove(player.getUUID());
		if (saw == null || saw.center == null) return;
		RingFx.send(saw.level, Kind.SAW, saw.center, saw.center.add(saw.dir), -1f, player.getId(), null);
		saw.level.playSound(null, saw.center.x, saw.center.y, saw.center.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 1.0f, 0.8f);
	}

	/** Called off (switched to a lantern charge, or a new saw picked): it dissolves. */
	public static void cancel(Player player) {
		release(player);
	}

	/** True while this player's saw is up (for tests). */
	public static boolean active(Player player) {
		Saw saw = SAWS.get(player.getUUID());
		return saw != null && saw.center != null;
	}

	/** Where the saw's middle is now, or null (for tests). */
	public static Vec3 center(Player player) {
		Saw saw = SAWS.get(player.getUUID());
		return saw == null ? null : saw.center;
	}

	/** Where the crosshair crosses the top of the picked block's level; looking above it, far ahead. */
	private static Vec3 dragPoint(Saw saw, Player player) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		double top = saw.picked.getY() + 1.0;
		if (look.y < -0.02 && eye.y > top) {
			double t = (top - eye.y) / look.y;
			return new Vec3(eye.x + look.x * t, top, eye.z + look.z * t);
		}
		return new Vec3(eye.x + look.x * 64, top, eye.z + look.z * 64);
	}

	private static void roll(Saw saw, ServerPlayer player, ItemStack ring) {
		if (saw.rolled >= MAX_DISTANCE) return;
		// Pay for each block before rolling into it.
		if (saw.rolled + 1 > saw.paid) {
			if (!player.isCreative() && PowerRingItem.getCharge(ring) < STEP_COST) {
				if (saw.level.getGameTime() % 20 == 0) {
					player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
				}
				return;
			}
			if (!player.isCreative()) PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - STEP_COST);
			saw.paid++;
		}
		double step = 1.0 / Math.max(1, RingTuning.SAW_BLOCK.ticks());
		// Something it can't cut (bedrock, a block entity) right at its leading edge stops it dead; it keeps spinning.
		Vec3 ahead = saw.center.add(saw.dir.scale(RADIUS + step));
		for (double b = -RADIUS + 0.5; b <= 0.5; b += 1) {
			BlockPos pos = BlockPos.containing(ahead.x, saw.center.y + b * 0.7, ahead.z);
			BlockState state = saw.level.getBlockState(pos);
			if (!state.isAir() && !cuttable(saw.level, player, pos, state) && state.getFluidState().isEmpty()) {
				cut(saw, player);
				return;
			}
		}
		saw.center = saw.center.add(saw.dir.scale(step));
		saw.rolled += step;
		cut(saw, player);
	}

	/** Breaks every block in the disc (one block wide) and cuts up the mobs in it. */
	private static void cut(Saw saw, ServerPlayer player) {
		ServerLevel level = saw.level;
		Set<BlockPos> inDisc = new LinkedHashSet<>();
		for (double a = -RADIUS; a <= RADIUS; a += 0.5) {
			for (double b = -RADIUS; b <= RADIUS; b += 0.5) {
				if (a * a + b * b > RADIUS * RADIUS) continue;
				inDisc.add(BlockPos.containing(saw.center.x + saw.dir.x * a, saw.center.y + b, saw.center.z + saw.dir.z * a));
			}
		}
		BlockState loudest = null;
		for (BlockPos pos : inDisc) {
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || !cuttable(level, player, pos, state)) continue;
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			HeldConstructs.debris(level, pos, state);
			if (state.getFluidState().isEmpty() && (loudest == null || state.getDestroySpeed(level, pos) > loudest.getDestroySpeed(level, pos))) {
				loudest = state;
			}
		}
		// Grit sprays back off the leading edge where the teeth bite the ground.
		Vec3 bite = saw.center.add(saw.dir.scale(RADIUS * 0.8)).add(0, -0.4, 0);
		BlockState under = level.getBlockState(BlockPos.containing(bite.x, bite.y - 0.6, bite.z));
		BlockState grit = loudest != null ? loudest : under;
		if (!grit.isAir() && grit.getFluidState().isEmpty() && level.getGameTime() % 2 == 0) {
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, grit), bite.x, bite.y + 0.3, bite.z, 6, 0.2, 0.25, 0.2, 0.25);
		}
		if (loudest != null && level.getGameTime() % 3 == 0) {
			level.playSound(null, bite.x, bite.y, bite.z, loudest.getSoundType().getBreakSound(), SoundSource.PLAYERS, 1.0f, 0.6f);
		}

		long now = level.getGameTime();
		AABB box = new AABB(saw.center, saw.center).inflate(RADIUS + 0.5);
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, box,
				e -> e != player && e.isAlive() && !e.isSpectator())) {
			Vec3 to = target.getBoundingBox().getCenter().subtract(saw.center);
			double along = to.x * saw.dir.x + to.z * saw.dir.z;
			double across = Math.abs(to.x * saw.dir.z - to.z * saw.dir.x);
			if (across > 0.6 + target.getBbWidth() / 2 || along * along + to.y * to.y > (RADIUS + 0.3) * (RADIUS + 0.3)) continue;
			Long last = saw.hits.get(target.getUUID());
			if (last != null && now - last < HIT_INTERVAL) continue;
			saw.hits.put(target.getUUID(), now);
			target.hurtServer(level, level.damageSources().indirectMagic(player, player), DAMAGE);
			// Flung forward and off to the side it's on, like off a real blade.
			double side = Math.signum(to.x * saw.dir.z - to.z * saw.dir.x);
			if (side == 0) side = 1;
			target.push(saw.dir.x * 0.5 + saw.dir.z * side * 0.6, 0.35, saw.dir.z * 0.5 - saw.dir.x * side * 0.6);
		}
	}

	private static boolean cuttable(ServerLevel level, Player player, BlockPos pos, BlockState state) {
		return !state.hasBlockEntity() && state.getDestroySpeed(level, pos) >= 0 && !state.is(ModRegistry.LIGHT_CONSTRUCT)
				&& !(state.getBlock() instanceof com.sparky.lanternring.block.BlastGlowBlock) && level.mayInteract(player, pos);
	}

	/** Outlines the picked block and where the drag has got to for the bearer's client (the Bridge's marker). */
	private static void mark(Saw saw, ServerPlayer player, Vec3 drag) {
		RingFx.send(saw.level, Kind.BRIDGE_MARK, Vec3.atCenterOf(saw.picked), drag.subtract(0, 0.5, 0), 0f, 0, player);
	}
}
