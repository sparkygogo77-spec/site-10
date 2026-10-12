package com.sparky.lanternring;

import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import net.minecraft.world.entity.ai.memory.WalkTarget;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.equipment.trim.ArmorTrim;
import net.minecraft.world.item.equipment.trim.TrimMaterial;
import net.minecraft.world.item.equipment.trim.TrimMaterials;
import net.minecraft.world.item.equipment.trim.TrimPattern;
import net.minecraft.world.item.equipment.trim.TrimPatterns;
import net.minecraft.world.phys.Vec3;

/**
 * The Violet Lantern's Mind Link. Right-click links every mob within {@link #RADIUS} blocks to you
 * with a violet thread: each one is given amethyst-trimmed iron armour and a sword, stops seeing you
 * (or each other) as a target, and turns on your target. Aim at a creature as you link to make it
 * the target; otherwise they go for whatever last hurt you or whatever you last hit, and follow you
 * while there's nothing to fight. Links last RingTuning.MIND_LINK_TIME; when one ends the mob gets
 * its own gear back. Linking costs {@link #COST_PER_MOB} for each mob, nearest first, as far as the
 * ring's charge goes.
 */
public final class MindLinks {
	public static final double RADIUS = 16;
	/** At most this many mobs linked to one player at a time. */
	public static final int MAX_LINKS = 24;
	/** Charge for each mob linked (2% of a full ring), on top of the mode's own cost. */
	public static final int COST_PER_MOB = 20;
	private static final double AIM_RANGE = 48;
	/** Linked mobs that can't fight by themselves hit this hard (a mob with a sword's own attack is used when it has one). */
	private static final float UNARMED_DAMAGE = 5f;
	private static final int STRIKE_INTERVAL = 20;
	/** A target that last hurt you (or that you last hit) this long ago is still fair game. */
	private static final int REVENGE_TICKS = 200;

	private static final Map<Mob, Link> LINKS = new HashMap<>();

	private static final class Link {
		final ServerPlayer owner;
		final Map<EquipmentSlot, ItemStack> ownGear = new EnumMap<>(EquipmentSlot.class);
		final Map<EquipmentSlot, Float> ownDropChance = new EnumMap<>(EquipmentSlot.class);
		long until;
		int nextStrike;

		Link(ServerPlayer owner, long until) {
			this.owner = owner;
			this.until = until;
		}
	}

	/** The creature each player has sent their linked mobs after (by aiming at it as they linked). */
	private static final Map<ServerPlayer, LivingEntity> TARGETS = new HashMap<>();

	private MindLinks() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(MindLinks::tick);
	}

	/** Whether {@code mob} is linked and {@code target} is its owner or another of the owner's linked mobs. */
	public static boolean spares(Mob mob, LivingEntity target) {
		if (target == null) return false;
		Link link = LINKS.get(mob);
		if (link == null) return false;
		if (target == link.owner) return true;
		Link other = target instanceof Mob m ? LINKS.get(m) : null;
		return other != null && other.owner == link.owner;
	}

	public static boolean isLinked(Mob mob) {
		return LINKS.containsKey(mob);
	}

	/** Mind Link: links the mobs around the player and sets the target they turn on. */
	public static boolean activate(ServerLevel level, Player user) {
		if (!(user instanceof ServerPlayer player)) return false;
		ItemStack ring = ring(player);
		LivingEntity aimed = aimed(level, player);
		long until = level.getGameTime() + RingTuning.MIND_LINK_TIME.ticks();

		int already = 0;
		for (Link link : LINKS.values()) {
			if (link.owner == player) {
				link.until = until;
				already++;
			}
		}
		List<Mob> candidates = new ArrayList<>(level.getEntitiesOfClass(Mob.class, player.getBoundingBox().inflate(RADIUS),
				mob -> canLink(player, mob) && mob != aimed));
		candidates.sort(Comparator.comparingDouble(mob -> mob.distanceToSqr(player)));

		int linked = 0;
		for (Mob mob : candidates) {
			if (already + linked >= MAX_LINKS) break;
			if (!player.isCreative() && ring != null && PowerRingItem.getCharge(ring) - RingMode.MIND_LINK.cost < COST_PER_MOB * (linked + 1)) break;
			link(level, player, mob, until);
			linked++;
		}
		if (!player.isCreative() && ring != null) PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - COST_PER_MOB * linked);

		if (aimed != null) {
			TARGETS.put(player, aimed);
			aimed.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.GLOWING, 100, 0, false, false));
		}
		if (linked == 0 && already == 0) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.mind_link_none").withStyle(ChatFormatting.LIGHT_PURPLE));
			return aimed != null;
		}
		player.sendOverlayMessage(Component.translatable("message.lanternring.mind_link", already + linked).withStyle(Corps.VIOLET.chat));
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.2f, 0.8f);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 0.7f, 1.6f);
		RingFx.send(level, RingFxPayload.Kind.CONSTRUCT, RingPowers.handPos(player), aimed != null ? aimed.getEyePosition() : player.position());
		return true;
	}

	private static boolean canLink(ServerPlayer player, Mob mob) {
		return mob.isAlive() && !mob.isNoAi() && !LINKS.containsKey(mob)
				&& !(mob instanceof ConstructAlly) && !(mob instanceof EnderDragon) && !(mob instanceof WitherBoss)
				&& mob.distanceToSqr(player) <= RADIUS * RADIUS;
	}

	/** The creature the player is looking at, if any. */
	private static LivingEntity aimed(ServerLevel level, Player player) {
		RingPowers.Target hit = RingPowers.trace(level, player, AIM_RANGE);
		return hit.entity() instanceof LivingEntity living && living.isAlive() ? living : null;
	}

	private static ItemStack ring(Player player) {
		if (player.getMainHandItem().getItem() instanceof PowerRingItem) return player.getMainHandItem();
		if (player.getOffhandItem().getItem() instanceof PowerRingItem) return player.getOffhandItem();
		return null;
	}

	private static void link(ServerLevel level, ServerPlayer player, Mob mob, long until) {
		Link link = new Link(player, until);
		LINKS.put(mob, link);
		arm(level, mob, link);
		if (mob.getTarget() == player) mob.setTarget(null);
		if (mob.getBrain().checkMemory(MemoryModuleType.ATTACK_TARGET, MemoryStatus.REGISTERED)) {
			mob.getBrain().eraseMemory(MemoryModuleType.ATTACK_TARGET);
		}
		level.sendParticles(ParticleTypes.HEART, mob.getX(), mob.getY() + mob.getBbHeight() + 0.3, mob.getZ(), 3, 0.3, 0.2, 0.3, 0);
		thread(level, player, mob, 1.0);
	}

	// ---- armour and weapons ----------------------------------------------------------------

	private static void arm(ServerLevel level, Mob mob, Link link) {
		Holder<TrimMaterial> amethyst = level.registryAccess().lookupOrThrow(Registries.TRIM_MATERIAL).getOrThrow(TrimMaterials.AMETHYST);
		Holder<TrimPattern> silence = level.registryAccess().lookupOrThrow(Registries.TRIM_PATTERN).getOrThrow(TrimPatterns.SILENCE);
		ArmorTrim trim = new ArmorTrim(amethyst, silence);
		give(mob, link, EquipmentSlot.HEAD, armour(Items.IRON_HELMET, trim));
		give(mob, link, EquipmentSlot.CHEST, armour(Items.IRON_CHESTPLATE, trim));
		give(mob, link, EquipmentSlot.LEGS, armour(Items.IRON_LEGGINGS, trim));
		give(mob, link, EquipmentSlot.FEET, armour(Items.IRON_BOOTS, trim));
		// Archers keep their bow; everyone else gets a sword.
		Item held = mob.getMainHandItem().getItem();
		boolean ranged = mob instanceof RangedAttackMob || held instanceof BowItem || held instanceof CrossbowItem;
		if (!ranged) give(mob, link, EquipmentSlot.MAINHAND, new ItemStack(Items.IRON_SWORD));
	}

	private static ItemStack armour(Item item, ArmorTrim trim) {
		ItemStack stack = new ItemStack(item);
		stack.set(DataComponents.TRIM, trim);
		return stack;
	}

	private static void give(Mob mob, Link link, EquipmentSlot slot, ItemStack stack) {
		link.ownGear.put(slot, mob.getItemBySlot(slot).copy());
		link.ownDropChance.put(slot, mob.getDropChances().byEquipment(slot));
		mob.setItemSlot(slot, stack);
		// The ring's gear fades with the link: nothing to farm.
		mob.setDropChance(slot, 0f);
	}

	private static void unlink(Mob mob, Link link) {
		LINKS.remove(mob);
		if (!mob.isAlive()) return;
		for (Map.Entry<EquipmentSlot, ItemStack> e : link.ownGear.entrySet()) {
			mob.setItemSlot(e.getKey(), e.getValue());
			mob.setDropChance(e.getKey(), link.ownDropChance.getOrDefault(e.getKey(), 0.085f));
		}
		mob.setTarget(null);
		if (mob.level() instanceof ServerLevel level) {
			Corps before = Corps.enter(Corps.VIOLET);
			try {
				level.sendParticles(ModParticles.of(ModParticles.SHARD), mob.getX(), mob.getY() + mob.getBbHeight() / 2, mob.getZ(),
						8, 0.3, 0.4, 0.3, 0.05);
			} finally {
				Corps.restore(before);
			}
		}
	}

	// ---- every tick ------------------------------------------------------------------------

	private static void tick(MinecraftServer server) {
		if (LINKS.isEmpty()) {
			TARGETS.clear();
			return;
		}
		Corps before = Corps.enter(Corps.VIOLET);
		try {
			Iterator<Map.Entry<Mob, Link>> it = LINKS.entrySet().iterator();
			List<Map.Entry<Mob, Link>> ended = new ArrayList<>();
			while (it.hasNext()) {
				Map.Entry<Mob, Link> e = it.next();
				Mob mob = e.getKey();
				Link link = e.getValue();
				ServerPlayer owner = link.owner;
				if (!mob.isAlive() || mob.isRemoved() || owner.isRemoved() || !owner.isAlive()
						|| owner.level() != mob.level() || mob.level().getGameTime() > link.until) {
					ended.add(e);
				}
			}
			for (Map.Entry<Mob, Link> e : ended) unlink(e.getKey(), e.getValue());
			TARGETS.entrySet().removeIf(e -> !e.getValue().isAlive() || e.getKey().isRemoved());

			for (Map.Entry<Mob, Link> e : LINKS.entrySet()) drive(e.getKey(), e.getValue());
		} finally {
			Corps.restore(before);
		}
	}

	/** What a linked mob does this tick: fight the owner's target, or keep close to the owner. */
	private static void drive(Mob mob, Link link) {
		if (!(mob.level() instanceof ServerLevel level)) return;
		ServerPlayer owner = link.owner;
		LivingEntity target = target(owner);
		long time = level.getGameTime();

		if (target != null && target != mob) {
			mob.setTarget(target);
			if (mob.getBrain().checkMemory(MemoryModuleType.ATTACK_TARGET, MemoryStatus.REGISTERED)) {
				mob.getBrain().setMemory(MemoryModuleType.ATTACK_TARGET, target);
			}
			// Mobs with no attack of their own (cows, villagers...) are walked up to it and strike.
			if (!fightsOnItsOwn(mob)) {
				if (time % 10 == 0) walkTo(mob, target, 1.3);
				if (mob.tickCount >= link.nextStrike && mob.isWithinMeleeAttackRange(target) && mob.hasLineOfSight(target)) {
					link.nextStrike = mob.tickCount + STRIKE_INTERVAL;
					float damage = mob.getMainHandItem().is(Items.IRON_SWORD) ? UNARMED_DAMAGE + 1 : UNARMED_DAMAGE;
					target.hurtServer(level, level.damageSources().mobAttack(mob), damage);
					Vec3 push = target.position().subtract(mob.position()).multiply(1, 0, 1).normalize().scale(0.4);
					target.push(push.x, 0.15, push.z);
					RingPowers.syncVelocity(target);
				}
			}
		} else {
			if (mob.getTarget() != null && !mob.getTarget().isAlive()) mob.setTarget(null);
			if (mob.getBrain().checkMemory(MemoryModuleType.ATTACK_TARGET, MemoryStatus.REGISTERED)) {
				mob.getBrain().eraseMemory(MemoryModuleType.ATTACK_TARGET);
			}
			if (time % 20 == 0 && mob.distanceToSqr(owner) > 8 * 8) walkTo(mob, owner, 1.2);
		}

		// The violet thread from the owner's hand.
		if ((time + mob.getId()) % 4 == 0) thread(level, owner, mob, 1.6);
	}

	private static boolean fightsOnItsOwn(Mob mob) {
		return mob.getAttributes().hasAttribute(Attributes.ATTACK_DAMAGE)
				&& !mob.getBrain().checkMemory(MemoryModuleType.WALK_TARGET, MemoryStatus.REGISTERED)
				|| mob instanceof RangedAttackMob;
	}

	private static void walkTo(Mob mob, LivingEntity to, double speed) {
		if (mob.getBrain().checkMemory(MemoryModuleType.WALK_TARGET, MemoryStatus.REGISTERED)) {
			mob.getBrain().setMemory(MemoryModuleType.WALK_TARGET, new WalkTarget(to, (float) speed, 1));
		} else {
			mob.getNavigation().moveTo(to, speed);
		}
	}

	/** The creature a player's linked mobs go for: the one aimed at, else whoever last hurt the player or was last hit by them. */
	private static LivingEntity target(ServerPlayer owner) {
		LivingEntity aimed = TARGETS.get(owner);
		if (aimed != null && aimed.isAlive() && aimed.level() == owner.level()) return aimed;
		int now = owner.tickCount;
		LivingEntity hit = owner.getLastHurtMob();
		if (valid(owner, hit) && now - owner.getLastHurtMobTimestamp() < REVENGE_TICKS) return hit;
		LivingEntity attacker = owner.getLastHurtByMob();
		if (valid(owner, attacker) && now - owner.getLastHurtByMobTimestamp() < REVENGE_TICKS) return attacker;
		return null;
	}

	private static boolean valid(ServerPlayer owner, LivingEntity entity) {
		if (entity == null || !entity.isAlive() || entity == owner || entity.level() != owner.level()) return false;
		Link link = entity instanceof Mob m ? LINKS.get(m) : null;
		return link == null || link.owner != owner;
	}

	/** A line of violet motes from the owner's hand to the mob. */
	private static void thread(ServerLevel level, Player owner, Mob mob, double spacing) {
		Vec3 from = RingPowers.handPos(owner);
		Vec3 to = mob.position().add(0, mob.getBbHeight() * 0.6, 0);
		Vec3 d = to.subtract(from);
		double len = d.length();
		if (len < 0.5 || len > 64) return;
		Vec3 step = d.scale(spacing / len);
		Vec3 at = from;
		for (double t = 0; t < len; t += spacing) {
			level.sendParticles(ModParticles.of(ModParticles.SPARK), at.x, at.y, at.z, 1, 0.02, 0.02, 0.02, 0);
			at = at.add(step);
		}
	}

	/** How many mobs a player has linked right now (for tests). */
	public static int linkedTo(Player player) {
		int n = 0;
		for (Link link : LINKS.values()) if (link.owner == player) n++;
		return n;
	}
}
