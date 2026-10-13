package com.sparky.lanternring.client;

import com.sparky.lanternring.BlastDrills;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.Shockwaves;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.particle.Particle;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** Draws every ring effect on this client, in the styles picked in the Ring Lab. */
public final class LabFx {
	private static final Vec3 UP = new Vec3(0, 1, 0);
	/** Blast tunnels whose walls keep dripping light for a while (SCORCH style). */
	private static final List<Scar> SCARS = new ArrayList<>();
	private static Level scarLevel;

	private record Scar(Vec3 from, Vec3 to, long until) {
	}

	/** Lines of light (LINE and SHARDS styles) still drawing themselves out from the ring to the target. */
	private static final List<Streak> STREAKS = new ArrayList<>();

	private static final class Streak {
		final Vec3 from;
		final Vec3 dir;
		final double length;
		final double speed;
		final boolean shards;
		final boolean burstAtEnd;
		final Corps corps = CorpsTint.current();
		double covered;

		Streak(Vec3 from, Vec3 dir, double length, boolean shards, boolean burstAtEnd) {
			this.from = from;
			this.dir = dir;
			this.length = length;
			// Fast enough that even a long Beam lands within STREAK_TICKS, never slower than a few blocks a tick.
			this.speed = Math.max(3, length / STREAK_TICKS);
			this.shards = shards;
			this.burstAtEnd = burstAtEnd;
		}
	}

	private static final int STREAK_TICKS = 4;

	/** The player whose ring the effect being drawn came out of (null if none), while handle runs. */
	static Player bearer;

	private LabFx() {
	}

	private static LabSettings s() {
		return LabSettings.get();
	}

	static int count(float base) {
		float n = base * s().amount();
		int whole = (int) n;
		return whole + (Math.random() < n - whole ? 1 : 0);
	}

	// ---- spawning ---------------------------------------------------------------------------

	/** Spawns one construct particle with an exact velocity, in one of the construct greens. */
	static ConstructParticle spawn(SimpleParticleType type, Vec3 at, Vec3 velocity, float size) {
		Minecraft mc = Minecraft.getInstance();
		Particle p = mc.particleEngine.createParticle(type, at.x, at.y, at.z, velocity.x, velocity.y, velocity.z);
		if (!(p instanceof ConstructParticle c)) return null;
		float shade = (float) Math.random();
		c.tinted(0.18f + 0.35f * shade, 0.85f + 0.15f * shade, 0.3f + 0.3f * shade);
		return c.sized(size);
	}

	static void spawn(SimpleParticleType type, Vec3 at, Vec3 velocity) {
		spawn(type, at, velocity, 1f);
	}

	static Vec3 jitter(RandomSource r, double amount) {
		return new Vec3((r.nextDouble() - 0.5) * amount, (r.nextDouble() - 0.5) * amount, (r.nextDouble() - 0.5) * amount);
	}

	private static RandomSource random() {
		return Minecraft.getInstance().level.getRandom();
	}

	// ---- server-announced effects ------------------------------------------------------------

	public static void handle(RingFxPayload fx) {
		if (Minecraft.getInstance().level == null) return;
		Corps before = CorpsTint.enter(fx.corps());
		bearer = RingEmit.bearer(fx.bearer());
		try {
			draw(fx);
		} finally {
			CorpsTint.restore(before);
			bearer = null;
		}
	}

	private static void draw(RingFxPayload fx) {
		Player b = bearer;
		// Powers that leave a ring start, on every client, at that ring as it is drawn there (the
		// server sends where the hand roughly is); a flash on the ring face goes with them.
		Vec3 from = b != null ? RingEmit.shotOrigin(b) : fx.from();
		switch (fx.kind()) {
			case BLAST -> {
				if (b != null) RingEmit.muzzle(b, from, fx.to(), 1.3f + 0.35f * Math.max(0, fx.variant() - 1));
				blast(b != null ? from : fx.from(), fx.to(), fx.value(), fx.variant());
			}
			case BEAM, TETHER, CONSTRUCT -> {
				if (b != null) RingEmit.muzzle(b, from, fx.to(), fx.kind() == RingFxPayload.Kind.CONSTRUCT ? 0.8f : 1f);
				useLine(from, fx.to(), fx.kind() != RingFxPayload.Kind.CONSTRUCT);
			}
			case EMIT -> {
				if (b != null) RingEmit.muzzle(b, from, fx.to(), 1.5f);
				useLine(from, fx.to(), true);
			}
			case PUSH -> {
				// The dome blows out round the bearer; the ring flares as it goes.
				if (b != null) RingEmit.flash(b, 1.8f);
				// The ring's Shockwave (variant 1) sends its charged size as how far "to" is from "from".
				shockwave(fx.from(), fx.variant() == 1 ? fx.to().distanceTo(fx.from()) : Shockwaves.RADIUS);
			}
			case CHARGE -> charge(fx.from(), b != null ? RingEmit.ringNow(b, 1f) : fx.to().add(0, 1, 0));
			case MODE_CHANGE -> {
				if (b != null) RingEmit.flash(b, 1f);
				else burst(fx.from().add(0, 1, 0), 10, 0.15);
			}
			case BEAM_CHARGED -> {
				if (b != null) RingEmit.muzzle(b, from, fx.to(), 2f);
				chargedBeam(from, fx.to());
			}
			case ANVIL_MARK -> {
				anvilMarker(fx.from(), fx.to().subtract(fx.from()));
				if (b != null) RingEmit.aimThread(b, fx.from().add(0, 0.3, 0));
			}
			case ANVIL_IMPACT -> anvilImpact(fx.from(), fx.to().distanceTo(fx.from()));
			case SHOCKWAVE -> shockwave(fx.from(), fx.to().distanceTo(fx.from()));
			case DELUGE_MARK -> {
				delugeMarker(fx.from(), fx.to().distanceTo(fx.from()));
				if (b != null) RingEmit.aimThread(b, fx.from().add(0, 0.3, 0));
			}
			case DELUGE_SPLASH -> delugeSplash(fx.from(), fx.to().distanceTo(fx.from()), fx.variant());
			case DELUGE_RECALL -> {
				if (b != null) delugeRecall(b, fx.from(), fx.variant() == 1);
			}
			case DELUGE_FORM -> {
				if (b != null) RingEmit.hold(b, fx.to(), fx.value());
				if (b != null && b == Minecraft.getInstance().player) DelugeRecallInput.formed(Minecraft.getInstance());
			}
			case REFLECT -> burst(fx.from(), 18, 0.22);
			case FEAR_NUKE -> FearNukeFx.start(fx.from(), fx.to(), (int) fx.value(), fx.variant());
			case FEAR_BURST -> AirburstFx.start(fx.from(), fx.to(), fx.value());
			case FEAR_GAS -> FearGasFx.start(fx.from(), fx.to().distanceTo(fx.from()), (int) fx.value());
			case FEAR_NUKE_FORM -> FearNukeFx.forming(b, fx.from(), fx.value(), fx.variant());
			case FEAR_NUKE_SCATTER -> FearNukeFx.scatter(fx.from(), fx.value());
			case BRIDGE_MARK -> bridgeMarker(fx.from(), fx.to(), fx.variant());
			case LASSO_SLAM -> {
				// The bubble's hard light chips where it hit, and every camera nearby jolts.
				burst(fx.from(), (int) Math.min(30, 8 + fx.value() * 6), 0.12 + fx.value() * 0.05);
				RingShake.impact(fx);
			}
			case NUKE_AURA -> NukeAuraFx.start(fx.from(), fx.to().distanceTo(fx.from()), (int) fx.value(), fx.variant());
			case BLACK_HOLE_MARK -> {
				BlackHoleFx.marker(fx.from(), fx.value(), fx.variant());
				if (b != null) RingEmit.aimThread(b, fx.from());
			}
			case BLACK_HOLE -> BlackHoleFx.open(fx.from(), fx.to().subtract(fx.from()), (int) fx.value(), fx.variant());
			case BLACK_HOLE_FEED -> BlackHoleFx.fed(fx.from(), (int) fx.value());
			case ALLY_SHOT -> {
				useLine(fx.from(), fx.to(), true);
				allyTrail(fx.from(), fx.to());
			}
			case ALLY_MARK -> {
				allyMarker(fx.from(), fx.variant());
				if (b != null) RingEmit.aimThread(b, fx.from().add(0, 0.3, 0));
			}
			case ALLY_SUMMON -> allySummon(fx.from(), fx.to(), fx.value());
			case RAM_BARRIER, RAM_HIT, RAM_BREAK -> RamBarrierFx.handle(fx);
		}
	}

	/**
	 * What a construct ally's shot leaves behind: glowing motes hanging along its path that drift
	 * and fade over a couple of seconds, brightest and thickest where it hit.
	 */
	static void allyTrail(Vec3 from, Vec3 to) {
		RandomSource r = random();
		Vec3 d = to.subtract(from);
		double len = d.length();
		if (len < 0.1) return;
		Vec3 dir = d.scale(1 / len);
		for (double t = 0.3; t < len; t += 0.35) {
			ConstructParticle p = spawn(r.nextInt(5) == 0 ? ModParticles.SPARK : ModParticles.MOTE, from.add(dir.scale(t)).add(jitter(r, 0.15)),
					jitter(r, 0.01).add(0, 0.004, 0), 0.7f + 0.3f * r.nextFloat());
			if (p != null) p.lasting(30 + r.nextInt(25));
		}
		for (int i = 0; i < 10; i++) {
			ConstructParticle p = spawn(ModParticles.MOTE, to.add(jitter(r, 0.5)), jitter(r, 0.04), 1.1f);
			if (p != null) p.lasting(25 + r.nextInt(20));
		}
	}

	/** Army mode's aim: a ring of motes where the construct will form (bigger for the Warden and Dragon). */
	static void allyMarker(Vec3 at, int type) {
		RandomSource r = random();
		double radius = type == 2 ? 0.6 : type == 1 ? 1.6 : 0.9;
		int motes = (int) (radius * 14);
		double spin = r.nextDouble() * Math.PI * 2;
		for (int i = 0; i < motes; i++) {
			double a = spin + i * Math.PI * 2 / motes;
			spawn(ModParticles.MOTE, at.add(Math.cos(a) * radius, 0.1, Math.sin(a) * radius), new Vec3(0, 0.01, 0), 0.8f);
		}
	}

	/** A construct forming: light rising up the height of its body, then a burst. */
	static void allySummon(Vec3 foot, Vec3 top, float width) {
		RandomSource r = random();
		double h = top.y - foot.y;
		for (int i = 0; i < count(40); i++) {
			double a = r.nextDouble() * Math.PI * 2;
			Vec3 at = foot.add(Math.cos(a) * width * 0.6, r.nextDouble() * h, Math.sin(a) * width * 0.6);
			spawn(i % 4 == 0 ? ModParticles.SHARD : ModParticles.MOTE, at, new Vec3(0, 0.04, 0));
		}
		burst(foot.add(0, h / 2, 0), 18, 0.12);
	}

	/**
	 * The Anvil's aim: the outline of what will drop (the anvil's top face with its horn and base,
	 * the drill tank, the anchor's arms and stock, or the ship) traced in glowing motes flat
	 * on the ground. Redrawn every other tick, so it follows the cursor.
	 */
	public static void anvilMarker(Vec3 at, Vec3 facing) {
		RandomSource r = random();
		// The facing's length is the anvil's size (1, 3 or 5): the outline scales with it.
		double size = Math.max(1, Math.round(facing.length()));
		// Same layout as AnvilShape: the long side runs across the way the bearer faces.
		Vec3 along = (Math.abs(facing.z) > Math.abs(facing.x) ? new Vec3(1, 0, 0) : new Vec3(0, 0, 1)).scale(size);
		Vec3 across = (Math.abs(facing.z) > Math.abs(facing.x) ? new Vec3(0, 0, 1) : new Vec3(1, 0, 0)).scale(size);
		Vec3 base = at.add(0, 0.08, 0);
		// Bigger outlines keep about the same gap between motes, with slightly bigger motes.
		double step = 1 / Math.sqrt(size);
		float grow = (float) Math.sqrt(size);
		if (size >= 7) {
			// Level 4, the ship, seen from above as it will land: its hull, and its funnels and bridge.
			along = along.scale(1 / size);
			across = across.scale(1 / size);
			trace(base, along, across, new double[][] {{-6.5, -2}, {-5, -5}, {0, -6.5}, {5, -5}, {6.5, -2}, {6.5, 3.5}, {-6.5, 3.5}}, 0.3, 1.5f * grow);
			trace(base, along, across, new double[][] {{-5.5, 3.5}, {5.5, 3.5}, {5.5, 8.5}, {-5.5, 8.5}}, 0.35, 1.3f * grow);
			trace(base, along, across, new double[][] {{-0.5, 8.5}, {0.5, 8.5}, {0.5, 14.5}, {-0.5, 14.5}}, 0.35, 1.1f * grow);
			sprinkle(r, base, along, across, 6.5, 6.5, (int) (6 * size));
			craterRing(base, along, across, 15, 16, 3);
		} else if (size >= 5) {
			// Level 3, the anchor, seen from above: its arms and stock in one line.
			along = along.scale(1 / size);
			across = across.scale(1 / size);
			trace(base, along, across, new double[][] {{-12, -1.5}, {12, -1.5}, {12, 1.5}, {-12, 1.5}}, 0.3, 1.5f * grow);
			sprinkle(r, base, along, across, 12, 1.5, (int) (6 * size));
			craterRing(base, along, across, 17, 7.5, 0);
		} else if (size >= 3) {
			// Level 2, the drill tank: its tracks and cab, and the drill under it.
			along = along.scale(1 / size);
			across = across.scale(1 / size);
			trace(base, along, across, new double[][] {{-6.5, -4.5}, {6.5, -4.5}, {6.5, 2.5}, {3.5, 2.5}, {3.5, 6.5}, {-3.5, 6.5}, {-3.5, 2.5}, {-6.5, 2.5}}, 0.3, 1.5f * grow);
			trace(base, along, across, circle(4, 24), 0.4, 1.1f * grow);
			sprinkle(r, base, along, across, 6, 5, (int) (6 * size));
			craterRing(base, along, across, 9.5, 9.5, 0);
		} else {
			double[][] outline = {{-1.5, -1.5}, {2.5, -1.5}, {2.5, 1.5}, {-1.5, 1.5}, {-1.5, 0.5}, {-3.5, 0.5}, {-3.5, -0.5}, {-1.5, -0.5}};
			trace(base, along, across, outline, 0.2 * step, 1.5f * grow);
			trace(base, along, across, new double[][] {{-1.5, -1.5}, {1.5, -1.5}, {1.5, 1.5}, {-1.5, 1.5}}, 0.4 * step, 1.1f * grow);
			for (int i = 0; i < count((int) (6 * size)); i++) {
				Vec3 p = base.add(along.scale(r.nextDouble() * 4 - 1.5)).add(across.scale(r.nextDouble() * 3 - 1.5));
				spawn(ModParticles.MOTE, p, new Vec3(0, 0.03, 0), 0.7f);
			}
			craterRing(base, along, across, 6.5, 6.5, 0);
		}
	}

	/**
	 * Bridge mode: the picked block glows in an outline of hard light, and once building has
	 * started the deck's front edge is outlined too, so you can see the level it's locked to.
	 */
	public static void bridgeMarker(Vec3 picked, Vec3 front, int built) {
		box(picked, 0.52, 1.2f);
		if (built > 0 || front.distanceToSqr(picked) > 0.25) box(front, 0.52, 0.9f);
	}

	/** An outline of motes round the block centred at c. */
	private static void box(Vec3 c, double h, float size) {
		double[] s = {-h, h};
		for (double a : s) {
			for (double b : s) {
				for (double t = -h; t <= h + 1e-6; t += 0.17) {
					mark(c.add(t, a, b), size);
					mark(c.add(a, t, b), size);
					mark(c.add(a, b, t), size);
				}
			}
		}
	}

	private static void mark(Vec3 at, float size) {
		ConstructParticle p = spawn(ModParticles.MOTE, at, Vec3.ZERO, size);
		if (p != null) p.lasting(3);
	}

	/**
	 * A dashed ring round the Anvil's marker showing how far its crater will reach (the crater's
	 * shape at ground level, Anvils.inCrater), so you can see what it will smash before you drop it.
	 */
	private static void craterRing(Vec3 base, Vec3 along, Vec3 across, double halfAlong, double halfAcross, double shiftAcross) {
		double around = Math.PI * (halfAlong + halfAcross);
		int dashes = Math.max(12, (int) (around / 1.6));
		for (int d = 0; d < dashes; d++) {
			// Each dash covers the first half of its slot, three motes long.
			for (int k = 0; k < 3; k++) {
				double a = (d + k / 6.0) * Math.PI * 2 / dashes;
				Vec3 p = base.add(along.scale(Math.cos(a) * halfAlong)).add(across.scale(Math.sin(a) * halfAcross + shiftAcross));
				ConstructParticle m = spawn(ModParticles.MOTE, p, Vec3.ZERO, 1.1f);
				if (m != null) m.lasting(3);
			}
		}
	}

	private static double[][] circle(double radius, int points) {
		double[][] out = new double[points][];
		for (int i = 0; i < points; i++) {
			double a = i * Math.PI * 2 / points;
			out[i] = new double[] {Math.cos(a) * radius, Math.sin(a) * radius};
		}
		return out;
	}

	/** A few motes rising anywhere in a box round the middle. */
	private static void sprinkle(RandomSource r, Vec3 base, Vec3 along, Vec3 across, double halfAlong, double halfAcross, int n) {
		for (int i = 0; i < count(n); i++) {
			Vec3 p = base.add(along.scale((r.nextDouble() * 2 - 1) * halfAlong)).add(across.scale((r.nextDouble() * 2 - 1) * halfAcross));
			spawn(ModParticles.MOTE, p, new Vec3(0, 0.03, 0), 0.7f);
		}
	}

	private static void trace(Vec3 base, Vec3 along, Vec3 across, double[][] points, double step, float size) {
		for (int i = 0; i < points.length; i++) {
			double[] a = points[i];
			double[] b = points[(i + 1) % points.length];
			double len = Math.hypot(b[0] - a[0], b[1] - a[1]);
			for (double t = 0; t < len; t += step) {
				double u = a[0] + (b[0] - a[0]) * t / len;
				double v = a[1] + (b[1] - a[1]) * t / len;
				ConstructParticle p = spawn(ModParticles.MOTE, base.add(along.scale(u)).add(across.scale(v)), Vec3.ZERO, size);
				if (p != null) p.lasting(3);
			}
		}
	}

	/**
	 * The Deluge's aim: a glowing ring on the ground as wide as the splash will be, with a small
	 * ring and a few rising motes in the middle where the globe comes down.
	 */
	public static void delugeMarker(Vec3 at, double radius) {
		RandomSource r = random();
		Vec3 base = at.add(0, 0.08, 0);
		Vec3 x = new Vec3(1, 0, 0), z = new Vec3(0, 0, 1);
		trace(base, x, z, circle(radius, (int) (radius * 5)), 0.45, 1.4f);
		trace(base, x, z, circle(1.5, 10), 0.35, 1.1f);
		sprinkle(r, base, x, z, radius * 0.6, radius * 0.6, (int) (radius * 0.8));
	}

	/**
	 * The Deluge's globe bursts: its glass shards and green drops thrown up and out, and a ring of
	 * light racing out over the ground as far as the liquid will reach.
	 */
	/**
	 * A bit of a Deluge sucked back into the ring: a few drops of it fly from where it was straight
	 * into the bearer's ring (arriving as they fade), and the ring glows as it takes them in.
	 */
	static void delugeRecall(Player bearer, Vec3 from, boolean red) {
		RandomSource r = random();
		Vec3 ring = RingEmit.ringNow(bearer, 1f);
		RingEmit.hold(bearer, from, 1f);
		for (int i = 0; i < count(3); i++) {
			Vec3 at = from.add(jitter(r, 0.8));
			// MOTE friction 0.92 over 8 ticks covers about 6.1 ticks' worth of its starting speed.
			Vec3 v = ring.subtract(at).scale(1 / (6.1 * (0.85 + 0.3 * r.nextDouble())));
			ConstructParticle p = spawn(i == 0 && !red ? ModParticles.DRIP : ModParticles.MOTE, at, v, red ? 0.9f : 1.1f);
			if (p != null) p.lasting(8);
		}
	}

	public static void delugeSplash(Vec3 at, double radius, int globe) {
		RandomSource r = random();
		if (CorpsTint.current() == Corps.RED) {
			bloodSplash(r, at, radius, globe);
			return;
		}
		int n = count(80);
		for (int i = 0; i < n; i++) {
			double a = i * Math.PI * 2 / n;
			Vec3 out = new Vec3(Math.cos(a), 0, Math.sin(a));
			spawn(ModParticles.MOTE, at.add(out.scale(1.5)).add(0, 0.3, 0), out.scale(radius * 0.08), 1.8f);
		}
		for (int i = 0; i < count(30 * globe); i++) {
			Vec3 v = jitter(r, 1.4).multiply(1, 0, 1).add(0, 0.4 + r.nextDouble() * 0.7, 0);
			spawn(ModParticles.SHARD, at.add(jitter(r, globe * 2)).add(0, globe, 0), v, 1.4f);
		}
		for (int i = 0; i < count(50 * globe); i++) {
			Vec3 v = jitter(r, 1.8).multiply(1, 0, 1).add(0, 0.5 + r.nextDouble() * 0.9, 0);
			spawn(ModParticles.DRIP, at.add(jitter(r, globe * 2)).add(0, globe, 0), v, 1.6f);
		}
		spawn(ModParticles.SPARK, at.add(0, 1, 0), Vec3.ZERO, 10f);
	}

	/**
	 * The red Deluge bursts: fine blood-red drops thrown up and out and a thin glowing ring racing
	 * over the ground; small particles, so it reads as liquid, not glowing squares.
	 */
	private static void bloodSplash(RandomSource r, Vec3 at, double radius, int globe) {
		int n = count(48);
		for (int i = 0; i < n; i++) {
			double a = i * Math.PI * 2 / n;
			Vec3 out = new Vec3(Math.cos(a), 0, Math.sin(a));
			spawn(ModParticles.MOTE, at.add(out.scale(1.5)).add(0, 0.2, 0), out.scale(radius * 0.08), 0.7f);
		}
		for (int i = 0; i < count(25 * globe); i++) {
			Vec3 v = jitter(r, 1.6).multiply(1, 0, 1).add(0, 0.5 + r.nextDouble() * 0.9, 0);
			spawn(ModParticles.DRIP, at.add(jitter(r, globe * 2)).add(0, globe, 0), v, 0.45f);
		}
	}

	/** The Anvil lands: a flash, a ring of light racing out over the ground, and shards thrown up. */
	public static void anvilImpact(Vec3 at, double radius) {
		RandomSource r = random();
		int n = count(60);
		for (int i = 0; i < n; i++) {
			double a = i * Math.PI * 2 / n;
			Vec3 out = new Vec3(Math.cos(a), 0, Math.sin(a));
			spawn(ModParticles.MOTE, at.add(out.scale(1.5)).add(0, 0.3, 0), out.scale(radius * 0.09), 1.6f);
		}
		for (int i = 0; i < count(40); i++) {
			Vec3 v = jitter(r, 1.2).multiply(1, 0, 1).add(0, 0.5 + r.nextDouble() * 0.6, 0);
			spawn(ModParticles.SHARD, at.add(jitter(r, 2)), v, 1.6f);
		}
		spawn(ModParticles.SPARK, at.add(0, 1, 0), Vec3.ZERO, 8f);
	}

	/** The Blast: a spinning drill bores down the tunnel (BlastDrillFx), leaving this style's particles. */
	public static void blast(Vec3 from, Vec3 to, double speed, int level) {
		BlastDrillFx.fire(from, to, speed, level);
	}

	/** The Blast style's particles from t0 to t1 blocks along the tunnel, as the drill passes. */
	static void blastStretch(Vec3 from, Vec3 dir, double t0, double t1, float girth) {
		RandomSource r = random();
		Vec3 right = dir.cross(UP);
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = right.cross(dir).normalize();
		switch (s().blastFx) {
			case RINGS -> {
				for (double t = Math.ceil(t0 / 1.5) * 1.5; t < t1; t += 1.5) {
					if (t < 1) continue;
					Vec3 c = from.add(dir.scale(t));
					int n = count(14);
					for (int i = 0; i < n; i++) {
						double a = i * Math.PI * 2 / n;
						Vec3 out = right.scale(Math.cos(a)).add(up.scale(Math.sin(a)));
						spawn(ModParticles.MOTE, c.add(out.scale(1.6 * girth)), out.scale(0.04).add(dir.scale(0.05)));
					}
					spawn(ModParticles.SPARK, c, Vec3.ZERO, 2f);
				}
			}
			case BEAM, SCORCH -> {
				// About one ember per block, flung off the drill's sides; they fall and glow on the floor.
				for (double t = Math.ceil(t0); t < t1; t += 1) {
					for (int i = 0; i < count(0.8f * girth); i++) ember(r, from.add(dir.scale(t + r.nextDouble())), right, up, girth);
				}
			}
		}
		// The odd chip of light off the spinning tip, falling too.
		Vec3 tip = from.add(dir.scale(t1));
		if (r.nextFloat() < 0.5f * s().amount()) ember(r, tip, right, up, girth);
	}

	/** A chip of hard light thrown off the drill near c: it drops to the floor and lies there glowing. */
	private static void ember(RandomSource r, Vec3 c, Vec3 right, Vec3 up, float girth) {
		double a = r.nextDouble() * Math.PI * 2;
		Vec3 out = right.scale(Math.cos(a)).add(up.scale(Math.sin(a)));
		ConstructParticle p = spawn(ModParticles.MOTE, c.add(out.scale(0.9 * girth)), out.scale(0.06), 1.6f);
		if (p != null) p.settling(50 + r.nextInt(50));
	}

	/** The drill has reached the end of the tunnel. */
	static void blastEnd(Vec3 from, Vec3 to, float girth) {
		if (s().blastFx == LabSettings.BlastFx.SCORCH) {
			long now = Minecraft.getInstance().level.getGameTime();
			SCARS.add(new Scar(from, to, now + Math.max(40, RingTuning.BLAST_AFTERGLOW.ticks())));
		}
		RandomSource r = random();
		Vec3 dir = to.subtract(from).normalize();
		Vec3 right = dir.cross(UP);
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = right.cross(dir).normalize();
		// The tip bursts: a bright flash, a ring of shards blown out round the tunnel's end and a
		// spray of embers that fall and lie glowing on the floor.
		spawn(ModParticles.SPARK, to, Vec3.ZERO, 6f * girth);
		spawn(ModParticles.SPARK, to.subtract(dir.scale(0.5)), Vec3.ZERO, 3.5f * girth);
		int n = count(18 * girth);
		for (int i = 0; i < n; i++) {
			double a = i * Math.PI * 2 / n;
			Vec3 out = right.scale(Math.cos(a)).add(up.scale(Math.sin(a)));
			spawn(ModParticles.SHARD, to.add(out.scale(0.4 * girth)), out.scale(0.32).add(dir.scale(0.08)).add(jitter(r, 0.04)), 1.3f);
		}
		for (int i = 0; i < count(10 * girth); i++) {
			spawn(ModParticles.MOTE, to, jitter(r, 0.5).add(dir.scale(-0.1)), 1.2f);
		}
		for (int i = 0; i < count(16 * girth); i++) {
			ConstructParticle p = spawn(ModParticles.MOTE, to.add(jitter(r, 0.3 * girth)), jitter(r, 0.35).add(0, 0.12, 0), 1.6f);
			if (p != null) p.settling(50 + r.nextInt(50));
		}
	}

	/** Beam, tether and construct casts: a line from the ring to the target. */
	public static void useLine(Vec3 from, Vec3 to, boolean burstAtEnd) {
		RandomSource r = random();
		Vec3 d = to.subtract(from);
		double len = d.length();
		if (len < 0.01) return;
		Vec3 dir = d.normalize();
		Vec3 right = dir.cross(UP);
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = right.cross(dir).normalize();
		switch (s().useFx) {
			case LINE, SHARDS -> {
				// Drawn out from the ring over the next few ticks; the burst lands when it reaches the target.
				Streak streak = new Streak(from, dir, len, s().useFx == LabSettings.UseFx.SHARDS, burstAtEnd);
				STREAKS.add(streak);
				streak(streak);
			}
			case HELIX, HELIX_RECALL -> {
				// Animated over the next few ticks; the burst lands when the tip reaches the target.
				HelixBeams.fire(from, to, s().useFx == LabSettings.UseFx.HELIX_RECALL, burstAtEnd, 1f, bearer);
			}
		}
	}

	/** Draws the next stretch of a LINE or SHARDS line; true once it has reached the target. */
	private static boolean streak(Streak k) {
		RandomSource r = random();
		double end = Math.min(k.length, k.covered + k.speed);
		if (k.shards) {
			for (double t = Math.ceil(k.covered / 0.45) * 0.45; t < end; t += 0.45) {
				spawn(ModParticles.SHARD, k.from.add(k.dir.scale(t)).add(jitter(r, 0.15)), k.dir.scale(0.08).add(jitter(r, 0.03)));
			}
		} else {
			for (double t = Math.ceil(k.covered / 0.25) * 0.25; t < end; t += 0.25) {
				spawn(ModParticles.MOTE, k.from.add(k.dir.scale(t)).add(jitter(r, 0.08)), Vec3.ZERO, t < 1 ? 0.5f : 0.9f);
			}
		}
		// The bright head of the line as it travels.
		spawn(ModParticles.SPARK, k.from.add(k.dir.scale(end)), Vec3.ZERO, 1.4f);
		k.covered = end;
		if (end >= k.length) {
			if (k.burstAtEnd) burst(k.from.add(k.dir.scale(k.length)), 12, 0.18);
			return true;
		}
		return false;
	}

	private static void streaks() {
		for (Iterator<Streak> it = STREAKS.iterator(); it.hasNext(); ) {
			Streak k = it.next();
			Corps before = CorpsTint.enter(k.corps);
			boolean done = k.covered >= k.length || streak(k);
			CorpsTint.restore(before);
			if (done) it.remove();
		}
	}

	/**
	 * The charged Beam: a fat helix (in a helix style; otherwise the normal line style) whose hit
	 * blows out a Shockwave-sized dome of hard light, matching the server's explosion.
	 */
	public static void chargedBeam(Vec3 from, Vec3 to) {
		if (s().useFx == LabSettings.UseFx.HELIX || s().useFx == LabSettings.UseFx.HELIX_RECALL) {
			HelixBeams.fire(from, to, s().useFx == LabSettings.UseFx.HELIX_RECALL, true, 2.2f, bearer);
		} else {
			useLine(from, to, true);
		}
		shockwave(to);
		burst(to, 40, 0.4);
	}

	/**
	 * A clear jade dome that grows out from the bearer's feet at the same speed as the server's
	 * Shockwaves barrier. The glass itself is a smooth mesh (ShockwaveDomes). Here a grid of panes
	 * flies out with it, one per direction, unseen except where the dome cuts into blocks: there
	 * they light up as the bright seam along the ground, a hill or a tunnel wall.
	 */
	public static void shockwave(Vec3 at) {
		shockwave(at, Shockwaves.RADIUS);
	}

	/** The same dome grown only to radius blocks, like the smaller one where a Beam lands. */
	public static void shockwave(Vec3 at, double radius) {
		ShockwaveDomes.start(at, (float) radius);
		double step = 0.08;
		double r0 = 0.4;
		// Panes just touch their neighbours (quadSize is half a pane's width), so the seam is unbroken.
		float size = (float) (0.53 * r0 * step);
		float growth = (float) (0.53 * Shockwaves.SPEED * step);
		int life = (int) Math.ceil((radius - r0) / Shockwaves.SPEED) + 3;
		int ring = 0;
		for (double pitch = -0.12; pitch < Math.PI / 2; pitch += step, ring++) {
			int n = Math.max(1, (int) Math.round(Math.PI * 2 * Math.cos(pitch) / step));
			double shift = (ring % 2) * 0.5;
			for (int i = 0; i < n; i++) {
				double yaw = (i + shift) * Math.PI * 2 / n;
				Vec3 out = new Vec3(Math.cos(yaw) * Math.cos(pitch), Math.sin(pitch), Math.sin(yaw) * Math.cos(pitch));
				ConstructParticle p = spawn(ModParticles.PANE, at.add(out.scale(r0)), out.scale(Shockwaves.SPEED), 1f);
				if (p != null) p.tinted(0.4f, 1f, 0.6f).paned(size, growth, life);
			}
		}
		spawn(ModParticles.SPARK, at.add(0, 0.8, 0), Vec3.ZERO, (float) (3 * radius / Shockwaves.RADIUS));
	}

	/** Light streaming from a battery (or the forge) up into the ring at top. */
	public static void charge(Vec3 battery, Vec3 top) {
		for (double t = 0; t < 1; t += 0.04) {
			double a = t * 14;
			Vec3 p = battery.lerp(top, t).add(Math.cos(a) * 0.35, 0, Math.sin(a) * 0.35);
			spawn(ModParticles.MOTE, p, new Vec3(0, 0.03, 0));
		}
		burst(battery, 24, 0.12);
	}

	static void burst(Vec3 at, int base, double speed) {
		RandomSource r = random();
		for (int i = 0; i < count(base); i++) {
			spawn(i % 3 == 0 ? ModParticles.SHARD : ModParticles.MOTE, at, jitter(r, speed * 2));
		}
		spawn(ModParticles.SPARK, at, Vec3.ZERO, 2.5f);
	}

	// ---- every tick: ring glow, flight, glowing blocks ---------------------------------------

	public static void tick(Minecraft mc) {
		// Scorch marks belong to one world: drop them on leaving it or changing dimension.
		if (mc.level != scarLevel) {
			SCARS.clear();
			scarLevel = mc.level;
		}
		if (mc.level == null || mc.player == null) {
			HelixBeams.clear();
			BlastDrillFx.clear();
			NukeAuraFx.clear();
			FearNukeFx.clear();
			AirburstFx.clear();
			FearGasFx.clear();
			NukeHold.clear();
			STREAKS.clear();
			RingEmit.clear();
		}
		if (mc.level == null || mc.player == null || mc.isPaused()) return;
		RandomSource r = mc.level.getRandom();
		for (Player player : mc.level.players()) {
			if (player.distanceToSqr(mc.player) > 48 * 48) continue;
			boolean right = holdsRing(player, HumanoidArm.RIGHT);
			boolean left = holdsRing(player, HumanoidArm.LEFT);
			Corps before = CorpsTint.enter(Corps.held(player));
			if (right) ringGlow(mc, player, HumanoidArm.RIGHT, r);
			if (left) ringGlow(mc, player, HumanoidArm.LEFT, r);
			if ((right || left) && isFlying(mc, player)) flight(player, r);
			CorpsTint.restore(before);
		}
		Corps before = CorpsTint.enter(Corps.held(mc.player));
		if (s().blockGlow == LabSettings.BlockGlow.NEARBY && (holdsRing(mc.player, HumanoidArm.RIGHT) || holdsRing(mc.player, HumanoidArm.LEFT))) {
			nearbyBlocks(mc, r);
		}
		BeamChargeGlow.tick(mc, r);
		CorpsTint.restore(before);
		scars(mc, r);
		HelixBeams.tick(mc);
		BlastDrillFx.tick(mc);
		NukeAuraFx.tick(mc);
		FearNukeFx.tick(mc);
		AirburstFx.tick(mc);
		FearGasFx.tick(mc);
		streaks();
		RingEmit.tick(mc);
	}

	public static boolean holdsRing(Player player, HumanoidArm arm) {
		boolean mainIsArm = player.getMainArm() == arm;
		return (mainIsArm ? player.getMainHandItem() : player.getOffhandItem()).getItem() instanceof PowerRingItem;
	}

	private static boolean isFlying(Minecraft mc, Player player) {
		if (player == mc.player) return player.getAbilities().flying;
		return !player.onGround() && Math.abs(player.getDeltaMovement().y) < 0.08 && !player.isInWater();
	}

	/** Where the ring sits in the world: on the first-person fist, or on the hand of the body. */
	public static Vec3 ringPos(Minecraft mc, Player player, HumanoidArm arm) {
		float side = arm == HumanoidArm.RIGHT ? 1 : -1;
		if (player == mc.player && mc.options.getCameraType().isFirstPerson()) {
			Vec3 drawn = RingFirstPerson.drawnFace(mc, arm);
			if (drawn != null) return drawn;
			Vec3 look = player.getViewVector(1f);
			Vec3 right = look.cross(UP);
			right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
			Vec3 up = right.cross(look).normalize();
			float[] at = RingFirstPerson.ringOffset(FlightPoses.localPoint(1f));
			return player.getEyePosition(1f).add(look.scale(at[2])).add(right.scale(side * at[0])).subtract(up.scale(at[1]));
		}
		float yaw = player.yBodyRot * Mth.DEG_TO_RAD;
		Vec3 forward = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		Vec3 right = new Vec3(-Mth.cos(yaw), 0, -Mth.sin(yaw));
		double height = player.isCrouching() ? 0.5 : 0.64;
		return player.position().add(right.scale(side * 0.37)).add(forward.scale(0.08)).add(0, height, 0);
	}

	private static void ringGlow(Minecraft mc, Player player, HumanoidArm arm, RandomSource r) {
		Vec3 at = ringPos(mc, player, arm);
		float amount = s().amount();
		switch (s().ringGlow) {
			case OFF -> { }
			case MOTES -> {
				if (r.nextFloat() < 0.45f * amount) {
					double a = player.tickCount * 0.35 + r.nextDouble();
					Vec3 off = new Vec3(Math.cos(a) * 0.09, (r.nextDouble() - 0.3) * 0.08, Math.sin(a) * 0.09);
					spawn(ModParticles.MOTE, at.add(off), new Vec3(0, 0.012, 0), 0.45f);
				}
			}
			case DRIPS -> {
				if (r.nextFloat() < 0.12f * amount) spawn(ModParticles.DRIP, at.add(jitter(r, 0.08)), Vec3.ZERO, 0.8f);
			}
			case AURA -> {
				if (r.nextFloat() < 0.5f * amount) {
					spawn(ModParticles.MOTE, at.add(jitter(r, 0.14)), new Vec3(0, 0.01, 0), 0.5f);
				}
				if (r.nextFloat() < 0.06f * amount) spawn(ModParticles.DRIP, at.add(jitter(r, 0.06)), Vec3.ZERO, 0.7f);
				if (r.nextFloat() < 0.04f * amount) spawn(ModParticles.SPARK, at, Vec3.ZERO, 0.6f);
			}
		}
	}

	private static void flight(Player player, RandomSource r) {
		float amount = s().amount();
		Vec3 feet = player.position();
		switch (s().flightFx) {
			case OFF -> { }
			case TRAIL -> {
				for (int i = 0; i < count(2); i++) {
					spawn(ModParticles.MOTE, feet.add(jitter(r, 0.5)).add(0, 0.2, 0), player.getDeltaMovement().scale(-0.2), 1.1f);
				}
			}
			case JETS -> {
				for (int i = 0; i < count(3); i++) {
					spawn(ModParticles.SPARK, feet.add(jitter(r, 0.25)), new Vec3(0, -0.25, 0), 0.9f);
				}
				if (r.nextFloat() < 0.3f * amount) spawn(ModParticles.DRIP, feet.add(jitter(r, 0.3)), new Vec3(0, -0.1, 0));
			}
			case HALO -> {
				int n = count(3);
				for (int i = 0; i < n; i++) {
					double a = player.tickCount * 0.25 + i * Math.PI * 2 / Math.max(1, n);
					spawn(ModParticles.MOTE, feet.add(Math.cos(a) * 0.7, 1.0, Math.sin(a) * 0.7), new Vec3(0, -0.02, 0), 0.9f);
				}
			}
		}
	}

	/** Crying-obsidian style: blocks around the ring bearer weep green drips and breathe motes. */
	private static void nearbyBlocks(Minecraft mc, RandomSource r) {
		Level level = mc.level;
		BlockPos center = mc.player.blockPosition();
		for (int i = 0; i < count(10); i++) {
			BlockPos pos = center.offset(r.nextInt(21) - 10, r.nextInt(13) - 5, r.nextInt(21) - 10);
			BlockState state = level.getBlockState(pos);
			if (!state.isSolidRender()) continue;
			if (level.getBlockState(pos.below()).isAir()) {
				spawn(ModParticles.DRIP, new Vec3(pos.getX() + r.nextDouble(), pos.getY() - 0.05, pos.getZ() + r.nextDouble()), Vec3.ZERO);
			} else if (level.getBlockState(pos.above()).isAir() && r.nextBoolean()) {
				spawn(ModParticles.MOTE, new Vec3(pos.getX() + r.nextDouble(), pos.getY() + 1.05, pos.getZ() + r.nextDouble()), new Vec3(0, 0.02, 0), 0.8f);
			}
		}
	}

	private static void scars(Minecraft mc, RandomSource r) {
		long now = mc.level.getGameTime();
		for (Iterator<Scar> it = SCARS.iterator(); it.hasNext(); ) {
			Scar scar = it.next();
			if (now > scar.until) {
				it.remove();
				continue;
			}
			// Now and then a drop of light gathers on the tunnel roof and falls to the floor.
			Vec3 dir = scar.to.subtract(scar.from);
			for (int i = 0; i < count(0.6f); i++) {
				Vec3 c = scar.from.add(dir.scale(r.nextDouble()));
				spawn(ModParticles.DRIP, c.add((r.nextDouble() - 0.5) * 2, 1.4, (r.nextDouble() - 0.5) * 2), Vec3.ZERO);
			}
		}
	}

	// ---- block ambience (called from the blocks' animateTick) --------------------------------

	public static void batteryAmbient(Level level, BlockPos pos, RandomSource r) {
		if (s().blockGlow == LabSettings.BlockGlow.OFF) return;
		Corps before = CorpsTint.enter(Corps.of(level.getBlockState(pos)));
		Vec3 c = Vec3.atCenterOf(pos);
		spawn(ModParticles.MOTE, c.add(jitter(r, 0.4)), new Vec3(0, 0.025, 0), 0.8f);
		if (r.nextInt(4) == 0) spawn(ModParticles.DRIP, new Vec3(c.x + (r.nextDouble() - 0.5) * 0.5, pos.getY() + 0.1, c.z + (r.nextDouble() - 0.5) * 0.5), Vec3.ZERO);
		CorpsTint.restore(before);
	}

	public static void constructAmbient(Level level, BlockPos pos, RandomSource r) {
		if (s().blockGlow == LabSettings.BlockGlow.OFF || r.nextInt(3) != 0) return;
		Corps before = CorpsTint.enter(Corps.of(level.getBlockState(pos)));
		if (level.getBlockState(pos.below()).isAir()) {
			spawn(ModParticles.DRIP, new Vec3(pos.getX() + r.nextDouble(), pos.getY() - 0.05, pos.getZ() + r.nextDouble()), Vec3.ZERO);
		} else {
			spawn(ModParticles.MOTE, Vec3.atCenterOf(pos).add(jitter(r, 1)), new Vec3(0, 0.01, 0), 0.6f);
		}
		CorpsTint.restore(before);
	}

	// ---- Ring Lab previews (client only, nothing is broken) ----------------------------------

	public static void preview(String what) {
		Minecraft mc = Minecraft.getInstance();
		Player p = mc.player;
		if (p == null) return;
		Vec3 eye = p.getEyePosition();
		Vec3 look = p.getViewVector(1f);
		Vec3 hand = RingEmit.shotOrigin(p);
		bearer = p;
		// Previews take the held ring's colour, like real shots do.
		Corps before = CorpsTint.enter(Corps.held(p));
		try {
			switch (what) {
				case "blast" -> {
					Vec3 end = eye.subtract(0, 0.6, 0).add(look.scale(BlastDrills.LENGTH));
					RingEmit.muzzle(p, hand, end, 1.3f);
					blast(hand, end, BlastDrills.speed(), 1);
				}
				case "use" -> {
					RingEmit.muzzle(p, hand, eye.add(look.scale(14)), 1f);
					useLine(hand, eye.add(look.scale(14)), true);
				}
				case "push" -> {
					RingEmit.flash(p, 1.8f);
					shockwave(p.position());
				}
				case "charge" -> charge(p.position().add(look.scale(2)), RingEmit.ringNow(p, 1f));
				default -> { }
			}
		} finally {
			bearer = null;
			CorpsTint.restore(before);
		}
	}
}
