package com.sparky.lanternring.client;

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

	private record Scar(Vec3 from, Vec3 to, long until) {
	}

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
		switch (fx.kind()) {
			case BLAST -> blast(fx.from(), fx.to());
			case BEAM, TETHER, CONSTRUCT -> useLine(fx.from(), fx.to(), fx.kind() != RingFxPayload.Kind.CONSTRUCT);
			case PUSH -> shockwave(fx.from());
			case CHARGE -> charge(fx.from(), fx.to());
			case MODE_CHANGE -> burst(fx.from().add(0, 1, 0), 10, 0.15);
			case BEAM_CHARGED -> chargedBeam(fx.from(), fx.to());
			case ANVIL_MARK -> anvilMarker(fx.from(), fx.to().subtract(fx.from()));
			case ANVIL_IMPACT -> anvilImpact(fx.from(), fx.to().distanceTo(fx.from()));
			case SHOCKWAVE -> shockwave(fx.from(), fx.to().distanceTo(fx.from()));
		}
	}

	/**
	 * The Anvil's aim: the anvil's outline (top face with its horn, and the base inside it) traced
	 * in glowing motes flat on the ground. Redrawn every other tick, so it follows the cursor.
	 */
	public static void anvilMarker(Vec3 at, Vec3 facing) {
		RandomSource r = random();
		// The facing's length is the anvil's size (1, 3 or 5): the outline scales with it.
		double size = Math.max(1, Math.round(facing.length()));
		// Same layout as Anvils.SHAPE: the long side runs across the way the bearer faces.
		Vec3 along = (Math.abs(facing.z) > Math.abs(facing.x) ? new Vec3(1, 0, 0) : new Vec3(0, 0, 1)).scale(size);
		Vec3 across = (Math.abs(facing.z) > Math.abs(facing.x) ? new Vec3(0, 0, 1) : new Vec3(1, 0, 0)).scale(size);
		Vec3 base = at.add(0, 0.08, 0);
		// Bigger outlines keep about the same gap between motes, with slightly bigger motes.
		double step = 1 / Math.sqrt(size);
		float grow = (float) Math.sqrt(size);
		double[][] outline = {{-1.5, -1.5}, {2.5, -1.5}, {2.5, 1.5}, {-1.5, 1.5}, {-1.5, 0.5}, {-3.5, 0.5}, {-3.5, -0.5}, {-1.5, -0.5}};
		trace(base, along, across, outline, 0.2 * step, 1.5f * grow);
		trace(base, along, across, new double[][] {{-1.5, -1.5}, {1.5, -1.5}, {1.5, 1.5}, {-1.5, 1.5}}, 0.4 * step, 1.1f * grow);
		for (int i = 0; i < count((int) (6 * size)); i++) {
			Vec3 p = base.add(along.scale(r.nextDouble() * 4 - 1.5)).add(across.scale(r.nextDouble() * 3 - 1.5));
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

	public static void blast(Vec3 from, Vec3 to) {
		RandomSource r = random();
		Vec3 dir = to.subtract(from);
		double len = dir.length();
		dir = dir.normalize();
		Vec3 right = dir.cross(UP);
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = right.cross(dir).normalize();
		switch (s().blastFx) {
			case RINGS -> {
				for (double t = 1; t < len; t += 1.5) {
					Vec3 c = from.add(dir.scale(t));
					int n = count(14);
					for (int i = 0; i < n; i++) {
						double a = i * Math.PI * 2 / n;
						Vec3 out = right.scale(Math.cos(a)).add(up.scale(Math.sin(a)));
						spawn(ModParticles.MOTE, c.add(out.scale(1.6)), out.scale(0.04).add(dir.scale(0.05)));
					}
					spawn(ModParticles.SPARK, c, Vec3.ZERO, 2f);
				}
			}
			case BEAM, SCORCH -> {
				for (double t = 0.5; t < len; t += 0.35) {
					Vec3 c = from.add(dir.scale(t));
					for (int i = 0; i < count(2); i++) {
						spawn(ModParticles.MOTE, c.add(jitter(r, 1.2)), dir.scale(0.2).add(jitter(r, 0.05)), 1.3f);
					}
					if (r.nextFloat() < 0.25f * s().amount()) spawn(ModParticles.SHARD, c.add(jitter(r, 2.4)), jitter(r, 0.2));
					if (r.nextFloat() < 0.15f) spawn(ModParticles.SPARK, c, Vec3.ZERO, 2.5f);
				}
				if (s().blastFx == LabSettings.BlastFx.SCORCH) {
					long now = Minecraft.getInstance().level.getGameTime();
					SCARS.add(new Scar(from, to, now + Math.max(40, RingTuning.BLAST_AFTERGLOW.ticks())));
				}
			}
		}
		burst(to, 20, 0.3);
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
			case LINE -> {
				for (double t = 0; t < len; t += 0.25) {
					spawn(ModParticles.MOTE, from.add(dir.scale(t)).add(jitter(r, 0.08)), Vec3.ZERO, 0.9f);
				}
			}
			case HELIX, HELIX_RECALL -> {
				// Animated over the next few ticks; the burst lands when the tip reaches the target.
				HelixBeams.fire(from, to, s().useFx == LabSettings.UseFx.HELIX_RECALL, burstAtEnd, 1f);
				return;
			}
			case SHARDS -> {
				for (double t = 0; t < len; t += 0.45) {
					spawn(ModParticles.SHARD, from.add(dir.scale(t)).add(jitter(r, 0.15)), dir.scale(0.08).add(jitter(r, 0.03)));
				}
			}
		}
		if (burstAtEnd) burst(to, 12, 0.18);
	}

	/**
	 * The charged Beam: a fat helix (in a helix style; otherwise the normal line style) whose hit
	 * blows out a Shockwave-sized dome of hard light, matching the server's explosion.
	 */
	public static void chargedBeam(Vec3 from, Vec3 to) {
		if (s().useFx == LabSettings.UseFx.HELIX || s().useFx == LabSettings.UseFx.HELIX_RECALL) {
			HelixBeams.fire(from, to, s().useFx == LabSettings.UseFx.HELIX_RECALL, true, 2.2f);
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

	public static void charge(Vec3 battery, Vec3 player) {
		Vec3 top = player.add(0, 1, 0);
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
		if (mc.level == null || mc.player == null) HelixBeams.clear();
		if (mc.level == null || mc.player == null || mc.isPaused()) return;
		RandomSource r = mc.level.getRandom();
		for (Player player : mc.level.players()) {
			if (player.distanceToSqr(mc.player) > 48 * 48) continue;
			boolean right = holdsRing(player, HumanoidArm.RIGHT);
			boolean left = holdsRing(player, HumanoidArm.LEFT);
			if (right) ringGlow(mc, player, HumanoidArm.RIGHT, r);
			if (left) ringGlow(mc, player, HumanoidArm.LEFT, r);
			if ((right || left) && isFlying(mc, player)) flight(player, r);
		}
		if (s().blockGlow == LabSettings.BlockGlow.NEARBY && (holdsRing(mc.player, HumanoidArm.RIGHT) || holdsRing(mc.player, HumanoidArm.LEFT))) {
			nearbyBlocks(mc, r);
		}
		scars(mc, r);
		HelixBeams.tick(mc);
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
			Vec3 dir = scar.to.subtract(scar.from);
			for (int i = 0; i < count(4); i++) {
				Vec3 c = scar.from.add(dir.scale(r.nextDouble()));
				Vec3 off = jitter(r, 1).normalize().scale(1.6);
				Vec3 p = c.add(off);
				if (off.y > 0.3) spawn(ModParticles.DRIP, p, Vec3.ZERO);
				else spawn(ModParticles.MOTE, p, off.scale(-0.01), 0.8f);
			}
		}
	}

	// ---- block ambience (called from the blocks' animateTick) --------------------------------

	public static void batteryAmbient(Level level, BlockPos pos, RandomSource r) {
		if (s().blockGlow == LabSettings.BlockGlow.OFF) return;
		Vec3 c = Vec3.atCenterOf(pos);
		spawn(ModParticles.MOTE, c.add(jitter(r, 0.4)), new Vec3(0, 0.025, 0), 0.8f);
		if (r.nextInt(4) == 0) spawn(ModParticles.DRIP, new Vec3(c.x + (r.nextDouble() - 0.5) * 0.5, pos.getY() + 0.1, c.z + (r.nextDouble() - 0.5) * 0.5), Vec3.ZERO);
	}

	public static void constructAmbient(Level level, BlockPos pos, RandomSource r) {
		if (s().blockGlow == LabSettings.BlockGlow.OFF || r.nextInt(3) != 0) return;
		if (level.getBlockState(pos.below()).isAir()) {
			spawn(ModParticles.DRIP, new Vec3(pos.getX() + r.nextDouble(), pos.getY() - 0.05, pos.getZ() + r.nextDouble()), Vec3.ZERO);
		} else {
			spawn(ModParticles.MOTE, Vec3.atCenterOf(pos).add(jitter(r, 1)), new Vec3(0, 0.01, 0), 0.6f);
		}
	}

	// ---- Ring Lab previews (client only, nothing is broken) ----------------------------------

	public static void preview(String what) {
		Minecraft mc = Minecraft.getInstance();
		Player p = mc.player;
		if (p == null) return;
		Vec3 eye = p.getEyePosition();
		Vec3 look = p.getViewVector(1f);
		Vec3 hand = ringPos(mc, p, p.getMainArm());
		switch (what) {
			case "blast" -> blast(eye.subtract(0, 0.6, 0).add(look), eye.add(look.scale(50)));
			case "use" -> useLine(hand, eye.add(look.scale(14)), true);
			case "push" -> shockwave(p.position());
			case "charge" -> charge(p.position().add(look.scale(2)), p.position());
			default -> { }
		}
	}
}
