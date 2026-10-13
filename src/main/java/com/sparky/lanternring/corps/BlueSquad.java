package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.ally.ConstructAlly;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Blue Lantern rescue squad (J, 2026-10-13). Four Blue Lantern villagers fly one after another
 * out of a Blue lantern, each with its own job:
 * <ul>
 * <li>two <b>flyers</b> hold the air, hovering between the monsters and the lantern and beaming
 * down on them, and circle high over the lantern once it's quiet;</li>
 * <li>a <b>ground warrior</b> lands and walks out to meet each monster, then stands guard by the
 * lantern;</li>
 * <li>a <b>rider</b> lands on a blue ravager that forms beside the lantern (BlueRavager) and fires
 * from its back while the beast charges.</li>
 * </ul>
 * First they clear the area: every monster within {@link #CLEAR_RADIUS} blocks of the lantern.
 * Clearing the land itself with construct tools, and rescuing the animals and villagers round
 * them, come next as their own systems.
 *
 * <p>Weapons are the ring's attacks (BlueCombat) for every role until J picks each role's weapon;
 * the armour is the Blue suit as a placeholder for the Blender construct armour (see
 * BlueVillagerRenderer's squad hook).
 */
public final class BlueSquad {
	public enum Role {
		NONE, FLYER, WARRIOR, RIDER;

		static Role of(int i) {
			Role[] all = values();
			return i >= 0 && i < all.length ? all[i] : NONE;
		}
	}

	/** How far round the lantern the squad clears of monsters (J: medium). */
	public static final double CLEAR_RADIUS = 32;
	/** The squad, in the order they fly out. */
	private static final Role[] SQUAD = {Role.FLYER, Role.FLYER, Role.WARRIOR, Role.RIDER};
	/** Ticks between one villager and the next flying out. */
	private static final int STAGGER = 12;
	/** Flyers: how high over a monster they hover, and how far back toward the lantern. */
	private static final double HOVER_UP = 6, HOVER_BACK = 5, HOVER_SIDE = 4;
	/** Flyers circling the lantern when it's quiet: radius, height and turn per tick (radians). */
	private static final double ORBIT_R = 10, ORBIT_UP = 9, ORBIT_TURN = 0.015;
	/** The warrior walks to this distance of a monster, then stands and fights. */
	private static final double WARRIOR_REACH = 9;
	private static final double RIDER_MOUNT = 3;

	private record Pending(ServerLevel level, BlockPos lantern, Role role, int index, long due) {
	}

	private static final List<Pending> PENDING = new ArrayList<>();
	/** Villagers whose attack was looked into lately (game time), so a fight doesn't scan for lanterns every hit. */
	private static final java.util.Map<java.util.UUID, Long> ALARMED = new java.util.HashMap<>();
	/** When each lantern last sent a squad out (game time). */
	private static final java.util.Map<BlockPos, Long> CALLED = new java.util.HashMap<>();
	/** How often one villager's attack is looked into, in ticks. */
	private static final int ALARM_EVERY = 100;

	private BlueSquad() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(BlueSquad::tickPending);
		BlueRescue.register();
		BlueCage.register();
		BluePrison.register();
		RedRage.register();
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			PENDING.clear();
			ALARMED.clear();
			CALLED.clear();
		});
		// A village under attack (J, 3a): a monster hurting a villager, golem, animal or player near a
		// Blue lantern calls a squad out of it, unless one is already out or the lantern is resting.
		net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, base, taken, blocked) -> {
			if (taken <= 0 || !(entity.level() instanceof ServerLevel level)) return;
			if (!(source.getEntity() instanceof LivingEntity by) || !ConstructAlly.isBadMob(by)) return;
			if (ConstructAlly.isBadMob(entity) || entity instanceof CorpsVillager cv && cv.inSquad()) return;
			underAttack(level, entity);
		});
	}

	private static void underAttack(ServerLevel level, LivingEntity victim) {
		long now = level.getGameTime();
		Long last = ALARMED.get(victim.getUUID());
		if (last != null && now - last < ALARM_EVERY) return;
		ALARMED.put(victim.getUUID(), now);
		if (ALARMED.size() > 512) ALARMED.values().removeIf(t -> now - t > ALARM_EVERY);
		BlockPos lantern = nearestBlueLantern(level, victim.blockPosition(), (int) CLEAR_RADIUS);
		if (lantern == null || squadOut(level, lantern)) return;
		Long called = CALLED.get(lantern);
		if (called != null && now - called < RingTuning.BLUE_SQUAD_REST.ticks()) return;
		callOut(level, lantern);
	}

	/**
	 * A bearer crouched and used their ring on a Blue lantern (J, 16a): its squad flies out, unless
	 * one from it is still out.
	 */
	public static void summon(ServerLevel level, BlockPos clicked, ServerPlayer by) {
		BlockPos lantern = clicked;
		while (level.getBlockState(lantern.below()).is(ModRegistry.POWER_BATTERY) && lantern.getY() > clicked.getY() - 8) lantern = lantern.below();
		if (squadOut(level, lantern)) {
			by.sendOverlayMessage(Component.translatable("message.lanternring.blue_squad_out").withStyle(ChatFormatting.AQUA));
			return;
		}
		callOut(level, lantern.immutable());
	}

	/** Whether a squad from this lantern is still out (alive, or still flying out of it). */
	static boolean squadOut(ServerLevel level, BlockPos lantern) {
		for (Pending p : PENDING) {
			if (p.lantern.equals(lantern)) return true;
		}
		return !level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern).inflate(CLEAR_RADIUS * 2),
				v -> v.isAlive() && lantern.equals(v.squadPost())).isEmpty();
	}

	/** Calls a rescue squad out of the Blue lantern at {@code lantern}: they fly out one by one. */
	public static void callOut(ServerLevel level, BlockPos lantern) {
		long now = level.getGameTime();
		CALLED.put(lantern.immutable(), now);
		for (int i = 0; i < SQUAD.length; i++) PENDING.add(new Pending(level, lantern.immutable(), SQUAD[i], i, now + (long) i * STAGGER));
		level.playSound(null, lantern, SoundEvents.BEACON_POWER_SELECT, SoundSource.NEUTRAL, 2f, 0.8f);
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(Vec3.atCenterOf(lantern)) < 96 * 96) {
				p.sendSystemMessage(Component.translatable("message.lanternring.blue_squad").withStyle(ChatFormatting.AQUA, ChatFormatting.ITALIC));
			}
		}
	}

	private static void tickPending(MinecraftServer server) {
		if (PENDING.isEmpty()) return;
		for (Pending p : List.copyOf(PENDING)) {
			if (p.level.getGameTime() < p.due) continue;
			PENDING.remove(p);
			emerge(p.level, p.lantern, p.role, p.index);
		}
	}

	/** One villager bursts out of the top of the lantern and flies to its place. */
	private static void emerge(ServerLevel level, BlockPos lantern, Role role, int index) {
		CorpsVillager v = CorpsMobs.CORPS_VILLAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (v == null) return;
		v.setCorps(Corps.BLUE);
		v.joinSquad(role, lantern);
		Vec3 top = lanternTop(level, lantern);
		v.snapTo(top.x, top.y, top.z, level.getRandom().nextFloat() * 360f, 0f);
		level.addFreshEntity(v);
		CorpsShots.summon(level, top, v.getBbHeight(), 1.5f, Corps.BLUE);
		level.playSound(null, lantern, SoundEvents.BEACON_ACTIVATE, SoundSource.NEUTRAL, 1.2f, 1.6f);
		// Each flies out a different way round the lantern.
		double a = index * Math.PI / 2 + level.getRandom().nextDouble() * 0.6;
		Vec3 c = Vec3.atCenterOf(lantern);
		switch (role) {
			case FLYER -> v.flyTo(new Vec3(c.x + Math.cos(a) * 6, c.y + ORBIT_UP, c.z + Math.sin(a) * 6), false);
			case WARRIOR -> v.flyTo(ground(level, c.x + Math.cos(a) * 4, c.z + Math.sin(a) * 4), true);
			case RIDER -> {
				Vec3 at = ground(level, c.x + Math.cos(a) * 5, c.z + Math.sin(a) * 5);
				BlueRavager mount = CorpsMobs.BLUE_RAVAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
				if (mount != null) {
					mount.guard(lantern);
					mount.snapTo(at.x, at.y, at.z, (float) (Math.toDegrees(a) - 90), 0f);
					level.addFreshEntity(mount);
					CorpsShots.summon(level, at, mount.getBbHeight(), 2.5f, Corps.BLUE);
					level.playSound(null, mount.blockPosition(), SoundEvents.RAVAGER_ROAR, SoundSource.NEUTRAL, 1.5f, 1.1f);
					v.setMount(mount);
				}
				v.flyTo(at.add(0, 3, 0), true);
			}
			default -> {
			}
		}
	}

	/** Every tick for a squad villager (after its flight step): what its role does now. */
	static void tick(ServerLevel level, CorpsVillager v) {
		// Recruited by a player: it goes with them (BlueRecruits).
		if (BlueRecruits.tick(level, v)) return;
		BlockPos post = v.squadPost();
		if (post == null) return;
		Vec3 c = Vec3.atCenterOf(post);
		// Still flying out of the lantern to its place: let it get there first.
		if (v.tickCount < 40 && v.flying()) return;
		LivingEntity threat = v.squadFocus();
		if (v.tickCount % 10 == 0 || threat == null || !inClearing(threat, c)) {
			threat = nearestThreat(level, c, v.position());
			v.setSquadFocus(threat);
		}
		BlueRescue.Site site = BlueRescue.site(post);
		BlueRescue.tickSite(level, site, threat != null);
		switch (v.squadRole()) {
			case FLYER -> {
				// Monsters first, unless it's already carrying someone in; then the rescue; then it circles.
				if ((threat == null || BlueRescue.carrying(v)) && BlueRescue.flyer(level, v, site)) return;
				// Everyone's safe: the caged monsters go up to the floating prison (J: 21a).
				if ((threat == null || BluePrison.carrying(v)) && BluePrison.flyer(level, v, post)) return;
				fly(v, BlueRescue.guardCentre(site), threat);
			}
			case WARRIOR -> {
				Vec3 beat = threat == null ? BlueRescue.patrolPoint(level, site, v) : null;
				if (beat != null && !v.flying()) {
					if (v.getNavigation().isDone()) v.getNavigation().moveTo(beat.x, beat.y, beat.z, 0.55);
				} else {
					walk(v, c, threat);
				}
			}
			case RIDER -> {
				BlueRavager mount = v.mount();
				if (mount != null && site.centre != null) mount.prowl(site.centre);
				ride(v, c, threat);
				if (v.getVehicle() instanceof BlueRavager m) m.lead(v, threat, site.centre != null ? Vec3.atBottomCenterOf(site.centre) : c);
			}
			default -> {
			}
		}
	}

	static void fly(CorpsVillager v, Vec3 c, @Nullable LivingEntity threat) {
		// The two flyers work opposite sides.
		double sideSign = (v.getUUID().getLeastSignificantBits() & 1) == 0 ? 1 : -1;
		if (threat != null) {
			Vec3 back = new Vec3(c.x - threat.getX(), 0, c.z - threat.getZ());
			back = back.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : back.normalize();
			Vec3 side = new Vec3(-back.z, 0, back.x).scale(HOVER_SIDE * sideSign);
			Vec3 at = threat.position().add(back.scale(HOVER_BACK)).add(side).add(0, HOVER_UP, 0);
			v.squadFly(at, threat.getEyePosition());
			return;
		}
		double a = v.level().getGameTime() * ORBIT_TURN + (sideSign > 0 ? 0 : Math.PI);
		v.squadFly(new Vec3(c.x + Math.cos(a) * ORBIT_R, c.y + ORBIT_UP, c.z + Math.sin(a) * ORBIT_R), null);
	}

	private static void walk(CorpsVillager v, Vec3 c, @Nullable LivingEntity threat) {
		if (v.flying() || v.hammerLeaping()) return;
		if (threat != null) {
			if (v.distanceToSqr(threat) > WARRIOR_REACH * WARRIOR_REACH) v.getNavigation().moveTo(threat, 0.75);
			else v.getNavigation().stop();
			return;
		}
		// Quiet: stand guard a few steps out from the lantern.
		if (v.distanceToSqr(c) > 5 * 5 && v.getNavigation().isDone()) v.getNavigation().moveTo(c.x + 3, c.y, c.z, 0.6);
	}

	static void ride(CorpsVillager v, Vec3 c, @Nullable LivingEntity threat) {
		if (v.getVehicle() instanceof BlueRavager) return;
		BlueRavager mount = v.mount();
		if (mount == null) {
			// Its beast is gone: it fights on foot like the warrior.
			walk(v, c, threat);
			return;
		}
		if (v.distanceToSqr(mount) < RIDER_MOUNT * RIDER_MOUNT) {
			v.landNow();
			v.startRiding(mount, true, true);
			return;
		}
		if (v.flying()) {
			v.squadFly(mount.position().add(0, 3, 0), null);
		} else if (v.getNavigation().isDone() || v.tickCount % 20 == 0) {
			v.getNavigation().moveTo(mount, 0.8);
		}
	}

	private static boolean inClearing(LivingEntity e, Vec3 c) {
		return e.isAlive() && e.distanceToSqr(c) < CLEAR_RADIUS * CLEAR_RADIUS;
	}

	/** The monster in the clearing nearest {@code from}, or null when it's clear. */
	@Nullable
	static LivingEntity nearestThreat(ServerLevel level, Vec3 c, Vec3 from) {
		return level.getEntitiesOfClass(LivingEntity.class, new AABB(c, c).inflate(CLEAR_RADIUS),
						e -> ConstructAlly.isBadMob(e) && inClearing(e, c)).stream()
				.min(Comparator.comparingDouble(e -> e.distanceToSqr(from))).orElse(null);
	}

	private static Vec3 ground(ServerLevel level, double x, double z) {
		int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, Mth.floor(x), Mth.floor(z));
		return new Vec3(Mth.floor(x) + 0.5, y, Mth.floor(z) + 0.5);
	}

	/** The floor near height {@code near} at x/z (scanning a few blocks round it, so not a dome's roof); near itself if none. */
	static double groundY(ServerLevel level, double x, double z, double near) {
		int bx = Mth.floor(x), bz = Mth.floor(z), from = Mth.floor(near) + 3;
		for (int y = from; y > from - 8; y--) {
			BlockPos p = new BlockPos(bx, y, bz);
			if (level.getBlockState(p.below()).isFaceSturdy(level, p.below(), net.minecraft.core.Direction.UP)
					&& level.getBlockState(p).getCollisionShape(level, p).isEmpty() && level.getBlockState(p.above()).getCollisionShape(level, p.above()).isEmpty()) return y;
		}
		return near;
	}

	/** Just above the top of the lantern (a big battery is several blocks tall). */
	private static Vec3 lanternTop(ServerLevel level, BlockPos lantern) {
		BlockPos p = lantern;
		while (level.getBlockState(p.above()).is(ModRegistry.POWER_BATTERY) && p.getY() < lantern.getY() + 8) p = p.above();
		return Vec3.atBottomCenterOf(p.above());
	}

	/** The nearest placed Blue lantern within {@code r} blocks, or null. */
	@Nullable
	public static BlockPos nearestBlueLantern(ServerLevel level, BlockPos at, int r) {
		BlockPos best = null;
		double bestD = Double.MAX_VALUE;
		for (BlockPos p : BlockPos.betweenClosed(at.offset(-r, -r / 2, -r), at.offset(r, r / 2, r))) {
			var s = level.getBlockState(p);
			if (!s.is(ModRegistry.POWER_BATTERY) || Corps.of(s) != Corps.BLUE) continue;
			// The bottom block of a tall battery.
			if (level.getBlockState(p.below()).is(ModRegistry.POWER_BATTERY)) continue;
			double d = p.distSqr(at);
			if (d < bestD) {
				bestD = d;
				best = p.immutable();
			}
		}
		return best;
	}
}
