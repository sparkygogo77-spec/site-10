package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.Iterator;
import java.util.List;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

/**
 * Powers come out of the ring: where a bearer's ring is right now (on your first-person fist as
 * drawn, or at the end of another player's raised ring arm), the flash as the power leaves it, the
 * light that keeps pouring out of it for a moment after, and the stream that feeds the Dome and
 * the Shield while they are held. The server still aims from the eyes; only the light starts here.
 */
public final class RingEmit {
	private static final Vec3 UP = new Vec3(0, 1, 0);
	/** Third person: shoulder height above the feet, its offsets, and the arm's length to the ring (as LassoFx). */
	private static final double SHOULDER = 1.375;
	private static final double CROUCH_DROP = 0.14;
	private static final double SHOULDER_SIDE = 0.37;
	private static final double SHOULDER_FORWARD = 0.08;
	private static final double ARM = 0.735;
	/** First person, the fist punched out to aim (RingFirstPerson.AIM_FIST): the ring face's offset {right, up, back} at hand scale. */
	private static final float[] AIMED_FACE = {0.17f, -0.14f, -1.0f};
	private static final float HAND_FOV = 70f;
	/** Ticks the ring keeps pouring light after a power leaves it. */
	private static final int AFTERGLOW = 6;

	private static final List<Glow> GLOWS = new ArrayList<>();
	/** Ticks the ring face flares for after a power leaves it (drawn on the hand, see BeamChargeGlow.renderFlash). */
	private static final float FLARE = 8f;
	/** When each bearer's ring last fired, by entity id, in game ticks. */
	private static final Map<Integer, Long> FLARES = new HashMap<>();
	private static final Map<Integer, Float> FLARE_POWER = new HashMap<>();
	/** Ticks a held flare lasts after the server's last word on it (it repeats every other tick). */
	private static final int HOLD_LAPSE = 4;
	/** Rings held flaring while they form something (the Deluge's ball), by bearer entity id. */
	private static final Map<Integer, Hold> HOLDS = new HashMap<>();

	/** A ring flaring and pouring light into what it is forming, until {@code until}. */
	private static final class Hold {
		long until;
		long since;
		float power;
		Vec3 target;
		Corps corps;
	}

	/** Light still pouring out of a bearer's ring toward where the power went. */
	private static final class Glow {
		final int bearer;
		final Vec3 target;
		final float power;
		final Corps corps = CorpsTint.current();
		int age;

		Glow(int bearer, Vec3 target, float power) {
			this.bearer = bearer;
			this.target = target;
			this.power = power;
		}
	}

	private RingEmit() {
	}

	/** The player whose ring an effect came out of, or null when none did (or they are out of sight). */
	public static Player bearer(int id) {
		Minecraft mc = Minecraft.getInstance();
		if (id < 0 || mc.level == null) return null;
		return mc.level.getEntity(id) instanceof Player p ? p : null;
	}

	/** The hand wearing the ring: the main hand if it holds one, else the off hand. */
	public static HumanoidArm ringArm(Player player) {
		return isRing(player.getMainHandItem()) || !isRing(player.getOffhandItem()) ? player.getMainArm() : player.getMainArm().getOpposite();
	}

	private static boolean isRing(ItemStack stack) {
		return stack != null && stack.getItem() instanceof PowerRingItem;
	}

	private static boolean firstPerson(Minecraft mc, Player player) {
		return player == mc.player && mc.options.getCameraType().isFirstPerson();
	}

	/**
	 * Where a power leaving the bearer's ring starts: in first person on the fist punched out to
	 * aim (it gets there a tick or two after the shot, so the light starts where the ring is going);
	 * in third person at the end of the ring arm, raised to point where they look.
	 */
	public static Vec3 shotOrigin(Player player) {
		Minecraft mc = Minecraft.getInstance();
		HumanoidArm arm = ringArm(player);
		if (firstPerson(mc, player)) {
			// Already pointing (a second shot, or holding a construct): exactly where it is drawn.
			if (FlightPoses.localPoint(1f) > 0.9f) {
				Vec3 drawn = RingFirstPerson.drawnFace(mc, arm);
				if (drawn != null) return drawn;
			}
			return aimedFace(mc, arm);
		}
		return armRing(player, 1f, 1f);
	}

	/** Where the bearer's ring is right now, as it is drawn (for light that follows the ring). */
	public static Vec3 ringNow(Player player, float partial) {
		Minecraft mc = Minecraft.getInstance();
		HumanoidArm arm = ringArm(player);
		if (firstPerson(mc, player)) return LabFx.ringPos(mc, player, arm);
		return armRing(player, partial, FlightPoses.aim(player, partial));
	}

	/** Like ringNow, for a ring that just fired: another player's ring arm is pointing where they look. */
	public static Vec3 ringFiring(Player player, float partial) {
		Minecraft mc = Minecraft.getInstance();
		if (firstPerson(mc, player)) return LabFx.ringPos(mc, player, ringArm(player));
		return armRing(player, partial, 1f);
	}

	/** First person: the ring face on the fist punched out at the crosshair, seen at the world's field of view. */
	private static Vec3 aimedFace(Minecraft mc, HumanoidArm arm) {
		Camera camera = mc.gameRenderer.mainCamera();
		double k = Math.tan(Math.toRadians(camera.getFov()) / 2) / Math.tan(Math.toRadians(HAND_FOV) / 2);
		float side = arm == HumanoidArm.RIGHT ? 1f : -1f;
		Vector3f world = camera.rotation().transform(new Vector3f((float) (side * AIMED_FACE[0] * k), (float) (AIMED_FACE[1] * k), AIMED_FACE[2]));
		return camera.position().add(world.x, world.y, world.z);
	}

	/** Third person: the end of the ring arm, raised by aim (0 hanging, 1 pointing where they look). */
	private static Vec3 armRing(Player player, float partial, float aim) {
		float side = ringArm(player) == HumanoidArm.RIGHT ? 1 : -1;
		float yaw = Mth.rotLerp(partial, player.yBodyRotO, player.yBodyRot) * Mth.DEG_TO_RAD;
		Vec3 forward = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		Vec3 right = new Vec3(-Mth.cos(yaw), 0, -Mth.sin(yaw));
		double height = SHOULDER - (player.isCrouching() ? CROUCH_DROP : 0);
		Vec3 shoulder = player.getPosition(partial).add(right.scale(side * SHOULDER_SIDE)).add(forward.scale(SHOULDER_FORWARD)).add(0, height, 0);
		Vec3 dir = new Vec3(0, -1, 0).lerp(player.getViewVector(partial), aim);
		dir = dir.lengthSqr() < 1e-4 ? player.getViewVector(partial) : dir.normalize();
		return shoulder.add(dir.scale(ARM));
	}

	// ---- the flash --------------------------------------------------------------------------

	/**
	 * A power leaves the ring at {@code at} heading for {@code target}: a flash on the ring face, a
	 * ring of light blown out round it, a cone of sparks thrown forward, and light that keeps
	 * pouring out of the ring for a few ticks. {@code power} scales it (1 a tap, 2 a big one).
	 */
	public static void muzzle(Player bearer, Vec3 at, Vec3 target, float power) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		RandomSource r = mc.level.getRandom();
		Vec3 d = target.subtract(at);
		Vec3 dir = d.lengthSqr() < 1e-4 ? bearer.getViewVector(1f) : d.normalize();
		Vec3 right = dir.cross(UP);
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = right.cross(dir).normalize();
		// Right in front of your own eyes everything is drawn smaller, so it frames the fist instead of hiding it.
		float near = firstPerson(mc, bearer) ? 0.45f : 1f;
		LabFx.spawn(ModParticles.SPARK, at, Vec3.ZERO, 1.6f * power * near);
		LabFx.spawn(ModParticles.SPARK, at.add(dir.scale(0.25)), dir.scale(0.08), 1.1f * power * near);
		// The ring of light blown out round the ring face.
		int n = LabFx.count(12 * power);
		for (int i = 0; i < n; i++) {
			double a = i * Math.PI * 2 / Math.max(1, n);
			Vec3 out = right.scale(Math.cos(a)).add(up.scale(Math.sin(a)));
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, at.add(out.scale(0.06)), out.scale(0.07 * power).add(dir.scale(0.05)), 0.55f * near);
			if (p != null) p.lasting(6 + r.nextInt(4));
		}
		// Sparks thrown forward along the shot.
		for (int i = 0; i < LabFx.count(8 * power); i++) {
			Vec3 v = dir.scale(0.25 + 0.35 * r.nextDouble()).add(LabFx.jitter(r, 0.12));
			ConstructParticle p = LabFx.spawn(i % 3 == 0 ? ModParticles.SHARD : ModParticles.MOTE, at.add(dir.scale(0.1)), v, 0.6f * near);
			if (p != null) p.lasting(5 + r.nextInt(5));
		}
		GLOWS.add(new Glow(bearer.getId(), target, power));
		flare(bearer);
	}

	static void flare(Player bearer) {
		softFlare(bearer, 1f);
	}

	/** A flare only {@code strength} (0..1) as bright: a punch's, which comes again and again (J's glow bug). */
	static void softFlare(Player bearer, float strength) {
		FLARES.put(bearer.getId(), bearer.level().getGameTime());
		FLARE_POWER.put(bearer.getId(), strength);
	}

	/** 1 the moment this player's ring fires, fading to 0 over FLARE ticks: how bright its flare is. */
	public static float flare(Player player, float partial) {
		Long at = FLARES.get(player.getId());
		if (at == null) return 0f;
		float age = player.level().getGameTime() - at + partial;
		return age < 0 || age >= FLARE ? 0f : (1f - age / FLARE) * FLARE_POWER.getOrDefault(player.getId(), 1f);
	}

	/**
	 * The ring keeps forming something out at {@code target} (the Deluge's held ball): it flares and
	 * pours light toward it for a few ticks; the server repeats this while it lasts. power 0..1.
	 */
	public static void hold(Player bearer, Vec3 target, float power) {
		Hold h = HOLDS.computeIfAbsent(bearer.getId(), id -> {
			Hold fresh = new Hold();
			fresh.since = bearer.level().getGameTime();
			return fresh;
		});
		h.until = bearer.level().getGameTime() + HOLD_LAPSE;
		h.power = power;
		h.target = target;
		h.corps = CorpsTint.current();
	}

	/** How strongly this player's ring glows while held forming something, 0 when it isn't: steady, easing in and out. */
	public static float held(Player player, float partial) {
		Hold h = HOLDS.get(player.getId());
		if (h == null) return 0f;
		float left = h.until - player.level().getGameTime() - partial;
		if (left <= 0) return 0f;
		float in = Mth.clamp((player.level().getGameTime() - h.since + partial) / 10f, 0f, 1f);
		float out = Math.min(1f, left / 2f);
		return h.power * in * in * (3 - 2 * in) * out;
	}

	/** The colour of the ring held forming something (for the screen's glare), or null when none is. */
	public static Corps heldCorps(Player player) {
		Hold h = HOLDS.get(player.getId());
		return h == null ? null : h.corps;
	}

	/** A small flash on the ring with no direction: changing mode, charging. */
	public static void flash(Player bearer, float size) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Vec3 at = ringNow(bearer, 1f);
		float near = firstPerson(mc, bearer) ? 0.45f : 1f;
		LabFx.spawn(ModParticles.SPARK, at, Vec3.ZERO, 1.2f * size * near);
		flare(bearer);
		RandomSource r = mc.level.getRandom();
		for (int i = 0; i < LabFx.count(8 * size); i++) {
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, at, LabFx.jitter(r, 0.08 * size), 0.5f * near);
			if (p != null) p.lasting(8 + r.nextInt(6));
		}
	}

	/**
	 * An aim marker is out in the world (Anvil, Deluge, Black Hole, Army): a faint thread of light
	 * runs from the ring to it, so you can see the ring is what's reaching there. Called with each
	 * marker redraw (every other tick or so).
	 */
	public static void aimThread(Player bearer, Vec3 target) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		RandomSource r = mc.level.getRandom();
		Vec3 from = ringNow(bearer, 1f);
		Vec3 d = target.subtract(from);
		double len = d.length();
		if (len < 1) return;
		Vec3 dir = d.scale(1 / len);
		float near = firstPerson(mc, bearer) ? 0.45f : 1f;
		// A glint on the ring face, and motes sliding out along the thread toward the marker.
		if (r.nextInt(2) == 0) LabFx.spawn(ModParticles.SPARK, from, Vec3.ZERO, 0.5f * near);
		int n = LabFx.count((float) Math.min(10, 2 + len / 4));
		for (int i = 0; i < n; i++) {
			double t = Math.min(len, 0.4 + r.nextDouble() * len);
			double speed = Math.min(1.5, len / 8);
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, from.add(dir.scale(t)), dir.scale(speed), t < 2 ? 0.4f * near : 0.6f);
			if (p != null) p.lasting(3);
		}
	}

	// ---- every tick -------------------------------------------------------------------------

	static void tick(Minecraft mc) {
		if (mc.level == null || mc.player == null) {
			clear();
			return;
		}
		long now = mc.level.getGameTime();
		FLARES.values().removeIf(at -> now - at > FLARE + 1 || now < at);
		FLARE_POWER.keySet().retainAll(FLARES.keySet());
		RandomSource r = mc.level.getRandom();
		for (Iterator<Map.Entry<Integer, Hold>> it = HOLDS.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<Integer, Hold> e = it.next();
			Hold h = e.getValue();
			Player bearer = bearer(e.getKey());
			if (bearer == null || now > h.until || h.until - now > HOLD_LAPSE + 1) {
				it.remove();
				continue;
			}
			// Light streaming out of the ring up into what it's forming.
			Corps before = CorpsTint.enter(h.corps);
			Vec3 from = ringNow(bearer, 1f);
			if (r.nextInt(2) == 0) pour(mc, r, bearer, from, h.target, LabFx.count(1 + h.power), 0.45f);
			CorpsTint.restore(before);
		}
		for (Iterator<Glow> it = GLOWS.iterator(); it.hasNext(); ) {
			Glow g = it.next();
			Player bearer = bearer(g.bearer);
			if (bearer == null || ++g.age > AFTERGLOW) {
				it.remove();
				continue;
			}
			Corps before = CorpsTint.enter(g.corps);
			pour(mc, r, bearer, ringFiring(bearer, 1f), g.target, LabFx.count(3 * g.power * (1f - g.age / (float) AFTERGLOW)), 0.5f);
			CorpsTint.restore(before);
		}
		for (Player player : mc.level.players()) {
			if (player.distanceToSqr(mc.player) > 48 * 48 || !player.isUsingItem() || !isRing(player.getUseItem())) continue;
			RingMode mode = PowerRingItem.getMode(player.getUseItem());
			if (mode != RingMode.DOME && mode != RingMode.SHIELD) continue;
			Corps before = CorpsTint.enter(Corps.of(player.getUseItem()));
			feed(mc, r, player, mode == RingMode.DOME);
			CorpsTint.restore(before);
		}
	}

	/** n motes leaving the ring at from and streaming toward target. */
	private static void pour(Minecraft mc, RandomSource r, Player bearer, Vec3 from, Vec3 target, int n, float size) {
		Vec3 d = target.subtract(from);
		double len = d.length();
		if (len < 0.1) return;
		Vec3 dir = d.scale(1 / len);
		float near = firstPerson(mc, bearer) ? 0.45f : 1f;
		for (int i = 0; i < n; i++) {
			Vec3 v = dir.scale(0.3 + 0.4 * r.nextDouble()).add(LabFx.jitter(r, 0.06));
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, from.add(dir.scale(0.08)), v, size * near);
			if (p != null) p.lasting(4 + r.nextInt(4));
		}
	}

	/**
	 * Holding the Dome or the Shield: light keeps flowing out of the ring into the construct, a
	 * widening spray out to the Dome's shell or a tight stream into the Shield in front.
	 */
	private static void feed(Minecraft mc, RandomSource r, Player player, boolean dome) {
		Vec3 from = ringNow(player, 1f);
		Vec3 look = player.getViewVector(1f);
		float near = firstPerson(mc, player) ? 0.45f : 1f;
		double reach = dome ? 4.5 : 1.6;
		double spread = dome ? 0.9 : 0.35;
		for (int i = 0; i < LabFx.count(dome ? 3 : 2); i++) {
			Vec3 aim = look.add(LabFx.jitter(r, spread)).normalize();
			// Lands on the construct as it fades: friction 0.92 over ~6 ticks covers about 4.6 ticks' worth of the speed.
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, from.add(aim.scale(0.08)), aim.scale(reach / 4.6), 0.5f * near);
			if (p != null) p.lasting(6);
		}
		if (r.nextInt(4) == 0) LabFx.spawn(ModParticles.SPARK, from, Vec3.ZERO, 0.5f * near);
	}

	static void clear() {
		GLOWS.clear();
		FLARES.clear();
		FLARE_POWER.clear();
		HOLDS.clear();
	}
}
