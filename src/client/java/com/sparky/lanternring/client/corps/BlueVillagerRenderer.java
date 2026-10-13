package com.sparky.lanternring.client.corps;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Hope;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.client.BeamChargeGlow;
import com.sparky.lanternring.client.CorpsTint;
import com.sparky.lanternring.client.HopeTint;
import com.sparky.lanternring.client.RingAuraLayer;
import com.sparky.lanternring.client.ShaderGlow;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.RingModels;
import com.sparky.lanternring.item.PowerRingItem;
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
 * they're still blue), all alike: the suit from J's reference sheet with its circuit lines and
 * emblems glowing, and a blue enchantment-like glint sliding over the whole villager. Both fly and build in ring poses. Other villagers keep the vanilla renderer
 * (EntityRenderDispatcherMixin picks this one only for blue ones).
 */
public class BlueVillagerRenderer extends HumanoidMobRenderer<Villager, BlueVillagerRenderer.State, BlueVillagerModel> {
	private static final Identifier GLOW = LanternRing.id("textures/entity/blue_villager_glow.png");
	/** Faces (tools/villager_faces.py): hopeful by default, focused while building, fierce in a fight, and a blink. */
	private static final Identifier[] FACES = faces("blue_villager");
	/** How much bigger than the body the glint shell is (just enough not to flicker against it), as RingAuraLayer. */
	private static final float GROW = 1.02f;
	private static final int FULL_BRIGHT = 0xF000F0;
	private static final int HOPE = 0, FOCUS = 1, FIERCE = 2, BLINK = 3;
	/** Ticks between blinks, and how long the eyes stay shut. */
	private static final int BLINK_EVERY = 97, BLINK_TICKS = 3;
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
		/** Fighting: 0..1 how far the ring arm is raised, where it points (radians, body-relative), and the ring's flare as it fires. */
		public float aim, aimYaw, aimPitch, flash;
		/** Wearing its corps ring (drawn on the right hand). */
		public boolean ring;
		/** Blue, or Orange for a fallen Blue villager raised in the Orange Lantern's Horde. */
		public Corps corps = Corps.BLUE;
		/** Which face to wear (HOPE, FOCUS, FIERCE or BLINK). */
		public int face;
		/**
		 * Its job in a Blue Lantern rescue squad (NONE for a village's own). The hook for the squad's
		 * construct armour and weapons from the Blender session: until they land, squad members wear
		 * the same Blue suit as every Blue villager.
		 */
		public com.sparky.lanternring.corps.BlueSquad.Role squad = com.sparky.lanternring.corps.BlueSquad.Role.NONE;
	}

	public BlueVillagerRenderer(EntityRendererProvider.Context context) {
		super(context, new BlueVillagerModel(BlueVillagerModel.create(false).bakeRoot()),
				new BlueVillagerModel(BlueVillagerModel.create(true).bakeRoot()), 0.5f);
		addLayer(new Glow(this));
		addLayer(new Glint(this));
		addLayer(new Ring(this));
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
		// The Blue villagers an Orange Lantern killed come back in its Horde wearing the suit, in orange.
		if (entity instanceof CorpsVillager cv) return cv.corps() == Corps.BLUE || cv.corps() == Corps.ORANGE && cv.suited();
		if (!(entity instanceof Villager)) return false;
		Hope.Mark mark = entity.getAttached(Hope.MARK);
		return mark != null && !mark.golem() && mark.blue(entity.level().getGameTime()) > 0;
	}

	private static Identifier[] faces(String name) {
		return new Identifier[] {LanternRing.id("textures/entity/" + name + ".png"), LanternRing.id("textures/entity/" + name + "_focus.png"),
				LanternRing.id("textures/entity/" + name + "_fierce.png"), LanternRing.id("textures/entity/" + name + "_blink.png")};
	}

	static float leanPitch(float forward) {
		return -LEAN * forward;
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return FACES[state.face];
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
			state.aim = cv.aimAnim(partialTick);
			state.aimYaw = cv.aimYaw();
			state.aimPitch = cv.aimPitch();
			state.flash = cv.flashAnim(partialTick);
			state.ring = cv.getMainHandItem().getItem() instanceof PowerRingItem;
			state.corps = cv.corps() == Corps.ORANGE ? Corps.ORANGE : Corps.BLUE;
			state.squad = cv.squadRole();
		} else {
			state.corps = Corps.BLUE;
			state.flying = state.building = state.forward = state.side = 0;
			state.aim = state.flash = 0;
			state.ring = false;
			state.squad = com.sparky.lanternring.corps.BlueSquad.Role.NONE;
		}
		// Each villager blinks on its own beat; otherwise fierce while it fights, focused while it builds.
		long t = entity.tickCount + entity.getId() * 31L;
		if (t % BLINK_EVERY < BLINK_TICKS && state.aim < 0.3f) state.face = BLINK;
		else if (state.aim > 0.3f) state.face = FIERCE;
		else if (state.building > 0.3f) state.face = FOCUS;
		else state.face = HOPE;
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

	/**
	 * Its Blue Lantern ring on the right hand, the same 3D ring a player wears (the Ring Lab's ring
	 * model), glowing while it aims and flaring each time a beam or the lasso leaves it.
	 */
	private static class Ring extends RenderLayer<State, BlueVillagerModel> {
		private static final float RING_SCALE = 1.6f;

		Ring(RenderLayerParent<State, BlueVillagerModel> parent) {
			super(parent);
		}

		@Override
		public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, State state, float yRot, float xRot) {
			if (state.isInvisible || !state.ring) return;
			LabSettings.RingModel model = LabSettings.get().ringModel;
			Corps before = CorpsTint.enter(state.corps);
			poseStack.pushPose();
			getParentModel().rightArm.translateAndRotate(poseStack);
			// Bigger than a player's, so it reads from across the village; grown around the ring face.
			float[] face = RingModels.ringFace(model, false, false);
			poseStack.translate(face[0] / 16f, face[1] / 16f, face[2] / 16f);
			poseStack.scale(RING_SCALE, RING_SCALE, RING_SCALE);
			poseStack.translate(-face[0] / 16f, -face[1] / 16f, -face[2] / 16f);
			RingModels.render(poseStack, collector, light, model, false, false);
			// Always a soft blue glow on it, brighter while it aims.
			BeamChargeGlow.renderHold(poseStack, collector, 0.35f + 0.55f * state.aim, state.ageInTicks, model, false, false, false);
			BeamChargeGlow.renderFlash(poseStack, collector, state.flash, state.ageInTicks, model, false, false, false);
			poseStack.popPose();
			CorpsTint.restore(before);
		}
	}

	/**
	 * The circuit lines and emblems, drawn again glowing (painted bright: glow isn't additive).
	 * Emissive translucent with the shader glow light, so packs light it up.
	 */
	private static class Glow extends RenderLayer<State, BlueVillagerModel> {
		Glow(RenderLayerParent<State, BlueVillagerModel> parent) {
			super(parent);
		}

		@Override
		public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, State state, float yRot, float xRot) {
			if (state.isInvisible) return;
			collector.order(1).submitModel(getParentModel(), state, poseStack, RenderTypes.entityTranslucentEmissive(GLOW), ShaderGlow.light(0.8f),
					OverlayTexture.NO_OVERLAY, state.corps == Corps.ORANGE ? ORANGE_LINES : -1, null, 0);
		}
	}

	/** The glowing lines' tint on a fallen Blue villager in the Orange Horde. */
	private static final int ORANGE_LINES = 0xFFFF9A2E;

	/** A blue glint sliding over the whole villager like an enchantment's: the ring wearer's aura (RingAuraLayer) in Blue. */
	private static class Glint extends RenderLayer<State, BlueVillagerModel> {
		Glint(RenderLayerParent<State, BlueVillagerModel> parent) {
			super(parent);
		}

		@Override
		public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, State state, float yRot, float xRot) {
			if (state.isInvisible) return;
			poseStack.pushPose();
			// Grow it around the body's middle (the model's feet are 1.5 blocks below its origin).
			poseStack.translate(0, 0.75f * (1 - GROW), 0);
			poseStack.scale(GROW, GROW, GROW);
			collector.order(2).submitModel(getParentModel(), state, poseStack, RingAuraLayer.type(state.ageInTicks), FULL_BRIGHT,
					OverlayTexture.NO_OVERLAY, RingAuraLayer.tint(state.corps, state.ageInTicks, 1f), null, 0);
			poseStack.popPose();
		}
	}
}
