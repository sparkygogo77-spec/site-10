package com.sparky.lanternring.corps;

import com.sparky.lanternring.ally.ConstructAlly;
import java.util.Comparator;
import java.util.List;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A Blue rescue squad that joins you (J, 2026-10-13: 36-40). Talk to one of the squad with Red rage
 * on you and the whole squad of four flies with you: a reverse raid on the Red Lanterns. They
 * follow you and fight anything that comes at you, Red Lanterns and their constructs first; while
 * the rage is on you and nothing's near, they fly ahead towards the nearest Red sanctuary to lead
 * you there. Talk to a flyer or the warrior again to have the squad guard where you stand (a full
 * rescue post there), and again to have them follow you once more.
 */
final class BlueRecruits {
	/** How far round you they look for something to fight, and for the Red Lanterns to lead you to. */
	private static final double GUARD_R = 24, SEEK_R = 600;
	/** How far ahead of you the squad flies while leading. */
	private static final double LEAD = 12;

	private BlueRecruits() {
	}

	/** Talking to a squad member: recruits the squad (with rage on you) or switches follow/guard. True if it did. */
	static boolean talk(ServerLevel level, CorpsVillager v, Player player) {
		UUID leader = v.leader();
		if (leader == null) {
			if (!RedRage.raging(player)) return false;
			for (CorpsVillager m : squadOf(level, v)) m.follow(player.getUUID());
			player.sendSystemMessage(Component.translatable("message.lanternring.blue_squad_recruited").withStyle(ChatFormatting.AQUA));
			level.playSound(null, v.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.NEUTRAL, 1f, 1.4f);
			return true;
		}
		if (!leader.equals(player.getUUID()) || v.squadRole() == BlueSquad.Role.RIDER) return false;
		boolean guard = !v.guarding();
		BlockPos here = player.blockPosition();
		for (CorpsVillager m : squadOf(level, v)) {
			if (guard) m.guardAt(here);
			else m.follow(player.getUUID());
		}
		player.sendSystemMessage(Component.translatable(guard ? "message.lanternring.blue_squad_guard" : "message.lanternring.blue_squad_follow").withStyle(ChatFormatting.AQUA));
		return true;
	}

	/** Everyone in this member's squad (same lantern, or same leader). */
	private static List<CorpsVillager> squadOf(ServerLevel level, CorpsVillager v) {
		UUID leader = v.leader();
		BlockPos post = v.squadPost();
		return level.getEntitiesOfClass(CorpsVillager.class, v.getBoundingBox().inflate(64), m -> m.inSquad()
				&& (leader != null ? leader.equals(m.leader()) : m.leader() == null && post != null && post.equals(m.squadPost())));
	}

	/** A recruited squad member following its leader. False when it isn't (it runs its post as usual). */
	static boolean tick(ServerLevel level, CorpsVillager v) {
		UUID id = v.leader();
		if (id == null || v.guarding()) return false;
		Player p = level.getPlayerByUUID(id);
		if (p == null || !p.isAlive()) {
			// Its leader's gone: it waits where it is.
			v.setSquadFocus(null);
			return true;
		}
		LivingEntity threat = v.squadFocus();
		if (v.tickCount % 10 == 0 || threat == null || !threat.isAlive() || threat.distanceToSqr(p) > GUARD_R * GUARD_R * 2) {
			threat = threat(level, p);
			v.setSquadFocus(threat);
		}
		Vec3 lead = threat == null && RedRage.raging(p) ? leadPoint(level, p) : null;
		Vec3 me = p.position();
		double side = (v.getUUID().getLeastSignificantBits() & 1) == 0 ? 1 : -1;
		switch (v.squadRole()) {
			case FLYER -> {
				if (threat != null) BlueSquad.fly(v, me, threat);
				else if (lead != null) v.squadFly(lead.add(side * 3, 5, 0), null);
				else {
					double a = level.getGameTime() * 0.03 + (side > 0 ? 0 : Math.PI);
					v.squadFly(me.add(Math.cos(a) * 5, 4.5, Math.sin(a) * 5), null);
				}
			}
			case WARRIOR -> {
				if (lead != null) v.squadFly(lead.add(0, 3, 0), null);
				else if (v.distanceToSqr(p) > 14 * 14) v.squadFly(me.add(side * 2, 2.5, 2), null);
				else {
					if (v.flying() && v.distanceToSqr(p) < 8 * 8) v.landNow();
					if (!v.flying() && threat == null && v.distanceToSqr(p) > 4 * 4 && v.getNavigation().isDone()) v.getNavigation().moveTo(p, 0.7);
					if (!v.flying() && threat != null && v.distanceToSqr(threat) > 9 * 9) v.getNavigation().moveTo(threat, 0.75);
				}
			}
			case RIDER -> {
				BlueRavager mount = v.mount();
				if (mount != null) mount.follow(lead != null ? lead : me, threat);
				BlueSquad.ride(v, me, threat);
				if (v.getVehicle() instanceof BlueRavager m) m.lead(v, threat, lead != null ? lead : me);
			}
			default -> {
			}
		}
		return true;
	}

	/** The nearest thing to fight round the leader: Red Lanterns and theirs first, then any monster. */
	private static @Nullable LivingEntity threat(ServerLevel level, Player p) {
		AABB box = p.getBoundingBox().inflate(GUARD_R);
		Comparator<LivingEntity> near = Comparator.comparingDouble(e -> e.distanceToSqr(p));
		LivingEntity red = level.getEntitiesOfClass(LivingEntity.class, box, e -> e.isAlive() && e != p && RedRage.red(e)).stream().min(near).orElse(null);
		if (red != null) return red;
		return level.getEntitiesOfClass(LivingEntity.class, box, ConstructAlly::isBadMob).stream().min(near).orElse(null);
	}

	/** A point ahead of the leader towards the nearest Red sanctuary or tower, or null when there's none. */
	private static @Nullable Vec3 leadPoint(ServerLevel level, Player p) {
		BlockPos best = null;
		double bestD = SEEK_R * SEEK_R;
		for (RedSanctuary.Site s : RedSanctuary.Data.get(level).all()) {
			double d = s.anchor().distSqr(p.blockPosition());
			if (d < bestD) {
				bestD = d;
				best = s.anchor();
			}
		}
		for (RedTower.Site s : RedTower.sites(level)) {
			double d = s.anchor().distSqr(p.blockPosition());
			if (d < bestD) {
				bestD = d;
				best = s.anchor();
			}
		}
		if (best == null) return null;
		Vec3 to = Vec3.atCenterOf(best).subtract(p.position());
		Vec3 flat = new Vec3(to.x, 0, to.z);
		if (flat.lengthSqr() < LEAD * LEAD) return Vec3.atCenterOf(best);
		return p.position().add(flat.normalize().scale(LEAD));
	}
}
