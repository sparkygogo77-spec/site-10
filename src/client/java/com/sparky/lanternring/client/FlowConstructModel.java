package com.sparky.lanternring.client;

import com.sparky.lanternring.ModRegistry;
import net.fabricmc.fabric.api.client.model.loading.v1.ModelLoadingPlugin;
import net.fabricmc.fabric.api.client.model.loading.v1.wrapper.WrapperBlockStateModel;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.MutableQuadView;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.QuadEmitter;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.client.renderer.block.dispatch.BlockStateModel;
import net.minecraft.client.renderer.block.dispatch.BlockStateModelPart;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.geometry.BakedQuad;
import net.minecraft.client.resources.model.sprite.Material;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;

/**
 * Construct blocks drawn from J's construct texture packs. What happens to each face depends on its
 * texture's name; anything else is left exactly as the model has it:
 * <ul>
 * <li>{@code construct_jade}: a sheet of the same jade six times, with a bright outline on 0 to 4
 *     sides (plain, edge, corner, strip, three, frame; 3 x 2 tiles). Each face shows the tile, turned,
 *     whose outlined sides are exactly the sides where the construct ends (no construct block next
 *     door that way), so outlines trace the construct's outer edges on every face.</li>
 * <li>{@code ..._flow} (PERIOD_FLOW blocks) and {@code construct_ripples...} / {@code construct_smoke}
 *     (PERIOD_LAYER blocks): one texture spread over several blocks; each face shows its own slice,
 *     picked by world position, so neighbouring blocks join into one surface. The ripple and smoke
 *     layers sit just outside the block; where a construct block is next door, a layer stops at the
 *     block's edge, so neighbouring layers meet instead of overlapping.</li>
 * </ul>
 * Each texture direction (u, then v) is matched to the block axis it runs along on that face, so it
 * holds for every face and any rotation.
 * <p>J's construct texture picks (ConstructLooks, chosen in the Ring Lab) swap in an animated strip: on
 * the jade model it replaces the ripples layer; on a plain construct model (classic glass and bricks)
 * it replaces the whole face. Either way it is sliced over PERIOD_LAYER blocks like the ripples.
 */
public final class FlowConstructModel extends WrapperBlockStateModel {
	public static final int PERIOD_FLOW = 8;
	public static final int PERIOD_LAYER = 4;

	private enum Kind { JADE, FLOW, LAYER }

	private record Region(float u0, float u1, float v0, float v1, Kind kind, boolean ripples) {
		boolean holds(float u, float v) {
			return u >= u0 - 1e-6f && u <= u1 + 1e-6f && v >= v0 - 1e-6f && v <= v1 + 1e-6f;
		}
	}

	private final List<Region> regions = new ArrayList<>();
	/** The model has a ripples layer (the jade pack's): a picked strip replaces just that layer. */
	private boolean hasRipples;

	private FlowConstructModel(BlockStateModel wrapped) {
		super(wrapped);
		List<BlockStateModelPart> parts = new ArrayList<>();
		wrapped.collectParts(RandomSource.create(0), parts);
		for (BlockStateModelPart part : parts) {
			for (Direction d : DIRS_AND_NULL) {
				for (BakedQuad quad : part.getQuads(d)) remember(quad.materialInfo().sprite());
			}
		}
	}

	private static final Direction[] DIRS_AND_NULL = {Direction.DOWN, Direction.UP, Direction.NORTH, Direction.SOUTH,
			Direction.WEST, Direction.EAST, null};

	private void remember(TextureAtlasSprite sprite) {
		String name = sprite.contents().name().getPath();
		Kind kind = name.endsWith("construct_jade") ? Kind.JADE
				: name.endsWith("_flow") ? Kind.FLOW
				: name.contains("construct_ripples") || name.endsWith("construct_smoke") ? Kind.LAYER : null;
		if (kind == null) return;
		for (Region r : regions) if (r.u0 == sprite.getU0() && r.v0 == sprite.getV0()) return;
		boolean ripples = name.contains("construct_ripples");
		regions.add(new Region(sprite.getU0(), sprite.getU1(), sprite.getV0(), sprite.getV1(), kind, ripples));
		hasRipples |= ripples;
	}

	public static void register() {
		ModelLoadingPlugin.register(ctx -> ctx.modifyBlockModelAfterBake().register((model, c) ->
				isConstruct(c.state()) ? new FlowConstructModel(model) : model));
	}

	private static boolean isConstruct(BlockState s) {
		return s.is(ModRegistry.LIGHT_CONSTRUCT) || s.is(ModRegistry.CONSTRUCT_BRICK);
	}

	@Override
	public void emitQuads(QuadEmitter emitter, BlockAndTintGetter level, BlockPos pos, BlockState state,
			RandomSource random, Predicate<Direction> cullTest) {
		TextureAtlasSprite strip = ConstructLooks.sprite(state);
		final int alpha = ConstructLooks.alpha() << 24 | 0xFFFFFF;
		final BlockPos at = pos.immutable();
		emitter.pushTransform(q -> {
			Region r = regionOf(q);
			if (strip != null && r == null && !hasRipples) {
				face(q, strip, at);
			} else if (strip != null && r != null && !r.ripples) {
				// A picked strip stands alone, as on the Blue constructs: the jade core and smoke under it
				// made the green ones read solid (J: match the Blue hex Dome's see-through).
				return false;
			} else if (r != null) {
				apply(q, r, level, at, strip != null && r.ripples ? strip : null);
			}
			// J: constructs see-through (Ring Lab "Construct opacity", half by default)
			for (int i = 0; i < 4; i++) q.color(i, alpha);
			return true;
		});
		super.emitQuads(emitter, level, pos, state, random, cullTest);
		emitter.popTransform();
	}

	/** Quads depend on the block's position and neighbours, so they must not be shared. */
	@Override
	public Object createGeometryKey(BlockAndTintGetter level, BlockPos pos, BlockState state, RandomSource random) {
		return null;
	}

	private Region regionOf(MutableQuadView q) {
		float u = 0, v = 0;
		for (int i = 0; i < 4; i++) { u += q.u(i) / 4; v += q.v(i) / 4; }
		for (Region r : regions) if (r.holds(u, v)) return r;
		return null;
	}

	/** For texture direction u (or v): the block axis it runs along on this quad and which way (+1 / -1), or null. */
	private static int[] axisOf(MutableQuadView q, Region r, boolean isU) {
		float lo = isU ? r.u0 : r.v0, span = isU ? r.u1 - r.u0 : r.v1 - r.v0;
		float tmin = Float.MAX_VALUE, tmax = -Float.MAX_VALUE;
		float[] t = new float[4];
		for (int i = 0; i < 4; i++) {
			t[i] = ((isU ? q.u(i) : q.v(i)) - lo) / span;
			tmin = Math.min(tmin, t[i]); tmax = Math.max(tmax, t[i]);
		}
		if (tmax - tmin < 1e-4f) return null;
		for (int axis = 0; axis < 3; axis++) {
			float pmin = Float.MAX_VALUE, pmax = -Float.MAX_VALUE;
			for (int i = 0; i < 4; i++) { float p = q.posByIndex(i, axis); pmin = Math.min(pmin, p); pmax = Math.max(pmax, p); }
			if (pmax - pmin < 1e-4f) continue;
			for (int sign = 1; sign >= -1; sign -= 2) {
				boolean match = true;
				for (int i = 0; i < 4 && match; i++) {
					float pn = (q.posByIndex(i, axis) - pmin) / (pmax - pmin);
					float tn = (t[i] - tmin) / (tmax - tmin);
					match = Math.abs((sign > 0 ? pn : 1 - pn) - tn) < 1e-3f;
				}
				if (match) return new int[] {axis, sign};
			}
		}
		return null;
	}

	private static boolean constructAt(BlockAndTintGetter level, BlockPos pos, int axis, int step) {
		return isConstruct(level.getBlockState(pos.relative(Direction.fromAxisAndDirection(
				Direction.Axis.values()[axis], step > 0 ? Direction.AxisDirection.POSITIVE : Direction.AxisDirection.NEGATIVE))));
	}

	/** A plain construct face showing a picked strip, sliced by world position (u and v along fixed block axes). */
	private static void face(MutableQuadView q, TextureAtlasSprite strip, BlockPos pos) {
		Direction d = q.nominalFace();
		if (d == null) return;
		int[] ua, va;
		switch (d.getAxis()) {
			case X -> { ua = new int[] {2, 1}; va = new int[] {1, -1}; }
			case Y -> { ua = new int[] {0, 1}; va = new int[] {2, 1}; }
			default -> { ua = new int[] {0, 1}; va = new int[] {1, -1}; }
		}
		int[] block = {pos.getX(), pos.getY(), pos.getZ()};
		for (int i = 0; i < 4; i++) {
			q.uv(i, slice(q, i, ua, block, PERIOD_LAYER, strip.getU0(), strip.getU1()),
					slice(q, i, va, block, PERIOD_LAYER, strip.getV0(), strip.getV1()));
		}
		q.postMaterialBake(new Material.Baked(strip, true));
	}

	private static void apply(MutableQuadView q, Region r, BlockAndTintGetter level, BlockPos pos, TextureAtlasSprite strip) {
		int[] ua = axisOf(q, r, true), va = axisOf(q, r, false);
		if (ua == null || va == null) return;
		if (r.kind == Kind.JADE) {
			jade(q, r, level, pos, ua, va);
			return;
		}
		int[] block = {pos.getX(), pos.getY(), pos.getZ()};
		if (r.kind == Kind.LAYER) {
			// stop the layer at the block's edge wherever another construct block carries on
			for (int i = 0; i < 4; i++) {
				for (int[] a : new int[][] {ua, va}) {
					float p = q.posByIndex(i, a[0]);
					if (p < 0 && constructAt(level, pos, a[0], -1)) p = 0;
					if (p > 1 && constructAt(level, pos, a[0], 1)) p = 1;
					setPos(q, i, a[0], p);
				}
			}
		}
		int period = r.kind == Kind.FLOW ? PERIOD_FLOW : PERIOD_LAYER;
		// a picked strip takes the ripples layer's place
		float u0 = strip != null ? strip.getU0() : r.u0, u1 = strip != null ? strip.getU1() : r.u1;
		float v0 = strip != null ? strip.getV0() : r.v0, v1 = strip != null ? strip.getV1() : r.v1;
		for (int i = 0; i < 4; i++) {
			float u = slice(q, i, ua, block, period, u0, u1);
			float v = slice(q, i, va, block, period, v0, v1);
			q.uv(i, u, v);
		}
		if (strip != null) q.postMaterialBake(new Material.Baked(strip, true));
	}

	private static float slice(MutableQuadView q, int i, int[] a, int[] block, int period, float lo, float hi) {
		float p = Mth.clamp(q.posByIndex(i, a[0]), 0f, 1f);
		int cell = Mth.positiveModulo(a[1] > 0 ? block[a[0]] : -block[a[0]] - 1, period);
		float f = (cell + (a[1] > 0 ? p : 1 - p)) / period;
		return lo + (hi - lo) * f;
	}

	private static void setPos(MutableQuadView q, int i, int axis, float p) {
		float x = q.x(i), y = q.y(i), z = q.z(i);
		if (axis == 0) x = p; else if (axis == 1) y = p; else z = p;
		((QuadEmitter) q).pos(i, x, y, z);
	}

	// ---- jade: the outline tile and its turn ---------------------------------------------------------
	// sides as bits: L (u = 0) 1, T (v = 0) 2, R (u = 1) 4, B (v = 1) 8; tiles in the sheet's order
	private static final int[] TILE_SIDES = {0, 1, 1 | 2, 1 | 4, 1 | 2 | 4, 15};

	private static int turnCw(int sides) {   // the picture turned a quarter clockwise: L->T->R->B->L
		return ((sides << 1) | (sides >> 3)) & 15;
	}

	private static void jade(MutableQuadView q, Region r, BlockAndTintGetter level, BlockPos pos, int[] ua, int[] va) {
		// where each side of the picture faces: u = 0 lies toward -sign of u's axis, v = 0 likewise
		int mask = 0;
		if (!constructAt(level, pos, ua[0], -ua[1])) mask |= 1;   // L
		if (!constructAt(level, pos, va[0], -va[1])) mask |= 2;   // T
		if (!constructAt(level, pos, ua[0], ua[1])) mask |= 4;    // R
		if (!constructAt(level, pos, va[0], va[1])) mask |= 8;    // B
		int tile = 0, turns = 0;
		search:
		for (int k = 0; k < TILE_SIDES.length; k++) {
			int s = TILE_SIDES[k];
			for (int t = 0; t < 4; t++) {
				if (s == mask) { tile = k; turns = t; break search; }
				s = turnCw(s);
			}
		}
		int col = tile % 3, row = tile / 3;
		float du = r.u1 - r.u0, dv = r.v1 - r.v0;
		for (int i = 0; i < 4; i++) {
			float x = (q.u(i) - r.u0) / du, y = (q.v(i) - r.v0) / dv;
			x = Math.round(x); y = Math.round(y);               // the face's own corner, 0 or 1
			for (int t = 0; t < turns; t++) { float nx = y, ny = 1 - x; x = nx; y = ny; }
			x = Mth.clamp(x, 0.002f, 0.998f); y = Mth.clamp(y, 0.002f, 0.998f);
			q.uv(i, r.u0 + du * (col + x) / 3f, r.v0 + dv * (row + y) / 2f);
		}
	}
}
