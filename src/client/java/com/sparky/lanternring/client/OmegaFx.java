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
 * smoke, E3 air brake, E4 crackling arcs); then the pair's line as two thin dark red lasers 0.26
 * blocks apart, built out of the eyes from the corners and head the server sends: straight sides,
 * sharp corners, joined to the eyes until it hits (a barrage's lets go at OmegaBeams.LET_GO blocks
 * long), then burning away from the eye end at 2.5x the head's speed.
 * <p>
 * Final look (J's pass 516): a core of (191, 26, 13), 0.02 blocks, full-bright, in a glow of (140, 3,
 * 0), 0.07 blocks, fading to its edges, never white; hot spots flicker along it (x0.55-1.8 from noise
 * about half a block across, running 0.4 blocks a tick); 2 embers a tick drift up off it, and a red
 * light rides the head. Each strike flashes a ring 0.3 to 1.8 blocks across over 7 ticks. Under water
 * (W2) the line boils: 9 bubbles a tick along it, fizzing on for 8 ticks after it is gone. Burnt
 * blocks are glowing embers of the block's own model that shrink and crumble to ash; burnt creatures
 * are tinted ember orange (LivingEntityRendererMixin) with embers rising off them, then ash.
 */
public final class OmegaFx {
	public static final RenderStateDataKey<Float> EMBER_KEY = RenderStateDataKey.create(() -> "lanternring:omega_ember");
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/flight_trail.png");
	/** The core's and the glow's colours (pass 516). */
	private static final float CORE_R = 191 / 255f, CORE_G = 26 / 255f, CORE_B = 13 / 255f;
	private static final float GLOW_R = 140 / 255f, GLOW_G = 3 / 255f, GLOW_B = 0f;
	/** Half widths of the core and its glow. */
	private static final float CORE = 0.02f, GLOW = 0.07f;
	/** How finely the line is cut for its hot spots (blocks). */
	private static final double STEP = 0.25;
	/** The burn-away after the hit runs this many times the head's speed. */
	private static final double BURN_AWAY = 2.5;
	/** The strike's flash ring: from and to (radius, blocks), over so many ticks. */
	private static final float RING_FROM = 0.3f, RING_TO = 1.8f;
	private static final int RING_TICKS = 7, FIZZ_TICKS = 8, BUBBLES = 9;
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
		final boolean barrage;
		/** Where the line left the eyes, then every corner it turned, in order. */
		final List<Vec3> corners = new ArrayList<>();
		Vec3 prev, head;
		float speed = (float) OmegaBeams.HEAD_SPEED;
		boolean attached = true, water;
		int age;
		int endAge = -1;
		/** After the end: how long the line was, and how much of it has burnt away from the eye end. */
		double endLength, burnt, burntPrev;
		/** Under water, once it is gone: the ticks left of its fizz, and where it was. */
		int fizz = -1;
		List<Vec3> lastLine = List.of();
		@Nullable BlockPos light;

		Trail(int bearer, Vec3 at, boolean barrage) {
			this.bearer = bearer;
			this.barrage = barrage;
			this.prev = at;
			this.head = at;
			corners.add(at);
		}

		void moved(Vec3 to) {
			prev = head;
			head = to;
		}
	}

	/** A strike's flash ring. */
	private static final class Flash {
		final Vec3 pos;
		int age;

		Flash(Vec3 pos) {
			this.pos = pos;
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
	private static final List<Flash> FLASHES = new ArrayList<>();
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
			case OmegaFxPayload.START -> TRAILS.put(fx.id(), new Trail(fx.other(), fx.pos(), fx.b() >= 1));
			case OmegaFxPayload.CORNER -> {
				Trail t = trail(fx);
				t.moved(fx.pos());
				t.corners.add(fx.pos());
			}
			case OmegaFxPayload.HEAD -> {
				Trail t = trail(fx);
				t.moved(fx.pos());
				t.speed = Math.max(0.1f, fx.a());
				int flags = Math.round(fx.b());
				t.attached = (flags & 1) == 0;
				t.water = (flags & 2) != 0;
			}
			case OmegaFxPayload.HIT -> {
				FLASHES.add(new Flash(fx.pos()));
				hit(mc, fx.pos(), 2);
			}
			case OmegaFxPayload.END -> {
				Trail t = TRAILS.get(fx.id());
				if (t != null && t.endAge < 0) {
					t.moved(fx.pos());
					t.corners.add(fx.pos());
					if (fx.a() > 0) t.speed = fx.a();
					t.endAge = 0;
					t.endLength = length(line(mc, t, 1f, false));
				}
				if (fx.other() == 0) hit(mc, fx.pos(), 0);
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

	private static Trail trail(OmegaFxPayload fx) {
		Trail t = TRAILS.get(fx.id());
		if (t == null) {
			// Its start went by unseen (out of range then).
			t = new Trail(fx.other(), fx.pos(), false);
			t.attached = false;
			TRAILS.put(fx.id(), t);
		}
		return t;
	}

	/**
	 * The line as it is drawn now, from its eye end to the head: the eyes (while it is joined to them),
	 * the corners and the head, cut to the part still there (a barrage's last LET_GO blocks once it let
	 * go; after the end, what hasn't burnt away).
	 */
	private static List<Vec3> line(Minecraft mc, Trail t, float partial, boolean cut) {
		List<Vec3> pts = new ArrayList<>(t.corners);
		boolean live = t.endAge < 0;
		if (live) pts.add(t.prev.lerp(t.head, partial));
		if (t.attached && live && mc.level.getEntity(t.bearer) instanceof LivingEntity bearer) {
			Vec3 eyes = bearer.getEyePosition(partial).add(bearer.getViewVector(partial).scale(0.3));
			if (eyes.distanceToSqr(pts.get(0)) < 64) pts.set(0, eyes);
		}
		if (!cut) return pts;
		double keep;
		if (live) keep = t.attached ? Double.MAX_VALUE : OmegaBeams.LET_GO;
		else keep = t.endLength - Mth.lerp(partial, t.burntPrev, t.burnt);
		if (keep <= 0.01) return List.of();
		// From the head back, keep blocks of it.
		List<Vec3> out = new ArrayList<>();
		out.add(pts.get(pts.size() - 1));
		double run = 0;
		for (int i = pts.size() - 2; i >= 0; i--) {
			Vec3 a = out.get(out.size() - 1), b = pts.get(i);
			double d = a.distanceTo(b);
			if (run + d >= keep) {
				out.add(a.add(b.subtract(a).scale((keep - run) / Math.max(d, 1e-9))));
				break;
			}
			run += d;
			out.add(b);
		}
		java.util.Collections.reverse(out);
		return out;
	}

	private static double length(List<Vec3> pts) {
		double run = 0;
		for (int i = 1; i < pts.size(); i++) run += pts.get(i).distanceTo(pts.get(i - 1));
		return run;
	}

	/** A random point on the polyline. */
	private static Vec3 along(List<Vec3> pts, double total, RandomSource r) {
		double s = r.nextDouble() * total;
		for (int i = 1; i < pts.size(); i++) {
			double d = pts.get(i).distanceTo(pts.get(i - 1));
			if (s <= d) return pts.get(i - 1).lerp(pts.get(i), s / Math.max(d, 1e-9));
			s -= d;
		}
		return pts.get(pts.size() - 1);
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
			FLASHES.clear();
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
			FLASHES.removeIf(f -> ++f.age > RING_TICKS);
			for (Iterator<Int2ObjectMap.Entry<Trail>> it = TRAILS.int2ObjectEntrySet().iterator(); it.hasNext(); ) {
				Trail t = it.next().getValue();
				t.age++;
				if (t.fizz >= 0) {
					// W2: the sleeve fizzes on where the line was, 9 bubbles a tick down to none.
					bubbles(mc, t.lastLine, Math.round(BUBBLES * t.fizz / (float) FIZZ_TICKS), r);
					if (--t.fizz < 0) it.remove();
					continue;
				}
				if (t.endAge >= 0) {
					t.endAge++;
					t.burntPrev = t.burnt;
					t.burnt += BURN_AWAY * t.speed;
				}
				List<Vec3> pts = line(mc, t, 1f, true);
				if (pts.size() < 2) {
					light(mc, t, null);
					if (t.water && !t.lastLine.isEmpty()) t.fizz = FIZZ_TICKS;
					else it.remove();
					continue;
				}
				t.lastLine = pts;
				light(mc, t, t.endAge < 0 ? BlockPos.containing(t.head) : null);
				double total = length(pts);
				for (int i = 0; i < 2; i++) {
					ConstructParticle ember = LabFx.spawn(ModParticles.MOTE, along(pts, total, r), new Vec3(0, 0.02 + r.nextDouble() * 0.02, 0), 0.3f);
					if (ember != null) ember.lasting(8);
				}
				if (t.water) bubbles(mc, pts, BUBBLES, r);
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
		if (TRAILS.isEmpty() && EMBERS.isEmpty() && FLASHES.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		if (!TRAILS.isEmpty() || !FLASHES.isEmpty()) {
			RenderType type = RenderTypes.entityTranslucentEmissive(TEXTURE);
			float time = mc.level.getGameTime() + partial;
			for (Trail t : TRAILS.values()) {
				if (t.fizz >= 0) continue;
				List<Vec3> pts = line(mc, t, partial, true);
				if (pts.size() < 2) continue;
				Vec3 right = Vec3.ZERO;
				if (mc.level.getEntity(t.bearer) instanceof LivingEntity bearer) right = bearer.getViewVector(partial).cross(new Vec3(0, 1, 0));
				double total = length(pts);
				// Where the drawn part starts along the whole line, so the hot spots stay put on it as it burns away.
				double from = length(line(mc, t, partial, false)) - total;
				List<Vec3> left = new ArrayList<>(), rightLine = new ArrayList<>();
				List<Float> heat = new ArrayList<>();
				pair(pts, right, left, rightLine, heat, from, time);
				context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type, (pose, buffer) -> {
					for (List<Vec3> pos : List.of(left, rightLine)) {
						ribbon(pose, buffer, pos, heat, camera, GLOW, GLOW_R, GLOW_G, GLOW_B, 0.75f);
						ribbon(pose, buffer, pos, heat, camera, CORE, CORE_R, CORE_G, CORE_B, 1f);
					}
				});
			}
			if (!FLASHES.isEmpty()) {
				context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type, (pose, buffer) -> {
					for (Flash f : FLASHES) ring(pose, buffer, f, partial, camera);
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
	 * Cuts the line into STEP pieces and lays its two lasers PAIR_SEPARATION apart, the gap turned
	 * along with the line from the eyes' left-right (so the pair never crosses over at a corner), with
	 * each point's hot-spot brightness.
	 */
	private static void pair(List<Vec3> pts, Vec3 right, List<Vec3> left, List<Vec3> rightLine, List<Float> heat, double from, float time) {
		List<Vec3> fine = new ArrayList<>();
		List<Double> at = new ArrayList<>();
		fine.add(pts.get(0));
		at.add(0.0);
		double run = 0;
		for (int i = 1; i < pts.size(); i++) {
			Vec3 a = pts.get(i - 1), b = pts.get(i);
			double d = a.distanceTo(b);
			if (d < 1e-5) continue;
			int n = Math.max(1, (int) Math.ceil(d / STEP));
			for (int k = 1; k <= n; k++) {
				fine.add(a.lerp(b, k / (double) n));
				at.add(run + d * k / n);
			}
			run += d;
		}
		Vec3 side = right;
		double half = OmegaBeams.PAIR_SEPARATION / 2;
		for (int i = 0; i < fine.size(); i++) {
			Vec3 dir = fine.get(Math.min(i + 1, fine.size() - 1)).subtract(fine.get(Math.max(i - 1, 0)));
			dir = dir.lengthSqr() < 1e-10 ? new Vec3(0, 0, 1) : dir.normalize();
			// Carry the gap along: the last one, squared up to this piece.
			Vec3 s = side.subtract(dir.scale(side.dot(dir)));
			if (s.lengthSqr() < 1e-6) s = dir.cross(new Vec3(0, 1, 0));
			if (s.lengthSqr() < 1e-6) s = dir.cross(new Vec3(1, 0, 0));
			side = s.normalize();
			Vec3 c = fine.get(i);
			left.add(c.subtract(side.scale(half)));
			rightLine.add(c.add(side.scale(half)));
			heat.add(hot(from + at.get(i), time));
		}
	}

	/** Hot spots: x0.55-1.8 from smooth noise about half a block across, running 0.4 blocks a tick along the line. */
	private static float hot(double s, float time) {
		double x = (s - 0.4 * time) / 0.5;
		int i = Mth.floor(x);
		double f = x - i, u = f * f * (3 - 2 * f);
		float n = (float) Mth.lerp(u, hash(i), hash(i + 1));
		return 0.55f + 1.25f * n;
	}

	private static float hash(int i) {
		int h = i * 0x27d4eb2d;
		h ^= h >>> 15;
		h *= 0x165667b1;
		h ^= h >>> 13;
		return (h & 0xFFFF) / 65535f;
	}

	/** W2: n small bubbles from random points along the line, rising, each in and out in a few ticks. Only in water. */
	private static void bubbles(Minecraft mc, List<Vec3> pts, int n, RandomSource r) {
		if (pts.size() < 2 || n <= 0) return;
		double total = length(pts);
		for (int i = 0; i < n; i++) {
			Vec3 p = along(pts, total, r).add(LabFx.jitter(r, 0.1));
			if (!mc.level.getFluidState(BlockPos.containing(p)).is(net.minecraft.tags.FluidTags.WATER)) continue;
			mc.level.addParticle(ParticleTypes.BUBBLE, p.x, p.y, p.z, 0, 0.05, 0);
		}
	}

	/** The strike's flash: a ring facing the camera, growing from RING_FROM to RING_TO and fading. */
	private static void ring(PoseStack.Pose pose, VertexConsumer buffer, Flash f, float partial, Vec3 camera) {
		float t = Mth.clamp((f.age + partial) / RING_TICKS, 0f, 1f);
		float radius = Mth.lerp(t, RING_FROM, RING_TO);
		float alpha = (1f - t) * 0.9f;
		Vec3 view = f.pos.subtract(camera);
		if (view.lengthSqr() < 1e-6) return;
		view = view.normalize();
		Vec3 u = view.cross(Math.abs(view.y) < 0.9 ? new Vec3(0, 1, 0) : new Vec3(1, 0, 0)).normalize();
		Vec3 v = view.cross(u);
		int n = 32;
		float w = 0.08f + 0.06f * (1 - t);
		for (int i = 0; i < n; i++) {
			double a0 = Mth.TWO_PI * i / n, a1 = Mth.TWO_PI * (i + 1) / n;
			Vec3 d0 = u.scale(Math.cos(a0)).add(v.scale(Math.sin(a0))), d1 = u.scale(Math.cos(a1)).add(v.scale(Math.sin(a1)));
			vertex(pose, buffer, f.pos.add(d0.scale(radius - w)), camera, 0, 0, CORE_R, CORE_G, CORE_B, alpha);
			vertex(pose, buffer, f.pos.add(d0.scale(radius + w)), camera, 0, 1, CORE_R, CORE_G, CORE_B, alpha);
			vertex(pose, buffer, f.pos.add(d1.scale(radius + w)), camera, 1, 1, CORE_R, CORE_G, CORE_B, alpha);
			vertex(pose, buffer, f.pos.add(d1.scale(radius - w)), camera, 1, 0, CORE_R, CORE_G, CORE_B, alpha);
		}
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

	/** A camera-facing strip through the points, each point's colour scaled by its heat (as FlightTrail draws its streak). */
	private static void ribbon(PoseStack.Pose pose, VertexConsumer buffer, List<Vec3> pos, List<Float> heat, Vec3 camera,
			float halfWidth, float r, float g, float b, float alpha) {
		int n = pos.size();
		Vec3[] side = new Vec3[n];
		for (int i = 0; i < n; i++) {
			Vec3 along = pos.get(Math.min(i + 1, n - 1)).subtract(pos.get(Math.max(i - 1, 0)));
			Vec3 s = along.cross(camera.subtract(pos.get(i)));
			side[i] = s.lengthSqr() < 1e-10 ? Vec3.ZERO : s.normalize().scale(halfWidth);
		}
		for (int i = 0; i + 1 < n; i++) {
			float a0 = alpha * near(pos.get(i), camera), a1 = alpha * near(pos.get(i + 1), camera);
			if (a0 < 0.02f && a1 < 0.02f) continue;
			float h0 = heat.get(i), h1 = heat.get(i + 1);
			Vec3 p0 = pos.get(i), p1 = pos.get(i + 1);
			vertex(pose, buffer, p0.subtract(side[i]), camera, 0, 1, Math.min(1, r * h0), Math.min(1, g * h0), Math.min(1, b * h0), a0);
			vertex(pose, buffer, p0.add(side[i]), camera, 0, 0, Math.min(1, r * h0), Math.min(1, g * h0), Math.min(1, b * h0), a0);
			vertex(pose, buffer, p1.add(side[i + 1]), camera, 1, 0, Math.min(1, r * h1), Math.min(1, g * h1), Math.min(1, b * h1), a1);
			vertex(pose, buffer, p1.subtract(side[i + 1]), camera, 1, 1, Math.min(1, r * h1), Math.min(1, g * h1), Math.min(1, b * h1), a1);
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
