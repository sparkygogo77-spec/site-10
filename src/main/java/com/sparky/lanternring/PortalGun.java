package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.GlobalPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * The Portal mode, a Rick and Morty portal gun. Hold right-click (RingTuning.PORTAL_SET) to set
 * the exit where you look; a tap then opens a portal where you look, linked to that exit, and both
 * stay open for RingTuning.PORTAL_LIFETIME. Walk in one, come out the other, in any dimension.
 * Aim at a chest when setting the exit and the Loot Golem (see LootGolems) stores its loot there.
 */
public final class PortalGun {
	private static final double RANGE = 48;
	/** A chest this close to the exit (in blocks) is where the Loot Golem stores loot. */
	private static final int STORAGE_REACH = 3;

	private PortalGun() {
	}

	/** Where a portal goes: its centre and the way its front faces. */
	public record Spot(Vec3 center, float yaw) {
	}

	public static PortalExit exit(ItemStack ring) {
		return ring.get(ModComponents.PORTAL_EXIT);
	}

	/** Charge to open a pair to this exit: double when it's in another dimension. */
	public static int cost(Player player, ItemStack ring) {
		PortalExit exit = exit(ring);
		boolean away = exit != null && !exit.pos().dimension().equals(player.level().dimension());
		return away ? 2 * RingMode.PORTAL.cost : RingMode.PORTAL.cost;
	}

	/** Server side of holding right-click: a rising hum, then at RingTuning.PORTAL_SET the exit is set. */
	public static void holdTick(ServerLevel level, ServerPlayer player, ItemStack ring, int held) {
		int full = Math.max(1, RingTuning.PORTAL_SET.ticks());
		if (held > 0 && held < full && held % 4 == 0) {
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 0.6f, 0.8f + 1.2f * held / full);
		}
		if (held != full) return;
		setExit(level, player, ring);
		player.stopUsingItem();
	}

	/** A tap: opens a pair to the exit, or sets the exit if there isn't one yet. */
	public static void tap(ServerLevel level, ServerPlayer player, ItemStack ring) {
		PortalExit exit = exit(ring);
		if (exit == null) {
			setExit(level, player, ring);
			return;
		}
		int cost = cost(player, ring);
		if (!player.isCreative() && PowerRingItem.getCharge(ring) < cost) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
			return;
		}
		ServerLevel exitLevel = level.getServer().getLevel(exit.pos().dimension());
		if (exitLevel == null) return;
		Spot entrance = aim(level, player);
		Vec3 exitCenter = exit.center();
		if (exitLevel == level && entrance.center().distanceTo(exitCenter) < 3) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.portal_too_close").withStyle(ChatFormatting.YELLOW));
			return;
		}
		Portals.openPair(level, entrance.center(), entrance.yaw(), exitLevel, exitCenter, exit.yaw(),
				player.getUUID(), false, RingTuning.PORTAL_LIFETIME.ticks());
		RingFx.send(level, Kind.BEAM, RingPowers.handPos(player), entrance.center());
		if (!player.isCreative()) PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - cost);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.PORTAL));
		player.sendOverlayMessage(PowerRingItem.chargeText(ring));
	}

	/** Sets the exit where the player looks and shows it for a moment. Free. */
	public static void setExit(ServerLevel level, ServerPlayer player, ItemStack ring) {
		Spot spot = aim(level, player);
		BlockPos foot = BlockPos.containing(spot.center().subtract(0, Portals.HALF_HEIGHT - 0.01, 0));
		PortalExit exit = new PortalExit(GlobalPos.of(level.dimension(), foot), spot.yaw());
		ring.set(ModComponents.PORTAL_EXIT, exit);
		Portals.show(level, exit.center(), exit.yaw(), player.getUUID(), 40);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), exit.center());
		boolean chest = storage(level, foot) != null;
		player.sendOverlayMessage(Component.translatable(chest ? "message.lanternring.portal_exit_chest" : "message.lanternring.portal_exit")
				.withStyle(ChatFormatting.GREEN));
		level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 0.8f);
	}

	/** The nearest chest (or barrel, hopper...) to an exit, or null. */
	public static Container storage(ServerLevel level, BlockPos foot) {
		Container best = null;
		double bestDist = Double.MAX_VALUE;
		for (BlockPos pos : BlockPos.betweenClosed(foot.offset(-STORAGE_REACH, -1, -STORAGE_REACH), foot.offset(STORAGE_REACH, 2, STORAGE_REACH))) {
			if (level.getBlockEntity(pos) == null) continue;
			Container c = HopperBlockEntity.getContainerAt(level, pos);
			if (c == null) continue;
			double d = pos.distSqr(foot);
			if (d < bestDist) {
				bestDist = d;
				best = c;
			}
		}
		return best;
	}

	/**
	 * Where a portal goes when the player aims: standing on the floor where they look, its front
	 * toward them; on a wall it stands against the wall facing out; at the sky, a few blocks ahead.
	 */
	public static Spot aim(ServerLevel level, Player player) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		BlockHitResult hit = level.clip(new ClipContext(eye, eye.add(look.scale(RANGE)), ClipContext.Block.COLLIDER,
				ClipContext.Fluid.NONE, player));
		float facePlayer = player.getYRot() + 180f;
		if (hit.getType() == HitResult.Type.MISS) {
			return standing(level, eye.add(look.scale(5)).subtract(0, 1, 0), facePlayer);
		}
		Direction face = hit.getDirection();
		Vec3 normal = face.getUnitVec3();
		if (face.getAxis().isHorizontal()) {
			return standing(level, hit.getLocation().add(normal.scale(0.5)).subtract(0, Portals.HALF_HEIGHT, 0), face.toYRot());
		}
		if (face == Direction.DOWN) {
			// Under a ceiling: hang it from there.
			Vec3 top = hit.getLocation().subtract(0, 0.05, 0);
			return new Spot(top.subtract(0, Portals.HALF_HEIGHT, 0), facePlayer);
		}
		return standing(level, hit.getLocation().add(0, 0.01, 0), facePlayer);
	}

	/** A portal whose foot is at {@code base}, dropped onto the floor if there's one just below. */
	private static Spot standing(ServerLevel level, Vec3 base, float yaw) {
		BlockPos pos = BlockPos.containing(base);
		for (int i = 0; i < 4; i++) {
			if (!level.getBlockState(pos.below()).getCollisionShape(level, pos.below()).isEmpty()) {
				base = new Vec3(base.x, pos.getY(), base.z);
				break;
			}
			pos = pos.below();
		}
		return new Spot(base.add(0, Portals.HALF_HEIGHT, 0), yaw);
	}
}
