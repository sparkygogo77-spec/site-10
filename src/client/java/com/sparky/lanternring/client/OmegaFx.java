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
 * smoke, E3 air brake, E4 crackling arcs); each beam as a thin red laser, about 0.8 px wide, with a
 * bright head and a fading tail about 1.4 blocks long, carrying a red light through the air; burnt
 * blocks as glowing embers of the block's own model that shrink and crumble to ash; burnt creatures
 * tinted ember orange (LivingEntityRendererMixin) with embers rising off them, then ash.
 */
public final class OmegaFx {
	public static final RenderStateDataKey<Float> EMBER_KEY = RenderStateDataKey.create(() -> "lanternring:omega_ember");
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/flight_trail.png");
	/** The laser's red, about (255, 15, 8), and its white-hot head. */
	private static final float RED_R = 1f, RED_G = 0.06f, RED_B = 0.03f;
	/** Half widths: the core is 0.8 px across, the glow round it wider and faint. */
	private static final float CORE = 0.025f, GLOW = 0.1f;
	private static final double TAIL = 1.4;
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
		final List<Vec3> points = new ArrayList<>();
		Vec3 prev, head;
		int endAge = -1;
		@Nullable BlockPos light;

		Trail(int bearer, Vec3 at) {
			this.bearer = bearer;
			this.prev = at;
			this.head = at;
			points.add(at);
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
			case OmegaFxPayload.HEAD -> {
				Trail t = TRAILS.get(fx.id());
				if (t == null) {
					t = new Trail(fx.other(), fx.pos());
					TRAILS.put(fx.id(), t);
				}
				t.prev = t.head;
				t.head = fx.pos();
				t.points.add(0, fx.pos());
				trim(t);
			}
			case OmegaFxPayload.END -> {
				Trail t = TRAILS.get(fx.id());
				if (t != null) {
					t.prev = t.head;
					t.head = fx.pos();
					t.points.add(0, fx.pos());
					trim(t);
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

	/** Keeps only the last TAIL blocks of the path behind the head. */
	private static void trim(Trail t) {
		double run = 0;
		for (int i = 1; i < t.points.size(); i++) {
			run += t.points.get(i).distanceTo(t.points.get(i - 1));
			if (run > TAIL + 1) {
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
				List<Vec3> pos = new ArrayList<>();
				List<Float> fade = new ArrayList<>();
				float gone = t.endAge < 0 ? 0f : Mth.clamp((t.endAge + partial) / 5f, 0f, 1f);
				// The head between its last two positions, then back along the path to TAIL behind it.
				Vec3 head = t.endAge < 0 ? t.prev.lerp(t.head, partial) : t.head;
				pos.add(head);
				fade.add(1f);
				double run = 0;
				Vec3 last = head;
				for (int i = 1; i < t.points.size(); i++) {
					Vec3 p = t.points.get(i);
					double d = p.distanceTo(last);
					if (d < 1e-4) continue;
					double tail = TAIL * (1 - gone);
					if (run + d >= tail) {
						pos.add(last.add(p.subtract(last).scale((tail - run) / d)));
						fade.add(0f);
						break;
					}
					run += d;
					pos.add(p);
					fade.add((float) (1 - run / Math.max(0.01, tail)));
					last = p;
				}
				if (pos.size() < 2) continue;
				float fadeAll = 1f - gone;
				context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type, (pose, buffer) -> {
					ribbon(pose, buffer, pos, fade, camera, GLOW, RED_R, RED_G, RED_B, 0.4f * fadeAll);
					ribbon(pose, buffer, pos, fade, camera, CORE, RED_R, RED_G, RED_B, fadeAll);
					// The white-hot head: the first sliver of the core, paler.
					List<Vec3> tip = new ArrayList<>(pos.subList(0, 2));
					Vec3 dir = tip.get(1).subtract(tip.get(0));
					if (dir.length() > 0.25) tip.set(1, tip.get(0).add(dir.normalize().scale(0.25)));
					ribbon(pose, buffer, tip, List.of(1f, 0.6f), camera, CORE * 1.6f, 1f, 0.75f, 0.65f, fadeAll);
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
