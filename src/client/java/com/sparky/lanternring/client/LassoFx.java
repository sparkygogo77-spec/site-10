package com.sparky.lanternring.client;

import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.net.LassoInputPayload;
import com.sparky.lanternring.net.LassoPayload;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * Draws Lasso catches (see the server's Lasso): a bubble of hard light around the mob and a thin
 * green string from the holder's ring to it, and sends the bearer's left-click and space to the
 * server while they are holding something.
 */
public final class LassoFx {
	private static final double GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

	private static final class Line {
		int target;
		float radius;
		boolean holding;
		int age;
		int lastSeen;
	}

	private static final Map<Integer, Line> LINES = new HashMap<>();
	private static int clock;
	private static boolean attackWasDown;
	private static boolean jumpWasDown;

	private LassoFx() {
	}

	public static void handle(LassoPayload payload) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		if (payload.target() < 0) {
			Line gone = LINES.remove(payload.holder());
			if (gone != null) snap(mc, gone);
			return;
		}
		Line line = LINES.computeIfAbsent(payload.holder(), id -> new Line());
		line.target = payload.target();
		line.radius = payload.radius();
		line.holding = payload.holding();
		line.lastSeen = clock;
	}

	public static void tick(Minecraft mc) {
		clock++;
		if (mc.level == null || mc.player == null) {
			LINES.clear();
			return;
		}
		input(mc);
		if (mc.isPaused()) return;
		for (Iterator<Map.Entry<Integer, Line>> it = LINES.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<Integer, Line> e = it.next();
			Line line = e.getValue();
			Entity holder = mc.level.getEntity(e.getKey());
			Entity target = mc.level.getEntity(line.target);
			if (holder == null || target == null || clock - line.lastSeen > 5) {
				it.remove();
				continue;
			}
			Vec3 center = target.getBoundingBox().getCenter();
			bubble(center, line);
			if (holder instanceof Player player) {
				string(LabFx.ringPos(mc, player, player.getMainArm()), center, line);
			}
			line.age++;
		}
	}

	/** Edge-detects left-click and space while this player is holding a catch. */
	private static void input(Minecraft mc) {
		boolean attack = mc.options.keyAttack.isDown();
		boolean jump = mc.options.keyJump.isDown();
		boolean lassoing = mc.screen == null && mc.player.isUsingItem() && LINES.containsKey(mc.player.getId());
		if (lassoing && ClientPlayNetworking.canSend(LassoInputPayload.TYPE)) {
			if (attack && !attackWasDown) ClientPlayNetworking.send(new LassoInputPayload(Lasso.INPUT_SEND));
			if (jump && !jumpWasDown) ClientPlayNetworking.send(new LassoInputPayload(Lasso.INPUT_HOLD));
		}
		attackWasDown = attack;
		jumpWasDown = jump;
	}

	/**
	 * A sphere of short-lived motes on a slowly turning golden-spiral grid, so it reads as one
	 * shimmering shell. It brightens to a solid rim of sparks while it is held in place.
	 */
	private static void bubble(Vec3 center, Line line) {
		double r = line.radius;
		int n = Mth.clamp((int) (r * r * 55), 40, 300);
		double turn = line.age * 0.05;
		for (int i = 0; i < n; i++) {
			double y = 1 - (i + 0.5) * 2 / n;
			double ring = Math.sqrt(1 - y * y);
			double a = i * GOLDEN_ANGLE + turn;
			Vec3 at = center.add(Math.cos(a) * ring * r, y * r, Math.sin(a) * ring * r);
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, at, Vec3.ZERO, 0.75f);
			if (p != null) p.tinted(0.35f, 1f, 0.5f).lasting(2);
		}
		// A band around the middle that sparkles brighter while the bubble is held in place.
		int band = line.holding ? 28 : 10;
		for (int i = 0; i < band; i++) {
			double a = i * Math.PI * 2 / band - turn * 2;
			Vec3 at = center.add(Math.cos(a) * r, 0, Math.sin(a) * r);
			ConstructParticle p = LabFx.spawn(line.holding ? ModParticles.SPARK : ModParticles.MOTE, at, Vec3.ZERO, line.holding ? 0.7f : 1f);
			if (p != null) p.lasting(2);
		}
	}

	/** A thin string from the ring to the bubble's surface, sagging a little like a real rope. */
	private static void string(Vec3 from, Vec3 center, Line line) {
		Vec3 d = center.subtract(from);
		double len = d.length();
		if (len <= line.radius + 0.05) return;
		Vec3 to = center.subtract(d.scale(line.radius / len));
		double span = len - line.radius;
		double sag = Math.min(0.6, span * 0.04);
		for (double t = 0; t <= span; t += 0.1) {
			double f = t / span;
			Vec3 at = from.lerp(to, f).subtract(0, sag * 4 * f * (1 - f), 0);
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, at, Vec3.ZERO, 0.4f);
			if (p != null) p.tinted(0.3f, 1f, 0.4f).lasting(2);
		}
		ConstructParticle knot = LabFx.spawn(ModParticles.SPARK, to, Vec3.ZERO, 1.2f);
		if (knot != null) knot.lasting(2);
	}

	/** The bubble pops into motes when the holder lets go. */
	private static void snap(Minecraft mc, Line line) {
		Entity target = mc.level.getEntity(line.target);
		if (target == null) return;
		Vec3 center = target.getBoundingBox().getCenter();
		for (int i = 0; i < 40; i++) {
			double y = 1 - (i + 0.5) * 2 / 40;
			double ring = Math.sqrt(1 - y * y);
			double a = i * GOLDEN_ANGLE;
			Vec3 out = new Vec3(Math.cos(a) * ring, y, Math.sin(a) * ring);
			LabFx.spawn(i % 3 == 0 ? ModParticles.SHARD : ModParticles.MOTE, center.add(out.scale(line.radius)), out.scale(0.12));
		}
	}
}
