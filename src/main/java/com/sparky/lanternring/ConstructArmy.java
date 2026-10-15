package com.sparky.lanternring;

import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.ally.FlyingConstruct;
import com.sparky.lanternring.ally.ModEntities;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.entity.EntityTypeTest;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Army mode: hold right-click to aim, left-click while holding to pick the construct, let go to
 * summon it. Each one takes a share of the ring's charge and lives on it (see ConstructAlly):
 * a full share keeps it going for RingTuning.ALLY_LIFETIME. With less than that left, it takes
 * the last of the charge and lasts that much less. Crouch as you let go to pour all of the ring's
 * charge into it: a long-lived protector to leave on guard while you do something else.
 */
public final class ConstructArmy {
	/** At most this many allies per player; another one replaces the oldest. */
	public static final int MAX_ALLIES = 4;
	private static final double AIM_RANGE = 24;

	public enum Type {
		WARDEN("warden", 250),
		DRAGON("dragon", 250),
		SENTRY("sentry", 150),
		/** Blender pass 828 (J kept P2 hex and P3 weave): a cheap hard-light pig that rams. Last, so saved rings keep their pick. */
		PIG("pig", 100);

		public final String key;
		/** Charge for a full share (0.1% each). */
		public final int cost;

		Type(String key, int cost) {
			this.key = key;
			this.cost = cost;
		}

		public Component displayName() {
			return Component.translatable("ally.lanternring." + key);
		}

		EntityType<? extends ConstructAlly> entityType() {
			return switch (this) {
				case WARDEN -> ModEntities.WARDEN;
				case DRAGON -> ModEntities.DRAGON;
				case SENTRY -> ModEntities.SENTRY;
				case PIG -> ModEntities.PIG;
			};
		}
	}

	private ConstructArmy() {
	}

	public static Type type(ItemStack ring) {
		Type[] types = Type.values();
		return types[Math.floorMod(ring.getOrDefault(ModComponents.ARMY_TYPE, 0), types.length)];
	}

	public static Component typeText(Type type) {
		return Component.translatable("message.lanternring.army_type", type.displayName(), String.valueOf(type.cost / 10));
	}

	/** Left-click while holding right-click: the next kind of construct. */
	public static void cycle(ServerPlayer player, ItemStack ring) {
		Type next = Type.values()[(type(ring).ordinal() + 1) % Type.values().length];
		ring.set(ModComponents.ARMY_TYPE, next.ordinal());
		player.sendOverlayMessage(typeText(next).copy().withStyle(Corps.of(ring).chat));
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.2f + 0.2f * next.ordinal());
	}

	/** Every tick right-click is held: a glowing ring where it will form. */
	public static void aimTick(ServerPlayer player, ItemStack ring, int held) {
		if (held == 1) player.sendOverlayMessage(typeText(type(ring)).copy().withStyle(Corps.of(ring).chat));
		if (held % 3 != 0) return;
		RingFx.send(player.level(), RingFxPayload.Kind.ALLY_MARK, spot(player, type(ring)), spot(player, type(ring)), 0f, type(ring).ordinal(), player);
	}

	/** Where the chosen construct forms: on the ground where you look (the Dragon and Sentry above it). */
	static Vec3 spot(Player player, Type type) {
		ServerLevel level = (ServerLevel) player.level();
		Vec3 eye = player.getEyePosition();
		Vec3 end = eye.add(player.getLookAngle().scale(AIM_RANGE));
		BlockHitResult hit = level.clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		Vec3 at = hit.getType() == HitResult.Type.MISS ? end : hit.getLocation().add(player.getLookAngle().scale(-0.6));
		// Down to the ground below that point, if there is some within a few blocks.
		BlockPos pos = BlockPos.containing(at);
		for (int i = 0; i < 12 && level.getBlockState(pos.below()).getCollisionShape(level, pos.below()).isEmpty(); i++) pos = pos.below();
		Vec3 ground = new Vec3(at.x, pos.getY(), at.z);
		return switch (type) {
			case WARDEN, PIG -> ground;
			case DRAGON -> ground.add(0, 4, 0);
			case SENTRY -> ground.add(0, 2.5, 0);
		};
	}

	/** Letting go of right-click: the construct forms, paid for from the ring. */
	public static void release(ServerPlayer player, ItemStack ring) {
		ServerLevel level = player.level();
		Type type = type(ring);
		int charge = PowerRingItem.getCharge(ring);
		boolean allIn = player.isShiftKeyDown();
		int paid;
		if (player.isCreative()) {
			paid = allIn ? PowerRingItem.MAX_CHARGE : type.cost;
		} else if (charge <= 0) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
			return;
		} else {
			paid = allIn ? charge : Math.min(charge, type.cost);
		}

		ConstructAlly ally = type.entityType().create(level, EntitySpawnReason.MOB_SUMMONED);
		if (ally == null) return;
		Vec3 at = spot(player, type);
		ally.snapTo(at.x, at.y, at.z, player.getYRot() + 180f, 0f);
		ally.setup(player, Math.max(20, (int) ((long) RingTuning.ALLY_LIFETIME.ticks() * paid / type.cost)));
		if (ally instanceof FlyingConstruct flying) flying.setHome(at);
		makeRoom(level, player);
		level.addFreshEntity(ally);

		if (!player.isCreative()) PowerRingItem.setCharge(ring, charge - paid);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.ARMY));
		RingFx.send(level, RingFxPayload.Kind.CONSTRUCT, RingPowers.handPos(player), at.add(0, ally.getBbHeight() / 2, 0));
		RingFx.send(level, RingFxPayload.Kind.ALLY_SUMMON, at, at.add(0, ally.getBbHeight(), 0), ally.getBbWidth(), type.ordinal());
		level.playSound(null, at.x, at.y, at.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.5f, 0.7f);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1f, 1.3f);

		int seconds = Math.round(ally.life() / 20f);
		Component note = allIn || paid < type.cost
				? Component.translatable("message.lanternring.army_all_in", type.displayName(), String.valueOf(paid / 10), String.valueOf(seconds))
				: Component.translatable("message.lanternring.army_summoned", type.displayName(), String.valueOf(seconds));
		player.sendOverlayMessage(note.copy().withStyle(Corps.of(ring).chat));
	}

	/** Each player keeps at most MAX_ALLIES; the oldest one goes to make room for a new one. */
	private static void makeRoom(ServerLevel level, Player player) {
		List<ConstructAlly> mine = new ArrayList<>(level.getEntities(EntityTypeTest.forClass(ConstructAlly.class),
				ally -> player.getUUID().equals(ally.ownerId())));
		if (mine.size() < MAX_ALLIES) return;
		mine.sort(Comparator.comparingInt((ConstructAlly a) -> a.tickCount).reversed());
		for (int i = 0; i <= mine.size() - MAX_ALLIES; i++) mine.get(i).shatter(level);
	}
}
