package com.sparky.lanternring.client.corps;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Hope;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.client.HopeTint;
import com.sparky.lanternring.corps.CorpsVillager;
import net.fabricmc.fabric.api.client.rendering.v1.FabricRenderState;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.npc.villager.Villager;
import org.jspecify.annotations.Nullable;

/**
 * Draws the Blue Lantern's villagers (Blue corps villagers, and the Villager Spark's builders while
 * they're still blue) in the suit from J's reference sheet, with its circuit lines and emblems
 * glowing, flying and building in ring poses. Other villagers keep the vanilla renderer
 * (EntityRenderDispatcherMixin picks this one only for blue ones).
 */
public class BlueVillagerRenderer extends HumanoidMobRenderer<Villager, BlueVillagerRenderer.State, BlueVillagerModel> {
	private static final Identifier SKIN = LanternRing.id("textures/entity/blue_villager.png");
	private static final Identifier GLOW = LanternRing.id("textures/entity/blue_villager_glow.png");
	private static final int FULL_BRIGHT = 0xF000F0;
	/** Slow-flight lean, in degrees at full forward speed (as FlightPoses leans a player). */
	private static final float LEAN = 20f, ROLL = 12f;
	/** Height of the turning point, so the body tips around its middle rather than its feet. */
	private static final float PIVOT = 0.95f;

	@Nullable
	private static BlueVillagerRenderer instance;

	public static class State extends HumanoidRenderState {
		/** 0..1 how far into the flight pose, and into the building pose (arms out at the construct). */
		public float flying, building;
		/** Travel relative to the body, -1..1. */
		public float forward, side;
	}

	public BlueVillagerRenderer(EntityRendererProvider.Context context) {
		super(context, new BlueVillagerModel(BlueVillagerModel.create(false).bakeRoot()),
				new BlueVillagerModel(BlueVillagerModel.create(true).bakeRoot()), 0.5f);
		addLayer(new Glow(this));
		instance = this;
	}

	/** The renderer for this entity, if it's one of the Blue Lantern's villagers. */
	public static @Nullable BlueVillagerRenderer forEntity(Entity entity) {
		return instance != null && isBlue(entity) ? instance : null;
	}

	public static @Nullable BlueVillagerRenderer forState(Object state) {
		return state instanceof State ? instance : null;
	}

	public static boolean isBlue(Entity entity) {
		if (entity instanceof CorpsVillager cv) return cv.corps() == Corps.BLUE;
		if (!(entity instanceof Villager)) return false;
		Hope.Mark mark = entity.getAttached(Hope.MARK);
		return mark != null && !mark.golem() && mark.blue(entity.level().getGameTime()) > 0;
	}

	static float leanPitch(float forward) {
		return -LEAN * forward;
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return SKIN;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(Villager entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		// The suit replaces the old all-over blue tint.
		((FabricRenderState) state).setData(HopeTint.KEY, 0f);
		if (entity instanceof CorpsVillager cv) {
			state.flying = cv.flyAnim(partialTick);
			state.building = cv.buildAnim(partialTick);
			state.forward = cv.leanForward(partialTick);
			state.side = cv.leanSide(partialTick);
		} else {
			state.flying = state.building = state.forward = state.side = 0;
		}
	}

	@Override
	protected void setupRotations(State state, PoseStack poseStack, float bodyRot, float scale) {
		super.setupRotations(state, poseStack, bodyRot, scale);
		float f = state.flying;
		if (f <= 0) return;
		// A slow bob while it hangs in the air, and the lean into where it's going.
		poseStack.translate(0, Mth.sin(state.ageInTicks * 0.1f) * 0.06f * f, 0);
		poseStack.translate(0, PIVOT, 0);
		poseStack.rotateDegrees(Axis.XP, leanPitch(state.forward) * f);
		poseStack.rotateDegrees(Axis.ZP, -ROLL * state.side * f);
		poseStack.translate(0, -PIVOT, 0);
	}

	@Override
	protected void scale(State state, PoseStack poseStack) {
		// Player scale: the suit body is player-sized and the villager head 2 pixels taller.
		poseStack.scale(0.9375f, 0.9375f, 0.9375f);
	}

	/** The circuit lines and emblems, drawn again at full brightness (painted bright: glow isn't additive). */
	private static class Glow extends RenderLayer<State, BlueVillagerModel> {
		Glow(RenderLayerParent<State, BlueVillagerModel> parent) {
			super(parent);
		}

		@Override
		public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, State state, float yRot, float xRot) {
			if (state.isInvisible) return;
			collector.order(1).submitModel(getParentModel(), state, poseStack, RenderTypes.eyes(GLOW), FULL_BRIGHT,
					OverlayTexture.NO_OVERLAY, -1, null, 0);
		}
	}
}
