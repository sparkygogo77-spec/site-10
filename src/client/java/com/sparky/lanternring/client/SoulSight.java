package com.sparky.lanternring.client;

import com.mojang.renderpearl.api.pipeline.BlendFunction;
import com.mojang.renderpearl.api.pipeline.ColorTargetState;
import com.mojang.renderpearl.api.pipeline.CompareOp;
import com.mojang.renderpearl.api.pipeline.DepthStencilState;
import com.mojang.renderpearl.api.pipeline.RenderPipeline;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.infinity.Infinity;
import com.sparky.lanternring.infinity.InfinityGauntletItem;
import com.sparky.lanternring.infinity.InfinityStone;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.client.renderer.rendertype.RenderSetup;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.TextureTransform;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * Soul sight: while you hold the Soul Stone (or a Gauntlet with it set in), other players, and
 * mobs unless the Ring Lab's Soul sight says otherwise, show as orange silhouettes through walls.
 * Drawn two ways: the game's Glowing outline in orange (EntityRendererMixin, MinecraftMixin), and,
 * without a shader pack, an additive orange shell drawn with no depth test (SoulSightLayer). Iris
 * can't run that shell's custom pipeline (under Complementary it drew huge black shapes over the
 * screen), so with a shader pack on only the outline is drawn; Iris keeps it.
 */
public final class SoulSight {
	/** The silhouette's orange, and how far away things still show. */
	public static final int ORANGE = 0xFF8A1C;
	private static final double RANGE = 96;

	/** Like the energy swirl (additive, full-bright) but drawn in front of everything. */
	private static final RenderPipeline PIPELINE = RenderPipelines.register(RenderPipeline.builder(RenderPipelines.ENERGY_SWIRL_SNIPPET)
			.withLocation(LanternRing.id("pipeline/soul_sight"))
			.withColorTargetState(new ColorTargetState(BlendFunction.ADDITIVE))
			.withDepthStencilState(new DepthStencilState(CompareOp.ALWAYS_PASS, false))
			.build());
	public static final RenderType FILL = type("fill", LanternRing.id("textures/entity/soul_sight.png"));
	public static final RenderType EDGE = type("edge", LanternRing.id("textures/entity/ring_aura_edge.png"));

	/** Added to every EntityRenderState by EntityRenderStateMixin. */
	public interface Holder {
		boolean lanternring$soulSight();

		void lanternring$setSoulSight(boolean seen);
	}

	private SoulSight() {
	}

	private static RenderType type(String name, net.minecraft.resources.Identifier texture) {
		return RenderType.create("lanternring_soul_sight_" + name, RenderSetup.builder(PIPELINE)
				.withTexture("Sampler0", texture)
				.setTextureTransform(TextureTransform.DEFAULT_TEXTURING)
				.useLightmap()
				.useOverlay()
				.sortOnUpload()
				.createRenderSetup());
	}

	/** Loads the class so its pipeline is registered before the game compiles shaders. */
	public static void register() {
	}

	private static final boolean IRIS = net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("iris");
	private static java.lang.reflect.Method shaderPackInUse;
	private static Object irisApi;
	private static boolean irisFailed;

	private static long packCheckedAt = Long.MIN_VALUE;
	private static boolean packOn;

	/** Whether Iris is drawing with a shader pack (assumed so if Iris is there but can't be asked). Asked at most every 250 ms: it is called per model part per frame. */
	public static boolean shaderPackOn() {
		if (!IRIS) return false;
		if (irisFailed) return true;
		long now = System.nanoTime();
		if (now - packCheckedAt < 250_000_000L) return packOn;
		packCheckedAt = now;
		packOn = askIris();
		return packOn;
	}

	private static boolean askIris() {
		try {
			if (shaderPackInUse == null) {
				Class<?> api = Class.forName("net.irisshaders.iris.api.v0.IrisApi");
				irisApi = api.getMethod("getInstance").invoke(null);
				shaderPackInUse = api.getMethod("isShaderPackInUse");
			}
			return (Boolean) shaderPackInUse.invoke(irisApi);
		} catch (ReflectiveOperationException | RuntimeException e) {
			irisFailed = true;
			return true;
		}
	}

	/** Whether the local player holds the Soul Stone. */
	public static boolean active() {
		Player me = Minecraft.getInstance().player;
		if (me == null || LabSettings.get().soulSight == LabSettings.SoulSightMode.OFF) return false;
		return soul(me.getMainHandItem()) || soul(me.getOffhandItem());
	}

	private static boolean soul(ItemStack stack) {
		return stack.is(Infinity.SOUL_STONE)
				|| stack.getItem() instanceof InfinityGauntletItem && InfinityGauntletItem.has(stack, InfinityStone.SOUL);
	}

	/** Whether this entity shows through walls for the local player right now. */
	public static boolean sees(Entity entity) {
		Player me = Minecraft.getInstance().player;
		if (me == null || entity == me || !(entity instanceof LivingEntity living) || !living.isAlive() || entity.isSpectator()) return false;
		if (!(entity instanceof Player) && !(entity instanceof Mob && LabSettings.get().soulSight == LabSettings.SoulSightMode.PLAYERS_AND_MOBS)) return false;
		return entity.distanceToSqr(me) < RANGE * RANGE && active();
	}
}
