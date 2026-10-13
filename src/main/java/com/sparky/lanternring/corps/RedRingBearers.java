package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.monster.warden.Warden;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Red rings choose their own bearers (J, 2026-10-13: "your red rings have to find wardens and
 * whatever dangerous mobs that would ruthlessly kill out of rage, they'll be powerful"). Any monster
 * that kills something may be chosen ({@link #KILL_CHANCE}): a red ring streaks down out of the sky
 * onto it. Every {@link RingTuning#RED_RING_SEEK} a standing Red sanctuary also sends a ring out to
 * the nearest monster. A bearer has double health and damage, carries Red rage (its aura and
 * dripping blood) and passes it to whatever it hits, spits burning blood bolts, and flies at its
 * prey in a red glow. It spares anyone holding a red ring, like the sanctuary's own.
 */
public final class RedRingBearers {
	public static final String TAG = "lanternring.red_ring_bearer";
	/** Chance a monster's kill draws a red ring to it. */
	public static float KILL_CHANCE = 0.35f;
	/** How far a sanctuary's ring flies out to find a bearer, and how many bearers it allows nearby. */
	private static final int SEEK_RANGE = 48, SEEK_CAP = 4;
	private static final double RING_SPEED = 0.9, FLY_SPEED = 0.38;
	private static final Identifier HEALTH_ID = LanternRing.id("red_ring_health");
	private static final Identifier DAMAGE_ID = LanternRing.id("red_ring_damage");

	/** A ring on its way to the monster it chose. */
	private static final class Flight {
		final ServerLevel level;
		Vec3 pos;
		final Mob target;
		int ticks;

		Flight(ServerLevel level, Vec3 pos, Mob target) {
			this.level = level;
			this.pos = pos;
			this.target = target;
		}
	}

	private static final List<Flight> FLIGHTS = new ArrayList<>();
	private static final Map<UUID, Mob> BEARERS = new HashMap<>();
	private static long nextSeek;

	private RedRingBearers() {
	}

	public static void register() {
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof Mob mob && bearer(mob)) BEARERS.put(mob.getUUID(), mob);
		});
		ServerLivingEntityEvents.AFTER_DEATH.register((victim, source) -> {
			if (source.getEntity() instanceof Mob killer && killer instanceof Enemy && killer != victim && killer.isAlive()
					&& !bearer(killer) && !chosen(killer) && killer.level() instanceof ServerLevel level
					&& level.getRandom().nextFloat() < KILL_CHANCE) {
				// It streaks in from high above, off to one side.
				double a = level.getRandom().nextDouble() * Math.PI * 2;
				send(level, killer.position().add(Math.cos(a) * 10, 16, Math.sin(a) * 10), killer);
			}
		});
		// Rage spreads to whatever a bearer hurts (players get it already through RedRage).
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, base, taken, blocked) -> {
			if (taken > 0 && !(entity instanceof Player) && (bearer(source.getEntity()) || bearer(source.getDirectEntity()))) RedRage.give(entity);
		});
		ServerTickEvents.END_SERVER_TICK.register(RedRingBearers::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			FLIGHTS.clear();
			BEARERS.clear();
			nextSeek = 0;
		});
	}

	public static boolean bearer(@Nullable Entity e) {
		return e != null && e.entityTags().contains(TAG);
	}

	private static boolean chosen(Mob mob) {
		for (Flight f : FLIGHTS) if (f.target == mob) return true;
		return false;
	}

	/** Sends a red ring flying from {@code from} to the monster it chose. */
	public static void send(ServerLevel level, Vec3 from, Mob target) {
		FLIGHTS.add(new Flight(level, from, target));
		level.playSound(null, target.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.HOSTILE, 2f, 0.5f);
	}

	/** The ring slips on: the monster becomes a Red Lantern. */
	public static void crown(ServerLevel level, Mob mob) {
		if (bearer(mob)) return;
		mob.addTag(TAG);
		mob.setPersistenceRequired();
		if (mob.getMainHandItem().isEmpty()) mob.setItemSlot(EquipmentSlot.MAINHAND, Corps.RED.ring());
		else if (mob.getOffhandItem().isEmpty()) mob.setItemSlot(EquipmentSlot.OFFHAND, Corps.RED.ring());
		boost(mob.getAttribute(Attributes.MAX_HEALTH), HEALTH_ID);
		boost(mob.getAttribute(Attributes.ATTACK_DAMAGE), DAMAGE_ID);
		mob.setHealth(mob.getMaxHealth());
		RedRage.give(mob);
		BEARERS.put(mob.getUUID(), mob);
		Vec3 mid = mob.position().add(0, mob.getBbHeight() * 0.5, 0);
		level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.RED), mid.x, mid.y, mid.z, 40, mob.getBbWidth(), mob.getBbHeight() * 0.5, mob.getBbWidth(), 0.15);
		level.playSound(null, mob.blockPosition(), SoundEvents.RAVAGER_ROAR, SoundSource.HOSTILE, 2f, 0.7f);
		Component name = mob.getDisplayName();
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(mob) < 64 * 64) {
				p.sendSystemMessage(Component.translatable("message.lanternring.red_ring_chose", name).withStyle(ChatFormatting.RED, ChatFormatting.ITALIC));
			}
		}
	}

	private static void boost(@Nullable AttributeInstance attr, Identifier id) {
		if (attr != null && !attr.hasModifier(id)) attr.addPermanentModifier(new AttributeModifier(id, 1.0, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Flight> it = FLIGHTS.iterator(); it.hasNext(); ) {
			Flight f = it.next();
			if (!f.target.isAlive() || f.target.level() != f.level || ++f.ticks > 400) {
				it.remove();
				continue;
			}
			Vec3 to = f.target.position().add(0, f.target.getBbHeight() * 0.6, 0);
			Vec3 d = to.subtract(f.pos);
			if (d.length() <= RING_SPEED) {
				it.remove();
				crown(f.level, f.target);
				continue;
			}
			Vec3 step = d.normalize().scale(RING_SPEED);
			for (int i = 0; i < 3; i++) {
				Vec3 p = f.pos.add(step.scale(i / 3.0));
				f.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.RED), p.x, p.y, p.z, 2, 0.05, 0.05, 0.05, 0.0);
			}
			f.pos = f.pos.add(step);
		}
		for (Iterator<Mob> it = BEARERS.values().iterator(); it.hasNext(); ) {
			Mob mob = it.next();
			if (mob.isRemoved() || !mob.isAlive() || !(mob.level() instanceof ServerLevel level)) {
				it.remove();
				continue;
			}
			rage(level, mob);
		}
		for (ServerLevel level : server.getAllLevels()) {
			long now = level.getGameTime();
			if (level == server.overworld() && now >= nextSeek) {
				nextSeek = now + Math.max(20, RingTuning.RED_RING_SEEK.ticks());
				seek(level);
			}
		}
	}

	/** Every standing sanctuary with players about sends a ring to the nearest monster in reach. */
	private static void seek(ServerLevel level) {
		for (RedSanctuary.Site site : RedSanctuary.Data.get(level).all()) {
			if (!site.standing()) continue;
			Vec3 core = Vec3.atCenterOf(RedSanctuary.core(site.anchor()));
			if (!level.isLoaded(site.anchor()) || level.getNearestPlayer(core.x, core.y, core.z, 96, false) == null) continue;
			AABB box = new AABB(core, core).inflate(SEEK_RANGE);
			if (level.getEntitiesOfClass(Mob.class, box.inflate(16), RedRingBearers::bearer).size() >= SEEK_CAP) continue;
			Mob best = null;
			double bestD = Double.MAX_VALUE;
			for (Mob m : level.getEntitiesOfClass(Mob.class, box, m -> m instanceof Enemy && m.isAlive() && !bearer(m) && !RedSanctuary.resident(m) && !chosen(m))) {
				double dist = m.distanceToSqr(core);
				if (dist < bestD) {
					bestD = dist;
					best = m;
				}
			}
			if (best != null) send(level, core, best);
		}
	}

	/** A bearer's rage: hunting, burning bolts, and flying at its prey. */
	private static void rage(ServerLevel level, Mob mob) {
		long t = level.getGameTime() + mob.getId();
		if (t % 100 == 0) RedRage.give(mob);
		mob.resetFallDistance();
		LivingEntity target = target(mob);
		if (target == null && t % 20 == 0) {
			target = prey(level, mob);
			if (target != null) {
				if (mob instanceof Warden w) w.increaseAngerAt(target, 100, false);
				else mob.setTarget(target);
			}
		}
		if (target == null || !target.isAlive() || target.level() != level) {
			mob.setNoGravity(false);
			return;
		}
		double dist = mob.distanceTo(target);
		if (t % 40 == 0 && dist > 3 && dist < 24 && mob.hasLineOfSight(target)) {
			CorpsShots.shoot(level, mob, target, Corps.RED, 5);
		}
		// It flies at prey that's above it or far off, and drops back to the ground to fight up close.
		boolean fly = target.getY() - mob.getY() > 1.5 || dist > 8 || !mob.onGround() && dist > 2.5;
		if (fly) {
			mob.setNoGravity(true);
			Vec3 aim = target.position().add(0, target.getBbHeight() * 0.5, 0).subtract(mob.position());
			mob.setDeltaMovement(mob.getDeltaMovement().scale(0.5).add(aim.normalize().scale(FLY_SPEED * 0.5)));
			mob.getLookControl().setLookAt(target);
			if (t % 2 == 0) level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.RED), mob.getX(), mob.getY() + 0.2, mob.getZ(), 2, mob.getBbWidth() * 0.4, 0.1, mob.getBbWidth() * 0.4, 0.01);
		} else {
			mob.setNoGravity(false);
		}
	}

	private static @Nullable LivingEntity target(Mob mob) {
		LivingEntity t = mob.getTarget();
		if (t == null && mob.getBrain().hasMemoryValue(MemoryModuleType.ATTACK_TARGET)) t = mob.getBrain().getMemory(MemoryModuleType.ATTACK_TARGET).orElse(null);
		return t;
	}

	/** Anything nearby that isn't one of the Red Lanterns' own: it kills out of rage. */
	private static @Nullable LivingEntity prey(ServerLevel level, Mob mob) {
		LivingEntity best = null;
		double bestD = Double.MAX_VALUE;
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, mob.getBoundingBox().inflate(16),
				e -> e != mob && e.isAlive() && !(e instanceof Enemy) && !RedSanctuary.friend(e) && !bearer(e)
						&& !(e instanceof Player p && (p.isCreative() || p.isSpectator())))) {
			double d = e.distanceToSqr(mob);
			if (d < bestD && mob.hasLineOfSight(e)) {
				bestD = d;
				best = e;
			}
		}
		return best;
	}
}
