package com.sparky.lanternring.client;

import net.fabricmc.fabric.api.client.render.fluid.v1.FluidRenderingRegistry;
import net.minecraft.client.renderer.block.FluidModel;
import net.minecraft.client.resources.model.sprite.Material;
import net.minecraft.resources.Identifier;
import com.sparky.lanternring.ModFluids;
import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.net.GolemPayload;
import com.sparky.lanternring.net.LassoPayload;
import com.sparky.lanternring.net.PortalPayload;
import com.sparky.lanternring.net.RingFxPayload;
import com.sparky.lanternring.net.ToggleFlightPayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.particle.v1.ParticleProviderRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.LivingEntityRenderLayerRegistrationCallback;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.core.particles.SimpleParticleType;

public class LanternRingClient implements ClientModInitializer {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(LanternRing.id("lanternring"));
	private static KeyMapping flightKey;
	private static KeyMapping labKey;

	/** The Deluge's liquid colour: the ring's bright green, a touch toward jade. */
	private static final int HARD_LIGHT_LIQUID_TINT = 0xFF2EE866;

	@Override
	public void onInitializeClient() {
		flightKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.lanternring.flight",
				InputConstants.Type.KEYBOARD, InputConstants.KEY_V, CATEGORY));
		labKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.lanternring.lab",
				InputConstants.Type.KEYBOARD, InputConstants.KEY_K, CATEGORY));

		particle(ModParticles.MOTE, ConstructParticle.Behavior.MOTE);
		particle(ModParticles.DRIP, ConstructParticle.Behavior.DRIP);
		particle(ModParticles.SHARD, ConstructParticle.Behavior.SHARD);
		particle(ModParticles.SPARK, ConstructParticle.Behavior.SPARK);
		particle(ModParticles.PANE, ConstructParticle.Behavior.PANE);

		// The Deluge's liquid: water's own textures, tinted green. Shader packs that colour water by
		// its tint (Complementary does by default) draw it as green shader water; see IrisGreenLight.
		FluidRenderingRegistry.register(ModFluids.SOURCE, ModFluids.FLOWING, new FluidModel.Unbaked(
				new Material(Identifier.withDefaultNamespace("block/water_still")),
				new Material(Identifier.withDefaultNamespace("block/water_flow")),
				new Material(Identifier.withDefaultNamespace("block/water_overlay")),
				state -> HARD_LIGHT_LIQUID_TINT));

		ShockwaveDomes.register();
		BlackHoleFx.register();
		RingModelProperty.register();
		LanternModelProperty.register();
		ChargeMeter.register();
		BuildInput.register();

		ClientHooks.batteryAmbient = LabFx::batteryAmbient;
		ClientHooks.constructAmbient = LabFx::constructAmbient;
		ClientPlayNetworking.registerGlobalReceiver(RingFxPayload.TYPE, (payload, context) -> {
			LabFx.handle(payload);
			RingFxPayload.Kind kind = payload.kind();
			if (kind != RingFxPayload.Kind.CHARGE && kind != RingFxPayload.Kind.MODE_CHANGE
					&& kind != RingFxPayload.Kind.ANVIL_MARK && kind != RingFxPayload.Kind.ANVIL_IMPACT
					&& kind != RingFxPayload.Kind.DELUGE_MARK && kind != RingFxPayload.Kind.DELUGE_SPLASH
					&& kind != RingFxPayload.Kind.BLACK_HOLE_MARK) {
				FlightPoses.shot(payload.from());
			}
		});
		ClientPlayNetworking.registerGlobalReceiver(LassoPayload.TYPE, (payload, context) -> LassoFx.handle(payload));
		ClientPlayNetworking.registerGlobalReceiver(PortalPayload.TYPE, (payload, context) -> PortalFx.handle(payload));
		ClientPlayNetworking.registerGlobalReceiver(GolemPayload.TYPE, (payload, context) -> GolemFx.handle(payload));
		LevelRenderEvents.COLLECT_SUBMITS.register(PortalFx::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(GolemFx::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(LassoFx::render);

		LivingEntityRenderLayerRegistrationCallback.EVENT.register((type, renderer, helper, context) -> {
			if (renderer instanceof AvatarRenderer<?> avatar) {
				@SuppressWarnings("unchecked")
				RenderLayerParent<AvatarRenderState, PlayerModel> parent = (RenderLayerParent<AvatarRenderState, PlayerModel>) (Object) avatar;
				helper.register(new RingHandLayer(parent));
			}
		});

		LevelRenderEvents.COLLECT_SUBMITS.register(HelixBeams::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(BlastDrillFx::render);

		ClientTickEvents.START_CLIENT_TICK.register(AnvilInput::startTick);
		ClientTickEvents.START_CLIENT_TICK.register(BuildInput::startTick);
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (flightKey.consumeClick()) {
				if (client.player != null && ClientPlayNetworking.canSend(ToggleFlightPayload.TYPE)) {
					ClientPlayNetworking.send(new ToggleFlightPayload());
				}
			}
			while (labKey.consumeClick()) {
				client.setScreenAndShow(new RingLabScreen(null));
			}
			LanternRingClientState.tick();
			FastFlight.tick(client);
			FlightPoses.tick(client);
			LabFx.tick(client);
			LanternFirstPerson.tick(client);
			LanternPlaceInput.tick(client);
			LanternChargeInput.tick(client);
			IrisGreenLight.tick(client);
			LassoFx.tick(client);
			PortalFx.tick(client);
			GolemFx.tick(client);
			AnvilInput.tick(client);
		});
	}

	private static void particle(SimpleParticleType type, ConstructParticle.Behavior behavior) {
		ParticleProviderRegistry.getInstance().register(type, sprites ->
				(options, level, x, y, z, vx, vy, vz, random) -> new ConstructParticle(level, x, y, z, vx, vy, vz, sprites, behavior));
	}
}
