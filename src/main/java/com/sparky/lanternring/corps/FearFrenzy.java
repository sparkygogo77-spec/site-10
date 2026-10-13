package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.item.ConstructWeaponItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.illager.AbstractIllager;
import net.minecraft.world.entity.monster.piglin.AbstractPiglin;
import net.minecraft.world.entity.monster.skeleton.AbstractSkeleton;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.SwingAnimation;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Fear Nuke's frenzy and its yellow gas (J, 2026-10-13: "they go crazy and start killing each
 * other and the yellow gas gives them yellow construct weapons to do it, villagers with crossbows
 * AKs"). Every mob the gas reaches gets Fear Frenzy (FrenzyEffect) for RingTuning.FEAR_FRENZY and
 * is handed a yellow construct weapon for RingTuning.FEAR_WEAPON at most:
 * <ul>
 * <li>villagers: an AK-style construct rifle (bursts of hard-light rounds) or a construct crossbow;</li>
 * <li>zombies, piglins and other monsters: a construct blade or crossbow (skeletons and illagers
 * shoot: crossbow or rifle);</li>
 * <li>animals fight with what they have.</li>
 * </ul>
 * A frenzied mob drops whatever it was doing and goes for the nearest other living thing, so they
 * kill each other. The nuke's bearer and Yellow Lanterns are spared, and players are never forced.
 * The gas lingers for RingTuning.FEAR_GAS, frenzying whatever walks in; each client draws it as a
 * darkening yellow fog (FearGasFx).
 */
public final class FearFrenzy {
	enum Weapon { RIFLE, CROSSBOW, BLADE, NONE }

	/** How far a frenzied mob looks for something to kill, and how far its guns reach. */
	static final double SEEK = 24, GUN_RANGE = 22;
	private static final DustParticleOptions GAS = new DustParticleOptions(0xD9B428, 3.5f);

	private static final class State {
		@Nullable UUID owner;
		@Nullable LivingEntity target;
		Weapon weapon = Weapon.NONE;
		ItemStack before = ItemStack.EMPTY;
		boolean armed;
		int cooldown, burst;
	}

	private static final Map<Mob, State> FRENZIED = new WeakHashMap<>();

	private static final class Gas {
		final ServerLevel level;
		final Vec3 centre;
		final double radius;
		final long end;
		final @Nullable UUID owner;

		Gas(ServerLevel level, Vec3 centre, double radius, long end, @Nullable UUID owner) {
			this.level = level;
			this.centre = centre;
			this.radius = radius;
			this.end = end;
			this.owner = owner;
		}
	}

	private static final List<Gas> GASES = new ArrayList<>();

	private FearFrenzy() {
	}

	/** Whether the gas can take {@code e}: any mob but the bearer's own constructs, armour stands and Yellow Lanterns. */
	static boolean takes(LivingEntity e, @Nullable UUID owner) {
		return e instanceof Mob && e.isAlive() && !(e instanceof ArmorStand) && !FearNuke.spared(e, owner);
	}

	/** Frenzies {@code mob} for RingTuning.FEAR_FRENZY (the nuke's bearer is spared from its attacks). */
	public static void frenzy(ServerLevel level, Mob mob, @Nullable UUID owner) {
		mob.addEffect(new MobEffectInstance(ModEffects.FRENZY, Math.max(20, RingTuning.FEAR_FRENZY.ticks()), 0, false, true));
		State s = FRENZIED.computeIfAbsent(mob, m -> new State());
		if (owner != null) s.owner = owner;
	}

	/** The yellow gas starts lingering round {@code centre}, frenzying every mob inside it now and later. */
	public static void gas(ServerLevel level, Vec3 centre, double radius, @Nullable UUID owner) {
		int ticks = Math.max(20, RingTuning.FEAR_GAS.ticks());
		GASES.add(new Gas(level, centre, radius, level.getGameTime() + ticks, owner));
		Corps before = Corps.enter(Corps.YELLOW);
		try {
			RingFx.send(level, Kind.FEAR_GAS, centre, centre.add(radius, 0, 0), ticks);
		} finally {
			Corps.restore(before);
		}
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(centre, centre).inflate(radius),
				e -> e.distanceToSqr(centre) < radius * radius && takes(e, owner))) {
			frenzy(level, (Mob) e, owner);
		}
	}

	static Weapon weaponFor(Mob mob) {
		boolean coin = mob.getRandom().nextBoolean();
		if (mob instanceof AbstractVillager) return coin ? Weapon.RIFLE : Weapon.CROSSBOW;
		if (mob instanceof AbstractSkeleton) return Weapon.CROSSBOW;
		if (mob instanceof AbstractIllager) return coin ? Weapon.RIFLE : Weapon.CROSSBOW;
		if (mob instanceof Zombie || mob instanceof AbstractPiglin) return coin ? Weapon.BLADE : Weapon.CROSSBOW;
		if (mob instanceof Monster) return Weapon.BLADE;
		return Weapon.NONE;
	}

	private static @Nullable Item item(Weapon w) {
		return switch (w) {
			case RIFLE -> ModRegistry.CONSTRUCT_RIFLE;
			case CROSSBOW -> ModRegistry.CONSTRUCT_CROSSBOW;
			case BLADE -> ModRegistry.CONSTRUCT_BLADE;
			case NONE -> null;
		};
	}

	/** The gas forms a weapon in the mob's hand. */
	private static void arm(ServerLevel level, Mob mob, State s) {
		s.armed = true;
		s.weapon = weaponFor(mob);
		Item item = item(s.weapon);
		if (item == null) return;
		ItemStack held = mob.getItemBySlot(EquipmentSlot.MAINHAND);
		s.before = held.getItem() instanceof ConstructWeaponItem ? ItemStack.EMPTY : held.copy();
		MobEffectInstance effect = mob.getEffect(ModEffects.FRENZY);
		int life = Math.max(20, RingTuning.FEAR_WEAPON.ticks());
		if (effect != null && !effect.isInfiniteDuration()) life = Math.min(life, effect.getDuration());
		ItemStack weapon = new ItemStack(item);
		weapon.set(ModComponents.FADES_AT, level.getGameTime() + life);
		mob.setItemSlot(EquipmentSlot.MAINHAND, weapon);
		mob.setDropChance(EquipmentSlot.MAINHAND, 0f);
		Vec3 hand = mob.position().add(0, mob.getBbHeight() * 0.6, 0);
		level.sendParticles(GAS, hand.x, hand.y, hand.z, 6, 0.2, 0.2, 0.2, 0);
		level.playSound(null, mob.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.HOSTILE, 0.8f, 0.6f);
	}

	/** The weapon fades and the mob gets back what it held. */
	private static void disarm(Mob mob, State s) {
		if (mob.getItemBySlot(EquipmentSlot.MAINHAND).getItem() instanceof ConstructWeaponItem) {
			mob.setItemSlot(EquipmentSlot.MAINHAND, s.before);
			if (!s.before.isEmpty()) mob.setDropChance(EquipmentSlot.MAINHAND, 0.085f);
			if (mob.level() instanceof ServerLevel level) {
				Vec3 hand = mob.position().add(0, mob.getBbHeight() * 0.6, 0);
				level.sendParticles(GAS, hand.x, hand.y, hand.z, 4, 0.2, 0.2, 0.2, 0);
			}
		}
		s.weapon = Weapon.NONE;
		s.before = ItemStack.EMPTY;
	}

	private static boolean valid(Mob mob, @Nullable LivingEntity t, @Nullable UUID owner) {
		return t != null && t.isAlive() && t != mob && t.level() == mob.level() && t.distanceToSqr(mob) < SEEK * SEEK * 1.5
				&& !(t instanceof ArmorStand) && !FearNuke.spared(t, owner);
	}

	private static @Nullable LivingEntity seek(ServerLevel level, Mob mob, @Nullable UUID owner) {
		LivingEntity best = null;
		double bestD = SEEK * SEEK;
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().inflate(SEEK), e -> valid(mob, e, owner))) {
			double d = e.distanceToSqr(mob);
			if (d < bestD) {
				bestD = d;
				best = e;
			}
		}
		return best;
	}

	/** One tick of a frenzied mob (from FrenzyEffect): find the nearest thing alive and kill it. */
	public static void frenzyTick(ServerLevel level, Mob mob) {
		if (mob instanceof ConstructAlly) return;
		State s = FRENZIED.computeIfAbsent(mob, m -> new State());
		if (!s.armed) arm(level, mob, s);
		if (s.weapon != Weapon.NONE && ConstructWeaponItem.faded(mob.getItemBySlot(EquipmentSlot.MAINHAND), level.getGameTime())) disarm(mob, s);
		if (s.cooldown > 0) s.cooldown--;
		if (!valid(mob, s.target, s.owner) || mob.tickCount % 20 == 0) {
			LivingEntity next = seek(level, mob, s.owner);
			if (next != null || !valid(mob, s.target, s.owner)) s.target = next;
		}
		LivingEntity t = s.target;
		if (t == null) return;
		if (mob.getTarget() != t) mob.setTarget(t);
		mob.getLookControl().setLookAt(t, 30f, 30f);
		double d = mob.distanceTo(t);
		boolean gun = s.weapon == Weapon.RIFLE || s.weapon == Weapon.CROSSBOW;
		boolean sees = mob.hasLineOfSight(t);
		if (gun && d < GUN_RANGE * 0.7 && sees) {
			if (mob.tickCount % 10 == 0) mob.getNavigation().stop();
		} else if (mob.tickCount % 6 == 0) {
			mob.getNavigation().moveTo(t, gun ? 1.1 : 1.35);
		}
		if (s.cooldown > 0) return;
		switch (s.weapon) {
			case RIFLE -> {
				if (d > GUN_RANGE || !sees) return;
				// Bursts of three hard-light rounds.
				CorpsShots.shoot(level, mob, t, Corps.YELLOW, 2f);
				s.cooldown = ++s.burst < 3 ? 3 : 24;
				if (s.burst >= 3) s.burst = 0;
			}
			case CROSSBOW -> {
				if (d > GUN_RANGE || !sees) return;
				CorpsShots.shoot(level, mob, t, Corps.YELLOW, 5f);
				level.playSound(null, mob.blockPosition(), SoundEvents.CROSSBOW_SHOOT, SoundSource.HOSTILE, 1f, 1.2f);
				s.cooldown = 30;
			}
			default -> {
				double reach = (mob.getBbWidth() + t.getBbWidth()) / 2 + 1.3;
				if (d > reach) return;
				mob.swing(InteractionHand.MAIN_HAND, SwingAnimation.DEFAULT, true);
				float damage = s.weapon == Weapon.BLADE ? 5f : 2f;
				if (t.hurtServer(level, level.damageSources().mobAttack(mob), damage) && s.weapon == Weapon.BLADE) {
					level.playSound(null, t.blockPosition(), SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.HOSTILE, 0.8f, 1.4f);
				}
				s.cooldown = 20;
			}
		}
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<Mob, State>> it = FRENZIED.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<Mob, State> e = it.next();
			Mob mob = e.getKey();
			if (!mob.isAlive() || !mob.hasEffect(ModEffects.FRENZY)) {
				disarm(mob, e.getValue());
				it.remove();
			}
		}
		for (Iterator<Gas> it = GASES.iterator(); it.hasNext(); ) {
			Gas g = it.next();
			long now = g.level.getGameTime();
			if (now >= g.end) {
				it.remove();
				continue;
			}
			if (now % 10 == 0) {
				for (LivingEntity e : g.level.getEntitiesOfClass(LivingEntity.class, new AABB(g.centre, g.centre).inflate(g.radius),
						e -> e.distanceToSqr(g.centre) < g.radius * g.radius && takes(e, g.owner) && !e.hasEffect(ModEffects.FRENZY))) {
					frenzy(g.level, (Mob) e, g.owner);
				}
			}
		}
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(FearFrenzy::tick);
		// A construct weapon saved on a mob when the game closed fades as it loads (the frenzy re-arms it if it's still on).
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof Mob mob && mob.getItemBySlot(EquipmentSlot.MAINHAND).getItem() instanceof ConstructWeaponItem
					&& !FRENZIED.containsKey(mob)) {
				mob.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
			}
		});
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Map.Entry<Mob, State> e : FRENZIED.entrySet()) disarm(e.getKey(), e.getValue());
			FRENZIED.clear();
			GASES.clear();
		});
	}
}
