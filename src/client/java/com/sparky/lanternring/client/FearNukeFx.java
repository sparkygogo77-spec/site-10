package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import com.sparky.lanternring.corps.FearNuke;
import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * The Fear Nuke's bomb (fear_nuke.bbmodel, a simple Fallout-style bomb in hard light), on the
 * server's clock (corps/FearNuke). It drops out of the sky into place over the bearer's raised ring
 * (J, 2026-10-15), joined to it (NukeHold) by a line of yellow light, and is carried there. Let go,
 * it's thrown: it falls nose first along the same heavy arc the server flies (FearNuke.nextVelocity)
 * until it airbursts and the yellow aura (NukeAuraFx) and the burst itself (AirburstFx) take over.
 * Let go too early and its plates scatter and fade.
 */
public final class FearNukeFx {
	/** How many times life size it is drawn: the model is 3.5 blocks long, so about 10. */
	private static final float SCALE = 3f;
	/** Ticks a forming bomb lingers after the server stops saying it's there. */
	private static final int FORM_LAPSE = 5;
	/** How far above its place over the ring the bomb starts its drop, in blocks. */
	private static final float DROP = 18f;
	/** Ticks the plates of a broken bomb take to scatter and fade. */
	private static final int SCATTER = 26;

	/** A bomb held over one bearer's ring: last told {@code built} at {@code seen}, at {@code site} (and {@code prev} the tick before). */
	private static final class Form {
		Vec3 site, prev;
		float built;
		int ticks;
		long seen;
		Corps corps;
	}

	private record Scatter(Vec3 site, float built, long start, Corps corps) {
	}

	private static final Int2ObjectMap<Form> FORMS = new Int2ObjectOpenHashMap<>();
	private static final List<Scatter> SCATTERS = new ArrayList<>();

	private record Nuke(Vec3 from, Vec3 vel, int fly, long start, Corps corps) {
		float total() {
			return fly;
		}

		/** Where it is {@code age} ticks in (the server's FearNuke.step, tick by tick, eased between ticks). */
		Vec3 at(float age) {
			Vec3 pos = from, v = vel;
			int whole = (int) Math.floor(Math.max(0, age));
			for (int i = 0; i < whole; i++) {
				v = FearNuke.nextVelocity(v);
				pos = pos.add(v);
			}
			return pos.add(FearNuke.nextVelocity(v).scale(Math.max(0, age) - whole));
		}
	}

	private static final List<Nuke> NUKES = new ArrayList<>();
	private static final Map<Corps, BbModel> MODELS = new EnumMap<>(Corps.class);

	private FearNukeFx() {
	}

	public static void start(Vec3 from, Vec3 vel, int fly) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		// It leaves the ring hand: that bomb is this one now.
		FORMS.values().removeIf(f -> f.site.distanceToSqr(from) < 4);
		NUKES.add(new Nuke(from, vel, Math.max(1, fly), mc.level.getGameTime(), CorpsTint.current()));
	}

	/** A nuke went off with its middle at {@code at}: the bomb nearest it is gone. */
	static void burst(Vec3 at) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		long now = mc.level.getGameTime();
		Nuke near = null;
		double best = 48 * 48;
		for (Nuke n : NUKES) {
			double d = n.at(now - n.start).distanceToSqr(at);
			if (d < best) {
				best = d;
				near = n;
			}
		}
		if (near != null) NUKES.remove(near);
	}

	/** The server says {@code bearer} is forming a bomb at {@code site}, {@code built} 0..1 of the way over {@code ticks}. */
	static void forming(Player bearer, Vec3 site, float built, int ticks) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || bearer == null) return;
		Form f = FORMS.computeIfAbsent(bearer.getId(), id -> new Form());
		f.prev = f.site == null || f.site.distanceToSqr(site) > 64 ? site : f.site;
		f.site = site;
		f.built = built;
		f.ticks = Math.max(1, ticks);
		f.seen = mc.level.getGameTime();
		f.corps = CorpsTint.current();
		// The ring flares and pours light up into it.
		RingEmit.hold(bearer, site, 1f);
	}

	/** The bomb forming at {@code site} breaks apart, {@code built} 0..1 of the way through. */
	static void scatter(Vec3 site, float built) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		FORMS.values().removeIf(f -> f.site.distanceToSqr(site) < 1);
		SCATTERS.add(new Scatter(site, Math.max(0.1f, built), mc.level.getGameTime(), CorpsTint.current()));
		// Plates of light flung out every way.
		RandomSource r = mc.level.getRandom();
		float size = SCALE * 1.75f * Math.max(0.3f, built);
		for (int i = 0; i < LabFx.count(60 * Math.max(0.3f, built)); i++) {
			Vec3 d = new Vec3(r.nextGaussian(), r.nextGaussian(), r.nextGaussian()).normalize();
			ConstructParticle p = LabFx.spawn(ModParticles.SPARK, site.add(d.scale(size * r.nextDouble())), d.scale(0.3 + 0.5 * r.nextDouble()), 1.6f);
			if (p != null) p.lasting(14 + r.nextInt(12));
		}
	}

	/** Test hook: how far the bomb {@code bearer} is forming is built, or -1. */
	public static float formed(Player bearer) {
		Form f = bearer == null ? null : FORMS.get(bearer.getId());
		return f == null ? -1f : f.built;
	}

	public static void clear() {
		NUKES.clear();
		FORMS.clear();
		SCATTERS.clear();
	}

	static void tick(Minecraft mc) {
		long now = mc.level.getGameTime();
		for (Iterator<Nuke> it = NUKES.iterator(); it.hasNext(); ) {
			Nuke n = it.next();
			float age = now - n.start;
			if (age > n.total() || age < -1) it.remove();
		}
		SCATTERS.removeIf(s -> now - s.start > SCATTER || now < s.start);
		RandomSource r = mc.level.getRandom();
		for (Iterator<Int2ObjectMap.Entry<Form>> it = FORMS.int2ObjectEntrySet().iterator(); it.hasNext(); ) {
			Int2ObjectMap.Entry<Form> e = it.next();
			Form f = e.getValue();
			Player bearer = RingEmit.bearer(e.getIntKey());
			if (now - f.seen > FORM_LAPSE || now < f.seen - 1 || bearer == null) {
				it.remove();
				continue;
			}
			Corps before = CorpsTint.enter(f.corps);
			try {
				tether(mc, r, RingEmit.ringNow(bearer, 1f), f.site);
			} finally {
				CorpsTint.restore(before);
			}
		}
	}

	/** The line of light from the raised ring up to the forming bomb, with sparks running up it. */
	private static void tether(Minecraft mc, RandomSource r, Vec3 from, Vec3 to) {
		Vec3 d = to.subtract(from);
		double len = d.length();
		if (len < 1) return;
		Vec3 dir = d.scale(1 / len);
		// Stops short at the bomb's skin.
		len = Math.max(0, len - SCALE * 0.6);
		int n = (int) Math.ceil(len / 0.3);
		double offset = r.nextDouble() * 0.3;
		for (int i = 0; i < n; i++) {
			double along = Math.min(len, i * 0.3 + offset);
			// Thin at the ring, thicker as it climbs, so it reads from below as well as from far off.
			float size = 0.5f + 0.9f * (float) (along / len);
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, from.add(dir.scale(along)), Vec3.ZERO, size);
			if (p != null) p.lasting(3);
		}
		for (int i = 0; i < LabFx.count(3); i++) {
			ConstructParticle p = LabFx.spawn(ModParticles.SPARK, from.add(dir.scale(r.nextDouble() * len)), dir.scale(0.9), 0.8f);
			if (p != null) p.lasting(3 + r.nextInt(3));
		}
	}

	public static void render(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) {
			NUKES.clear();
			return;
		}
		if (NUKES.isEmpty() && FORMS.isEmpty() && SCATTERS.isEmpty()) return;
		float now = mc.level.getGameTime() + ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		for (Form f : FORMS.values()) {
			// Drops out of the sky into place over the ring, fast and heavy.
			float built = Mth.clamp(f.built + Math.max(0, now - f.seen) / f.ticks, 0f, 1f);
			float fall = (1 - built) * (1 - built);
			float bright = built < 1f ? 0.55f + 0.3f * built : 0.85f + 0.15f * Mth.sin(now * 0.6f);
			float partial = Mth.clamp(now - f.seen, 0f, 1f);
			Vec3 site = f.prev.lerp(f.site, partial);
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(site.x - cam.x, site.y + DROP * fall - cam.y, site.z - cam.z);
			pose.rotateDegrees(Axis.YP, now * 2f);
			float s = SCALE;
			pose.scale(s, s, s);
			model(f.corps).renderLit(pose, ctx.submitNodeCollector(), BbModel.glow(bright));
			pose.popPose();
		}
		for (Scatter sc : SCATTERS) {
			// Bursts outward and dims away to nothing.
			float k = Mth.clamp((now - sc.start) / SCATTER, 0f, 1f);
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(sc.site.x - cam.x, sc.site.y - cam.y, sc.site.z - cam.z);
			pose.rotateDegrees(Axis.YP, now * 2f + k * 90f);
			pose.rotateDegrees(Axis.XP, k * 25f);
			float s = SCALE * (1f + 0.8f * k * (2 - k));
			pose.scale(s, s, s);
			model(sc.corps).renderBuilt(pose, ctx.submitNodeCollector(), BbModel.glow(0.9f * (1 - k) * (1 - k)), sc.built * (1 - k));
			pose.popPose();
		}
		for (Nuke n : NUKES) {
			float age = Math.max(0, now - n.start);
			if (age >= n.total()) continue;
			Vec3 at = n.at(age);
			// Nose first along its fall, its seams flickering white-hot as it comes down.
			float size = 1f, wobble = 0f;
			float bright = age < n.fly - 1 && ((int) age) % 4 < 2 ? 1f : 0.8f;
			Vec3 v = n.at(age + 0.5f).subtract(n.at(Math.max(0, age - 0.5f)));
			double flat = Math.sqrt(v.x * v.x + v.z * v.z);
			float heading = (float) Math.toDegrees(Math.atan2(v.x, v.z));
			// How far the nose leans off straight down.
			float lean = (float) Math.toDegrees(Math.atan2(flat, -v.y));
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(at.x - cam.x, at.y - cam.y, at.z - cam.z);
			pose.rotateDegrees(Axis.YP, heading);
			// The nose (model -Y) swings toward +Z, the way it is going.
			pose.rotateDegrees(Axis.XN, lean + wobble * 0.3f);
			pose.rotateDegrees(Axis.ZP, wobble * 0.2f);
			pose.rotateDegrees(Axis.YP, age * 1.5f);
			float s = size * SCALE;
			pose.scale(s, s, s);
			model(n.corps).renderLit(pose, ctx.submitNodeCollector(), BbModel.glow(bright));
			pose.popPose();
		}
	}

	private static BbModel model(Corps corps) {
		return MODELS.computeIfAbsent(corps, c -> BbModel.load("fear_nuke").forCorps(c));
	}
}
