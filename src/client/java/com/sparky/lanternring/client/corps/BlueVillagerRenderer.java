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
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import com.sparky.lanternring.client.ally.ConstructSkins;
import net.minecraft.core.BlockPos;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.npc.villager.Villager;
import org.jspecify.annotations.Nullable;

/**
 * Draws the Blue Lantern's villagers (Blue corps villagers, and the Villager Spark's builders while
 * they're still blue): see-through blue hard-light constructs at first, then, once a Blue corps
 * villager has its suit, the suit from J's reference sheet with its circuit lines and emblems
 * glowing. Both fly and build in ring poses. Other villagers keep the vanilla renderer
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
		/** False while it's still a see-through blue construct (before it gains the suit). */
		public boolean suited;
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
		return state.suited ? SKIN : ConstructSkins.get("blue_villager", model.root(), SKIN, 1, Corps.BLUE);
	}

	@Override
	protected @Nullable RenderType getRenderType(State state, boolean visible, boolean transparent, boolean glowing) {
		if (state.suited) return super.getRenderType(state, visible, transparent, glowing);
		return visible || transparent ? RenderTypes.entityTranslucentEmissive(getTextureLocation(state)) : null;
	}

	@Override
	protected int getModelTint(State state) {
		// The construct is see-through hard light, a slow shimmer in its alpha.
		if (state.suited) return super.getModelTint(state);
		float a = 0.72f + 0.08f * Mth.sin(state.ageInTicks * 0.12f);
		return Math.round(a * 255) << 24 | 0xFFFFFF;
	}

	@Override
	protected int getBlockLightLevel(Villager entity, BlockPos pos) {
		return entity instanceof CorpsVillager cv && cv.suited() ? super.getBlockLightLevel(entity, pos) : 15;
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
		state.suited = entity instanceof CorpsVillager cv0 && cv0.suited();
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
			if (state.isInvisible || !state.suited) return;
			collector.order(1).submitModel(getParentModel(), state, poseStack, RenderTypes.eyes(GLOW), FULL_BRIGHT,
					OverlayTexture.NO_OVERLAY, -1, null, 0);
		}
	}
}
