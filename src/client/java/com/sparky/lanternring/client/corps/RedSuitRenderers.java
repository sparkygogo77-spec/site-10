package com.sparky.lanternring.client.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.client.ally.ConstructSkins;
import com.sparky.lanternring.corps.CorpsGolem;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.monster.warden.WardenModel;
import net.minecraft.client.renderer.entity.CatRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.IronGolemRenderer;
import net.minecraft.client.renderer.entity.PillagerRenderer;
import net.minecraft.client.renderer.entity.WardenRenderer;
import net.minecraft.client.renderer.entity.layers.LivingEntityEmissiveLayer;
import net.minecraft.client.renderer.entity.state.CatRenderState;
import net.minecraft.client.renderer.entity.state.IllagerRenderState;
import net.minecraft.client.renderer.entity.state.IronGolemRenderState;
import net.minecraft.client.renderer.entity.state.WardenRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.animal.golem.IronGolem;

/**
 * The Red Lantern sanctuary's suits from J's picks (tools/red_suits.py): P1 Rage Raider on the sky
 * raiders, W1 Caged Heart on the rage warden, C1 Rage Suit on the rage cats, G1 Blood Iron on red
 * corps golems. Each keeps the vanilla model; only the skin changes.
 */
public final class RedSuitRenderers {
	private static Identifier skin(String name) {
		return LanternRing.id("textures/entity/red_lantern/" + name + ".png");
	}

	private RedSuitRenderers() {
	}

	public static class Raider extends PillagerRenderer {
		private static final Identifier SKIN = skin("rage_raider");

		public Raider(EntityRendererProvider.Context context) {
			super(context);
		}

		@Override
		public Identifier getTextureLocation(IllagerRenderState state) {
			return SKIN;
		}
	}

	public static class Cat extends CatRenderer {
		private static final Identifier SKIN = skin("rage_cat");

		public Cat(EntityRendererProvider.Context context) {
			super(context);
		}

		@Override
		public Identifier getTextureLocation(CatRenderState state) {
			return SKIN;
		}
	}

	/** The warden in its cage of black bands, with every glowing layer turned red. */
	public static class Warden extends WardenRenderer {
		private static final Identifier SKIN = skin("caged_heart_warden");
		private static final Identifier BIOLUMINESCENT = Identifier.withDefaultNamespace("textures/entity/warden/warden_bioluminescent_layer.png");
		private static final Identifier SPOTS_1 = Identifier.withDefaultNamespace("textures/entity/warden/warden_pulsating_spots_1.png");
		private static final Identifier SPOTS_2 = Identifier.withDefaultNamespace("textures/entity/warden/warden_pulsating_spots_2.png");
		private static final Identifier HEART = Identifier.withDefaultNamespace("textures/entity/warden/warden_heart.png");

		public Warden(EntityRendererProvider.Context context) {
			super(context);
			layers.clear();
			WardenModel glowModel = new WardenModel(context.bakeLayer(ModelLayers.WARDEN_BIOLUMINESCENT));
			WardenModel spotsModel = new WardenModel(context.bakeLayer(ModelLayers.WARDEN_PULSATING_SPOTS));
			WardenModel heartModel = new WardenModel(context.bakeLayer(ModelLayers.WARDEN_HEART));
			addLayer(new LivingEntityEmissiveLayer<>(this, state -> ConstructSkins.glow("warden_markings", BIOLUMINESCENT, Corps.RED),
					(state, age) -> 1f, glowModel, RenderTypes::entityTranslucentEmissive, false));
			addLayer(new LivingEntityEmissiveLayer<>(this, state -> ConstructSkins.glow("warden_spots_1", SPOTS_1, Corps.RED),
					(state, age) -> Math.max(0f, Mth.cos(age * 0.045f)) * 0.25f, spotsModel, RenderTypes::entityTranslucentEmissive, false));
			addLayer(new LivingEntityEmissiveLayer<>(this, state -> ConstructSkins.glow("warden_spots_2", SPOTS_2, Corps.RED),
					(state, age) -> Math.max(0f, Mth.cos(age * 0.045f + Mth.PI)) * 0.25f, spotsModel, RenderTypes::entityTranslucentEmissive, false));
			addLayer(new LivingEntityEmissiveLayer<>(this, state -> ConstructSkins.glow("warden_heart", HEART, Corps.RED),
					(state, age) -> state.heartAnimation, heartModel, RenderTypes::entityTranslucentEmissive, false));
		}

		@Override
		public Identifier getTextureLocation(WardenRenderState state) {
			return SKIN;
		}
	}

	/** Corps golems: the red ones wear Blood Iron, the rest stay iron (blue ones go to HopeGolemRenderer). */
	public static class Golem extends IronGolemRenderer {
		private static final Identifier SKIN = skin("blood_iron_golem");

		public static class State extends IronGolemRenderState {
			boolean red;
		}

		public Golem(EntityRendererProvider.Context context) {
			super(context);
		}

		@Override
		public IronGolemRenderState createRenderState() {
			return new State();
		}

		@Override
		public void extractRenderState(IronGolem entity, IronGolemRenderState state, float partialTick) {
			super.extractRenderState(entity, state, partialTick);
			((State) state).red = entity instanceof CorpsGolem cg && cg.corps() == Corps.RED;
		}

		@Override
		public Identifier getTextureLocation(IronGolemRenderState state) {
			return state instanceof State s && s.red ? SKIN : super.getTextureLocation(state);
		}
	}
}
