package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.SuperJumps;
import com.sparky.lanternring.net.RingFxPayload;
import com.sparky.lanternring.net.CraterLiningPayload;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.data.AtlasIds;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The hard-light construct a super jump lands on (J's Blender picks, 2026-10-13; server side:
 * SuperJumps). J (2026-10-13, after playing it): the crater of everything the landing destroyed is
 * lined with the construct pad, every face of every block round it fully covered, and nothing
 * else; every landing's crater, the Hammer's too. The server sends the blasted blocks
 * (CraterLiningPayload) and each face of a block left
 * standing against them gets a 3 px plate, switching on and flaring as the impact reaches it.
 * With no crater (on water, or Super crater set to primed only) a pad lies under the jumper
 * instead, with the low wall (Ring Lab Super wall) round its edge, or the tall guard walls on a
 * deeper fall than meant. After the stand-up every piece dissolves
 * at its own moment, like a dismissed construct (DismissFx); the crater stays. The plates take the
 * Construct look row's texture and the walls the Wall look row's, in a low jade glow.
 */
public final class SuperLandConstruct {
	private static final Identifier DISSOLVE = LanternRing.id("textures/entity/construct_dissolve.png");
	private static final int DISSOLVE_FRAMES = 16;
	private static final float DISSOLVE_TICKS = 14;
	/** The pad's radius: normal, on water, and on the deeper fall. */
	private static final double PAD = 1.6, PAD_WATER = 2.2, PAD_DEEP = 2.3;
	/** Plates are 3 px thick; each switches on at its distance x this many ticks. */
	private static final float PLATE = 3 / 16f, WAVE = 0.8f;
	/** Ticks a plate flares as it forms, the low wall takes to rise, and the guard walls (with their overshoot). */
	private static final float FLARE = 4f, WALL_RISE = 4f, GUARD_RISE = 7f;
	private static final float GUARD_HIGH = 2.6f, GUARD_THICK = 3 / 16f, GUARD_OVERSHOOT = 0.12f;
	/** About 70% opaque (the brief's low jade glow). */
	private static final float ALPHA = 0.7f;
	/** How long the floor under a piece keeps being looked up (the crater's blocks may arrive just after the landing). */
	private static final int SETTLE = 4;

	private enum Kind { PAD, WALL, GUARD, LINING }

	/** The last crater each jumper's landing blasted (bearer id), waiting for its SUPER_LAND. */
	private record Crater(Set<BlockPos> blocks, long at) {
	}

	private static final Int2ObjectMap<Crater> CRATERS = new Int2ObjectOpenHashMap<>();

	private static final class Piece {
		final Kind kind;
		final int x, z;
		/** For a wall: the side of its column it stands on. */
		final Direction side;
		final float delay, fadeAt;
		double floor = Double.NaN;
		/** A lining plate's box (x0, y0, z0, x1, y1, z1); null for the others, which sit on the floor. */
		float @Nullable [] box;

		Piece(Kind kind, int x, int z, Direction side, float delay, float fadeAt) {
			this.kind = kind;
			this.x = x;
			this.z = z;
			this.side = side;
			this.delay = delay;
			this.fadeAt = fadeAt;
		}
	}

	private static final class Landing {
		final Corps corps;
		final Vec3 at;
		final long start;
		final List<Piece> pieces = new ArrayList<>();
		float end;

		Landing(Corps corps, Vec3 at, long start) {
			this.corps = corps;
			this.at = at;
			this.start = start;
		}
	}

	private static final List<Landing> LANDINGS = new ArrayList<>();

	private SuperLandConstruct() {
	}

	/** A crater to line: a super jump's waits for its SUPER_LAND (hold 0); any other landing's is lined now. */
	static void crater(CraterLiningPayload payload) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Set<BlockPos> blocks = new HashSet<>(payload.blocks());
		if (payload.hold() <= 0) CRATERS.put(payload.bearer(), new Crater(blocks, mc.level.getGameTime()));
		else line(mc.level, payload.corps(), payload.centre(), blocks, payload.hold(), false);
	}

	/** SUPER_LAND, while LabFx has the jumper's corps current. */
	static void land(RingFxPayload fx) {
		Minecraft mc = Minecraft.getInstance();
		ClientLevel level = mc.level;
		if (level == null) return;
		boolean deep = (fx.variant() & SuperJumps.DEEP_BIT) != 0;
		Vec3 at = fx.from();
		Crater crater = CRATERS.remove(fx.bearer());
		if (crater != null && Math.abs(level.getGameTime() - crater.at) < 40 && !crater.blocks.isEmpty()) {
			line(level, CorpsTint.current(), at, crater.blocks, SuperJumpPoses.landingTicks(deep), deep);
			return;
		}
		BlockPos feet = BlockPos.containing(at.x, at.y + 0.2, at.z);
		boolean water = !level.getFluidState(feet).isEmpty() || !level.getFluidState(feet.below()).isEmpty();
		double radius = deep ? PAD_DEEP : water ? PAD_WATER : PAD;
		LabSettings.SuperWall wall = LabSettings.get().superWall;
		Landing landing = new Landing(CorpsTint.current(), at, level.getGameTime());
		RandomSource r = level.getRandom();
		float standUp = SuperJumpPoses.landingTicks(deep);
		int bx = feet.getX(), bz = feet.getZ(), reach = (int) Math.ceil(radius) + 1;
		for (int dx = -reach; dx <= reach; dx++) {
			for (int dz = -reach; dz <= reach; dz++) {
				int x = bx + dx, z = bz + dz;
				double d = distance(at, x, z);
				if (!inside(at, radius, x, z, bx, bz)) continue;
				landing.pieces.add(new Piece(Kind.PAD, x, z, Direction.UP, (float) d * WAVE, fade(r, standUp, deep)));
				if (!deep && wall == LabSettings.SuperWall.OFF) continue;
				for (Direction side : Direction.Plane.HORIZONTAL) {
					if (inside(at, radius, x + side.getStepX(), z + side.getStepZ(), bx, bz)) continue;
					landing.pieces.add(new Piece(deep ? Kind.GUARD : Kind.WALL, x, z, side, (float) d * WAVE, fade(r, standUp, deep)));
				}
			}
		}
		for (Piece p : landing.pieces) landing.end = Math.max(landing.end, p.fadeAt + DISSOLVE_TICKS);
		LANDINGS.add(landing);
	}

	/** Lines the crater: a plate on every face of a block left standing against a blasted one, and nothing more. */
	private static void line(ClientLevel level, Corps corps, Vec3 at, Set<BlockPos> blasted, float standUp, boolean deep) {
		Landing landing = new Landing(corps, at, level.getGameTime());
		RandomSource r = level.getRandom();
		for (BlockPos cell : blasted) {
			double dx = cell.getX() + 0.5 - at.x, dy = cell.getY() + 0.5 - at.y, dz = cell.getZ() + 0.5 - at.z;
			float delay = (float) Math.sqrt(dx * dx + dy * dy + dz * dz) * WAVE;
			for (Direction face : Direction.values()) {
				BlockPos wall = cell.relative(face);
				if (blasted.contains(wall) || level.getBlockState(wall).getCollisionShape(level, wall).isEmpty()) continue;
				Piece p = new Piece(Kind.LINING, cell.getX(), cell.getZ(), face, delay, fade(r, standUp, deep));
				p.floor = cell.getY();
				p.box = plate(cell, face);
				landing.pieces.add(p);
			}
		}
		for (Piece p : landing.pieces) landing.end = Math.max(landing.end, p.fadeAt + DISSOLVE_TICKS);
		if (!landing.pieces.isEmpty()) LANDINGS.add(landing);
	}

	/** A 3 px plate filling the side of the cell that faces the solid block across face. */
	private static float[] plate(BlockPos cell, Direction face) {
		float[] b = {cell.getX(), cell.getY(), cell.getZ(), cell.getX() + 1, cell.getY() + 1, cell.getZ() + 1};
		int axis = face.getAxis().ordinal();
		if (face.getAxisDirection() == Direction.AxisDirection.POSITIVE) b[axis] = b[axis + 3] - PLATE;
		else b[axis + 3] = b[axis] + PLATE;
		return b;
	}

	/** When a piece starts to dissolve, in ticks after the landing: at its own moment after the stand-up. */
	private static float fade(RandomSource r, float standUp, boolean deep) {
		return standUp + (deep ? 6 + r.nextFloat() * 14 : 4 + r.nextFloat() * 12);
	}

	private static double distance(Vec3 at, int x, int z) {
		double dx = x + 0.5 - at.x, dz = z + 0.5 - at.z;
		return Math.sqrt(dx * dx + dz * dz);
	}

	private static boolean inside(Vec3 at, double radius, int x, int z, int bx, int bz) {
		return x == bx && z == bz || distance(at, x, z) <= radius;
	}

	static void tick(Minecraft mc) {
		ClientLevel level = mc.level;
		if (level == null) {
			LANDINGS.clear();
			return;
		}
		long now = level.getGameTime();
		LANDINGS.removeIf(l -> now - l.start > l.end || now < l.start - 20);
		for (Landing l : LANDINGS) {
			if (now - l.start > SETTLE + 2) continue;
			for (Piece p : l.pieces) {
				if (p.box == null) p.floor = floor(level, l.at, p.x, p.z);
			}
		}
		CRATERS.int2ObjectEntrySet().removeIf(e -> Math.abs(now - e.getValue().at) > 40);
	}

	/** The top of what the column stands on near the landing: solid ground, or the water's surface. */
	private static double floor(ClientLevel level, Vec3 at, int x, int z) {
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		int top = Mth.floor(at.y) + 1;
		for (int y = top; y >= top - 8; y--) {
			pos.set(x, y, z);
			var fluid = level.getFluidState(pos);
			if (!fluid.isEmpty()) return y + fluid.getHeight(level, pos);
			BlockState state = level.getBlockState(pos);
			var shape = state.getCollisionShape(level, pos);
			if (!shape.isEmpty()) return y + shape.max(Direction.Axis.Y);
		}
		return Double.NaN;
	}

	public static void render(LevelRenderContext ctx) {
		if (LANDINGS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float now = mc.level.getGameTime() + ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS), (pose, vc) -> {
			for (Landing l : LANDINGS) {
				TextureAtlasSprite pad = sprite(ModRegistry.LIGHT_CONSTRUCT, l.corps), brick = sprite(ModRegistry.CONSTRUCT_BRICK, l.corps);
				float[] tint = l.corps == Corps.GREEN ? new float[] {0.6f, 1f, 0.75f} : new float[] {1f, 1f, 1f};
				for (Piece p : l.pieces) {
					float age = now - l.start - p.delay;
					if (age < 0 || Double.isNaN(p.floor) || now - l.start >= p.fadeAt) continue;
					float flare = Math.max(0f, 1f - age / FLARE);
					float[] c = {Mth.lerp(flare * 0.5f, tint[0], 1f), Mth.lerp(flare * 0.5f, tint[1], 1f), Mth.lerp(flare * 0.5f, tint[2], 1f)};
					float[] box = shape(p, age);
					if (box == null) continue;
					Uv uv = atlas(p.kind == Kind.PAD || p.kind == Kind.LINING ? pad : brick);
					box(pose, vc, box, cam, uv, c, ALPHA, ShaderGlow.light(0.5f + 0.5f * flare));
				}
			}
		});
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(DISSOLVE), (pose, vc) -> {
			for (Landing l : LANDINGS) {
				float[] tint = CorpsTint.apply(l.corps, 0.45f, 1f, 0.65f);
				for (Piece p : l.pieces) {
					float t = (now - l.start - p.fadeAt) / DISSOLVE_TICKS;
					if (t < 0 || t >= 1 || Double.isNaN(p.floor)) continue;
					float[] box = shape(p, now - l.start - p.delay);
					if (box == null) continue;
					int frame = Math.min(DISSOLVE_FRAMES - 1, (int) (t * DISSOLVE_FRAMES));
					float v0 = frame / (float) DISSOLVE_FRAMES, v1 = (frame + 1) / (float) DISSOLVE_FRAMES;
					box(pose, vc, box, cam, (axis, a, b, a0, b0) -> new float[] {a - a0, Mth.lerp(b - b0, v0, v1)}, tint, 0.9f, ShaderGlow.light(0.6f));
				}
			}
		});
	}

	/** A piece's box now (x0, y0, z0, x1, y1, z1), or null while it has no height yet. */
	private static float[] shape(Piece p, float age) {
		if (p.box != null) return p.box;
		double y = p.floor;
		if (p.kind == Kind.PAD) return new float[] {p.x, (float) y + 0.002f, p.z, p.x + 1, (float) y + PLATE, p.z + 1};
		float thick, high;
		if (p.kind == Kind.GUARD) {
			thick = GUARD_THICK;
			float s = age / GUARD_RISE, over = GUARD_OVERSHOOT / GUARD_HIGH;
			float f = s < 0.7f ? (1 + over) * smooth(s / 0.7f) : 1 + over * (1 - smooth((s - 0.7f) / 0.3f));
			high = GUARD_HIGH * f;
		} else {
			LabSettings.SuperWall w = LabSettings.get().superWall;
			if (w == LabSettings.SuperWall.OFF) return null;
			thick = w.thick / 16f;
			high = w.high / 16f * smooth(age / WALL_RISE);
		}
		if (high < 0.01f) return null;
		float x0 = p.x, x1 = p.x + 1, z0 = p.z, z1 = p.z + 1;
		switch (p.side) {
			case EAST -> x0 = x1 - thick;
			case WEST -> x1 = x0 + thick;
			case SOUTH -> z0 = z1 - thick;
			default -> z1 = z0 + thick;
		}
		return new float[] {x0, (float) y, z0, x1, (float) y + high, z1};
	}

	/** The look row's strip for this construct block in the jumper's corps (W1 neon if the pick has none). */
	private static TextureAtlasSprite sprite(Block block, Corps corps) {
		BlockState state = block.defaultBlockState();
		if (state.hasProperty(Corps.PROPERTY)) state = state.setValue(Corps.PROPERTY, corps);
		TextureAtlasSprite s = ConstructLooks.displaySprite(state);
		if (s != null) return s;
		TextureAtlas atlas = Minecraft.getInstance().getAtlasManager().getAtlasOrThrow(AtlasIds.BLOCKS);
		return atlas.getSprite(LanternRing.id("block/construct_ripples_w1_neon"));
	}

	/** UV for a point on a face: axis is the face's normal axis, a and b the point's in-plane coordinates, a0 and b0 the face's corner. */
	private interface Uv {
		float[] at(int axis, float a, float b, float a0, float b0);
	}

	/** The strip laid over 4 x 4 blocks by world position, like the placed constructs (FlowConstructModel). */
	private static Uv atlas(TextureAtlasSprite s) {
		return (axis, a, b, a0, b0) -> {
			float ca = (Math.floorMod(Mth.floor(a0), 4) + Mth.clamp(a - a0, 0f, 1f)) / 4f;
			float cb = (Math.floorMod(Mth.floor(b0), 4) + Mth.clamp(b - b0, 0f, 1f)) / 4f;
			if (axis != 1) cb = 1 - cb;
			return new float[] {Mth.lerp(ca, s.getU0(), s.getU1()), Mth.lerp(cb, s.getV0(), s.getV1())};
		};
	}

	/** A box, every face both ways round; tall sides are cut into one-block bands so the texture isn't stretched. */
	private static void box(PoseStack.Pose pose, VertexConsumer vc, float[] b, Vec3 cam, Uv uv, float[] c, float alpha, int light) {
		float[] lo = {b[0], b[1], b[2]}, hi = {b[3], b[4], b[5]};
		for (int axis = 0; axis < 3; axis++) {
			int ua = axis == 0 ? 2 : 0, va = axis == 1 ? 2 : 1;
			for (int sign = -1; sign <= 1; sign += 2) {
				float plane = sign > 0 ? hi[axis] : lo[axis];
				for (float v0 = lo[va]; v0 < hi[va] - 1e-4f; v0 += 1f) {
					float v1 = Math.min(hi[va], v0 + 1f);
					float[][] corners = {{lo[ua], v0}, {hi[ua], v0}, {hi[ua], v1}, {lo[ua], v1}};
					for (int side = 0; side < 2; side++) {
						for (int k = 0; k < 4; k++) {
							float[] q = corners[side == 0 ? k : 3 - k];
							float[] p = new float[3];
							p[axis] = plane;
							p[ua] = q[0];
							p[va] = q[1];
							float[] t = uv.at(axis, q[0], q[1], lo[ua], v0);
							float n = side == 0 ? sign : -sign;
							vc.addVertex(pose, (float) (p[0] - cam.x), (float) (p[1] - cam.y), (float) (p[2] - cam.z))
									.setColor(c[0], c[1], c[2], alpha)
									.setUv(t[0], t[1])
									.setOverlay(OverlayTexture.NO_OVERLAY)
									.setLight(light)
									.setNormal(pose, axis == 0 ? n : 0, axis == 1 ? n : 0, axis == 2 ? n : 0);
						}
					}
				}
			}
		}
	}

	private static float smooth(float t) {
		t = Mth.clamp(t, 0f, 1f);
		return t * t * (3 - 2 * t);
	}
}
