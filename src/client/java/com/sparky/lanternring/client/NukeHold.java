package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.corps.AerialDrops;
import com.sparky.lanternring.corps.FearNuke;
import com.sparky.lanternring.item.PowerRingItem;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * Building the Fear Nuke in the hand (J, 2026-10-13: "the ring should be locked into the
 * constructing position which people should see your hand come up when you use the ring"). While a
 * Yellow ring is held in Aerial mode, its arm goes straight up and stays locked there, and the bomb
 * (fear_nuke.bbmodel, J's hand-built model to come) assembles plate by plate on the fist over
 * RingTuning.FEAR_NUKE_BUILD. Every client tracks every bearer from their held item, so it needs no
 * packets; first and third person both draw it.
 */
public final class NukeHold {
	/** How fast the arm comes up and goes down, per tick (0..1). */
	private static final float RAISE_STEP = 0.25f, LOWER_STEP = 0.2f;
	/** Third person: the ring arm straight up (model pitch; slightly out from the head). */
	public static float upX = -2.95f, upZ = 0.18f;
	/** The bomb's length on the fist when it's built, in blocks; the world model (FearNukeFx) is 3.5 long at scale 1. */
	public static float handLength = 1.2f, firstPersonLength = 0.55f;
	/** The nose's depth below the model's middle, in model units (as FearNukeFx). */
	private static final float NOSE = 23f;
	private static final float MODEL_LENGTH = 3.5f;

	private static final class Track {
		float raise, prevRaise;
		HumanoidArm arm = HumanoidArm.RIGHT;
		Corps corps = Corps.YELLOW;
		/** Ticks it has been building, and last tick's (for smooth growth). */
		float built, prevBuilt;
	}

	private static final Int2ObjectMap<Track> TRACKS = new Int2ObjectOpenHashMap<>();
	private static final java.util.Map<Corps, BbModel> MODELS = new java.util.EnumMap<>(Corps.class);

	private NukeHold() {
	}

	public static void register() {
		ClientTickEvents.END_CLIENT_TICK.register(NukeHold::tick);
	}

	/** Whether {@code player} is building a Fear Nuke right now (holding a Yellow ring in Aerial mode, charged enough). */
	static boolean building(Player player) {
		if (!player.isUsingItem()) return false;
		ItemStack used = player.getUseItem();
		if (!(used.getItem() instanceof PowerRingItem) || PowerRingItem.getMode(used) != RingMode.AERIAL || Corps.of(used) != Corps.YELLOW) return false;
		if (player == Minecraft.getInstance().player && !player.isCreative()) {
			// Our own copy knows the charge; the server won't build without it.
			return PowerRingItem.getCharge(used) >= AerialDrops.cost(used) && !player.getCooldowns().isOnCooldown(used);
		}
		return true;
	}

	private static void tick(Minecraft mc) {
		if (mc.level == null || mc.isPaused()) {
			if (mc.level == null) TRACKS.clear();
			return;
		}
		for (Player player : mc.level.players()) {
			boolean up = building(player);
			Track t = TRACKS.get(player.getId());
			if (t == null) {
				if (!up) continue;
				t = new Track();
				TRACKS.put(player.getId(), t);
			}
			t.prevRaise = t.raise;
			t.prevBuilt = t.built;
			if (up) {
				t.arm = RingEmit.ringArm(player);
				t.corps = Corps.of(player.getUseItem());
				t.raise = Math.min(1f, t.raise + RAISE_STEP);
				t.built = Math.min(t.built + 1, FearNuke.buildTicks());
			} else {
				t.raise = Math.max(0f, t.raise - LOWER_STEP);
				// Let go: it has flown (FearNukeFx takes over) or come apart.
				t.built = 0;
				t.prevBuilt = 0;
			}
		}
		TRACKS.int2ObjectEntrySet().removeIf(e -> e.getValue().raise <= 0 && e.getValue().prevRaise <= 0
				|| !(mc.level.getEntity(e.getIntKey()) instanceof Player));
	}

	/** 0 = down, 1 = locked straight up; eased so it snaps up and settles. */
	public static float raise(Player player, float partial) {
		Track t = player == null ? null : TRACKS.get(player.getId());
		if (t == null) return 0f;
		float r = Mth.lerp(partial, t.prevRaise, t.raise);
		return 1f - (1f - r) * (1f - r);
	}

	/** How far the bomb on the fist is built, 0..1. */
	public static float built(Player player, float partial) {
		Track t = player == null ? null : TRACKS.get(player.getId());
		if (t == null) return 0f;
		return Mth.clamp(Mth.lerp(partial, t.prevBuilt, t.built) / FearNuke.buildTicks(), 0f, 1f);
	}

	/** The arm holding the bomb up, or null. */
	public static HumanoidArm arm(Player player) {
		Track t = player == null ? null : TRACKS.get(player.getId());
		return t == null ? null : t.arm;
	}

	/** Third person: locks the ring arm straight up over the head (after every other pose). */
	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player)) return;
		float r = raise(player, mc.getDeltaTracker().getGameTimeDeltaPartialTick(false));
		HumanoidArm side = arm(player);
		if (r <= 0f || side == null) return;
		boolean right = side == HumanoidArm.RIGHT;
		ModelPart arm = right ? model.rightArm : model.leftArm;
		arm.xRot = Mth.lerp(r, arm.xRot, upX);
		arm.yRot = Mth.lerp(r, arm.yRot, 0f);
		arm.zRot = Mth.lerp(r, arm.zRot, right ? upZ : -upZ);
	}

	/** Third person: the bomb on the raised fist of {@code armPart}. */
	public static void submitOnArm(PoseStack pose, SubmitNodeCollector collector, ModelPart armPart, boolean right, Player player, float partial) {
		if (arm(player) != (right ? HumanoidArm.RIGHT : HumanoidArm.LEFT) || raise(player, partial) < 0.5f) return;
		pose.pushPose();
		armPart.translateAndRotate(pose);
		submitBomb(pose, collector, player, partial, handLength, 11f / 16f);
		pose.popPose();
	}

	/**
	 * Draws the bomb as built so far on the end of the fist, in arm space (the arm runs down +y to
	 * the fist, which with the arm raised is straight up). {@code fist} is the fist's end along the arm.
	 */
	static void submitBomb(PoseStack pose, SubmitNodeCollector collector, Player player, float partial, float length, float fist) {
		float built = built(player, partial);
		Track t = TRACKS.get(player.getId());
		if (t == null) return;
		float scale = length / MODEL_LENGTH;
		// It swells a touch as each plate locks on, and settles once it's built.
		float age = player.tickCount + partial;
		float throb = built < 1f ? 1f + 0.03f * Mth.sin(age * 1.7f) : 1f + 0.015f * Mth.sin(age * 0.5f);
		float s = scale * throb;
		pose.pushPose();
		// The nose (model -y) rests on the fist; the arm's +y runs on up past it.
		pose.translate(0f, fist + NOSE / 16f * s, 0f);
		pose.rotateDegrees(Axis.YP, age * 2f);
		pose.scale(s, s, s);
		BbModel tinted = MODELS.computeIfAbsent(t.corps, corps -> BbModel.load("fear_nuke").forCorps(corps));
		float bright = built < 1f ? 0.5f + 0.3f * built : 0.85f + 0.15f * Mth.sin(age * 0.6f);
		tinted.renderBuilt(pose, collector, BbModel.glow(bright), Math.max(0.04f, built));
		pose.popPose();
	}

	public static void clear() {
		TRACKS.clear();
	}
}
