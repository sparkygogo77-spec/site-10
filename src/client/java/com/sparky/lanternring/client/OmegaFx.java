package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.OmegaBeams;
import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.net.OmegaFxPayload;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.RenderStateDataKey;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Draws the omega beams (server: OmegaBeams). The eyes' start (E1 snap flash, E2 smoulder with red
 * smoke, E3 air brake, E4 crackling arcs); each use as a pair of thin red lasers, about 0.8 px wide
 * and 0.22 blocks apart, with bright heads and fading tails 4.5 blocks long, carrying a red light
 * through the air; burnt blocks as glowing embers of the block's own model that shrink and crumble
 * to ash; burnt creatures tinted ember orange (LivingEntityRendererMixin) with embers rising off
 * them, then ash.
 * <p>
 * Pass 506's lightning zigzag: the server sends the route's head positions (smoothed here with a
 * Catmull-Rom curve) and, at the start, the shot's seed and zigzag style. From the seed each client
 * lays corners along the route at random gaps (Z2 0.22-0.4 blocks, Z1 0.35-0.6), each kicked
 * 0.14-0.32 blocks out in its own direction round the line and turning at its own rate (up to 0.35
 * rad a tick), joined by straight streaks, so the tail is never straight and keeps flickering into
 * new shapes. The kicks fade out at the eyes (first 1.2 blocks) and in the last block before the
 * target, so it leaves clean and strikes dead on; at a block the pair opens out to 1 block apart.
 */
public final class OmegaFx {
	public static final RenderStateDataKey<Float> EMBER_KEY = RenderStateDataKey.create(() -> "lanternring:omega_ember");
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/flight_trail.png");
	/** The laser's red, about (255, 15, 8), and its white-hot head. */
	private static final float RED_R = 1f, RED_G = 0.06f, RED_B = 0.03f;
	/** Half widths: the core is 0.8 px across, the glow round it wider and faint. */
	private static final float CORE = 0.025f, GLOW = 0.1f;
	private static final double TAIL = OmegaBeams.TAIL;
	/** How far apart the pair ends when it opens out on two blocks, and over how much of its last stretch. */
	private static final double OPEN_SEP = 1.0, OPEN_OVER = 1.5;
	private static final int EMBER_RGB = 0xFF8A3A;
	private static final DustParticleOptions ASH = new DustParticleOptions(0x3A3632, 1.1f);
	private static final DustParticleOptions ASH_PALE = new DustParticleOptions(0x8A8580, 0.8f);
	private static final DustParticleOptions RED_SMOKE = new DustParticleOptions(0xC01008, 1.3f);

	private static final class Eyes {
		final int bearer;
		final OmegaBeams.Start start;
		final int windup;
		int age;

		Eyes(int bearer, OmegaBeams.Start start, int windup) {
			this.bearer = bearer;
			this.start = start;
			this.windup = windup;
		}
	}

	private static final class Trail {
		final int bearer;
		/** The head's positions, newest first, back to where it left the eyes. */
		final List<Vec3> points = new ArrayList<>();
		final Vec3 start;
		Vec3 prev, head;
		/** How far the head has come along its route, last tick and now. */
		double runPrev, run;
		/** How far it still has to go to its target, last tick and now (negative: unknown). */
		float remPrev = -1, rem = -1;
		OmegaBeams.Zig zig = OmegaBeams.Zig.Z2;
		boolean opens;
		int age;
		int endAge = -1;
		@Nullable BlockPos light;
		/** The zigzag's corners: where each sits along the route, its kick's first angle, turning rate and size. */
		final java.util.Random rng;
		double[] cornerAt = new double[64];
		float[] angle = new float[64], rate = new float[64], amp = new float[64];
		int corners;

		Trail(int bearer, Vec3 at, int seed) {
			this.bearer = bearer;
			this.start = at;
			this.prev = at;
			this.head = at;
			this.rng = new java.util.Random(seed);
			points.add(at);
		}

		/** Lays corners out to at least s blocks along the route. */
		void cornersTo(double s) {
			while (corners < 2 || cornerAt[corners - 1] < s) {
				if (corners == cornerAt.length) {
					int n = corners * 2;
					cornerAt = java.util.Arrays.copyOf(cornerAt, n);
					angle = java.util.Arrays.copyOf(angle, n);
					rate = java.util.Arrays.copyOf(rate, n);
					amp = java.util.Arrays.copyOf(amp, n);
				}
				cornerAt[corners] = corners == 0 ? 0 : cornerAt[corners - 1] + zig.gapMin + rng.nextDouble() * (zig.gapMax - zig.gapMin);
				angle[corners] = rng.nextFloat() * Mth.TWO_PI;
				rate[corners] = (rng.nextFloat() * 2f - 1f) * 0.35f;
				amp[corners] = 0.14f + rng.nextFloat() * 0.18f;
				corners++;
			}
		}

		/** The zigzag's offset at s blocks along the route at the given time (ticks): across and up from the line. */
		double[] kick(double s, float time) {
			cornersTo(s + 1);
			int i = java.util.Arrays.binarySearch(cornerAt, 0, corners, s);
			if (i < 0) i = -i - 2;
			i = Mth.clamp(i, 0, corners - 2);
			double u = Mth.clamp((s - cornerAt[i]) / (cornerAt[i + 1] - cornerAt[i]), 0, 1);
			float a0 = angle[i] + rate[i] * time, a1 = angle[i + 1] + rate[i + 1] * time;
			return new double[] {
					Mth.lerp(u, amp[i] * Mth.cos(a0), amp[i + 1] * Mth.cos(a1)),
					Mth.lerp(u, amp[i] * Mth.sin(a0), amp[i + 1] * Mth.sin(a1))};
		}

		void moved(Vec3 to, float remaining) {
			prev = head;
			runPrev = run;
			run += to.distanceTo(head);
			head = to;
			remPrev = rem;
			rem = remaining;
			points.add(0, to);
			trim(this);
		}
	}

	private static final class Ember {
		final BlockState state;
		final BlockPos pos;
		final int ticks;
		int age;

		Ember(BlockState state, BlockPos pos, int ticks) {
			this.state = state;
			this.pos = pos;
			this.ticks = ticks;
		}
	}

	private record Burn(long start, int ticks) {
	}

	private static final Int2ObjectMap<Eyes> EYES = new Int2ObjectOpenHashMap<>();
	private static final Int2ObjectMap<Trail> TRAILS = new Int2ObjectOpenHashMap<>();
	private static final List<Ember> EMBERS = new ArrayList<>();
	private static final Int2ObjectMap<Burn> BURNS = new Int2ObjectOpenHashMap<>();
	/** The first-person red flash over the screen, last tick and now. */
	private static float flashOld, flash;
	private static @Nullable ClientLevel seen;

	private OmegaFx() {
	}

	public static void register() {
		ClientPlayNetworking.registerGlobalReceiver(OmegaFxPayload.TYPE, (payload, context) -> handle(payload));
		LevelRenderEvents.COLLECT_SUBMITS.register(OmegaFx::render);
		HudElementRegistry.addFirst(LanternRing.id("omega_flash"), OmegaFx::extract);
	}

	/** How far into its embers a burnt creature is (0 none, up to 1 just before it crumbles). */
	public static float ember(LivingEntity entity) {
		Burn b = BURNS.get(entity.getId());
		if (b == null || entity.level() == null) return 0f;
		float t = (entity.level().getGameTime() - b.start) / (float) Math.max(1, b.ticks);
		return Mth.clamp(0.55f + t * 0.45f, 0f, 1f);
	}

	/** {@code argb} turned toward ember orange by t, and charred dark near the end. */
	public static int emberTint(int argb, float t) {
		float dark = 1f - 0.55f * Mth.clamp((t - 0.8f) / 0.2f, 0f, 1f);
		int r = Math.round((255 + ((EMBER_RGB >> 16 & 0xFF) - 255) * t) * dark);
		int g = Math.round((255 + ((EMBER_RGB >> 8 & 0xFF) - 255) * t) * dark);
		int b = Math.round((255 + ((EMBER_RGB & 0xFF) - 255) * t) * dark);
		return argb & 0xFF000000
				| ((argb >> 16 & 0xFF) * r / 255) << 16
				| ((argb >> 8 & 0xFF) * g / 255) << 8
				| (argb & 0xFF) * b / 255;
	}

	static void handle(OmegaFxPayload fx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		switch (fx.kind()) {
			case OmegaFxPayload.EYES -> {
				OmegaBeams.Start start = OmegaBeams.Start.values()[Mth.clamp(fx.other(), 0, OmegaBeams.Start.values().length - 1)];
				EYES.put(fx.id(), new Eyes(fx.id(), start, Math.max(1, Math.round(fx.a()))));
				if (mc.player != null && fx.id() == mc.player.getId()) {
					flash = start == OmegaBeams.Start.SMOULDER ? 0.05f : 0.45f;
				}
			}
			case OmegaFxPayload.START -> {
				Trail t = new Trail(fx.other(), fx.pos(), Math.round(fx.a()));
				int style = Math.round(fx.b());
				t.zig = OmegaBeams.Zig.of(style % 10);
				t.opens = style >= 10;
				TRAILS.put(fx.id(), t);
			}
			case OmegaFxPayload.HEAD -> {
				Trail t = TRAILS.get(fx.id());
				if (t == null) {
					// Its start went by unseen (out of range then): any seed will do.
					t = new Trail(fx.other(), fx.pos(), fx.id());
					TRAILS.put(fx.id(), t);
				}
				t.moved(fx.pos(), fx.a());
			}
			case OmegaFxPayload.END -> {
				Trail t = TRAILS.get(fx.id());
				if (t != null) {
					t.moved(fx.pos(), fx.other() != 0 ? 0f : -1f);
					t.endAge = 0;
				}
				hit(mc, fx.pos(), fx.other());
			}
			case OmegaFxPayload.BURN_BLOCK -> {
				BlockState state = Block.stateById(fx.id());
				BlockPos pos = BlockPos.containing(fx.pos().add(0.5, 0.5, 0.5));
				if (fx.other() == 0 && !state.isAir()) EMBERS.add(new Ember(state, pos, Math.max(1, Math.round(fx.a()))));
				else scorch(mc, Vec3.atCenterOf(pos));
			}
			case OmegaFxPayload.BURN_MOB -> BURNS.put(fx.id(), new Burn(mc.level.getGameTime(), Math.max(1, Math.round(fx.a()))));
			case OmegaFxPayload.ASH -> {
				BURNS.remove(fx.id());
				ash(mc, fx.pos(), fx.a(), fx.b());
			}
			default -> {
			}
		}
	}

	/** Keeps only the last TAIL blocks of the path behind the head (and a little more for the curve through them). */
	private static void trim(Trail t) {
		double run = 0;
		for (int i = 1; i < t.points.size(); i++) {
			run += t.points.get(i).distanceTo(t.points.get(i - 1));
			if (run > TAIL + 3) {
				t.points.subList(i + 1, t.points.size()).clear();
				return;
			}
		}
	}

	// ---- every tick ---------------------------------------------------------------------------

	static void tick(Minecraft mc) {
		flashOld = flash;
		flash = Math.max(0f, flash * 0.75f - 0.01f);
		if (mc.level != seen) {
			EYES.clear();
			TRAILS.clear();
			EMBERS.clear();
			BURNS.clear();
			seen = mc.level;
		}
		if (mc.level == null || mc.isPaused()) return;
		RandomSource r = mc.level.getRandom();
		Corps before = CorpsTint.enter(Corps.RED);
		try {
			for (Iterator<Eyes> it = EYES.values().iterator(); it.hasNext(); ) {
				Eyes e = it.next();
				if (!eyes(mc, e, r)) it.remove();
				e.age++;
			}
			for (Iterator<Int2ObjectMap.Entry<Trail>> it = TRAILS.int2ObjectEntrySet().iterator(); it.hasNext(); ) {
				Trail t = it.next().getValue();
				t.age++;
				if (t.endAge >= 0 && t.endAge++ > 4) {
					light(mc, t, null);
					it.remove();
					continue;
				}
				light(mc, t, t.endAge < 0 ? BlockPos.containing(t.head) : null);
				if (t.endAge < 0) {
					LabFx.spawn(ModParticles.SPARK, t.head, Vec3.ZERO, 0.7f);
					if (r.nextInt(3) == 0 && t.points.size() > 2) {
						Vec3 at = t.points.get(1 + r.nextInt(t.points.size() - 1));
						LabFx.spawn(ModParticles.MOTE, at.add(LabFx.jitter(r, 0.15)), LabFx.jitter(r, 0.01), 0.45f);
					}
				}
			}
		} finally {
			CorpsTint.restore(before);
		}
		before = CorpsTint.enter(Corps.ORANGE);
		try {
			for (Iterator<Ember> it = EMBERS.iterator(); it.hasNext(); ) {
				Ember e = it.next();
				Vec3 c = Vec3.atCenterOf(e.pos);
				if (r.nextFloat() < 0.8f) {
					LabFx.spawn(ModParticles.MOTE, c.add(LabFx.jitter(r, 1.0)), new Vec3(0, 0.02 + r.nextDouble() * 0.03, 0), 0.5f);
				}
				if (r.nextInt(6) == 0) mc.level.addParticle(ParticleTypes.LAVA, c.x, c.y + 0.3, c.z, 0, 0, 0);
				if (r.nextInt(3) == 0) mc.level.addParticle(ParticleTypes.SMOKE, c.x + (r.nextDouble() - 0.5) * 0.8, c.y + 0.5, c.z + (r.nextDouble() - 0.5) * 0.8, 0, 0.04, 0);
				if (++e.age >= e.ticks) {
					it.remove();
					ash(mc, Vec3.atBottomCenterOf(e.pos), 1f, 1f);
				}
			}
			for (Int2ObjectMap.Entry<Burn> b : BURNS.int2ObjectEntrySet()) {
				Entity mob = mc.level.getEntity(b.getIntKey());
				if (mob == null) continue;
				for (int i = 0; i < 2; i++) {
					Vec3 at = mob.position().add((r.nextDouble() - 0.5) * mob.getBbWidth(), r.nextDouble() * mob.getBbHeight(), (r.nextDouble() - 0.5) * mob.getBbWidth());
					LabFx.spawn(r.nextInt(4) == 0 ? ModParticles.SPARK : ModParticles.MOTE, at, new Vec3(0, 0.03 + r.nextDouble() * 0.03, 0), 0.6f);
				}
				if (r.nextInt(3) == 0) {
					mc.level.addParticle(ParticleTypes.SMALL_FLAME, mob.getX() + (r.nextDouble() - 0.5) * mob.getBbWidth(),
							mob.getY() + r.nextDouble() * mob.getBbHeight(), mob.getZ() + (r.nextDouble() - 0.5) * mob.getBbWidth(), 0, 0.02, 0);
				}
			}
			// A creature that took a burn but isn't crumbling (a player, a boss) glows only for that long.
			long now = mc.level.getGameTime();
			BURNS.int2ObjectEntrySet().removeIf(b -> now - b.getValue().start > b.getValue().ticks + 40);
		} finally {
			CorpsTint.restore(before);
		}
	}

	/** The start at the bearer's eyes; then, while their beams fly, a steady glow. False once it's over. */
	private static boolean eyes(Minecraft mc, Eyes e, RandomSource r) {
		if (!(mc.level.getEntity(e.bearer) instanceof LivingEntity bearer)) return false;
		boolean mine = bearer == mc.player;
		boolean firing = e.age >= e.windup;
		if (firing && !beamsOf(e.bearer) && e.age > e.windup + 2) return false;
		Vec3 look = bearer.getViewVector(1f);
		Vec3 right = look.cross(new Vec3(0, 1, 0));
		right = right.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : right.normalize();
		// In first person the eyes are the camera, so their light sits a little further out, low in the view.
		Vec3 face = bearer.getEyePosition().add(look.scale(mine && mc.options.getCameraType().isFirstPerson() ? 0.7 : 0.26))
				.add(mine && mc.options.getCameraType().isFirstPerson() ? new Vec3(0, -0.18, 0) : Vec3.ZERO);
		Vec3[] eye = {face.add(right.scale(-0.12)), face.add(right.scale(0.12))};
		float grow = Mth.clamp(e.age / (float) e.windup, 0f, 1f);
		if (firing) {
			for (Vec3 p : eye) LabFx.spawn(ModParticles.MOTE, p, Vec3.ZERO, 0.5f);
			if (mine) flash = Math.max(flash, 0.06f);
			return true;
		}
		switch (e.start) {
			case SNAP, AIR_BRAKE -> {
				if (e.age == 0) {
					for (Vec3 p : eye) {
						LabFx.spawn(ModParticles.SPARK, p, Vec3.ZERO, 1.8f);
						for (int i = 0; i < 4; i++) LabFx.spawn(ModParticles.MOTE, p, LabFx.jitter(r, 0.12), 0.6f);
					}
				}
				for (Vec3 p : eye) LabFx.spawn(ModParticles.MOTE, p, Vec3.ZERO, 0.7f);
				if (e.start == OmegaBeams.Start.AIR_BRAKE && !bearer.onGround()) {
					// The brake: light shed behind the body as it slows.
					Vec3 back = bearer.position().add(0, 1, 0).subtract(bearer.getDeltaMovement().scale(3));
					LabFx.spawn(ModParticles.MOTE, back.add(LabFx.jitter(r, 0.6)), bearer.getDeltaMovement().scale(-0.3), 0.6f);
				}
			}
			case SMOULDER -> {
				for (Vec3 p : eye) {
					LabFx.spawn(ModParticles.MOTE, p, Vec3.ZERO, 0.25f + 0.6f * grow);
					if (r.nextFloat() < 0.4f + 0.5f * grow) {
						Vec3 curl = new Vec3((r.nextDouble() - 0.5) * 0.03, 0.03 + 0.03 * grow, (r.nextDouble() - 0.5) * 0.03);
						mc.level.addParticle(RED_SMOKE, p.x, p.y + 0.05, p.z, curl.x, curl.y, curl.z);
						if (r.nextInt(3) == 0) mc.level.addParticle(ParticleTypes.SMOKE, p.x, p.y + 0.08, p.z, curl.x, curl.y * 0.6, curl.z);
					}
				}
				if (mine) flash = Math.max(flash, 0.05f + 0.14f * grow);
				if (e.age == e.windup - 1) for (Vec3 p : eye) LabFx.spawn(ModParticles.SPARK, p, Vec3.ZERO, 1.6f);
			}
			case CRACKLE -> {
				for (Vec3 p : eye) {
					LabFx.spawn(ModParticles.MOTE, p, Vec3.ZERO, 0.4f + 0.3f * grow);
					// A little lightning arc: a jagged line between two points round the eye.
					if (r.nextFloat() < 0.7f) {
						Vec3 a = p.add(LabFx.jitter(r, 0.35)), c = p.add(LabFx.jitter(r, 0.35));
						for (int i = 0; i <= 4; i++) {
							Vec3 q = a.lerp(c, i / 4.0).add(i == 0 || i == 4 ? Vec3.ZERO : LabFx.jitter(r, 0.08));
							LabFx.spawn(ModParticles.SPARK, q, Vec3.ZERO, 0.35f);
						}
					}
				}
				if (mine && r.nextInt(3) == 0) flash = Math.max(flash, 0.12f);
			}
		}
		return true;
	}

	private static boolean beamsOf(int bearer) {
		for (Trail t : TRAILS.values()) if (t.bearer == bearer && t.endAge < 0) return true;
		return false;
	}

	/** Moves the red light that travels with a beam's head: a light block only this client sees, in open air. */
	private static void light(Minecraft mc, Trail t, @Nullable BlockPos want) {
		if (want != null && want.equals(t.light)) return;
		ClientLevel level = mc.level;
		if (t.light != null) {
			BlockState there = level.getBlockState(t.light);
			if (there.is(ModRegistry.BLAST_GLOW) && there.getValue(Corps.PROPERTY) == Corps.RED) level.setBlock(t.light, Blocks.AIR.defaultBlockState(), 3);
			t.light = null;
		}
		BlockState open = want == null ? null : level.getBlockState(want);
		if (open != null && (open.is(Blocks.AIR) || open.is(Blocks.CAVE_AIR))) {
			level.setBlock(want, ModRegistry.BLAST_GLOW.defaultBlockState().setValue(Corps.PROPERTY, Corps.RED).setValue(BlastGlowBlock.LEVEL, 11), 3);
			t.light = want;
		}
	}

	private static void hit(Minecraft mc, Vec3 at, int how) {
		RandomSource r = mc.level.getRandom();
		Corps before = CorpsTint.enter(Corps.RED);
		try {
			LabFx.spawn(ModParticles.SPARK, at, Vec3.ZERO, how == 0 ? 0.8f : 1.8f);
			if (how != 0) for (int i = 0; i < 8; i++) LabFx.spawn(ModParticles.SPARK, at, LabFx.jitter(r, 0.25), 0.5f);
		} finally {
			CorpsTint.restore(before);
		}
	}

	/** Bedrock and the like: just a scorch. */
	private static void scorch(Minecraft mc, Vec3 at) {
		RandomSource r = mc.level.getRandom();
		for (int i = 0; i < 6; i++) mc.level.addParticle(ParticleTypes.SMOKE, at.x, at.y + 0.5, at.z, (r.nextDouble() - 0.5) * 0.05, 0.05, (r.nextDouble() - 0.5) * 0.05);
	}

	/** Something w wide and h high crumbles to ash that drifts up. */
	private static void ash(Minecraft mc, Vec3 feet, float w, float h) {
		RandomSource r = mc.level.getRandom();
		int n = Mth.clamp(Math.round(24 * w * h), 12, 60);
		for (int i = 0; i < n; i++) {
			double x = feet.x + (r.nextDouble() - 0.5) * w, y = feet.y + r.nextDouble() * h, z = feet.z + (r.nextDouble() - 0.5) * w;
			mc.level.addParticle(r.nextInt(3) == 0 ? ASH_PALE : ASH, x, y, z, (r.nextDouble() - 0.5) * 0.04, 0.04 + r.nextDouble() * 0.05, (r.nextDouble() - 0.5) * 0.04);
			if (i % 3 == 0) mc.level.addParticle(ParticleTypes.SMOKE, x, y, z, 0, 0.05, 0);
			if (i % 5 == 0) mc.level.addParticle(ParticleTypes.WHITE_ASH, x, y, z, 0, 0.02, 0);
		}
		Corps before = CorpsTint.enter(Corps.ORANGE);
		try {
			for (int i = 0; i < n / 4; i++) {
				LabFx.spawn(ModParticles.MOTE, feet.add((r.nextDouble() - 0.5) * w, r.nextDouble() * h, (r.nextDouble() - 0.5) * w), new Vec3(0, 0.05, 0), 0.4f);
			}
		} finally {
			CorpsTint.restore(before);
		}
	}

	// ---- every frame --------------------------------------------------------------------------

	static void render(LevelRenderContext context) {
		if (TRAILS.isEmpty() && EMBERS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		if (!TRAILS.isEmpty()) {
			RenderType type = RenderTypes.entityTranslucentEmissive(TEXTURE);
			for (Trail t : TRAILS.values()) {
				float gone = t.endAge < 0 ? 0f : Mth.clamp((t.endAge + partial) / 5f, 0f, 1f);
				List<Vec3> centre = new ArrayList<>();
				List<Double> back = new ArrayList<>();
				if (!centreLine(t, partial, TAIL * (1 - gone), centre, back)) continue;
				boolean live = t.endAge < 0;
				double sHead = live ? Mth.lerp(partial, t.runPrev, t.run) : t.run;
				double remHead = live && t.remPrev >= 0 && t.rem >= 0 ? Mth.lerp(partial, t.remPrev, t.rem) : t.rem;
				float time = t.age + partial;
				// The start sticks to the eyes while the tail is still in them.
				Vec3 drift = Vec3.ZERO;
				if (mc.level.getEntity(t.bearer) instanceof LivingEntity bearer) {
					drift = bearer.getEyePosition(partial).add(bearer.getViewVector(partial).scale(0.3)).subtract(t.start);
					if (drift.lengthSqr() > 4) drift = Vec3.ZERO;
				}
				int n = centre.size();
				List<Vec3> left = new ArrayList<>(n), right = new ArrayList<>(n);
				List<Float> fade = new ArrayList<>(n);
				double tail = Math.max(0.01, TAIL * (1 - gone));
				for (int i = 0; i < n; i++) {
					Vec3 c = centre.get(i);
					Vec3 along = centre.get(Math.max(0, i - 1)).subtract(centre.get(Math.min(n - 1, i + 1)));
					along = along.lengthSqr() < 1e-10 ? new Vec3(0, 0, 1) : along.normalize();
					Vec3 side = along.cross(new Vec3(0, 1, 0));
					side = side.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : side.normalize();
					Vec3 up = side.cross(along);
					double b = back.get(i);
					double s = Math.max(0, sHead - b);
					double toTarget = remHead >= 0 ? remHead + b : Double.MAX_VALUE;
					// No kick at the eyes or right at the target: it leaves clean and strikes dead on.
					double w = Math.max(0, Math.min(1, Math.min(s / 1.2, toTarget / 1.0)));
					double[] k = t.kick(s, time);
					Vec3 p = c.add(side.scale(w * k[0])).add(up.scale(w * k[1])).add(drift.scale(Math.max(0, 1 - s / 2)));
					double sep = OmegaBeams.PAIR_SEPARATION;
					if (t.opens && toTarget < OPEN_OVER) sep += (OPEN_SEP - sep) * smooth(1 - toTarget / OPEN_OVER);
					left.add(p.subtract(side.scale(sep / 2)));
					right.add(p.add(side.scale(sep / 2)));
					fade.add((float) Math.max(0, 1 - b / tail));
				}
				float fadeAll = 1f - gone;
				context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type, (pose, buffer) -> {
					for (List<Vec3> pos : List.of(left, right)) {
						ribbon(pose, buffer, pos, fade, camera, GLOW, RED_R, RED_G, RED_B, 0.4f * fadeAll);
						ribbon(pose, buffer, pos, fade, camera, CORE, RED_R, RED_G, RED_B, fadeAll);
						// The white-hot head: the first sliver of the core, paler.
						List<Vec3> tip = new ArrayList<>(pos.subList(0, 2));
						Vec3 dir = tip.get(1).subtract(tip.get(0));
						if (dir.length() > 0.25) tip.set(1, tip.get(0).add(dir.normalize().scale(0.25)));
						ribbon(pose, buffer, tip, List.of(1f, 0.6f), camera, CORE * 1.6f, 1f, 0.75f, 0.65f, fadeAll);
					}
				});
			}
		}
		if (!EMBERS.isEmpty()) {
			IrisIds.cleared(() -> context.submitNodeCollector().submitCustomGeometry(context.poseStack(),
					RenderTypes.entityCutout(TextureAtlas.LOCATION_BLOCKS), (pose, buffer) -> {
						for (Ember e : EMBERS) ember(pose, buffer, e, partial, camera);
					}));
		}
	}

	/**
	 * The route's middle line from the head back {@code tail} blocks: a Catmull-Rom curve through the
	 * head's positions about 0.1 blocks apart, with how far back along it each point is. False if
	 * there is nothing to draw yet.
	 */
	private static boolean centreLine(Trail t, float partial, double tail, List<Vec3> out, List<Double> back) {
		List<Vec3> raw = new ArrayList<>();
		raw.add(t.endAge < 0 ? t.prev.lerp(t.head, partial) : t.head);
		for (int i = 1; i < t.points.size(); i++) {
			if (t.points.get(i).distanceToSqr(raw.get(raw.size() - 1)) > 1e-6) raw.add(t.points.get(i));
		}
		if (raw.size() < 2 || tail <= 0.01) return false;
		out.add(raw.get(0));
		back.add(0.0);
		double run = 0;
		Vec3 last = raw.get(0);
		for (int i = 0; i + 1 < raw.size(); i++) {
			Vec3 p0 = raw.get(Math.max(0, i - 1)), p1 = raw.get(i), p2 = raw.get(i + 1), p3 = raw.get(Math.min(raw.size() - 1, i + 2));
			int steps = Math.max(1, (int) Math.ceil(p1.distanceTo(p2) / 0.1));
			for (int k = 1; k <= steps; k++) {
				double u = k / (double) steps, u2 = u * u, u3 = u2 * u;
				Vec3 q = p0.scale(-0.5 * u3 + u2 - 0.5 * u)
						.add(p1.scale(1.5 * u3 - 2.5 * u2 + 1))
						.add(p2.scale(-1.5 * u3 + 2 * u2 + 0.5 * u))
						.add(p3.scale(0.5 * u3 - 0.5 * u2));
				double d = q.distanceTo(last);
				if (d < 1e-5) continue;
				if (run + d >= tail) {
					out.add(last.add(q.subtract(last).scale((tail - run) / d)));
					back.add(tail);
					return out.size() >= 2;
				}
				run += d;
				out.add(q);
				back.add(run);
				last = q;
			}
		}
		return out.size() >= 2;
	}

	private static double smooth(double x) {
		x = Mth.clamp(x, 0, 1);
		return x * x * (3 - 2 * x);
	}

	/** The burnt block's own model, glowing orange and shrinking toward its middle as it crumbles. */
	private static void ember(PoseStack.Pose pose, VertexConsumer buffer, Ember e, float partial, Vec3 camera) {
		List<GhostMimicRenderer.Quad> quads = GhostMimicRenderer.quads(e.state);
		if (quads.isEmpty()) return;
		float t = Mth.clamp((e.age + partial) / e.ticks, 0f, 1f);
		float scale = 1f - 0.4f * t * t;
		float flicker = 0.9f + 0.1f * Mth.sin((e.age + partial) * 1.7f + e.pos.hashCode());
		// Bright orange cooling to dull red.
		int r = Math.round(255 * flicker), g = Math.round(Mth.lerp(t, 185, 40) * flicker), b = Math.round(Mth.lerp(t, 85, 10) * flicker);
		int argb = 0xFF000000 | r << 16 | g << 8 | b;
		int light = ShaderGlow.light(1f - 0.4f * t);
		float ox = (float) (e.pos.getX() - camera.x), oy = (float) (e.pos.getY() - camera.y), oz = (float) (e.pos.getZ() - camera.z);
		for (GhostMimicRenderer.Quad q : quads) {
			Direction n = q.face() == null ? Direction.UP : q.face();
			for (int i = 0; i < 4; i++) {
				float x = 0.5f + (q.xyz()[i * 3] - 0.5f) * scale, y = (q.xyz()[i * 3 + 1]) * scale, z = 0.5f + (q.xyz()[i * 3 + 2] - 0.5f) * scale;
				buffer.addVertex(pose, ox + x, oy + y, oz + z).setColor(argb).setUv(q.uv()[i * 2], q.uv()[i * 2 + 1])
						.setOverlay(OverlayTexture.NO_OVERLAY).setLight(light).setNormal(pose, n.getStepX(), n.getStepY(), n.getStepZ());
			}
		}
	}

	/** A camera-facing strip through the points, fading toward its tail (as FlightTrail draws its streak). */
	private static void ribbon(PoseStack.Pose pose, VertexConsumer buffer, List<Vec3> pos, List<Float> fade, Vec3 camera,
			float halfWidth, float r, float g, float b, float alpha) {
		int n = pos.size();
		Vec3[] side = new Vec3[n];
		for (int i = 0; i < n; i++) {
			Vec3 along = pos.get(Math.min(i + 1, n - 1)).subtract(pos.get(Math.max(i - 1, 0)));
			Vec3 s = along.cross(camera.subtract(pos.get(i)));
			side[i] = s.lengthSqr() < 1e-10 ? Vec3.ZERO : s.normalize().scale(halfWidth);
		}
		for (int i = 0; i + 1 < n; i++) {
			float a0 = alpha * fade.get(i) * near(pos.get(i), camera), a1 = alpha * fade.get(i + 1) * near(pos.get(i + 1), camera);
			if (a0 < 0.02f && a1 < 0.02f) continue;
			Vec3 p0 = pos.get(i), p1 = pos.get(i + 1);
			vertex(pose, buffer, p0.subtract(side[i]), camera, 0, 1, r, g, b, a0);
			vertex(pose, buffer, p0.add(side[i]), camera, 0, 0, r, g, b, a0);
			vertex(pose, buffer, p1.add(side[i + 1]), camera, 1, 0, r, g, b, a1);
			vertex(pose, buffer, p1.subtract(side[i + 1]), camera, 1, 1, r, g, b, a1);
		}
	}

	/** Fades the laser right at the camera, so your own doesn't fill the screen as it leaves your eyes. */
	private static float near(Vec3 p, Vec3 camera) {
		return Mth.clamp((float) (p.distanceTo(camera) - 0.6) / 1.2f, 0f, 1f);
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer buffer, Vec3 p, Vec3 camera, float u, float v,
			float r, float g, float b, float a) {
		buffer.addVertex(pose, (float) (p.x - camera.x), (float) (p.y - camera.y), (float) (p.z - camera.z))
				.setColor(r, g, b, a)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(ShaderGlow.light())
				.setNormal(pose, 0, 1, 0);
	}

	/** First person: the eyes' red flash over the screen. */
	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null || !mc.options.getCameraType().isFirstPerson()) return;
		float f = Mth.lerp(delta.getGameTimeDeltaPartialTick(false), flashOld, flash);
		if (f <= 0.004f) return;
		int alpha = Math.round(255 * Mth.clamp(f, 0f, 0.6f));
		graphics.fill(0, 0, graphics.guiWidth(), graphics.guiHeight(), alpha << 24 | 0xFF1A0C);
	}
}
