package com.sparky.lanternring.item;

import com.sparky.lanternring.ally.ConstructAlly;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Blender pass 844 S3b (J's KEEP): the construct sword's stepping wide sweep pair. The first sweep is the hit you land;
 * the backswing sweeps again 5 ticks later (the take's hits at ticks 5 and 10), striking everything in a wide arc in
 * front of you once (3.2 blocks, 120 degrees), never your own constructs.
 */
public final class SwordSweeps {
	/** Ticks from the first hit to the backswing's, and its reach and half-arc. */
	static final int BACKSWING = 5;
	private static final double REACH = 3.2, COS_HALF_ARC = Math.cos(Math.toRadians(60));

	private record Sweep(Player player, ServerLevel level, long due, com.sparky.lanternring.Corps corps) {
	}

	private static final List<Sweep> PENDING = new ArrayList<>();

	private SwordSweeps() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(server -> tick());
	}

	/** A sword hit just landed: queue the backswing, unless one is already coming. */
	static void hit(Player player, com.sparky.lanternring.Corps corps) {
		if (!(player.level() instanceof ServerLevel level)) return;
		for (Sweep s : PENDING) if (s.player == player) return;
		PENDING.add(new Sweep(player, level, level.getGameTime() + BACKSWING, corps));
	}

	private static void tick() {
		for (Iterator<Sweep> it = PENDING.iterator(); it.hasNext(); ) {
			Sweep s = it.next();
			if (s.player.isRemoved() || s.player.level() != s.level) {
				it.remove();
				continue;
			}
			if (s.level.getGameTime() < s.due) continue;
			it.remove();
			if (!(s.player.getMainHandItem().getItem() instanceof ConstructToolItem tool) || tool.tool != ConstructTools.Tool.SWORD) continue;
			sweep(s);
		}
	}

	private static void sweep(Sweep s) {
		Player p = s.player;
		Vec3 eye = p.getEyePosition();
		Vec3 look = p.getLookAngle();
		Vec3 flat = new Vec3(look.x, 0, look.z);
		flat = flat.lengthSqr() < 1e-4 ? look : flat.normalize();
		float damage = (float) p.getAttributeValue(Attributes.ATTACK_DAMAGE);
		boolean landed = false;
		for (LivingEntity e : s.level.getEntitiesOfClass(LivingEntity.class, new AABB(eye, eye).inflate(REACH),
				e -> e != p && e.isAlive() && !(e instanceof ConstructAlly) && !e.isAlliedTo(p))) {
			Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
			if (to.length() > REACH) continue;
			Vec3 toFlat = new Vec3(to.x, 0, to.z);
			if (toFlat.lengthSqr() > 1e-4 && toFlat.normalize().dot(flat) < COS_HALF_ARC) continue;
			// The hit's own knockback throws it along the sweep.
			if (e.hurtServer(s.level, s.level.damageSources().playerAttack(p), damage)) landed = true;
		}
		if (landed) ConstructTools.spend(p, s.corps);
	}
}
