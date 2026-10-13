package com.sparky.lanternring.item;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.RingTuning;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * The 1911 (J, 2026-10-13: "I'd even like a nice 1911 added as a new item"). Right-click fires a
 * hitscan .45 round with a muzzle flash; the magazine holds {@link #MAGAZINE}. Sneak + right-click
 * or R reloads (RingTuning.PISTOL_RELOAD), and an empty magazine reloads on the next pull.
 * The model is J's, from Blender; until it lands a flat stand-in texture is used.
 */
public class Pistol1911Item extends Item {
	public static final int MAGAZINE = 7;
	static final double RANGE = 64;
	static final float DAMAGE = 8f;
	/** Ticks between shots (semi-automatic). */
	static final int REFIRE = 4;
	private static final DustParticleOptions TRACE = new DustParticleOptions(0xFFE9A0, 0.5f);

	public Pistol1911Item(Properties properties) {
		super(properties);
	}

	public static int rounds(ItemStack stack) {
		return Mth.clamp(stack.getOrDefault(ModComponents.ROUNDS, MAGAZINE), 0, MAGAZINE);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (player.getCooldowns().isOnCooldown(stack)) return InteractionResult.FAIL;
		if (!(level instanceof ServerLevel server)) return InteractionResult.CONSUME;
		if (player.isShiftKeyDown() || rounds(stack) == 0) {
			reload(player, stack);
		} else {
			fire(server, player, stack, hand);
		}
		return InteractionResult.CONSUME;
	}

	/** Starts a reload: the magazine is full once the cooldown runs out. */
	public static void reload(Player player, ItemStack stack) {
		if (!(player.level() instanceof ServerLevel level) || player.getCooldowns().isOnCooldown(stack)) return;
		if (rounds(stack) >= MAGAZINE) return;
		stack.set(ModComponents.ROUNDS, MAGAZINE);
		player.getCooldowns().addCooldown(stack, Math.max(1, RingTuning.PISTOL_RELOAD.ticks()));
		level.playSound(null, player.blockPosition(), SoundEvents.IRON_TRAPDOOR_OPEN, SoundSource.PLAYERS, 0.6f, 1.8f);
		level.playSound(null, player.blockPosition(), SoundEvents.CROSSBOW_LOADING_END.value(), SoundSource.PLAYERS, 0.7f, 1.6f);
		if (player instanceof ServerPlayer sp) sp.sendOverlayMessage(Component.translatable("message.lanternring.pistol_reload").withStyle(ChatFormatting.GRAY));
	}

	private static void fire(ServerLevel level, Player player, ItemStack stack, InteractionHand hand) {
		stack.set(ModComponents.ROUNDS, rounds(stack) - 1);
		player.getCooldowns().addCooldown(stack, REFIRE);
		RingPowers.Target aim = RingPowers.trace(level, player, RANGE);
		Vec3 look = player.getLookAngle();
		Vec3 side = look.cross(new Vec3(0, 1, 0));
		side = side.lengthSqr() < 1e-4 ? Vec3.ZERO : side.normalize();
		float f = (player.getMainArm() == net.minecraft.world.entity.HumanoidArm.RIGHT) == (hand == InteractionHand.MAIN_HAND) ? 1f : -1f;
		Vec3 muzzle = player.getEyePosition().add(look.scale(1.5)).add(side.scale(0.35 * f)).add(0, -0.25, 0);
		// The muzzle flash and the round's trail.
		level.sendParticles(ParticleTypes.SMALL_FLAME, muzzle.x, muzzle.y, muzzle.z, 2, 0.02, 0.02, 0.02, 0.01);
		level.sendParticles(ParticleTypes.SMOKE, muzzle.x, muzzle.y, muzzle.z, 2, 0.02, 0.02, 0.02, 0.01);
		Vec3 path = aim.pos().subtract(muzzle);
		int steps = Math.min(48, (int) (path.length() * 1.5));
		for (int i = 2; i < steps; i++) {
			Vec3 p = muzzle.add(path.scale(i / (double) steps));
			level.sendParticles(TRACE, p.x, p.y, p.z, 1, 0, 0, 0, 0);
		}
		level.playSound(null, player.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.45f, 2.0f);
		level.playSound(null, player.blockPosition(), SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 1.0f, 0.8f);
		if (aim.entity() instanceof LivingEntity target) {
			target.hurtServer(level, level.damageSources().playerAttack(player), DAMAGE);
			level.sendParticles(ParticleTypes.CRIT, aim.pos().x, aim.pos().y, aim.pos().z, 6, 0.1, 0.1, 0.1, 0.2);
		} else if (aim.hitBlock()) {
			level.sendParticles(ParticleTypes.SMOKE, aim.pos().x, aim.pos().y, aim.pos().z, 4, 0.05, 0.05, 0.05, 0.02);
		}
		if (player instanceof ServerPlayer sp) {
			sp.sendOverlayMessage(Component.translatable("message.lanternring.pistol_rounds", rounds(stack), MAGAZINE).withStyle(ChatFormatting.GRAY));
		}
	}

	@Override
	public boolean allowComponentsUpdateAnimation(Player player, InteractionHand hand, ItemStack oldStack, ItemStack newStack) {
		// A round fired is still the same gun in the same hand: no lowering and raising it again.
		return false;
	}

	@Override
	public boolean isBarVisible(ItemStack stack) {
		return rounds(stack) < MAGAZINE;
	}

	@Override
	public int getBarWidth(ItemStack stack) {
		return Math.round(13f * rounds(stack) / MAGAZINE);
	}

	@Override
	public int getBarColor(ItemStack stack) {
		return 0xC8C8C8;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
		tooltip.accept(Component.translatable("message.lanternring.pistol_rounds", rounds(stack), MAGAZINE).withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("item.lanternring.pistol_1911.desc").withStyle(ChatFormatting.DARK_GRAY));
	}
}
