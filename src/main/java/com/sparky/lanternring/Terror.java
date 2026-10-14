package com.sparky.lanternring;

import com.sparky.lanternring.ally.BroodSpider;
import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.ally.ModEntities;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.EntityReference;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.entity.EntityTypeTest;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Yellow Lantern's Fear mode. Used on a mob (or the ground), it strikes terror into it and
 * everything within a few blocks: Fear (see FearEffect), Weakness and Slowness for
 * RingTuning.FEAR_TIME. Used again on a mob it frightened, the Brood comes for it: a giant
 * hard-light spider and its spiderlings crawl out of the darkness round the mob, from every side
 * but yours, and hunt it down (see BroodSpider).
 *
 * <p>A green ring at full charge can't be frightened: will overcomes fear.
 */
public final class Terror {
	private static final double RANGE = 32;
	/** Everything this close to the target is frightened with it. */
	private static final double SPREAD = 4;
	/** What the Brood costs on top of the Fear itself (0.1% each). */
	public static final int BROOD_COST = 120;
	private static final int SPIDERLINGS = 6;

	private record Fear(UUID fearer, long since) {
	}

	/** Who frightened each feared mob, and when. */
	private static final Map<LivingEntity, Fear> FEARED = new WeakHashMap<>();

	private Terror() {
	}

	public static boolean activate(ServerLevel level, Player player) {
		RingPowers.Target aim = RingPowers.trace(level, player, RANGE);
		LivingEntity target = aim.entity() instanceof LivingEntity living && canFear(player, living) ? living : null;
		if (target != null && fearedBy(target, player)) return brood(level, player, target);

		Vec3 at = target != null ? target.position() : aim.pos();
		List<LivingEntity> victims = target == null && !aim.hitBlock() ? List.of()
				: level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(SPREAD), e -> canFear(player, e));
		if (victims.isEmpty()) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.fear_nothing").withStyle(ChatFormatting.YELLOW));
			return false;
		}
		int ticks = RingTuning.FEAR_TIME.ticks();
		for (LivingEntity victim : victims) {
			victim.addEffect(new MobEffectInstance(ModEffects.FEAR, ticks, 0, false, true), player);
			victim.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, ticks, 1, false, false), player);
			victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, ticks, 0, false, false), player);
			FEARED.put(victim, new Fear(player.getUUID(), level.getGameTime()));
		}
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), at.add(0, target != null ? target.getBbHeight() / 2 : 0.5, 0));
		level.playSound(null, at.x, at.y, at.z, SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 2f, 0.6f);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.SCULK_SHRIEKER_SHRIEK, SoundSource.PLAYERS, 0.6f, 0.5f);
		level.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y + 1, at.z, 40, SPREAD / 2, 0.8, SPREAD / 2, 0.02);
		Component note = victims.size() == 1
				? Component.translatable("message.lanternring.feared", victims.getFirst().getDisplayName())
				: Component.translatable("message.lanternring.feared_many", String.valueOf(victims.size()));
		player.sendOverlayMessage(note.copy().withStyle(ChatFormatting.YELLOW));
		return true;
	}

	/** A Yellow construct's hit: Fear and Weakness for {@code ticks}, counted as {@code owner}'s, so the Brood can follow up. */
	public static void frighten(ServerLevel level, LivingEntity victim, UUID owner, int ticks) {
		if (victim instanceof Player p && (p.isCreative() || p.isSpectator())) return;
		victim.addEffect(new MobEffectInstance(ModEffects.FEAR, ticks, 0, false, true));
		victim.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, ticks, 0, false, false));
		Fear old = FEARED.get(victim);
		FEARED.put(victim, old != null && old.fearer.equals(owner) && victim.hasEffect(ModEffects.FEAR) ? old : new Fear(owner, level.getGameTime()));
	}

	/** Mobs and other players; not you, your pets, constructs, armour stands, creative players or a fully charged green ring. */
	public static boolean canFear(Player player, LivingEntity e) {
		if (e == player || !e.isAlive() || e instanceof ConstructAlly || e instanceof ArmorStand) return false;
		if (e instanceof OwnableEntity pet) {
			EntityReference<LivingEntity> owner = pet.getOwnerReference();
			if (owner != null && owner.getUUID().equals(player.getUUID())) return false;
		}
		if (e instanceof Player other) {
			if (other.isCreative() || other.isSpectator()) return false;
			for (ItemStack ring : new ItemStack[] {other.getMainHandItem(), other.getOffhandItem(), com.sparky.lanternring.RingSlot.worn(other)}) {
				if (ring.getItem() instanceof PowerRingItem && Corps.of(ring) == Corps.GREEN
						&& PowerRingItem.getCharge(ring) >= PowerRingItem.MAX_CHARGE) return false;
			}
		}
		return true;
	}

	/** The nearest mob {@code owner} frightened within {@code range} of {@code at}, or null. */
	public static @Nullable LivingEntity nearestFeared(ServerLevel level, Vec3 at, double range, UUID owner) {
		LivingEntity best = null;
		double bestD = range * range;
		for (Map.Entry<LivingEntity, Fear> e : FEARED.entrySet()) {
			LivingEntity m = e.getKey();
			if (m.level() != level || !m.isAlive() || !e.getValue().fearer.equals(owner) || !m.hasEffect(ModEffects.FEAR)) continue;
			double d = m.distanceToSqr(at);
			if (d < bestD) {
				bestD = d;
				best = m;
			}
		}
		return best;
	}

	/** How many living mobs {@code owner} has frightened within {@code range} of {@code at}. */
	public static int fearedNear(ServerLevel level, Vec3 at, double range, UUID owner) {
		int n = 0;
		for (Map.Entry<LivingEntity, Fear> e : FEARED.entrySet()) {
			LivingEntity m = e.getKey();
			if (m.level() == level && m.isAlive() && e.getValue().fearer.equals(owner) && m.hasEffect(ModEffects.FEAR)
					&& m.distanceToSqr(at) < range * range) n++;
		}
		return n;
	}

	/** Whoever frightened this mob, or null (public for the Fear Nuke, which counts what dies afraid). */
	public static @Nullable UUID fearerId(LivingEntity e) {
		Fear fear = FEARED.get(e);
		return fear == null ? null : fear.fearer;
	}

	static boolean fearedBy(LivingEntity e, Player player) {
		Fear fear = FEARED.get(e);
		return fear != null && fear.fearer.equals(player.getUUID()) && e.hasEffect(ModEffects.FEAR);
	}

	/** Who frightened this mob, if they're still around. */
	static @Nullable Player fearer(ServerLevel level, LivingEntity e) {
		Fear fear = FEARED.get(e);
		return fear == null ? null : level.getPlayerByUUID(fear.fearer);
	}

	/** Ticks since this mob was frightened (40, fully closed in, if it drank its fear). */
	static long fearedFor(ServerLevel level, LivingEntity e) {
		Fear fear = FEARED.get(e);
		return fear == null ? 40 : level.getGameTime() - fear.since;
	}

	/** Whether the Brood may go for this mob: something its owner frightened. */
	public static boolean isPreyOf(LivingEntity e, @Nullable UUID owner) {
		Fear fear = FEARED.get(e);
		return owner != null && fear != null && fear.fearer.equals(owner) && e.hasEffect(ModEffects.FEAR);
	}

	/** The giant spider and its spiderlings crawl out of the dark round the target. */
	private static boolean brood(ServerLevel level, Player player, LivingEntity target) {
		ItemStack ring = RingSlot.ring(player);
		if (!player.isCreative()) {
			int charge = PowerRingItem.getCharge(ring);
			if (charge < RingMode.FEAR.cost + BROOD_COST) {
				player.sendOverlayMessage(Component.translatable("message.lanternring.brood_no_charge").withStyle(ChatFormatting.RED));
				level.playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
				return false;
			}
			PowerRingItem.setCharge(ring, charge - BROOD_COST);
		}
		// One brood at a time: the last one fades back into the dark.
		for (BroodSpider old : level.getEntities(EntityTypeTest.forClass(BroodSpider.class), s -> player.getUUID().equals(s.ownerId()))) {
			old.shatter(level);
		}
		// They come from the far side of it, never from behind you.
		Vec3 away = target.position().subtract(player.position()).multiply(1, 0, 1);
		double base = away.lengthSqr() < 1e-4 ? player.getYRot() * Mth.DEG_TO_RAD : Math.atan2(away.z, away.x);
		var random = target.getRandom();
		spawn(level, player, target, ModEntities.BROOD_SPIDER, base, 9);
		for (int i = 0; i < SPIDERLINGS; i++) {
			double angle = base + (i - (SPIDERLINGS - 1) / 2.0) * 0.5 + (random.nextDouble() - 0.5) * 0.3;
			spawn(level, player, target, ModEntities.SPIDERLING, angle, 6.5 + random.nextDouble() * 3);
		}
		// Keep it afraid while they come.
		int ticks = RingTuning.FEAR_TIME.ticks();
		target.addEffect(new MobEffectInstance(ModEffects.FEAR, ticks, 0, false, true), player);
		target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, ticks, 1, false, false), player);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), target.position().add(0, target.getBbHeight() / 2, 0));
		level.playSound(null, target.getX(), target.getY(), target.getZ(), SoundEvents.WARDEN_EMERGE, SoundSource.PLAYERS, 1.2f, 1.4f);
		player.sendOverlayMessage(Component.translatable("message.lanternring.brood").withStyle(ChatFormatting.YELLOW));
		return true;
	}

	private static void spawn(ServerLevel level, Player player, LivingEntity target, EntityType<BroodSpider> type, double angle, double distance) {
		BroodSpider spider = type.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (spider == null) return;
		Vec3 spot = ground(level, target.position().add(Math.cos(angle) * distance, 0, Math.sin(angle) * distance));
		float yaw = (float) (Mth.atan2(target.getZ() - spot.z, target.getX() - spot.x) * Mth.RAD_TO_DEG) - 90f;
		spider.snapTo(spot.x, spot.y, spot.z, yaw, 0f);
		spider.setYHeadRot(yaw);
		spider.setup(player, RingTuning.BROOD_LIFETIME.ticks());
		spider.setPrey(target);
		level.addFreshEntity(spider);
		double w = spider.getBbWidth() / 2;
		level.sendParticles(ParticleTypes.LARGE_SMOKE, spot.x, spot.y + 0.5, spot.z, spider.isGiant() ? 50 : 15, w + 0.4, 0.6, w + 0.4, 0.03);
		level.sendParticles(ParticleTypes.SQUID_INK, spot.x, spot.y + 0.5, spot.z, spider.isGiant() ? 25 : 6, w, 0.4, w, 0.05);
		level.playSound(null, spot.x, spot.y, spot.z, SoundEvents.SPIDER_AMBIENT, SoundSource.HOSTILE,
				spider.isGiant() ? 2f : 0.8f, spider.isGiant() ? 0.45f : 1.5f);
	}

	/** The ground near {@code at}: the first open spot with something solid under it, a few blocks up or down. */
	private static Vec3 ground(ServerLevel level, Vec3 at) {
		BlockPos start = BlockPos.containing(at);
		for (int dy = 4; dy >= -8; dy--) {
			BlockPos pos = start.above(dy);
			if (level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()
					&& level.getBlockState(pos.above()).getCollisionShape(level, pos.above()).isEmpty()
					&& !level.getBlockState(pos.below()).getCollisionShape(level, pos.below()).isEmpty()) {
				return new Vec3(at.x, pos.getY(), at.z);
			}
		}
		return at;
	}
}
