package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.block.GhostMimicBlockEntity;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.builders.UVPair;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.BlockStateModelSet;
import net.minecraft.client.renderer.block.dispatch.BlockStateModelPart;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderers;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.model.geometry.BakedQuad;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3fc;

/**
 * Draws a GhostMimicBlock as its real block in hard light: the block's own model (every quad of
 * it, so flowers, crops, grass, leaves, stairs and torches keep their exact look) washed in the
 * ring's colour, see-through and glowing. Blocks drawn by a special renderer (chests, beds, signs)
 * have no model quads; they get their shape in boxes with their own texture instead.
 */
public class GhostMimicRenderer implements BlockEntityRenderer<GhostMimicBlockEntity, GhostMimicRenderer.State> {
	private static final int FULL_BRIGHT = 0xF000F0;
	private static final int ALPHA = 0xB4;
	private static final RenderType TYPE = RenderTypes.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS);

	private record Quad(float[] xyz, float[] uv, Direction face) {
	}

	private static final Map<BlockState, List<Quad>> CACHE = new HashMap<>();
	private static BlockStateModelSet cachedFor;

	public static class State extends BlockEntityRenderState {
		BlockState real;
		int color;
	}

	public static void register() {
		BlockEntityRenderers.register(ModRegistry.GHOST_MIMIC_ENTITY, ctx -> new GhostMimicRenderer());
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(GhostMimicBlockEntity mimic, State state, float partialTick, Vec3 camera,
			ModelFeatureRenderer.CrumblingOverlay breaking) {
		BlockEntityRenderer.super.extractRenderState(mimic, state, partialTick, camera, breaking);
		state.real = mimic.real();
		BlockState own = mimic.getBlockState();
		Corps corps = own.hasProperty(Corps.PROPERTY) ? own.getValue(Corps.PROPERTY) : Corps.GREEN;
		// Mostly the corps' colour, with enough white left that the block's own texture shows through.
		int rgb = corps.rgb;
		int r = 120 + ((rgb >> 16) & 0xFF) * 135 / 255, g = 120 + ((rgb >> 8) & 0xFF) * 135 / 255, b = 120 + (rgb & 0xFF) * 135 / 255;
		state.color = r << 16 | g << 8 | b;
	}

	@Override
	public void submit(State state, PoseStack pose, SubmitNodeCollector collector, CameraRenderState camera) {
		if (state.real == null || state.real.isAir()) return;
		List<Quad> quads = quads(state.real);
		if (quads.isEmpty()) return;
		int color = state.color;
		collector.submitCustomGeometry(pose, TYPE, (p, vc) -> {
			for (Quad q : quads) put(p, vc, q, color);
		});
	}

	private static void put(PoseStack.Pose pose, VertexConsumer vc, Quad q, int rgb) {
		// A little shading by side so the shape reads, as the world's own blocks have.
		float shade = q.face == null ? 0.9f : switch (q.face) {
			case UP -> 1f;
			case DOWN -> 0.55f;
			case NORTH, SOUTH -> 0.82f;
			default -> 0.68f;
		};
		int r = (int) (((rgb >> 16) & 0xFF) * shade), g = (int) (((rgb >> 8) & 0xFF) * shade), b = (int) ((rgb & 0xFF) * shade);
		int argb = ALPHA << 24 | r << 16 | g << 8 | b;
		Direction n = q.face == null ? Direction.UP : q.face;
		for (int i = 0; i < 4; i++) {
			vc.addVertex(pose, q.xyz[i * 3], q.xyz[i * 3 + 1], q.xyz[i * 3 + 2]).setColor(argb).setUv(q.uv[i * 2], q.uv[i * 2 + 1])
					.setOverlay(OverlayTexture.NO_OVERLAY).setLight(FULL_BRIGHT).setNormal(pose, n.getStepX(), n.getStepY(), n.getStepZ());
		}
	}

	/** Every quad of the block's model, worked out once per block state (and again after a resource reload). */
	private static List<Quad> quads(BlockState real) {
		BlockStateModelSet models = Minecraft.getInstance().getModelManager().getBlockStateModelSet();
		if (models != cachedFor) {
			CACHE.clear();
			cachedFor = models;
		}
		return CACHE.computeIfAbsent(real, s -> build(models, s));
	}

	private static List<Quad> build(BlockStateModelSet models, BlockState real) {
		List<Quad> out = new ArrayList<>();
		try {
			List<BlockStateModelPart> parts = new ArrayList<>();
			models.get(real).collectParts(RandomSource.create(42L), parts);
			for (BlockStateModelPart part : parts) {
				add(out, part.getQuads(null));
				for (Direction d : Direction.values()) add(out, part.getQuads(d));
			}
		} catch (RuntimeException e) {
			out.clear();
		}
		if (out.isEmpty()) boxes(out, models, real);
		return out;
	}

	private static void add(List<Quad> out, List<BakedQuad> quads) {
		for (BakedQuad q : quads) {
			float[] xyz = new float[12], uv = new float[8];
			for (int i = 0; i < 4; i++) {
				Vector3fc v = q.position(i);
				xyz[i * 3] = v.x();
				xyz[i * 3 + 1] = v.y();
				xyz[i * 3 + 2] = v.z();
				long packed = q.packedUV(i);
				uv[i * 2] = UVPair.unpackU(packed);
				uv[i * 2 + 1] = UVPair.unpackV(packed);
			}
			out.add(new Quad(xyz, uv, q.direction()));
		}
	}

	/** For blocks without model quads: their shape as boxes, each side showing the block's particle texture. */
	private static void boxes(List<Quad> out, BlockStateModelSet models, BlockState real) {
		TextureAtlasSprite sprite;
		try {
			sprite = models.getParticleMaterial(real).sprite();
		} catch (RuntimeException e) {
			return;
		}
		for (AABB box : real.getShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO).toAabbs()) {
			float x0 = (float) box.minX, y0 = (float) box.minY, z0 = (float) box.minZ, x1 = (float) box.maxX, y1 = (float) box.maxY, z1 = (float) box.maxZ;
			face(out, sprite, Direction.UP, x0, y1, z0, x0, y1, z1, x1, y1, z1, x1, y1, z0);
			face(out, sprite, Direction.DOWN, x0, y0, z1, x0, y0, z0, x1, y0, z0, x1, y0, z1);
			face(out, sprite, Direction.NORTH, x1, y1, z0, x1, y0, z0, x0, y0, z0, x0, y1, z0);
			face(out, sprite, Direction.SOUTH, x0, y1, z1, x0, y0, z1, x1, y0, z1, x1, y1, z1);
			face(out, sprite, Direction.WEST, x0, y1, z0, x0, y0, z0, x0, y0, z1, x0, y1, z1);
			face(out, sprite, Direction.EAST, x1, y1, z1, x1, y0, z1, x1, y0, z0, x1, y1, z0);
		}
	}

	private static void face(List<Quad> out, TextureAtlasSprite s, Direction d, float... xyz) {
		float[] uv = {s.getU0(), s.getV0(), s.getU0(), s.getV1(), s.getU1(), s.getV1(), s.getU1(), s.getV0()};
		out.add(new Quad(xyz, uv, d));
	}

	@Override
	public boolean shouldRenderOffScreen() {
		return false;
	}
}
