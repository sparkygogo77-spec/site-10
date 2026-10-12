package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.block.RingForgeBlockEntity;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderers;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * The Ring Forge's floating parts (tools/blockbench_models.py): a glowing core over the well, a
 * hard-light port on each side of it facing in, and the lantern emblem above, always turned to
 * the viewer, its opening full of endless light. Everything bobs gently.
 */
public class RingForgeRenderer implements BlockEntityRenderer<RingForgeBlockEntity, RingForgeRenderer.State> {
	private static final int FULL_BRIGHT = 0xF000F0;
	private static final float CORE_Y = 15f, PORT_R = 6.5f, EMBLEM_Y = 23f;
	private static final int LIGHT_FRAMES = 16;
	private static final int LIGHT_FRAME_TICKS = 2;

	private static BbModel core, port, emblem;
	private static final BbModel[] LIGHT = new BbModel[LIGHT_FRAMES];

	public static class State extends BlockEntityRenderState {
		float time;
	}

	public static void register() {
		BlockEntityRenderers.register(ModRegistry.RING_FORGE_ENTITY, ctx -> new RingForgeRenderer());
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(RingForgeBlockEntity forge, State state, float partialTick, Vec3 camera,
			ModelFeatureRenderer.CrumblingOverlay breaking) {
		BlockEntityRenderer.super.extractRenderState(forge, state, partialTick, camera, breaking);
		state.time = forge.getLevel() == null ? 0 : (forge.getLevel().getGameTime() % 24000) + partialTick;
	}

	@Override
	public void submit(State state, PoseStack pose, SubmitNodeCollector collector, CameraRenderState camera) {
		if (core == null) {
			core = BbModel.load("ring_forge_core");
			port = BbModel.load("ring_forge_port");
			emblem = BbModel.load("ring_forge_emblem");
			BbModel light = BbModel.load("ring_forge_light");
			for (int i = 0; i < LIGHT_FRAMES; i++) {
				LIGHT[i] = light.retextured(LanternRing.id("textures/entity/bb/ring_forge_light_f" + i + ".png"));
			}
		}
		float t = state.time;
		pose.pushPose();
		pose.translate(0.5f, 0f, 0.5f);

		pose.pushPose();
		pose.translate(0f, (CORE_Y + 0.4f * Mth.sin(t * 0.07f)) / 16f, 0f);
		pose.rotateDegrees(Axis.YP, t * 1.5f);
		core.render(pose, collector, FULL_BRIGHT, -1);
		pose.popPose();

		for (int i = 0; i < 4; i++) {
			pose.pushPose();
			pose.rotateDegrees(Axis.YP, 90f * i);
			pose.translate(0f, (CORE_Y + 0.6f * Mth.sin(t * 0.09f + i * 1.7f)) / 16f, -PORT_R / 16f);
			port.render(pose, collector, FULL_BRIGHT, -1);
			pose.popPose();
		}

		// The emblem turns to face whoever looks at it, so its opening of light always faces them.
		pose.pushPose();
		pose.translate(0f, (EMBLEM_Y + 0.5f * Mth.sin(t * 0.05f)) / 16f, 0f);
		if (camera.pos != null && state.blockPos != null) {
			double dx = camera.pos.x - (state.blockPos.getX() + 0.5);
			double dz = camera.pos.z - (state.blockPos.getZ() + 0.5);
			pose.rotateDegrees(Axis.YP, (float) Math.toDegrees(Math.atan2(dx, dz)));
		}
		emblem.render(pose, collector, FULL_BRIGHT, -1);
		LIGHT[(int) (t / LIGHT_FRAME_TICKS) % LIGHT_FRAMES].render(pose, collector, FULL_BRIGHT, -1);
		pose.popPose();

		pose.popPose();
	}

	@Override
	public boolean shouldRenderOffScreen() {
		return true;
	}
}
