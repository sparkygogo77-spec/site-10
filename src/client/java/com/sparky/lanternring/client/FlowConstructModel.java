package com.sparky.lanternring.client;

import com.sparky.lanternring.ModRegistry;
import net.fabricmc.fabric.api.client.model.loading.v1.ModelLoadingPlugin;
import net.fabricmc.fabric.api.client.model.loading.v1.wrapper.WrapperBlockStateModel;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.MutableQuadView;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.QuadEmitter;
import net.minecraft.client.renderer.block.BlockAndTintGetter;
import net.minecraft.client.renderer.block.dispatch.BlockStateModel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;

import java.util.function.Predicate;

/**
 * Seamless construct surfaces. A texture whose name ends in "_flow" (the White Constructs pack)
 * covers PERIOD x PERIOD blocks, not one: each block face shows only its own slice of it, picked by
 * the block's position, so blocks side by side join into one unbroken surface (the texture also
 * wraps at its edges, so the slices continue past every PERIOD blocks).
 *
 * <p>How a face finds its slice: for each texture direction (u, then v) it finds the block axis
 * that direction runs along on this face and which way, then maps the face's corner from 0..1 of
 * the whole texture to (slice + corner) / PERIOD of it. Working this out from the quad itself
 * means it holds for every face and any rotation. Other textures are left exactly as they are.
 */
public final class FlowConstructModel extends WrapperBlockStateModel {
	public static final int PERIOD = 8;

	private final boolean flow;

	private FlowConstructModel(BlockStateModel wrapped) {
		super(wrapped);
		this.flow = wrapped.particleMaterial().sprite().contents().name().getPath().endsWith("_flow");
	}

	public static void register() {
		ModelLoadingPlugin.register(ctx -> ctx.modifyBlockModelAfterBake().register((model, c) ->
				c.state().is(ModRegistry.LIGHT_CONSTRUCT) || c.state().is(ModRegistry.CONSTRUCT_BRICK)
						? new FlowConstructModel(model) : model));
	}

	@Override
	public void emitQuads(QuadEmitter emitter, BlockAndTintGetter level, BlockPos pos, BlockState state,
			RandomSource random, Predicate<Direction> cullTest) {
		if (!flow) {
			super.emitQuads(emitter, level, pos, state, random, cullTest);
			return;
		}
		final int bx = pos.getX(), by = pos.getY(), bz = pos.getZ();
		emitter.pushTransform(q -> {
			slice(q, bx, by, bz, true);
			slice(q, bx, by, bz, false);
			return true;
		});
		super.emitQuads(emitter, level, pos, state, random, cullTest);
		emitter.popTransform();
	}

	/** Quads now depend on the block's position, so they must not be shared between positions. */
	@Override
	public Object createGeometryKey(BlockAndTintGetter level, BlockPos pos, BlockState state, RandomSource random) {
		return null;
	}

	private static void slice(MutableQuadView q, int bx, int by, int bz, boolean isU) {
		float lo = Float.MAX_VALUE, hi = -Float.MAX_VALUE;
		for (int i = 0; i < 4; i++) {
			float t = isU ? q.u(i) : q.v(i);
			lo = Math.min(lo, t);
			hi = Math.max(hi, t);
		}
		float span = hi - lo;
		if (span <= 1e-7f) return;
		int[] block = {bx, by, bz};
		for (int axis = 0; axis < 3; axis++) {
			for (int sign = 1; sign >= -1; sign -= 2) {
				boolean match = true;
				for (int i = 0; i < 4 && match; i++) {
					float t = ((isU ? q.u(i) : q.v(i)) - lo) / span;
					float p = q.posByIndex(i, axis);
					match = Math.abs((sign > 0 ? p : 1 - p) - t) < 1e-3f;
				}
				if (!match) continue;
				// Count blocks along this texture direction: forward with the axis, or backward against it.
				int cell = Mth.positiveModulo(sign > 0 ? block[axis] : -block[axis] - 1, PERIOD);
				for (int i = 0; i < 4; i++) {
					float p = q.posByIndex(i, axis);
					float f = (cell + (sign > 0 ? p : 1 - p)) / PERIOD;
					if (isU) q.uv(i, lo + span * f, q.v(i));
					else q.uv(i, q.u(i), lo + span * f);
				}
				return;
			}
		}
	}
}
