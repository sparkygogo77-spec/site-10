package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * BRIDGE: hold right-click and the block you aim at is picked (outlined in hard light), and the
 * bridge is locked to its level. Holding left-click as well builds the bridge out from it, a block
 * at a time, towards wherever the crosshair points on that level. Crouching lowers the deck a
 * level for the next stretch and space raises it one. Let go of right-click and the bridge stands
 * for RingTuning.CONSTRUCT_LIFETIME, then goes back into the ring. Each block of length costs
 * STEP_COST as it is built.
 */
public final class Bridges {
	/** How far away the starting block can be picked. */
	private static final double REACH = 48;
	/** Ticks between blocks of length while left-click is held. */
	private static final int BUILD_INTERVAL = 2;
	/** The longest a bridge can be, in blocks of length. */
	private static final int MAX_LENGTH = 96;
	/** Charge per block of length (0.4% of a full ring). */
	public static final int STEP_COST = 4;
	/** How long a bridge being built may stand before it is let go, as a backstop. */
	private static final int MAX_HOLD_TICKS = 20 * 60 * 5;

	private static final class Draft {
		final ServerLevel level;
		/** The deck's level now: the picked block's, moved by crouch and space. */
		int y;
		/** The middle of the bridge's front edge, on the deck's level. */
		double headX;
		double headZ;
		/** The way the last block of length went (flat), for the deck's width. */
		double dirX;
		double dirZ = 1;
		final BlockPos picked;
		final Set<BlockPos> blocks;
		int length;
		long lastBuild = -100;
		long lastInput = -100;

		Draft(ServerLevel level, BlockPos picked, Set<BlockPos> blocks) {
			this.level = level;
			this.picked = picked;
			this.blocks = blocks;
			this.y = picked.getY();
			this.headX = picked.getX() + 0.5;
			this.headZ = picked.getZ() + 0.5;
		}
	}

	private static final Map<UUID, Draft> DRAFTS = new HashMap<>();

	private Bridges() {
	}

	static void register() {
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> DRAFTS.clear());
	}

	/** Right-click in Bridge mode: picks the block aimed at (or the one underfoot) and locks its level. */
	public static void begin(ServerPlayer player) {
		cancel(player);
		ServerLevel level = player.level();
		Vec3 eye = player.getEyePosition();
		BlockHitResult hit = level.clip(new ClipContext(eye, eye.add(player.getLookAngle().scale(REACH)),
				ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		BlockPos picked = hit.getType() == HitResult.Type.MISS ? player.blockPosition().below() : hit.getBlockPos();
		// Registered now so the blocks hold while it's built; the real lifetime starts on release.
		Set<BlockPos> blocks = HeldConstructs.stand(level, player, MAX_HOLD_TICKS);
		Draft draft = new Draft(level, picked, blocks);
		Vec3 flat = player.getLookAngle().multiply(1, 0, 1);
		if (flat.lengthSqr() > 1.0e-4) {
			flat = flat.normalize();
			draft.dirX = flat.x;
			draft.dirZ = flat.z;
		}
		DRAFTS.put(player.getUUID(), draft);
		mark(draft, player);
		level.playSound(null, picked, SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.PLAYERS, 1.0f, 1.4f);
	}

	/** Every tick right-click is held: keeps the picked block (and the deck's front) outlined. */
	public static void tick(ServerPlayer player) {
		Draft draft = DRAFTS.get(player.getUUID());
		if (draft == null || draft.level != player.level()) return;
		if (draft.level.getGameTime() % 2 == 0) mark(draft, player);
	}

	/** Left-click is held (sent each tick): the next block of length goes down every BUILD_INTERVAL ticks. */
	public static void build(ServerPlayer player, ItemStack ring) {
		Draft draft = DRAFTS.get(player.getUUID());
		if (draft == null || draft.level != player.level() || !player.isUsingItem()) return;
		long now = draft.level.getGameTime();
		draft.lastInput = now;
		if (now - draft.lastBuild < BUILD_INTERVAL || draft.length >= MAX_LENGTH) return;
		if (!player.isCreative() && PowerRingItem.getCharge(ring) < STEP_COST) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
			return;
		}
		draft.lastBuild = now;

		// Where the crosshair crosses the deck's level; looking above it, straight ahead on it.
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		double deckTop = draft.y + 1.0;
		double toX, toZ;
		if (look.y < -0.02 && eye.y > deckTop) {
			double t = (deckTop - eye.y) / look.y;
			toX = eye.x + look.x * t;
			toZ = eye.z + look.z * t;
		} else {
			toX = eye.x + look.x * 64;
			toZ = eye.z + look.z * 64;
		}
		double dx = toX - draft.headX, dz = toZ - draft.headZ;
		double len = Math.sqrt(dx * dx + dz * dz);
		double flatLen = Math.sqrt(look.x * look.x + look.z * look.z);
		if (flatLen > 1.0e-3 && (len < 1.5 || dx * look.x + dz * look.z < 0)) {
			// The crosshair is on the front already (or behind it): keep going the way you face.
			dx = look.x / flatLen;
			dz = look.z / flatLen;
			len = 1;
		} else if (len < 1.0e-3) {
			return;
		}
		draft.dirX = dx / len;
		draft.dirZ = dz / len;
		draft.headX += draft.dirX;
		draft.headZ += draft.dirZ;
		draft.length++;

		// Three wide across the way it's heading, the sides edged like a wall.
		double sideX = -draft.dirZ, sideZ = draft.dirX;
		int placed = 0;
		for (int across = -1; across <= 1; across++) {
			for (double half = 0; half <= 0.5; half += 0.5) {
				// Two samples along the step so diagonals come out solid.
				double x = draft.headX - draft.dirX * half + sideX * across;
				double z = draft.headZ - draft.dirZ * half + sideZ * across;
				BlockPos pos = BlockPos.containing(x, draft.y + 0.5, z);
				if (draft.blocks.contains(pos)) continue;
				if (RingPowers.placeConstruct(draft.level, player, pos, across != 0)) {
					draft.blocks.add(pos);
					placed++;
				}
			}
		}
		if (placed > 0 && !player.isCreative()) PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - STEP_COST);
		if (placed > 0) {
			Vec3 at = new Vec3(draft.headX, draft.y + 0.5, draft.headZ);
			RingFx.send(draft.level, Kind.CONSTRUCT, RingPowers.handPos(player), at);
			draft.level.playSound(null, at.x, at.y, at.z, SoundEvents.AMETHYST_BLOCK_PLACE, SoundSource.PLAYERS, 0.6f, 1.2f + 0.02f * (draft.length % 20));
		}
	}

	/** Space (up 1) or crouch (down 1) while building: the next stretch is a level higher or lower. */
	public static void shift(ServerPlayer player, int levels) {
		Draft draft = DRAFTS.get(player.getUUID());
		if (draft == null || draft.level != player.level() || !player.isUsingItem()) return;
		draft.y += levels;
		mark(draft, player);
		draft.level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 0.8f, levels > 0 ? 1.6f : 1.0f);
		player.sendOverlayMessage(Component.translatable("message.lanternring.bridge_level", draft.y - draft.picked.getY() >= 0 ? "+" + (draft.y - draft.picked.getY()) : String.valueOf(draft.y - draft.picked.getY()))
				.withStyle(Corps.of(player.getMainHandItem()).chat));
	}

	/** Right-click let go: the bridge stands for RingTuning.CONSTRUCT_LIFETIME from now. */
	public static void release(Player player) {
		Draft draft = DRAFTS.remove(player.getUUID());
		if (draft == null) return;
		HeldConstructs.restand(draft.blocks, RingTuning.CONSTRUCT_LIFETIME.ticks());
		if (!draft.blocks.isEmpty()) RingSounds.bridge(draft.level, BlockPos.containing(draft.headX, draft.y, draft.headZ));
	}

	/** Called off (switched to a lantern charge): what was built stays its normal lifetime. */
	public static void cancel(Player player) {
		release(player);
	}

	/** Outlines the picked block and the deck's front for the bearer's client (BRIDGE_MARK). */
	private static void mark(Draft draft, ServerPlayer player) {
		Vec3 picked = Vec3.atCenterOf(draft.picked);
		Vec3 front = new Vec3(draft.headX, draft.y + 0.5, draft.headZ);
		RingFx.send(draft.level, Kind.BRIDGE_MARK, picked, front, 0f, draft.length, player);
	}
}
