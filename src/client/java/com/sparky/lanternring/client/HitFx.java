package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.HitEffects;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.CombatFxPayload;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.RenderStateDataKey;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * The hit effects J kept from Blender pass 815 (server side: HitEffects), shader-safe and in the corps colour of the
 * ring that made them:
 * <ul>
 * <li>F3 outline flash: a shell round the creature, full for 3 ticks and gone by RingTuning.HIT_FLASH (9 ticks),
 * drawn additively without a shader pack and as emissive glass under one; 24 sparks spray off the hit for 9 ticks
 * and the creature rocks 12 degrees away from the blow;
 * <li>F1 construct shatter: each block of the punched construct breaks, nearest the punch first, into construct
 * pixels that fly out (nearer ones faster, 0.22/(0.6+d) blocks a tick), tumble, fall (gravity 0.01) and shrink out
 * over 16 ticks.
 * </ul>
 */
public final class HitFx {
	/** A creature's flash on its render state: how strong the shell is, how far it rocks, and the blow's way (world x, z). */
	public record Hit(float shell, float rock, float dx, float dz, Corps corps) {
	}

	private static final Hit NONE = new Hit(0f, 0f, 0f, 0f, Corps.GREEN);
	public static final RenderStateDataKey<Hit> KEY = RenderStateDataKey.create(() -> "lanternring:hit_flash");
	private static final Identifier SHELL = LanternRing.id("textures/entity/soul_sight.png");
	/** F3: full for this many ticks, then fading to nothing by HIT_FLASH; the rock and the sparks. */
	private static final int SHELL_FULL = 3, SPARKS = 24, SPARK_TICKS = 9;
	private static final float ROCK = 12f, GROW = 1.1f;
	private static final int FULL_BRIGHT = 0xF000F0;
	/** F1: pixels per block, their life, gravity and drag; the most flying at once. */
	private static final int PIXELS = 10, PIXEL_LIFE = 16, MAX_BITS = 4000;
	private static final double GRAVITY = 0.01, DRAG = 0.98;
	/** A block whose turn came stays waiting this long for the server to take it, then is let be. */
	private static final int WAIT = 8;

	private record Flash(long start, Corps corps, float dx, float dz) {
	}

	private record Cell(BlockPos pos, Block block, Corps corps, long due, Vec3 hit, Vec3 normal) {
	}

	private static final class Bit {
		final Block block;
		final Corps corps;
		Vec3 pos, vel;
		final float size, u, v;
		int age;
		final Quaternionf turn = new Quaternionf();
		final Vector3f spin;

		Bit(Block block, Corps corps, Vec3 pos, Vec3 vel, float size, RandomSource r) {
			this.block = block;
			this.corps = corps;
			this.pos = pos;
			this.vel = vel;
			this.size = size;
			this.u = r.nextFloat() * 0.75f;
			this.v = r.nextFloat() * 0.75f;
			this.spin = new Vector3f(r.nextFloat() - 0.5f, r.nextFloat() - 0.5f, r.nextFloat() - 0.5f).mul(0.6f);
		}
	}

	private static final Int2ObjectMap<Flash> FLASHES = new Int2ObjectOpenHashMap<>();
	private static final List<Cell> CELLS = new ArrayList<>();
	private static final List<Bit> BITS = new ArrayList<>();

	private HitFx() {
	}

	/** F3, from CombatFx (inside the ring's corps): the target's shell, the rock and the sparks off "from". */
	static void flash(ClientLevel level, CombatFxPayload fx, RandomSource r) {
		Vec3 way = fx.from().subtract(fx.to());
		Vec3 flat = new Vec3(way.x, 0, way.z);
		flat = flat.lengthSqr() < 1e-4 ? Vec3.ZERO : flat.normalize();
		FLASHES.put(fx.target(), new Flash(level.getGameTime(), CorpsTint.current(), (float) flat.x, (float) flat.z));
		Vec3 out = way.lengthSqr() < 1e-4 ? new Vec3(0, 1, 0) : way.normalize();
		LabFx.spawn(ModParticles.SPARK, fx.from(), Vec3.ZERO, 1.3f);
		for (int i = 0; i < LabFx.count(SPARKS); i++) {
			Vec3 v = out.scale(0.12 + r.nextDouble() * 0.2).add(LabFx.jitter(r, 0.35)).add(0, 0.05, 0);
			ConstructParticle p = LabFx.spawn(i % 3 == 0 ? ModParticles.SPARK : ModParticles.MOTE, fx.from(), v, 0.35f + 0.25f * r.nextFloat());
			if (p != null) p.lasting(SPARK_TICKS - r.nextInt(3));
		}
	}

	/** F1, from CombatFx: the construct punched at "from" goes block by block as the server takes it. */
	static void shatter(ClientLevel level, CombatFxPayload fx) {
		Vec3 hit = fx.from();
		Direction face = Direction.values()[Math.clamp(fx.variant(), 0, 5)];
		Vec3 normal = new Vec3(face.getStepX(), face.getStepY(), face.getStepZ());
		long now = level.getGameTime();
		for (BlockPos pos : HitEffects.shatterCells(level, BlockPos.containing(fx.to()), hit, p -> true)) {
			CELLS.add(new Cell(pos, level.getBlockState(pos).getBlock(), Corps.of(level.getBlockState(pos)), now + 1 + HitEffects.delay(pos, hit), hit, normal));
		}
	}

	static void tick(Minecraft mc) {
		ClientLevel level = mc.level;
		if (level == null) {
			FLASHES.clear();
			CELLS.clear();
			BITS.clear();
			return;
		}
		if (mc.isPaused()) return;
		long now = level.getGameTime();
		int life = Math.max(SHELL_FULL + 1, RingTuning.HIT_FLASH.ticks());
		FLASHES.values().removeIf(f -> now - f.start > life || now < f.start - 20);
		RandomSource r = level.getRandom();
		CELLS.removeIf(c -> {
			if (now < c.due) return now < c.due - 400;
			if (HitEffects.isConstruct(level.getBlockState(c.pos))) return now > c.due + WAIT;
			pixels(c, r);
			return true;
		});
		for (int i = BITS.size() - 1; i >= 0; i--) {
			Bit b = BITS.get(i);
			b.age++;
			b.pos = b.pos.add(b.vel);
			b.vel = new Vec3(b.vel.x * DRAG, b.vel.y * DRAG - GRAVITY, b.vel.z * DRAG);
			b.turn.rotateXYZ(b.spin.x, b.spin.y, b.spin.z);
			if (b.age >= PIXEL_LIFE) BITS.remove(i);
		}
	}

	/** One block breaking into construct pixels thrown away from the punch. */
	private static void pixels(Cell c, RandomSource r) {
		if (BITS.size() > MAX_BITS) return;
		Vec3 centre = Vec3.atCenterOf(c.pos);
		double d = Math.max(0, centre.distanceTo(c.hit) - 0.5);
		double speed = 0.22 / (0.6 + d);
		for (int i = 0; i < PIXELS; i++) {
			Vec3 p = centre.add((r.nextDouble() - 0.5) * 0.8, (r.nextDouble() - 0.5) * 0.8, (r.nextDouble() - 0.5) * 0.8);
			Vec3 away = p.subtract(c.hit);
			away = away.lengthSqr() < 1e-4 ? c.normal.scale(-1) : away.normalize();
			// Out from the punch, mostly through the construct (away from the face that was hit), with a little scatter.
			Vec3 v = away.scale(speed * (0.7 + 0.6 * r.nextDouble())).add(LabFx.jitter(r, 0.04));
			BITS.add(new Bit(c.block, c.corps, p, v, Mth.lerp(r.nextFloat(), 0.16f, 0.26f), r));
		}
	}

	/** The flash on this creature right now (LivingEntityRendererMixin; render states are reused, so never null). */
	public static Hit hit(LivingEntity e, float partial) {
		if (FLASHES.isEmpty()) return NONE;
		Flash f = FLASHES.get(e.getId());
		if (f == null) return NONE;
		float age = e.level().getGameTime() - f.start + partial;
		float end = Math.max(SHELL_FULL + 1, RingTuning.HIT_FLASH.ticks());
		if (age < 0 || age > end) return NONE;
		float shell = age <= SHELL_FULL ? 1f : 1f - SuperJumpPoses.smooth((age - SHELL_FULL) / (end - SHELL_FULL));
		// Knocked over fast (2 ticks), settling back by the end.
		float rock = age < 2 ? age / 2 : 1f - SuperJumpPoses.smooth((age - 2) / Math.max(1f, end - 2));
		return new Hit(shell, rock * ROCK, f.dx, f.dz, f.corps);
	}

	/** The colour the shell is drawn in: construct green, recoloured for the corps. */
	private static int colour(Corps corps) {
		return CorpsTint.apply(corps, 0xFF22D45E) & 0xFFFFFF;
	}

	/** Rocks the creature about its feet, its top going the way the blow went (after vanilla's turns, so in body space). */
	public static void rotate(LivingEntityRenderState state, PoseStack poseStack) {
		Hit hit = state.getDataOrDefault(KEY, NONE);
		if (hit.rock < 0.01f || hit.dx == 0 && hit.dz == 0) return;
		// Vanilla turned the body by 180 - bodyRot about Y; the blow's way in body space is the world way turned back.
		float a = (180f - state.bodyRot) * Mth.DEG_TO_RAD;
		float lx = hit.dx * Mth.cos(a) - hit.dz * Mth.sin(a);
		float lz = hit.dx * Mth.sin(a) + hit.dz * Mth.cos(a);
		// Turning about up x way tips the top toward the way.
		Vector3f axis = new Vector3f(0, 1, 0).cross(lx, 0, lz);
		if (axis.lengthSquared() < 1e-6f) return;
		axis.normalize();
		poseStack.rotate(new Quaternionf().rotationAxis(hit.rock * Mth.DEG_TO_RAD, axis));
	}

	/** F3's shell, drawn on every living thing's renderer. */
	public static class Layer<S extends LivingEntityRenderState, M extends EntityModel<? super S>> extends RenderLayer<S, M> {
		public Layer(RenderLayerParent<S, M> renderer) {
			super(renderer);
		}

		@Override
		public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, S state, float yRot, float xRot) {
			Hit hit = state.getDataOrDefault(KEY, NONE);
			if (hit.shell <= 0.01f) return;
			int rgb = colour(hit.corps);
			boolean pack = SoulSight.shaderPackOn();
			RenderType type = pack ? RenderTypes.entityTranslucentEmissive(SHELL) : RenderTypes.energySwirl(SHELL, 0f, 0f);
			// Under a shader pack the glass isn't additive, so alpha fades it; without one the colour does (kept low: added to a
			// sunlit mob, full colour burns to white).
			int tint = pack ? withAlpha(rgb, 0.7f * hit.shell) : scale(rgb, 0.55f * hit.shell);
			poseStack.pushPose();
			// Grown about the body's middle (the model hangs 1.501 down from its origin, y pointing down).
			float mid = 1.501f - state.boundingBoxHeight / 2;
			poseStack.translate(0, mid, 0);
			poseStack.scale(GROW, GROW, GROW);
			poseStack.translate(0, -mid, 0);
			collector.order(2).submitModel(getParentModel(), state, poseStack, type, pack ? ShaderGlow.light(hit.shell) : FULL_BRIGHT,
					OverlayTexture.NO_OVERLAY, tint, null, 0);
			poseStack.popPose();
		}
	}

	/** F1's flying pixels. */
	public static void render(LevelRenderContext ctx) {
		if (BITS.isEmpty()) return;
		float partial = ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS), (pose, vc) -> {
			for (Bit b : BITS) {
				float t = Mth.clamp((b.age + partial) / PIXEL_LIFE, 0f, 1f);
				float half = b.size / 2 * (1 - t);
				if (half < 0.005f) continue;
				TextureAtlasSprite s = SuperLandConstruct.sprite(b.block == ModRegistry.CONSTRUCT_BRICK ? ModRegistry.CONSTRUCT_BRICK : ModRegistry.LIGHT_CONSTRUCT, b.corps);
				PowerLandingFx.cube(pose, vc, cam, b.pos.add(b.vel.scale(partial)), b.turn, half, half, half, s, b.u, b.v, 0.25f,
						PowerLandingFx.bright(PowerLandingFx.tint(b.corps), 0.2f), 0.9f * (1 - t * t), ShaderGlow.light(0.8f));
			}
		});
	}

	/** How many creatures are flashing (for tests). */
	public static int flashes() {
		return FLASHES.size();
	}

	/** How many shatter pixels are flying (for tests). */
	public static int bits() {
		return BITS.size();
	}

	private static int withAlpha(int rgb, float alpha) {
		return Math.clamp(Math.round(alpha * 255), 0, 255) << 24 | rgb & 0xFFFFFF;
	}

	private static int scale(int rgb, float f) {
		int r = Math.round((rgb >> 16 & 0xFF) * f), g = Math.round((rgb >> 8 & 0xFF) * f), b = Math.round((rgb & 0xFF) * f);
		return 0xFF000000 | r << 16 | g << 8 | b;
	}
}
