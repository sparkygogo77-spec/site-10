package com.sparky.lanternring.client;

import net.fabricmc.fabric.api.client.render.fluid.v1.FluidRenderingRegistry;
import net.minecraft.client.renderer.block.FluidModel;
import net.minecraft.client.resources.model.sprite.Material;
import net.minecraft.resources.Identifier;
import com.sparky.lanternring.ModFluids;
import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.net.GolemPayload;
import com.sparky.lanternring.ally.ModEntities;
import com.sparky.lanternring.client.ally.BroodSpiderRenderer;
import com.sparky.lanternring.client.ally.DragonConstructRenderer;
import com.sparky.lanternring.client.ally.SentryConstructRenderer;
import com.sparky.lanternring.client.ally.WardenConstructRenderer;
import com.sparky.lanternring.corps.CorpsMobs;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.minecraft.client.renderer.entity.VillagerRenderer;
import com.sparky.lanternring.net.DismissPayload;
import com.sparky.lanternring.net.LassoPayload;
import com.sparky.lanternring.net.PortalPayload;
import com.sparky.lanternring.net.RingFxPayload;
import com.sparky.lanternring.net.ToggleFlightPayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.command.v2.ClientCommandRegistrationCallback;
import net.fabricmc.fabric.api.client.command.v2.ClientCommands;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.particle.v1.ParticleProviderRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.LivingEntityRenderLayerRegistrationCallback;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import com.sparky.lanternring.ModRegistry;
import net.minecraft.client.KeyMapping;
import net.minecraft.world.item.ItemStack;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.core.particles.SimpleParticleType;

public class LanternRingClient implements ClientModInitializer {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(LanternRing.id("lanternring"));
	private static KeyMapping flightKey;
	private static KeyMapping labKey;
	private static KeyMapping wheelKey;
	private static KeyMapping lanternKey;

	/** The Deluge's liquid colour: the ring's bright green, a touch toward jade. */
	private static final int HARD_LIGHT_LIQUID_TINT = 0xFF3FC489;
	/** The Red Lantern's liquid: deep blood red. */
	private static final int EMBER_LIQUID_TINT = 0xFF870019;

	@Override
	public void onInitializeClient() {
		flightKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.lanternring.flight",
				InputConstants.Type.KEYBOARD, InputConstants.KEY_V, CATEGORY));
		labKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.lanternring.lab",
				InputConstants.Type.KEYBOARD, InputConstants.KEY_K, CATEGORY));
		// R belongs to the lantern now (J, 2026-10-13); the wheel moved to G under a new id, so a saved
		// R binding from before doesn't land on both.
		wheelKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.lanternring.ring_wheel",
				InputConstants.Type.KEYBOARD, InputConstants.KEY_G, CATEGORY));
		lanternKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.lanternring.lantern",
				InputConstants.Type.KEYBOARD, InputConstants.KEY_R, CATEGORY));

		// White Constructs pack: flowing textures that run seamlessly across neighbouring blocks.
		FlowConstructModel.register();
		ConstructLooks.register();
		ConstructDisplays.register();

		// Updates: check for a newer jar on joining a world; the chat link runs /lanternring update.
		RingUpdater.init();
		ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> RingUpdater.onJoin());
		// Complementary: a Lantern Ring copy of the pack with the corps' own light colours.
		ShaderPackPatcher.init();
		com.sparky.lanternring.item.PowerRingItem.shaderHeldLight = () -> ShaderGlow.patchedPackOn() ? 12 : 0;
		com.sparky.lanternring.item.PowerRingItem.shaderSunDim = SunDim::forShader;
		ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> ShaderPackPatcher.onJoin());
		ClientTickEvents.END_CLIENT_TICK.register(RingUpdater::tick);
		ClientCommandRegistrationCallback.EVENT.register((dispatcher, context) -> dispatcher.register(
				ClientCommands.literal("lanternring").then(ClientCommands.literal("update").executes(c -> {
					RingUpdater.download();
					return 1;
				}))));

		// Each corps has its own copy of the particles, drawn in its colour.
		ModParticles.all(ModParticles.MOTE).forEach((corps, type) -> particle(type, ConstructParticle.Behavior.MOTE, corps));
		ModParticles.all(ModParticles.DRIP).forEach((corps, type) -> particle(type, ConstructParticle.Behavior.DRIP, corps));
		ModParticles.all(ModParticles.SHARD).forEach((corps, type) -> particle(type, ConstructParticle.Behavior.SHARD, corps));
		ModParticles.all(ModParticles.SPARK).forEach((corps, type) -> particle(type, ConstructParticle.Behavior.SPARK, corps));
		ModParticles.all(ModParticles.PANE).forEach((corps, type) -> particle(type, ConstructParticle.Behavior.PANE, corps));

		// The Deluge's liquid: solid hard light (J's W3 pick, tools/hardlight_liquid_textures.py), near
		// white and fairly opaque with soft ripples, tinted green. Water's own textures were dark and
		// see-through, so the tint landed dark. The patched Complementary draws it as glowing light (ID
		// 32002, see ShaderPackPatcher); other packs that colour water by its tint draw it green.
		FluidRenderingRegistry.register(ModFluids.SOURCE, ModFluids.FLOWING, new FluidModel.Unbaked(
				new Material(LanternRing.id("block/hardlight_still")),
				new Material(LanternRing.id("block/hardlight_flow")),
				new Material(LanternRing.id("block/hardlight_still")),
				state -> HARD_LIGHT_LIQUID_TINT));
		// The Red Lantern's Deluge: thick blood-red liquid (J, 2026-10-12). Soft ripples tinted deep red
		// and nearly opaque (tools/blood_liquid_textures.py), so the bottom doesn't show; the patched
		// Complementary draws it as its water, opaque and calm (ID 32003, see ShaderPackPatcher).
		FluidRenderingRegistry.register(ModFluids.EMBER_SOURCE, ModFluids.EMBER_FLOWING, new FluidModel.Unbaked(
				new Material(LanternRing.id("block/blood_still")),
				new Material(LanternRing.id("block/blood_flow")),
				new Material(LanternRing.id("block/blood_still")),
				state -> EMBER_LIQUID_TINT));

		ShockwaveDomes.register();
		RiotShields.register();
		BlackHoleFx.register();
		EntityRendererRegistry.register(ModEntities.WARDEN, WardenConstructRenderer::new);
		EntityRendererRegistry.register(ModEntities.DRAGON, DragonConstructRenderer::new);
		EntityRendererRegistry.register(ModEntities.SENTRY, SentryConstructRenderer::new);
		// Blue corps villagers (and the Villager Spark's blue builders) wear the Blue Lantern suit instead.
		EntityRendererRegistry.register(CorpsMobs.CORPS_VILLAGER, context -> {
			new com.sparky.lanternring.client.corps.BlueVillagerRenderer(context);
			return new VillagerRenderer(context);
		});
		// Blue corps golems and the Hope Golem are hard light constructs (HopeGolemRenderer).
		EntityRendererRegistry.register(CorpsMobs.CORPS_GOLEM, context -> {
			new com.sparky.lanternring.client.corps.HopeGolemRenderer(context);
			return new com.sparky.lanternring.client.corps.RedSuitRenderers.Golem(context);
		});
		EntityRendererRegistry.register(CorpsMobs.BLUE_RAVAGER, com.sparky.lanternring.client.corps.BlueRavagerRenderer::new);
		// The Red Lantern sanctuary's suits (RedSuitRenderers).
		EntityRendererRegistry.register(CorpsMobs.SKY_RAIDER, com.sparky.lanternring.client.corps.RedSuitRenderers.Raider::new);
		EntityRendererRegistry.register(CorpsMobs.RAGE_WARDEN, com.sparky.lanternring.client.corps.RedSuitRenderers.Warden::new);
		EntityRendererRegistry.register(CorpsMobs.RAGE_CAT, com.sparky.lanternring.client.corps.RedSuitRenderers.Cat::new);
		EntityRendererRegistry.register(com.sparky.lanternring.corps.FlierHighway.DIVING_HAWK, com.sparky.lanternring.client.hawk.DivingHawkRenderer::new);
		EntityRendererRegistry.register(ModEntities.BROOD_SPIDER, context -> new BroodSpiderRenderer(context, 2.2f));
		EntityRendererRegistry.register(ModEntities.SPIDERLING, context -> new BroodSpiderRenderer(context, 0.43f));
		EntityRendererRegistry.register(ModEntities.RAGE_BULL, com.sparky.lanternring.client.ally.RageBullRenderer::new);
		EntityRendererRegistry.register(ModEntities.DREAD_RUNNER, com.sparky.lanternring.client.ally.DreadRunnerRenderer::new);
		EntityRendererRegistry.register(ModEntities.HOPE_TURBINE, com.sparky.lanternring.client.corps.HopeTurbineRenderer::new);
		FearFog.register();
		FearVignette.register();
		FearBlind.register();
		RageTint.register();
		RingModelProperty.register();
		LanternModelProperty.register();
		RedLanternProperty.register();
		HasStoneProperty.register();
		SoulSight.register();
		RingForgeRenderer.register();
		GhostMimicRenderer.register();
		ChargeMeter.register();
		NukeHold.register();
		AirburstFx.register();
		FearGasFx.register();
		LanternGlare.register();
		LanternFlash.register();
		DelugeGlare.register();
		BuildInput.register();

		ClientHooks.batteryAmbient = LabFx::batteryAmbient;
		ClientHooks.constructAmbient = LabFx::constructAmbient;
		ClientPlayNetworking.registerGlobalReceiver(RingFxPayload.TYPE, (payload, context) -> {
			RingFxPayload.Kind kind = payload.kind();
			// Point the ring arm first, so the effect starts where the raised ring will be.
			boolean aimed = kind != RingFxPayload.Kind.CHARGE && kind != RingFxPayload.Kind.MODE_CHANGE
					&& kind != RingFxPayload.Kind.SUPER_JUMP && kind != RingFxPayload.Kind.SUPER_LAND;
			if (payload.bearer() >= 0 && aimed) FlightPoses.shotBy(payload.bearer());
			LabFx.handle(payload);
			RingShake.shot(payload);
			if (payload.bearer() < 0 && kind != RingFxPayload.Kind.CHARGE && kind != RingFxPayload.Kind.MODE_CHANGE
					&& kind != RingFxPayload.Kind.ANVIL_MARK && kind != RingFxPayload.Kind.ANVIL_IMPACT && kind != RingFxPayload.Kind.LASSO_SLAM
					&& kind != RingFxPayload.Kind.DELUGE_MARK && kind != RingFxPayload.Kind.DELUGE_SPLASH
					&& kind != RingFxPayload.Kind.BLACK_HOLE_MARK && kind != RingFxPayload.Kind.BLACK_HOLE_FEED && kind != RingFxPayload.Kind.NUKE_AURA
					&& kind != RingFxPayload.Kind.FEAR_NUKE && kind != RingFxPayload.Kind.FEAR_BURST && kind != RingFxPayload.Kind.FEAR_GAS && kind != RingFxPayload.Kind.FEAR_NUKE_FORM && kind != RingFxPayload.Kind.FEAR_NUKE_SCATTER
					&& kind != RingFxPayload.Kind.ALLY_SHOT && kind != RingFxPayload.Kind.ALLY_MARK && kind != RingFxPayload.Kind.ALLY_SUMMON
					&& kind != RingFxPayload.Kind.RAM_BARRIER && kind != RingFxPayload.Kind.RAM_HIT && kind != RingFxPayload.Kind.RAM_BREAK) {
				FlightPoses.shot(payload.from());
			}
		});
		ClientPlayNetworking.registerGlobalReceiver(LassoPayload.TYPE, (payload, context) -> LassoFx.handle(payload));
		ClientPlayNetworking.registerGlobalReceiver(DismissPayload.TYPE, (payload, context) -> DismissFx.handle(payload));
		ClientPlayNetworking.registerGlobalReceiver(com.sparky.lanternring.net.CraterLiningPayload.TYPE, (payload, context) -> SuperLandConstruct.crater(payload));
		ClientPlayNetworking.registerGlobalReceiver(PortalPayload.TYPE, (payload, context) -> PortalFx.handle(payload));
		ClientPlayNetworking.registerGlobalReceiver(GolemPayload.TYPE, (payload, context) -> GolemFx.handle(payload));
		LevelRenderEvents.COLLECT_SUBMITS.register(PortalFx::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(GolemFx::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(LassoFx::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(DismissFx::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(LanternShrine::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(FlightTrail::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(RamBarrierFx::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(SuperLandConstruct::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(SuperJumpAir::render);

		LivingEntityRenderLayerRegistrationCallback.EVENT.register((type, renderer, helper, context) -> {
			if (renderer instanceof AvatarRenderer<?> avatar) {
				@SuppressWarnings("unchecked")
				RenderLayerParent<AvatarRenderState, PlayerModel> parent = (RenderLayerParent<AvatarRenderState, PlayerModel>) (Object) avatar;
				helper.register(new RingHandLayer(parent));
				helper.register(new RingAuraLayer(parent));
				helper.register(new LanternCarry(parent));
			}
			helper.register(new SoulSightLayer<>(raw(renderer)));
		});

		LevelRenderEvents.COLLECT_SUBMITS.register(HelixBeams::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(BlastDrillFx::render);
		LevelRenderEvents.COLLECT_SUBMITS.register(FearNukeFx::render);

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
			LanternKeyInput.tick(client, lanternKey);
			while (wheelKey.consumeClick()) {
				if (client.player == null) continue;
				ItemStack ring = client.player.getMainHandItem().is(ModRegistry.POWER_RING) ? client.player.getMainHandItem()
						: client.player.getOffhandItem().is(ModRegistry.POWER_RING) ? client.player.getOffhandItem() : null;
				if (ring != null) client.setScreenAndShow(new ModeWheelScreen(wheelKey, ring));
			}
			LanternRingClientState.tick();
			FastFlight.tick(client);
			SuperJumpInput.tick(client);
			SuperJumpAir.tick(client);
			SuperJumpFx.tick(client);
			SuperLandConstruct.tick(client);
			FlightPoses.tick(client);
			FlightTrail.tick(client);
			RamBarrierFx.tick(client);
			LabFx.tick(client);
			LanternSlotFx.tick(client);
			LanternFirstPerson.tick(client);
			LanternLight.tick(client);
			LanternGlare.tick(client);
			LanternFlash.tick(client);
			FearBlind.tick(client);
			RageTint.tick(client);
			SunDim.tick(client);
			LanternShrine.tick(client);
			DelugeGlare.tick(client);
			LanternPlaceInput.tick(client);
			LanternChargeInput.tick(client);
			ShaderPackIds.tick(client);
			LassoFx.tick(client);
			DismissFx.tick(client);
			PortalFx.tick(client);
			GolemFx.tick(client);
			AnvilInput.tick(client);
			DelugeRecallInput.tick(client);
			BridgeInput.tick(client);
		});
	}

	private static void particle(SimpleParticleType type, ConstructParticle.Behavior behavior, Corps corps) {
		ParticleProviderRegistry.getInstance().register(type, sprites ->
				(options, level, x, y, z, vx, vy, vz, random) -> new ConstructParticle(level, x, y, z, vx, vy, vz, sprites, behavior, corps));
	}

	@SuppressWarnings({"unchecked", "rawtypes"})
	private static RenderLayerParent raw(Object renderer) {
		return (RenderLayerParent) renderer;
	}
}
