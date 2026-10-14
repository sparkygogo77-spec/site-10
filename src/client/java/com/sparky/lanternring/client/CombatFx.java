package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import com.sparky.lanternring.AbsorbBlasts;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.FlightSlams;
import com.sparky.lanternring.FlyingFlurries;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.PowerLandings;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.CombatFxPayload;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.RenderStateDataKey;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.jspecify.annotations.Nullable;

/**
 * What every client draws for the combat moves (server side: FlightSlams, FlyingFlurries, AbsorbBlasts), in the
 * corps colour of the ring that made them, shader-safe (entityTranslucentEmissive with ShaderGlow light):
 * <ul>
 * <li>craters: the blocks they take turn construct as they light and break into construct pixels as they go (the
 * slam's 7x7 on the ground, the flurry's 3x3 across whatever face it hit), the slam's landing block holding you in
 * construct through the lock, and an impact ring running out over the face (the slam's to 7 blocks in 12 ticks);
 * <li>the flurry's punches (a spark at each) and the launched target tumbling head over heels until it craters
 * (stuck in at that angle) or regains control (rights itself in 6 ticks);
 * <li>the absorb: the caught shot flying into the ring, then held in the viewer's Ring Lab pick (R4b at the ring,
 * turning from the attacker's colour to green and growing to 1.8x as it charges; R4a in a construct cage in front
 * of the ring; R4c swallowed, the ring burning brighter), and the green blast twice the size with 3 trailing bolts.
 * </ul>
 */
public final class CombatFx {
	/** The tumble angle (degrees) a launched mob is drawn at, on its render state. */
	public static final RenderStateDataKey<Float> TUMBLE_KEY = RenderStateDataKey.create(() -> "lanternring:tumble");
	/** The slam's landing block fades back over this many ticks after the lock; the slam's ring runs out over PULSE. */
	private static final int HOLD_FADE = 6, PULSE = 12;
	/** The flurry's impact ring: reach and ticks. */
	private static final float IMPACT_REACH = 2.5f;
	private static final int IMPACT_TICKS = 8;
	/** Pixels per cleared block. */
	private static final int PIXELS = 8;
	/** A tumbling mob turns this fast (radians a tick), stays stuck this long, and rights itself in RIGHT ticks. */
	private static final float TUMBLE_RATE = 0.55f;
	private static final int STUCK = 30, RIGHT = 6;
	/** The held shot's colour once fully charged: construct green (recoloured for the corps). */
	private static final float[] GREEN = {0.35f, 1f, 0.45f};
	/** The construct hammer's shockwave ticks. */
	private static final int HAMMER_WAVE = 16;

	private record Cell(BlockPos pos, int lit, int cleared, boolean taken) {
	}

	private static final class Crater {
		final Corps corps;
		final long start;
		final List<Cell> cells = new ArrayList<>();
		final boolean[] gone;
		/** The block held in construct (the slam's landing block) and until when, or null. */
		@Nullable BlockPos hold;
		int holdTicks;
		/** The impact ring: its middle, the face's normal, reach and ticks. */
		final Vec3 at, normal;
		final float reach;
		final int ringTicks;

		Crater(Corps corps, long start, List<Cell> cells, Vec3 at, Vec3 normal, float reach, int ringTicks) {
			this.corps = corps;
			this.start = start;
			this.cells.addAll(cells);
			this.gone = new boolean[cells.size()];
			this.at = at;
			this.normal = normal;
			this.reach = reach;
			this.ringTicks = ringTicks;
		}

		int end() {
			int last = Math.max(ringTicks, hold != null ? holdTicks + HOLD_FADE : 0);
			for (Cell c : cells) last = Math.max(last, c.cleared());
			return last + 2;
		}
	}

	private static final class Bit {
		final Corps corps;
		Vec3 pos, vel;
		final float size;
		final int life;
		int age;
		final Quaternionf turn = new Quaternionf();
		final Vector3f spin;
		final float u, v;

		Bit(Corps corps, Vec3 pos, Vec3 vel, float size, int life, RandomSource r) {
			this.corps = corps;
			this.pos = pos;
			this.vel = vel;
			this.size = size;
			this.life = life;
			this.spin = new Vector3f(r.nextFloat() - 0.5f, r.nextFloat() - 0.5f, r.nextFloat() - 0.5f).mul(0.8f);
			this.u = r.nextFloat() * 0.85f;
			this.v = r.nextFloat() * 0.85f;
		}
	}

	private static final class Held {
		final Corps corps;
		final int colour;
		final Vec3 from;
		final long caught;
		Vec3 pos;

		Held(Corps corps, int colour, Vec3 from, long caught) {
			this.corps = corps;
			this.colour = colour;
			this.from = from;
			this.pos = from;
			this.caught = caught;
		}
	}

	private static final class Blast {
		final int bearer;
		final Corps corps;
		final float charge;
		final int life;
		Vec3 pos;
		final Vec3 vel;
		int age;

		Blast(int bearer, Corps corps, Vec3 pos, Vec3 vel, float charge) {
			this.bearer = bearer;
			this.corps = corps;
			this.pos = pos;
			this.vel = vel;
			this.charge = charge;
			this.life = (int) Math.ceil(70 / Math.max(0.5, vel.length()));
		}
	}

	private static final class Tumble {
		final long start;
		long stop = -1, right = -1;
		float frozen;

		Tumble(long start) {
			this.start = start;
		}

		/** The tumble angle (radians) at time now. */
		float angle(float now) {
			if (stop < 0) return TUMBLE_RATE * (now - start);
			if (right < 0 || now < right) return frozen;
			return frozen * (1f - SuperJumpPoses.smooth((now - right) / RIGHT));
		}

		boolean done(long now) {
			return right >= 0 && now > right + RIGHT + 2 || now - start > 400;
		}
	}

	private static final List<Crater> CRATERS = new ArrayList<>();
	/** A primed crater's block coming back (PrimedSlams' rebuild): construct fading to its real look over REBUILT_FADE. */
	private record Rebuilt(BlockPos pos, Corps corps, long start) {
	}

	private static final List<Rebuilt> REBUILT = new ArrayList<>();
	private static final float REBUILT_FADE = 10f;
	/** The primed slam's landing block holds you through the lock (0.7 s). */
	private static final int PRIMED_HOLD = 14;

	/** How many craters are drawing right now (for tests). */
	public static int craters() {
		return CRATERS.size();
	}
	private static final List<Bit> BITS = new ArrayList<>();
	private static final Int2ObjectMap<Held> HELD = new Int2ObjectOpenHashMap<>();
	private static final List<Blast> BLASTS = new ArrayList<>();
	private static final Int2ObjectMap<Tumble> TUMBLES = new Int2ObjectOpenHashMap<>();

	private CombatFx() {
	}

	public static void handle(CombatFxPayload fx) {
		Minecraft mc = Minecraft.getInstance();
		ClientLevel level = mc.level;
		if (level == null) return;
		Corps before = CorpsTint.enter(fx.corps());
		try {
			draw(mc, level, fx, RingEmit.bearer(fx.bearer()));
		} finally {
			CorpsTint.restore(before);
		}
	}

	private static void draw(Minecraft mc, ClientLevel level, CombatFxPayload fx, @Nullable Player bearer) {
		long now = level.getGameTime();
		boolean own = mc.player != null && fx.bearer() == mc.player.getId();
		RandomSource r = level.getRandom();
		switch (fx.kind()) {
			case SLAM_DIVE -> {
				if (fx.bearer() >= 0) CombatPoses.slam(fx.bearer(), Math.round(fx.value()));
				if (bearer != null) RingEmit.flash(bearer, 1f);
			}
			case SLAM_LAND -> {
				if (fx.bearer() >= 0) CombatPoses.slamLand(fx.bearer());
				if (bearer != null) RingEmit.flash(bearer, 1.8f);
				BlockPos centre = BlockPos.containing(fx.from().x, PowerLandings.groundY(fx.from().y), fx.from().z);
				List<Cell> cells = new ArrayList<>();
				for (FlightSlams.Cell c : FlightSlams.cells(fx.variant())) {
					if (c.cleared() < 0) continue;
					BlockPos pos = FlightSlams.surface(level, centre.offset(c.dx(), 0, c.dz()));
					if (pos == null) continue;
					cells.add(new Cell(pos, c.lit(), c.cleared(), PowerLandings.takes(level, pos, level.getBlockState(pos))));
				}
				Vec3 top = new Vec3(fx.from().x, centre.getY() + 1.03, fx.from().z);
				Crater crater = new Crater(CorpsTint.current(), now, cells, top, new Vec3(0, 1, 0), (float) FlightSlams.WAVE, PULSE);
				crater.hold = centre;
				crater.holdTicks = Math.round(fx.value());
				CRATERS.add(crater);
				if (!own && mc.player != null && mc.player.position().distanceTo(fx.from()) < 24) RingShake.kick(0.6f, true);
			}
			case PRIMED_DIVE -> {
				if (fx.bearer() >= 0) CombatPoses.primeDive(fx.bearer(), fx.variant());
				if (own && fx.variant() == 1) CombatInput.jumpPrimed();
				if (bearer != null) RingEmit.flash(bearer, 1.2f);
			}
			case PRIMED_LAND -> {
				int reach = fx.variant() & 7;
				int take = (fx.variant() & 8) != 0 ? 1 : 0;
				if (fx.bearer() >= 0) CombatPoses.primedLand(fx.bearer(), take);
				if (bearer != null) RingEmit.flash(bearer, 2f);
				BlockPos centre = BlockPos.containing(fx.to());
				// Every block of it opens at once, the tick after touchdown (the server's PrimedSlams).
				List<Cell> cells = new ArrayList<>();
				for (int dx = -reach; dx <= reach; dx++) {
					for (int dz = -reach; dz <= reach; dz++) {
						if (dx == 0 && dz == 0) continue;
						BlockPos pos = FlightSlams.surface(level, centre.offset(dx, 0, dz));
						if (pos != null) cells.add(new Cell(pos, -1, 1, PowerLandings.takes(level, pos, level.getBlockState(pos))));
					}
				}
				Vec3 top = new Vec3(fx.from().x, centre.getY() + 1.03, fx.from().z);
				Crater crater = new Crater(CorpsTint.current(), now, cells, top, new Vec3(0, 1, 0), (float) (FlightSlams.WAVE + reach - 3), PULSE);
				crater.hold = centre;
				crater.holdTicks = PRIMED_HOLD;
				CRATERS.add(crater);
				if (own) {
					CombatInput.crater(centre, reach, Math.round(fx.value()));
					RingShake.kick(1.6f, true);
				} else if (mc.player != null && mc.player.position().distanceTo(fx.from()) < 32) {
					RingShake.kick(0.8f, true);
				}
			}
			case REBUILT -> {
				REBUILT.add(new Rebuilt(BlockPos.containing(fx.from()), CorpsTint.current(), now));
				if (fx.bearer() >= 0 && !own) CombatPoses.rebuild(fx.bearer());
				for (int i = 0; i < LabFx.count(4); i++) {
					ConstructParticle p = LabFx.spawn(ModParticles.MOTE, fx.from().add(LabFx.jitter(r, 0.5)), LabFx.jitter(r, 0.05), 0.6f);
					if (p != null) p.lasting(6 + r.nextInt(4));
				}
			}
			case FLURRY_HIT -> {
				if (fx.variant() == 0 && fx.bearer() >= 0) CombatPoses.flurry(fx.bearer());
				if (own) CombatInput.punched(fx.variant());
				if (bearer != null) RingEmit.flare(bearer);
				Vec3 way = fx.to().subtract(fx.from());
				LabFx.spawn(ModParticles.SPARK, fx.from(), Vec3.ZERO, 1.2f + 0.4f * fx.variant());
				for (int i = 0; i < LabFx.count(6 + 4 * fx.variant()); i++) {
					ConstructParticle p = LabFx.spawn(ModParticles.MOTE, fx.from(), way.scale(0.15).add(LabFx.jitter(r, 0.2)), 0.5f);
					if (p != null) p.lasting(6 + r.nextInt(4));
				}
			}
			case FLURRY_LAUNCH -> TUMBLES.put(fx.target(), new Tumble(now));
			case FLURRY_IMPACT -> {
				stopTumble(fx.target(), now, false);
				Vec3 n = fx.to().subtract(fx.from());
				n = n.lengthSqr() < 1e-6 ? new Vec3(0, 1, 0) : n.normalize();
				List<Cell> cells = new ArrayList<>();
				if (fx.variant() >= 0) {
					Direction face = Direction.from3DDataValue(fx.variant());
					BlockPos centre = BlockPos.containing(fx.from().subtract(n.scale(0.05)));
					for (int[] c : FlyingFlurries.craterCells(face)) {
						BlockPos pos = centre.offset(c[0], c[1], c[2]);
						cells.add(new Cell(pos, c[3], c[4], PowerLandings.takes(level, pos, level.getBlockState(pos))));
					}
				}
				CRATERS.add(new Crater(CorpsTint.current(), now, cells, fx.from().add(n.scale(0.03)), n, fx.variant() >= 0 ? IMPACT_REACH : 1.5f,
						IMPACT_TICKS));
				LabFx.spawn(ModParticles.SPARK, fx.from(), Vec3.ZERO, 2.2f);
				if (mc.player != null && mc.player.position().distanceTo(fx.from()) < 16) RingShake.kick(0.5f, true);
			}
			case FLURRY_REGAIN -> stopTumble(fx.target(), now, true);
			case ABSORB_CATCH -> {
				HELD.put(fx.bearer(), new Held(CorpsTint.current(), fx.variant(), fx.from(), now));
				if (fx.bearer() >= 0) CombatPoses.absorbCatch(fx.bearer());
				if (own) CombatInput.holding(true);
				if (bearer != null) RingEmit.flash(bearer, 1.2f);
			}
			case ABSORB_RELEASE -> {
				HELD.remove(fx.bearer());
				if (own) CombatInput.holding(false);
				if (fx.bearer() >= 0) CombatPoses.absorbRelease(fx.bearer());
				Vec3 from = bearer != null ? RingEmit.shotOrigin(bearer) : fx.from();
				Vec3 vel = fx.to().subtract(fx.from());
				if (bearer != null) RingEmit.muzzle(bearer, from, from.add(vel.scale(10)), 2f);
				BLASTS.add(new Blast(fx.bearer(), CorpsTint.current(), from, vel, fx.variant() / 100f));
			}
			case ABSORB_HIT -> {
				Blast hit = null;
				for (Blast b : BLASTS) {
					if (b.bearer == fx.bearer() && (hit == null || b.pos.distanceToSqr(fx.from()) < hit.pos.distanceToSqr(fx.from()))) hit = b;
				}
				BLASTS.remove(hit);
				float charge = fx.variant() / 100f;
				Vec3 n = fx.to().subtract(fx.from());
				n = n.lengthSqr() < 1e-6 ? new Vec3(0, 1, 0) : n.normalize();
				CRATERS.add(new Crater(CorpsTint.current(), now, List.of(), fx.from(), n, 2f + charge, 7));
				LabFx.spawn(ModParticles.SPARK, fx.from(), Vec3.ZERO, 3f + 1.5f * charge);
				for (int i = 0; i < LabFx.count(24); i++) {
					ConstructParticle p = LabFx.spawn(i % 3 == 0 ? ModParticles.SHARD : ModParticles.MOTE, fx.from(), LabFx.jitter(r, 0.6), 0.7f);
					if (p != null) p.lasting(8 + r.nextInt(8));
				}
			}
			case HAMMER_FORM -> ConstructHammerFx.form(level, fx, bearer);
			case HAMMER_HIT -> {
				if (bearer != null) ConstructHammerFx.hit(bearer);
				Vec3 n = fx.to().subtract(fx.from());
				n = n.lengthSqr() < 1e-6 ? new Vec3(0, 1, 0) : n.normalize();
				List<Cell> cells = new ArrayList<>();
				if (fx.variant() >= 0) {
					Direction face = Direction.from3DDataValue(fx.variant());
					BlockPos centre = BlockPos.containing(fx.from().subtract(n.scale(0.05)));
					for (int[] c : FlyingFlurries.craterCells(face)) {
						BlockPos pos = centre.offset(c[0], c[1], c[2]);
						cells.add(new Cell(pos, c[3], c[4], PowerLandings.takes(level, pos, level.getBlockState(pos))));
					}
				}
				// Pass 503: the shockwave runs out 0.3 + 0.35 blocks a tick for 16 ticks.
				CRATERS.add(new Crater(CorpsTint.current(), now, cells, fx.from().add(n.scale(0.03)), n, 0.3f + 0.35f * HAMMER_WAVE, HAMMER_WAVE));
				LabFx.spawn(ModParticles.SPARK, fx.from(), Vec3.ZERO, 2.6f);
				if (mc.player != null && mc.player.position().distanceTo(fx.from()) < 16) RingShake.kick(own ? 0.5f : 0.6f, true);
			}
			case ABSORB_END -> {
				HELD.remove(fx.bearer());
				if (own) CombatInput.holding(false);
				if (fx.bearer() >= 0) CombatPoses.absorbEnd(fx.bearer());
			}
		}
	}

	private static void stopTumble(int id, long now, boolean right) {
		Tumble t = TUMBLES.get(id);
		if (t == null || t.stop >= 0) return;
		t.stop = now;
		float a = Mth.wrapDegrees(t.angle(now) * Mth.RAD_TO_DEG) * Mth.DEG_TO_RAD;
		t.frozen = a;
		t.right = right ? now : now + STUCK;
	}

	/** The tumble angle (degrees) to draw this entity at, or 0. */
	public static float tumble(LivingEntity e, float partial) {
		Tumble t = TUMBLES.get(e.getId());
		if (t == null) return 0f;
		return t.angle(e.level().getGameTime() + partial) * Mth.RAD_TO_DEG;
	}

	/** Turns a tumbling mob head over heels about its middle (LivingEntityRendererMixin, after vanilla's turns). */
	public static void rotate(LivingEntityRenderState state, PoseStack poseStack) {
		float angle = state.getDataOrDefault(TUMBLE_KEY, 0f);
		if (angle == 0f) return;
		float mid = state.boundingBoxHeight / 2;
		poseStack.translate(0, mid, 0);
		poseStack.rotateDegrees(Axis.XP, angle);
		poseStack.translate(0, -mid, 0);
	}

	static void tick(Minecraft mc) {
		ClientLevel level = mc.level;
		if (level == null) {
			CRATERS.clear();
			REBUILT.clear();
			BITS.clear();
			HELD.clear();
			BLASTS.clear();
			TUMBLES.clear();
			ConstructHammerFx.clear();
			return;
		}
		if (mc.isPaused()) return;
		long now = level.getGameTime();
		RandomSource r = level.getRandom();
		for (Crater c : CRATERS) {
			int age = (int) (now - c.start);
			for (int i = 0; i < c.cells.size(); i++) {
				Cell cell = c.cells.get(i);
				if (c.gone[i] || !cell.taken() || age < cell.cleared()) continue;
				c.gone[i] = true;
				pixels(c.corps, Vec3.atCenterOf(cell.pos()), c.normal, r);
			}
		}
		CRATERS.removeIf(c -> now - c.start > c.end() || now < c.start - 20);
		REBUILT.removeIf(b -> now - b.start > REBUILT_FADE || now < b.start - 20);
		for (int i = BITS.size() - 1; i >= 0; i--) {
			Bit b = BITS.get(i);
			b.age++;
			b.pos = b.pos.add(b.vel);
			b.vel = new Vec3(b.vel.x * 0.92, b.vel.y - 0.02, b.vel.z * 0.92);
			b.turn.rotateXYZ(b.spin.x, b.spin.y, b.spin.z);
			if (b.age >= b.life) BITS.remove(i);
		}
		TUMBLES.values().removeIf(t -> t.done(now));
		ConstructHammerFx.tick(mc, level);
		held(mc, now, r);
		for (int i = BLASTS.size() - 1; i >= 0; i--) {
			Blast b = BLASTS.get(i);
			if (++b.age > b.life) {
				BLASTS.remove(i);
				continue;
			}
			Corps before = CorpsTint.enter(b.corps);
			try {
				blast(b, r);
			} finally {
				CorpsTint.restore(before);
			}
			b.pos = b.pos.add(b.vel);
		}
	}

	/** count construct pixels bursting out of at, thrown off along normal (the construct hammer breaking up). */
	static void burst(Corps corps, Vec3 at, Vec3 normal, int count) {
		RandomSource r = RandomSource.create();
		for (int i = 0; i < count; i++) {
			Vec3 p = at.add((r.nextDouble() - 0.5) * 0.7, (r.nextDouble() - 0.5) * 0.5, (r.nextDouble() - 0.5) * 0.7);
			Vec3 v = normal.scale(0.12 + r.nextDouble() * 0.12).add((r.nextDouble() - 0.5) * 0.18, 0.05, (r.nextDouble() - 0.5) * 0.18);
			BITS.add(new Bit(corps, p, v, Mth.lerp(r.nextFloat(), 0.1f, 0.18f), 10 + r.nextInt(8), r));
		}
	}

	/** A block breaking into construct pixels thrown off the face. */
	private static void pixels(Corps corps, Vec3 at, Vec3 normal, RandomSource r) {
		for (int i = 0; i < PIXELS; i++) {
			Vec3 p = at.add((r.nextDouble() - 0.5) * 0.8, (r.nextDouble() - 0.5) * 0.8, (r.nextDouble() - 0.5) * 0.8);
			Vec3 v = normal.scale(0.08 + r.nextDouble() * 0.14).add((r.nextDouble() - 0.5) * 0.1, 0.04, (r.nextDouble() - 0.5) * 0.1);
			BITS.add(new Bit(corps, p, v, Mth.lerp(r.nextFloat(), 0.09f, 0.17f), 12 + r.nextInt(10), r));
		}
	}

	/** The held shots: into the ring, then held in the viewer's pick (particles each tick; R4a's cage is drawn in render). */
	private static void held(Minecraft mc, long now, RandomSource r) {
		LabSettings.AbsorbHold pick = LabSettings.get().absorbHold;
		for (Int2ObjectMap.Entry<Held> e : HELD.int2ObjectEntrySet()) {
			Held h = e.getValue();
			Player bearer = RingEmit.bearer(e.getIntKey());
			if (bearer == null) continue;
			int age = (int) (now - h.caught);
			int pull = Math.max(1, RingTuning.ABSORB_PULL.ticks());
			float in = SuperJumpPoses.smooth(age / (float) pull);
			float charge = AbsorbBlasts.charge(age - pull);
			Vec3 ring = RingEmit.ringNow(bearer, 1f);
			Vec3 rest = pick == LabSettings.AbsorbHold.R4A ? ring.add(bearer.getViewVector(1f).scale(0.65)) : ring;
			h.pos = h.from.lerp(rest, in);
			boolean near = bearer == mc.player && mc.options.getCameraType().isFirstPerson();
			float scale = near ? 0.45f : 1f;
			Corps before = CorpsTint.enter(h.corps);
			try {
				if (pick == LabSettings.AbsorbHold.R4C && in >= 1f) {
					// Swallowed: the ring burns brighter the longer it's held.
					float glow = CombatPoses.absorbGlow(bearer.getId(), 2);
					RingEmit.hold(bearer, ring, Mth.clamp(0.4f + glow / 30f + 0.4f * charge, 0f, 1f));
					if (age % 3 == 0) {
						ConstructParticle p = LabFx.spawn(ModParticles.MOTE, ring, LabFx.jitter(r, 0.05), 0.5f * scale);
						if (p != null) p.lasting(6);
					}
					continue;
				}
				// R4b turns from the attacker's colour to green and grows to 1.8x as it charges; R4a stays as caught.
				float green = pick == LabSettings.AbsorbHold.R4B ? charge : 0f;
				float size = (pick == LabSettings.AbsorbHold.R4B ? 1f + 0.8f * charge : 1f) * scale;
				float[] g = CorpsTint.apply(h.corps, GREEN[0], GREEN[1], GREEN[2]);
				float cr = Mth.lerp(green, (h.colour >> 16 & 0xFF) / 255f, g[0]);
				float cg = Mth.lerp(green, (h.colour >> 8 & 0xFF) / 255f, g[1]);
				float cb = Mth.lerp(green, (h.colour & 0xFF) / 255f, g[2]);
				ConstructParticle core = LabFx.spawn(ModParticles.SPARK, h.pos, Vec3.ZERO, 0.9f * size);
				if (core != null) {
					core.lasting(2);
					core.setColor(cr, cg, cb);
				}
				for (int i = 0; i < 2; i++) {
					double a = (age * 0.6 + i * Math.PI);
					Vec3 off = new Vec3(Math.cos(a), Math.sin(a * 0.7), Math.sin(a)).scale(0.12 * size);
					ConstructParticle p = LabFx.spawn(ModParticles.MOTE, h.pos.add(off), off.scale(-0.2), 0.45f * size);
					if (p != null) {
						p.lasting(4);
						p.setColor(cr, cg, cb);
					}
				}
				if (in >= 1f && age % 4 == 0) RingEmit.hold(bearer, h.pos, 0.4f + 0.4f * charge);
			} finally {
				CorpsTint.restore(before);
			}
		}
	}

	/** One tick of the green blast: a core twice the shot's size with 3 bolts trailing round it. */
	private static void blast(Blast b, RandomSource r) {
		float size = 2f * (1f + 0.8f * b.charge);
		ConstructParticle core = LabFx.spawn(ModParticles.SPARK, b.pos, Vec3.ZERO, 1.1f * size);
		if (core != null) core.lasting(2);
		Vec3 dir = b.vel.normalize();
		Vec3 side = dir.cross(new Vec3(0, 1, 0));
		side = side.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : side.normalize();
		Vec3 up = side.cross(dir).normalize();
		for (int i = 0; i < 3; i++) {
			double a = b.age * 0.9 + i * Math.PI * 2 / 3;
			Vec3 off = side.scale(Math.cos(a) * 0.35 * size / 2).add(up.scale(Math.sin(a) * 0.35 * size / 2));
			for (int k = 0; k < 3; k++) {
				Vec3 at = b.pos.add(off).subtract(dir.scale(0.3 + k * b.vel.length() / 3));
				ConstructParticle p = LabFx.spawn(k == 0 ? ModParticles.SPARK : ModParticles.MOTE, at, dir.scale(-0.05), k == 0 ? 0.6f : 0.4f);
				if (p != null) p.lasting(k == 0 ? 3 : 6);
			}
		}
		if (r.nextInt(2) == 0) {
			ConstructParticle p = LabFx.spawn(ModParticles.SHARD, b.pos, LabFx.jitter(r, 0.15), 0.5f);
			if (p != null) p.lasting(5);
		}
	}

	public static void render(LevelRenderContext ctx) {
		if (CRATERS.isEmpty() && REBUILT.isEmpty() && BITS.isEmpty() && HELD.isEmpty() && !ConstructHammerFx.active()) return;
		Minecraft mc = Minecraft.getInstance();
		ClientLevel level = mc.level;
		if (level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		float now = level.getGameTime() + partial;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		boolean cage = LabSettings.get().absorbHold == LabSettings.AbsorbHold.R4A;
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS), (pose, vc) -> {
			for (Crater c : CRATERS) {
				TextureAtlasSprite s = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, c.corps);
				float[] tint = PowerLandingFx.tint(c.corps);
				float age = now - c.start;
				for (int i = 0; i < c.cells.size(); i++) {
					Cell cell = c.cells.get(i);
					if (!cell.taken() || c.gone[i] || age < cell.lit()) continue;
					float lit = Mth.clamp((age - cell.lit()) / 2f, 0f, 1f);
					float flare = Math.max(0f, 1f - (cell.cleared() - age) / 3f);
					PowerLandingFx.cube(pose, vc, cam, Vec3.atCenterOf(cell.pos()), null, 0.502f, 0.502f, 0.502f, s, 0f, 0f, 1f,
							PowerLandingFx.bright(tint, 0.3f * flare), 0.7f * lit + 0.2f * flare, ShaderGlow.light(0.5f + 0.5f * flare));
				}
				if (c.hold != null && age < c.holdTicks + HOLD_FADE) {
					float a = age < c.holdTicks ? 0.85f : 0.85f * (1 - (age - c.holdTicks) / HOLD_FADE);
					PowerLandingFx.cube(pose, vc, cam, Vec3.atCenterOf(c.hold), null, 0.503f, 0.503f, 0.503f, s, 0f, 0f, 1f,
							PowerLandingFx.bright(tint, age < 3 ? 0.4f : 0f), a, ShaderGlow.light(0.7f));
				}
				if (age < c.ringTicks) ring(pose, vc, cam, c, s, tint, age / c.ringTicks);
			}
			for (Rebuilt b : REBUILT) {
				float t = Mth.clamp((now - b.start) / REBUILT_FADE, 0f, 1f);
				TextureAtlasSprite s = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, b.corps);
				PowerLandingFx.cube(pose, vc, cam, Vec3.atCenterOf(b.pos), null, 0.505f, 0.505f, 0.505f, s, 0f, 0f, 1f,
						PowerLandingFx.bright(PowerLandingFx.tint(b.corps), 0.3f * (1 - t)), 0.9f * (1 - t), ShaderGlow.light(0.7f));
			}
			for (Bit b : BITS) {
				float t = Mth.clamp((b.age + partial) / b.life, 0f, 1f);
				float half = b.size / 2 * (1 - t);
				if (half < 0.005f) continue;
				TextureAtlasSprite s = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, b.corps);
				PowerLandingFx.cube(pose, vc, cam, b.pos.add(b.vel.scale(partial)), b.turn, half, half, half, s, b.u, b.v, 0.15f,
						PowerLandingFx.bright(PowerLandingFx.tint(b.corps), 0.25f), 0.9f * (1 - t * t), ShaderGlow.light(0.8f));
			}
			ConstructHammerFx.draw(pose, vc, cam, now);
			if (cage) {
				for (Held h : HELD.values()) {
					TextureAtlasSprite s = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, h.corps);
					cage(pose, vc, cam, h.pos, s, PowerLandingFx.tint(h.corps), now - h.caught);
				}
			}
		});
	}

	/** The impact ring running out over the face: a flat band growing to the crater's reach and fading. */
	private static void ring(PoseStack.Pose pose, VertexConsumer vc, Vec3 cam, Crater c, TextureAtlasSprite s, float[] tint, float t) {
		float radius = 0.5f + (c.reach - 0.5f) * SuperJumpPoses.smooth(t);
		float width = 0.35f;
		float alpha = 0.7f * (1 - t);
		Vec3 n = c.normal;
		Vec3 u = Math.abs(n.y) > 0.9 ? new Vec3(1, 0, 0) : n.cross(new Vec3(0, 1, 0)).normalize();
		Vec3 v = n.cross(u).normalize();
		int count = 40;
		float[] col = PowerLandingFx.bright(tint, 0.3f);
		int light = ShaderGlow.light(0.8f);
		for (int i = 0; i < count; i++) {
			float a0 = i * Mth.TWO_PI / count, a1 = (i + 1) * Mth.TWO_PI / count;
			Vec3[] q = {
					c.at.add(u.scale(Mth.cos(a0) * (radius - width))).add(v.scale(Mth.sin(a0) * (radius - width))),
					c.at.add(u.scale(Mth.cos(a1) * (radius - width))).add(v.scale(Mth.sin(a1) * (radius - width))),
					c.at.add(u.scale(Mth.cos(a1) * radius)).add(v.scale(Mth.sin(a1) * radius)),
					c.at.add(u.scale(Mth.cos(a0) * radius)).add(v.scale(Mth.sin(a0) * radius))};
			float[][] uv = {{s.getU0(), s.getV1()}, {s.getU1(), s.getV1()}, {s.getU1(), s.getV0()}, {s.getU0(), s.getV0()}};
			for (int side = 0; side < 2; side++) {
				float f = side == 0 ? 1 : -1;
				for (int k = 0; k < 4; k++) {
					int idx = side == 0 ? k : 3 - k;
					PowerLandingFx.vertex(pose, vc, cam, (float) q[idx].x, (float) q[idx].y, (float) q[idx].z, uv[idx][0], uv[idx][1], col, alpha, light,
							(float) n.x * f, (float) n.y * f, (float) n.z * f);
				}
			}
		}
	}

	/** R4a: a construct cage round the held shot, its 12 bars forming as it's caught. */
	private static void cage(PoseStack.Pose pose, VertexConsumer vc, Vec3 cam, Vec3 at, TextureAtlasSprite s, float[] tint, float age) {
		float form = Mth.clamp(age / 6f, 0f, 1f);
		if (form <= 0f) return;
		float h = 0.28f, bar = 0.025f;
		float[] col = PowerLandingFx.bright(tint, 0.2f);
		int light = ShaderGlow.light(0.8f);
		for (int axis = 0; axis < 3; axis++) {
			for (int a = -1; a <= 1; a += 2) {
				for (int b = -1; b <= 1; b += 2) {
					float x = axis == 0 ? 0 : a * h, y = axis == 1 ? 0 : axis == 0 ? a * h : b * h, z = axis == 2 ? 0 : b * h;
					float len = h * form;
					PowerLandingFx.cube(pose, vc, cam, at.add(x, y, z), null, axis == 0 ? len : bar, axis == 1 ? len : bar, axis == 2 ? len : bar,
							s, 0f, 0f, 0.3f, col, 0.75f, light);
				}
			}
		}
	}
}
