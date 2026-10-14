package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.PowerLandings;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.jspecify.annotations.Nullable;

/**
 * What every client draws for a power landing (server side: PowerLandings; J's Blender pass 400).
 * The blocks it takes turn construct (the Construct look row's texture, in the jumper's corps) and
 * then go:
 * <ul>
 * <li>D0 stop dead: the block you land on goes construct for 0.8 s and fades back, the 8 round it
 * light up and dissolve to pixels, and a construct ring runs out to 3 blocks;
 * <li>A3 dissolve: each trench block lights up as the planted foot nears it and breaks into about
 * 10 pixels as it gets there (the side columns a tick later); a construct pad under the foot keeps
 * you level and fades after the halt;
 * <li>B2 plough: a construct bow wave rides ahead of the foot and throws each block aside; they land
 * square beside the trench and dissolve to pixels 12 ticks later.
 * </ul>
 * Pixels fly up 0.08 to 0.24 a tick, drift with you, fall at 0.02 a tick, and shrink out over 12 to
 * 22 ticks. Everything stays see-through (at most 95% opaque).
 */
public final class PowerLandingFx {
	/** The ring's flare at impact (Blender glow 18, as a flash size). */
	private static final float IMPACT_FLASH = 1.8f;
	/** Pixels per cleared block and their size range (blocks). */
	private static final int PIXELS = 10;
	private static final float PIXEL_MIN = 0.09f, PIXEL_MAX = 0.17f;
	/** Stop dead: how long the landing block stays construct, and the ring's reach and ticks. */
	private static final int HOLD_BLOCK = 16, PULSE_TICKS = 8;
	private static final float PULSE_REACH = 3f;
	/** The pad: its size (blocks), opacity, and fade after the halt. */
	private static final float PAD_W = 0.55f, PAD_L = 1.1f, PAD_ALPHA = 0.85f, PAD_FADE = 11f, PAD_HOLD = 6f;
	/** The plough's blade: how far ahead of the foot, how wide, and its push and fade after the halt. */
	private static final float BLADE_AHEAD = 0.65f, BLADE_W = 3.3f, BLADE_PUSH = 0.25f, BLADE_FADE = 9f;
	/** Thrown blocks: gravity, and ticks they sit beside the trench before dissolving. */
	private static final double THROW_GRAVITY = 0.045;
	private static final int THROWN_SIT = 12;

	private static final class Cell {
		final PowerLandings.Cell cell;
		final boolean taken;
		boolean gone;

		Cell(PowerLandings.Cell cell, boolean taken) {
			this.cell = cell;
			this.taken = taken;
		}
	}

	private static final class Landing {
		final Corps corps;
		final int take, bearer, slide;
		final Vec3 from, to, dir;
		final double speed, top;
		final long start;
		final List<Cell> cells = new ArrayList<>();

		Landing(RingFxPayload fx, Corps corps, long start, int slide) {
			this.corps = corps;
			this.take = fx.variant();
			this.bearer = fx.bearer();
			this.from = fx.from();
			this.to = fx.to();
			Vec3 d = new Vec3(to.x - from.x, 0, to.z - from.z);
			this.dir = d.lengthSqr() > 1e-6 ? d.normalize() : Vec3.ZERO;
			this.speed = fx.value();
			this.top = PowerLandings.groundY(from.y) + 1;
			this.start = start;
			this.slide = slide;
		}

		/** How long it lasts: the slide, the hold and the pad's or blade's fade, or the stop's ring and block. */
		float end() {
			return take == PowerLandings.STOP ? Math.max(HOLD_BLOCK, PowerLandings.STOP_CORNER) + 2 : slide + PAD_HOLD + PAD_FADE + 2;
		}
	}

	/** A construct pixel or a thrown block. */
	private static final class Bit {
		final Corps corps;
		Vec3 pos, vel;
		final float size;
		final int life;
		int age;
		final Quaternionf turn = new Quaternionf();
		final Vector3f spin;
		/** For a thrown block: the top of the ground it lands on, and when it landed (-1 still flying). */
		final boolean block;
		final double ground;
		int landed = -1;
		/** Which part of the texture a pixel shows. */
		final float u, v;

		Bit(Corps corps, Vec3 pos, Vec3 vel, float size, int life, boolean block, double ground, RandomSource r) {
			this.corps = corps;
			this.pos = pos;
			this.vel = vel;
			this.size = size;
			this.life = life;
			this.block = block;
			this.ground = ground;
			this.spin = new Vector3f(r.nextFloat() - 0.5f, r.nextFloat() - 0.5f, r.nextFloat() - 0.5f).mul(block ? 0.5f : 0.8f);
			this.u = r.nextFloat() * 0.85f;
			this.v = r.nextFloat() * 0.85f;
		}
	}

	private static final List<Landing> LANDINGS = new ArrayList<>();
	private static final List<Bit> BITS = new ArrayList<>();

	private PowerLandingFx() {
	}

	/** POWER_LAND, while LabFx has the jumper's corps current. */
	static void handle(RingFxPayload fx, @Nullable Player bearer) {
		Minecraft mc = Minecraft.getInstance();
		ClientLevel level = mc.level;
		if (level == null) return;
		Vec3 d = fx.to().subtract(fx.from());
		double length = Math.sqrt(d.x * d.x + d.z * d.z);
		int slide = fx.variant() == PowerLandings.STOP ? 0 : PowerLandings.slideTicks(length, fx.value());
		if (fx.bearer() >= 0) MovePoses.power(fx.bearer(), fx.variant(), slide);
		if (mc.player != null && fx.bearer() == mc.player.getId()) PowerSlide.start(mc.player, fx);
		if (bearer != null) RingEmit.flash(bearer, IMPACT_FLASH);
		Landing l = new Landing(fx, CorpsTint.current(), level.getGameTime(), slide);
		var cells = PowerLandings.cells(fx.from(), l.dir, length, fx.value(), fx.variant());
		for (PowerLandings.Cell c : PowerLandings.onGround(level, cells, PowerLandings.groundY(fx.from().y))) {
			BlockState state = level.getBlockState(c.pos());
			l.cells.add(new Cell(c, PowerLandings.takes(level, c.pos(), state)));
		}
		LANDINGS.add(l);
	}

	static void tick(Minecraft mc) {
		ClientLevel level = mc.level;
		if (level == null) {
			LANDINGS.clear();
			BITS.clear();
			return;
		}
		if (mc.isPaused()) return;
		long now = level.getGameTime();
		RandomSource r = level.getRandom();
		for (Landing l : LANDINGS) {
			int age = (int) (now - l.start);
			for (Cell c : l.cells) {
				if (c.gone || !c.taken || age < c.cell.cleared()) continue;
				c.gone = true;
				if (l.take == PowerLandings.PLOUGH) thrown(l, c, r);
				else pixels(l, Vec3.atCenterOf(c.cell.pos()), r);
			}
		}
		LANDINGS.removeIf(l -> now - l.start > l.end() || now < l.start - 20);
		for (int i = BITS.size() - 1; i >= 0; i--) {
			Bit b = BITS.get(i);
			if (!move(b, r)) BITS.remove(i);
		}
	}

	/** A block breaking into construct pixels that fly up, drift with you and fall. */
	private static void pixels(Landing l, Vec3 at, RandomSource r) {
		Vec3 drift = l.dir.scale(l.speed / 20 * 0.35);
		for (int i = 0; i < PIXELS; i++) {
			Vec3 p = at.add((r.nextDouble() - 0.5) * 0.8, (r.nextDouble() - 0.5) * 0.8, (r.nextDouble() - 0.5) * 0.8);
			Vec3 v = drift.add((r.nextDouble() - 0.5) * 0.08, 0.08 + r.nextDouble() * 0.16, (r.nextDouble() - 0.5) * 0.08);
			BITS.add(new Bit(l.corps, p, v, Mth.lerp(r.nextFloat(), PIXEL_MIN, PIXEL_MAX), 12 + r.nextInt(11), false, 0, r));
		}
	}

	/** The plough throws a block aside: out to its side (the middle column alternates), a little forward, up and tumbling. */
	private static void thrown(Landing l, Cell c, RandomSource r) {
		int side = c.cell.side();
		if (side == 0) {
			int along = (int) Math.floor(Vec3.atCenterOf(c.cell.pos()).subtract(l.from).dot(l.dir));
			side = (along & 1) == 0 ? 1 : -1;
		}
		Vec3 perp = new Vec3(-l.dir.z, 0, l.dir.x).scale(side);
		Vec3 v = perp.scale(0.24 + r.nextDouble() * 0.08).add(l.dir.scale(l.speed / 20 * (0.08 + r.nextDouble() * 0.08))).add(0, 0.24 + r.nextDouble() * 0.06, 0);
		BITS.add(new Bit(l.corps, Vec3.atCenterOf(c.cell.pos()), v, 0.98f, 120, true, l.top, r));
	}

	/** One tick of a pixel or thrown block; false once it's gone. */
	private static boolean move(Bit b, RandomSource r) {
		b.age++;
		if (b.block) {
			if (b.landed >= 0) {
				if (b.age - b.landed < THROWN_SIT) return true;
				// Sat beside the trench long enough: it dissolves to pixels.
				for (int i = 0; i < PIXELS; i++) {
					Vec3 p = b.pos.add((r.nextDouble() - 0.5) * 0.8, (r.nextDouble() - 0.5) * 0.8, (r.nextDouble() - 0.5) * 0.8);
					Vec3 v = new Vec3((r.nextDouble() - 0.5) * 0.06, 0.08 + r.nextDouble() * 0.16, (r.nextDouble() - 0.5) * 0.06);
					BITS.add(new Bit(b.corps, p, v, Mth.lerp(r.nextFloat(), PIXEL_MIN, PIXEL_MAX), 12 + r.nextInt(11), false, 0, r));
				}
				return false;
			}
			b.pos = b.pos.add(b.vel);
			b.vel = b.vel.add(0, -THROW_GRAVITY, 0);
			b.turn.rotateXYZ(b.spin.x, b.spin.y, b.spin.z);
			// Lands square on the surface beside the trench.
			if (b.vel.y < 0 && b.pos.y - 0.5 <= b.ground) {
				b.pos = new Vec3(Math.floor(b.pos.x) + 0.5, b.ground + 0.5, Math.floor(b.pos.z) + 0.5);
				b.turn.identity();
				b.landed = b.age;
			}
			return b.age < b.life;
		}
		b.pos = b.pos.add(b.vel);
		b.vel = new Vec3(b.vel.x * 0.92, b.vel.y - 0.02, b.vel.z * 0.92);
		b.turn.rotateXYZ(b.spin.x, b.spin.y, b.spin.z);
		return b.age < b.life;
	}

	public static void render(LevelRenderContext ctx) {
		if (LANDINGS.isEmpty() && BITS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		ClientLevel level = mc.level;
		if (level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		float now = level.getGameTime() + partial;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS), (pose, vc) -> {
			for (Landing l : LANDINGS) {
				TextureAtlasSprite s = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, l.corps);
				float[] tint = tint(l.corps);
				float age = now - l.start;
				// The blocks lighting up, construct until they go.
				for (Cell c : l.cells) {
					if (!c.taken || c.gone || age < c.cell.lit()) continue;
					float lit = Mth.clamp((age - c.cell.lit()) / 2f, 0f, 1f);
					float flare = Math.max(0f, 1f - (c.cell.cleared() - age) / 3f);
					Vec3 m = Vec3.atCenterOf(c.cell.pos());
					cube(pose, vc, cam, m, null, 0.502f, 0.502f, 0.502f, s, 0f, 0f, 1f, bright(tint, 0.3f * flare), 0.7f * lit + 0.2f * flare,
							ShaderGlow.light(0.5f + 0.5f * flare));
				}
				if (l.take == PowerLandings.STOP) {
					stop(pose, vc, cam, l, s, tint, age);
					continue;
				}
				Entity who = l.bearer >= 0 ? level.getEntity(l.bearer) : null;
				Vec3 feet = who != null ? who.getPosition(partial) : l.to;
				pad(pose, vc, cam, l, s, tint, age, feet);
				if (l.take == PowerLandings.PLOUGH) blade(pose, vc, cam, l, s, tint, age, feet);
			}
			for (Bit b : BITS) {
				float t = b.block ? 0f : Mth.clamp((b.age + partial) / b.life, 0f, 1f);
				Vec3 p = b.block && b.landed >= 0 ? b.pos : b.pos.add(b.vel.scale(partial));
				TextureAtlasSprite s = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, b.corps);
				float half = b.size / 2 * (1 - t);
				if (half < 0.005f) continue;
				float[] tint = tint(b.corps);
				if (b.block) {
					cube(pose, vc, cam, p, b.landed >= 0 ? null : b.turn, half, half, half, s, 0f, 0f, 1f, tint, 0.85f, ShaderGlow.light(0.6f));
				} else {
					cube(pose, vc, cam, p, b.turn, half, half, half, s, b.u, b.v, 0.15f, bright(tint, 0.25f), 0.9f * (1 - t * t), ShaderGlow.light(0.8f));
				}
			}
		});
	}

	/** Stop dead: the landing block construct for a moment, and the ring running out over the ground. */
	private static void stop(PoseStack.Pose pose, VertexConsumer vc, Vec3 cam, Landing l, TextureAtlasSprite s, float[] tint, float age) {
		if (age < HOLD_BLOCK) {
			float a = age < 10 ? 0.85f : 0.85f * (1 - (age - 10) / (HOLD_BLOCK - 10f));
			Vec3 m = new Vec3(Math.floor(l.from.x) + 0.5, l.top - 0.5, Math.floor(l.from.z) + 0.5);
			cube(pose, vc, cam, m, null, 0.503f, 0.503f, 0.503f, s, 0f, 0f, 1f, bright(tint, age < 3 ? 0.4f : 0f), a, ShaderGlow.light(0.7f));
		}
		if (age < PULSE_TICKS) {
			float t = age / PULSE_TICKS;
			float radius = 0.5f + (PULSE_REACH - 0.5f) * smooth(t);
			float width = 0.35f;
			float alpha = 0.7f * (1 - t);
			int n = 40;
			float y = (float) l.top + 0.03f;
			for (int i = 0; i < n; i++) {
				float a0 = i * Mth.TWO_PI / n, a1 = (i + 1) * Mth.TWO_PI / n;
				float[][] q = {
						{(float) l.from.x + Mth.cos(a0) * (radius - width), (float) l.from.z + Mth.sin(a0) * (radius - width)},
						{(float) l.from.x + Mth.cos(a1) * (radius - width), (float) l.from.z + Mth.sin(a1) * (radius - width)},
						{(float) l.from.x + Mth.cos(a1) * radius, (float) l.from.z + Mth.sin(a1) * radius},
						{(float) l.from.x + Mth.cos(a0) * radius, (float) l.from.z + Mth.sin(a0) * radius}};
				for (int side = 0; side < 2; side++) {
					for (int k = 0; k < 4; k++) {
						float[] c = q[side == 0 ? k : 3 - k];
						float u = Mth.lerp(Math.floorMod((int) Math.floor(c[0]), 4) / 4f + (c[0] - (float) Math.floor(c[0])) / 4f, s.getU0(), s.getU1());
						float v = Mth.lerp(Math.floorMod((int) Math.floor(c[1]), 4) / 4f + (c[1] - (float) Math.floor(c[1])) / 4f, s.getV0(), s.getV1());
						vertex(pose, vc, cam, c[0], y, c[1], u, v, bright(tint, 0.3f), alpha, ShaderGlow.light(0.8f), 0, side == 0 ? 1 : -1, 0);
					}
				}
			}
		}
	}

	/** The construct pad under the planted foot: level with the ground, along the slide, fading after the halt. */
	private static void pad(PoseStack.Pose pose, VertexConsumer vc, Vec3 cam, Landing l, TextureAtlasSprite s, float[] tint, float age, Vec3 feet) {
		float fade = age < l.slide + PAD_HOLD ? 1f : 1f - (age - l.slide - PAD_HOLD) / PAD_FADE;
		if (fade <= 0f) return;
		Quaternionf yaw = new Quaternionf().rotationY((float) Math.atan2(l.dir.x, l.dir.z));
		Vec3 m = new Vec3(feet.x, l.top - 1 / 32.0, feet.z);
		cube(pose, vc, cam, m, yaw, PAD_W / 2, 1 / 32f, PAD_L / 2, s, 0f, 0f, 0.5f, bright(tint, 0.2f), PAD_ALPHA * fade, ShaderGlow.light(0.7f));
	}

	/**
	 * The plough's bow wave: a shallow V pointing forward, 3.3 wide, its top edge curling forward,
	 * riding just ahead of the foot; at the halt it pushes on a little and fades.
	 */
	private static void blade(PoseStack.Pose pose, VertexConsumer vc, Vec3 cam, Landing l, TextureAtlasSprite s, float[] tint, float age, Vec3 feet) {
		float after = age - l.slide;
		float fade = after < 0 ? Math.min(1f, age / 1.5f) : 1f - after / BLADE_FADE;
		if (fade <= 0f) return;
		Vec3 tip = new Vec3(feet.x, l.top, feet.z).add(l.dir.scale(BLADE_AHEAD + Math.max(0f, after) * BLADE_PUSH));
		Vec3 perp = new Vec3(-l.dir.z, 0, l.dir.x);
		double back = 0.45;
		float high = 0.75f, curl = 0.25f;
		float alpha = 0.8f * fade;
		float[] c = bright(tint, 0.25f);
		int light = ShaderGlow.light(0.8f);
		for (int side = -1; side <= 1; side += 2) {
			Vec3 wing = tip.add(perp.scale(side * BLADE_W / 2)).subtract(l.dir.scale(back));
			// The wing: from the tip at the ground up to the top edge, which leans forward (the curl).
			Vec3[] q = {tip, wing, wing.add(l.dir.scale(curl)).add(0, high, 0), tip.add(l.dir.scale(curl)).add(0, high, 0)};
			float[][] uv = {{s.getU0(), s.getV1()}, {s.getU1(), s.getV1()}, {s.getU1(), s.getV0()}, {s.getU0(), s.getV0()}};
			for (int face = 0; face < 2; face++) {
				for (int k = 0; k < 4; k++) {
					int i = face == 0 ? k : 3 - k;
					vertex(pose, vc, cam, (float) q[i].x, (float) q[i].y, (float) q[i].z, uv[i][0], uv[i][1], c, alpha, light,
							(float) l.dir.x, 0.3f, (float) l.dir.z);
				}
			}
		}
	}

	/**
	 * A box of half sizes hx, hy, hz centred on m, turned by turn (null: square to the world), every
	 * face both ways round. Its faces show the part of the sprite at (u, v) of size span (0..1).
	 */
	static void cube(PoseStack.Pose pose, VertexConsumer vc, Vec3 cam, Vec3 m, @Nullable Quaternionf turn, float hx, float hy, float hz,
			TextureAtlasSprite s, float u, float v, float span, float[] c, float alpha, int light) {
		float u0 = Mth.lerp(u, s.getU0(), s.getU1()), u1 = Mth.lerp(Math.min(1f, u + span), s.getU0(), s.getU1());
		float v0 = Mth.lerp(v, s.getV0(), s.getV1()), v1 = Mth.lerp(Math.min(1f, v + span), s.getV0(), s.getV1());
		float[][] uv = {{u0, v1}, {u1, v1}, {u1, v0}, {u0, v0}};
		for (int axis = 0; axis < 3; axis++) {
			for (int sign = -1; sign <= 1; sign += 2) {
				Vector3f n = new Vector3f(axis == 0 ? sign : 0, axis == 1 ? sign : 0, axis == 2 ? sign : 0);
				Vector3f a = new Vector3f(axis == 1 ? 1 : 0, axis == 1 ? 0 : 1, 0);
				if (axis == 2) a.set(1, 0, 0);
				Vector3f b = new Vector3f(n).cross(a);
				Vector3f[] q = new Vector3f[4];
				float[][] corners = {{-1, -1}, {1, -1}, {1, 1}, {-1, 1}};
				for (int k = 0; k < 4; k++) {
					Vector3f p = new Vector3f(n).add(new Vector3f(a).mul(corners[k][0])).add(new Vector3f(b).mul(corners[k][1]));
					p.mul(hx, hy, hz);
					if (turn != null) turn.transform(p);
					q[k] = p;
				}
				Vector3f nw = turn != null ? turn.transform(new Vector3f(n)) : n;
				for (int face = 0; face < 2; face++) {
					for (int k = 0; k < 4; k++) {
						int i = face == 0 ? k : 3 - k;
						float f = face == 0 ? 1 : -1;
						vertex(pose, vc, cam, (float) (m.x + q[i].x), (float) (m.y + q[i].y), (float) (m.z + q[i].z), uv[i][0], uv[i][1], c, alpha, light,
								nw.x * f, nw.y * f, nw.z * f);
					}
				}
			}
		}
	}

	static void vertex(PoseStack.Pose pose, VertexConsumer vc, Vec3 cam, float x, float y, float z, float u, float v, float[] c, float alpha,
			int light, float nx, float ny, float nz) {
		vc.addVertex(pose, (float) (x - cam.x), (float) (y - cam.y), (float) (z - cam.z))
				.setColor(c[0], c[1], c[2], Math.min(0.95f, alpha))
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(light)
				.setNormal(pose, nx, ny, nz);
	}

	/** The construct strip already carries the corps colour; green gets SuperLandConstruct's low jade. */
	static float[] tint(Corps corps) {
		return corps == Corps.GREEN ? new float[] {0.6f, 1f, 0.75f} : new float[] {1f, 1f, 1f};
	}

	static float[] bright(float[] c, float flare) {
		return new float[] {Mth.lerp(flare, c[0], 1f), Mth.lerp(flare, c[1], 1f), Mth.lerp(flare, c[2], 1f)};
	}

	private static float smooth(float t) {
		t = Mth.clamp(t, 0f, 1f);
		return t * t * (3 - 2 * t);
	}
}
