package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import org.jspecify.annotations.Nullable;

/**
 * J (2026-10-16): a dropped ring is the real, physical ring, not its flat inventory icon. Drawn with
 * the worn ring's model (RingModels) in its corps colour, standing on its band a little bigger than
 * life, bobbing and turning slowly like any dropped item; its gem glows (DroppedRingLight adds a soft
 * light round it). EntityRenderDispatcherMixin picks this renderer for item entities holding a ring.
 */
public class DroppedRingRenderer extends EntityRenderer<ItemEntity, DroppedRingRenderer.State> {
	/** How many times its worn size the ring is drawn on the ground: some 0.3 blocks across. */
	public static float size = 2.5f;
	/** Degrees a second the dropped ring turns. */
	private static final float TURN = 40f;

	@Nullable
	private static DroppedRingRenderer instance;
	private static boolean told;

	public static class State extends EntityRenderState {
		Corps corps = Corps.GREEN;
		float bob;
		float spin;
	}

	public DroppedRingRenderer(EntityRendererProvider.Context context) {
		super(context);
		shadowRadius = 0.12f;
		shadowStrength = 0.6f;
		instance = this;
	}

	public static boolean isRing(Entity entity) {
		return entity instanceof ItemEntity item && item.getItem().getItem() instanceof PowerRingItem;
	}

	public static @Nullable DroppedRingRenderer forEntity(Entity entity) {
		return instance != null && isRing(entity) ? instance : null;
	}

	public static @Nullable DroppedRingRenderer forState(Object state) {
		return state instanceof State ? instance : null;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(ItemEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.corps = Corps.of(entity.getItem());
		float age = entity.getAge() + partialTick;
		// Each ring its own phase, as vanilla items have.
		float phase = (entity.getId() * 0.6180339f % 1f) * Mth.TWO_PI;
		state.bob = Mth.sin(age / 10f + phase) * 0.05f + 0.05f;
		state.spin = age / 20f * TURN + phase * Mth.RAD_TO_DEG;
	}

	@Override
	public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
		if (!told) {
			told = true;
			WhatsNewClient.tell("ring.dropped");
		}
		Corps before = CorpsTint.enter(state.corps);
		poseStack.pushPose();
		poseStack.translate(0f, 0.2f + state.bob, 0f);
		poseStack.rotateDegrees(Axis.YP, state.spin);
		// Stood on its band, face out sideways and tipped back a little, so it catches the eye from above too.
		poseStack.rotateDegrees(Axis.XP, 70f);
		poseStack.rotateDegrees(Axis.ZP, 180f);
		RingModels.renderDropped(poseStack, collector, state.lightCoords, LabSettings.get().ringModel, size);
		poseStack.popPose();
		CorpsTint.restore(before);
		super.submit(state, poseStack, collector, camera);
	}
}
