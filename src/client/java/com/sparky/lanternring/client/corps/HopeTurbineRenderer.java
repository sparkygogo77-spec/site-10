package com.sparky.lanternring.client.corps;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.client.ShaderGlow;
import com.sparky.lanternring.corps.HopeSanctuary;
import com.sparky.lanternring.corps.HopeTurbine;
import com.sparky.lanternring.designs.BlockPlan;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.BlockModelResolver;
import net.minecraft.client.renderer.block.model.BlockDisplayContext;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

/**
 * Draws the Hope sanctuary's turbine and the Hope mark through its hub from the sanctuary's block
 * plan, turning about the entity once every {@link HopeTurbine#TURN_TICKS} ticks. The quartz takes
 * the light where it is; the construct brick, lamps and mark glow.
 */
public class HopeTurbineRenderer extends EntityRenderer<HopeTurbine, HopeTurbineRenderer.State> {

	public static class State extends EntityRenderState {
		float angle;
	}

	private record Block(float x, float y, float z, BlockState state) {
	}

	private final BlockModelResolver resolver;
	private final List<Block> blocks = new ArrayList<>();
	private final Map<BlockState, BlockModelRenderState> models = new IdentityHashMap<>();

	public HopeTurbineRenderer(EntityRendererProvider.Context context) {
		super(context);
		resolver = context.getBlockModelResolver();
		BlockPlan plan = BlockPlan.get(HopeSanctuary.PLAN);
		for (String part : HopeSanctuary.TURBINE_PARTS) {
			for (BlockPlan.Entry e : plan.part(part).blocks()) {
				blocks.add(new Block(e.x(), e.y() - HopeSanctuary.TURBINE_Y, e.z(), e.state()));
			}
		}
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(HopeTurbine entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.angle = HopeTurbine.angle(entity.level().getGameTime(), partialTicks);
		// Each block kind's model, resolved afresh every frame like a block display's.
		for (Block b : blocks) {
			if (!models.containsKey(b.state)) models.put(b.state, new BlockModelRenderState());
		}
		models.forEach((blockState, m) -> resolver.update(m, blockState, BlockDisplayContext.create()));
	}

	@Override
	protected AABB getBoundingBoxForCulling(HopeTurbine entity, float partialTicks) {
		return entity.getBoundingBox().inflate(11, 14, 11).move(0, 6, 0);
	}

	@Override
	public void submit(State state, PoseStack pose, SubmitNodeCollector collector, CameraRenderState camera) {
		pose.pushPose();
		pose.rotateDegrees(Axis.YP, state.angle);
		int glow = ShaderGlow.light(1f);
		for (Block b : blocks) {
			BlockModelRenderState m = models.get(b.state);
			if (m == null || m.isEmpty()) continue;
			pose.pushPose();
			pose.translate(b.x, b.y, b.z);
			boolean bright = !b.state.is(com.sparky.lanternring.city.CityBlocks.HOPE_QUARTZ_BRICKS);
			m.submit(pose, collector, bright ? glow : state.lightCoords, OverlayTexture.NO_OVERLAY, 0);
			pose.popPose();
		}
		pose.popPose();
		super.submit(state, pose, collector, camera);
	}
}
