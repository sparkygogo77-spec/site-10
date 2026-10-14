package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.item.ConstructTools;
import com.sparky.lanternring.item.ConstructTools.Tool;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.HashMap;
import java.util.Map;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import org.joml.Matrix4f;
import org.jspecify.annotations.Nullable;

/**
 * Draws the construct tool a Green or Blue ring forms in its hand (ConstructTools: J's T3 and U3
 * designs). Every client works it out for every player from what they swing at, so it needs no
 * packets: a swing at a block forms that block's tool, a swing at a mob or at the air the sword. It
 * grows out of the ring as the swing starts, stays a moment after the last one and fades away.
 * Third person draws it on the ring arm (RingHandLayer), first person on your fist
 * (RingFirstPerson); both call {@link #submitInHand} in the arm's own space.
 */
public final class ConstructToolHold {
	/** Ticks to form, how long it stays after the last swing, and how long it takes to fade. */
	private static final int FORM = 3, STAY = 30, FADE = 8;
	/** The models are about 30 px tall at half a pixel per voxel: half size is a sword's length. */
	private static final float SCALE = 0.5f;
	/** Where the hand closes on the handle, up from the pommel (model px). */
	private static final float GRIP = 5f;
	/** How far a reach counts when working out what someone else swings at. */
	private static final double REACH = 4.5;

	private record Track(Tool tool, Corps corps, long since, long last) {
	}

	private static final Int2ObjectMap<Track> TRACKS = new Int2ObjectOpenHashMap<>();
	private static final Map<String, BbModel> MODELS = new HashMap<>();

	private ConstructToolHold() {
	}

	public static void register() {
		ClientTickEvents.END_CLIENT_TICK.register(ConstructToolHold::tick);
	}

	private static void tick(Minecraft mc) {
		if (mc.level == null) {
			TRACKS.clear();
			return;
		}
		long now = mc.level.getGameTime();
		for (Player p : mc.level.players()) {
			if (!ConstructTools.forms(p.getMainHandItem())) {
				TRACKS.remove(p.getId());
				continue;
			}
			boolean mining = p == mc.player && mc.gameMode != null && mc.gameMode.isDestroying();
			if (!p.isSwinging() && !mining) continue;
			Tool tool = aim(mc, p);
			Corps corps = Corps.of(p.getMainHandItem());
			Track t = TRACKS.get(p.getId());
			// A new tool forms afresh; the same one just stays longer.
			long since = t != null && t.tool == tool && now - t.last <= STAY + FADE ? t.since : now;
			TRACKS.put(p.getId(), new Track(tool, corps, since, now));
		}
		TRACKS.int2ObjectEntrySet().removeIf(e -> now - e.getValue().last > STAY + FADE);
	}

	/** The tool for what {@code p} is swinging at. */
	private static Tool aim(Minecraft mc, Player p) {
		HitResult hit = p == mc.player ? mc.hitResult : p.pick(REACH, 1f, false);
		if (hit instanceof BlockHitResult b && hit.getType() == HitResult.Type.BLOCK) {
			Tool tool = ConstructTools.forBlock(p.level().getBlockState(b.getBlockPos()));
			return tool == null ? Tool.SWORD : tool;
		}
		return Tool.SWORD;
	}

	/** 0..1 how far the tool is formed in {@code player}'s hand, and which tool, or null if none. */
	private static @Nullable Track track(Player player) {
		return TRACKS.get(player.getId());
	}

	private static float shown(Track t, Player player, float partial) {
		float now = player.level().getGameTime() + partial;
		float in = Mth.clamp((now - t.since) / FORM, 0f, 1f);
		float out = 1f - Mth.clamp((now - t.last - STAY) / FADE, 0f, 1f);
		return Math.min(in, out);
	}

	/**
	 * Draws {@code player}'s formed tool held in the hand, with {@code pose} in the arm's space (after
	 * the arm part's translateAndRotate; y runs down the arm, the hand at its end).
	 */
	public static void submitInHand(PoseStack pose, SubmitNodeCollector collector, int light, Player player, boolean right, float partial) {
		Track t = track(player);
		if (t == null) return;
		float a = shown(t, player, partial);
		if (a <= 0.01f) return;
		BbModel model = MODELS.computeIfAbsent(t.tool.model(t.corps), BbModel::load);
		pose.pushPose();
		// The fist, at the end of the arm.
		pose.translate((right ? -1f : 1f) / 16f, 10f / 16f, 0f);
		// Model up (+y) points ahead of the fist (-z); its head's side (-x, the axe blade) leads the swing (+y down the arm).
		pose.mulPose(new Matrix4f(0f, -1f, 0f, 0f, 0f, 0f, -1f, 0f, 1f, 0f, 0f, 0f, 0f, 0f, 0f, 1f));
		// Grows out of the fist as it forms.
		float s = SCALE * (0.3f + 0.7f * a);
		pose.scale(s, s, s);
		pose.translate(0f, -GRIP / 16f, 0f);
		model.render(pose, collector, light, BbModel.glow(a));
		pose.popPose();
	}

	/** First person: the tool stands up from the fist in hand space (x right, y up, z toward you), leant away and in, at this size. */
	private static final float VIEW_LEAN = 20f, VIEW_IN = 20f, VIEW_SCALE = 0.75f;
	/** How far the swing tips it forward, in degrees. */
	private static final float VIEW_SWING = 70f;

	/**
	 * First person: {@code pose} is in your arm's space (as {@link #submitInHand}), {@code base} and
	 * {@code baseNormal} the hand space before the arm was placed. The tool sits on the fist, but
	 * stands up in hand space rather than lying along the arm, and tips forward with the swing.
	 */
	public static void submitFirstPerson(PoseStack pose, Matrix4f base, org.joml.Matrix3f baseNormal, SubmitNodeCollector collector, int light,
			Player player, boolean right, float swing, float partial) {
		Track t = track(player);
		if (t == null) return;
		float a = shown(t, player, partial);
		if (a <= 0.01f) return;
		pose.pushPose();
		pose.translate((right ? -1f : 1f) / 16f, 9f / 16f, 0f);
		org.joml.Vector3f fist = new Matrix4f(base).invert().mul(pose.last().pose()).getTranslation(new org.joml.Vector3f());
		pose.popPose();
		BbModel model = MODELS.computeIfAbsent(t.tool.model(t.corps), BbModel::load);
		PoseStack view = new PoseStack();
		view.last().pose().set(base);
		view.last().normal().set(baseNormal);
		view.translate(fist.x, fist.y, fist.z);
		float f = right ? 1f : -1f;
		// Head side on to you so its shape shows, the blade (-x) towards the middle; tipped in, and away from you as you swing.
		view.rotateDegrees(com.mojang.math.Axis.ZP, f * VIEW_IN);
		view.rotateDegrees(com.mojang.math.Axis.XP, -(VIEW_LEAN + VIEW_SWING * Mth.sin(swing * Mth.PI)));
		if (!right) view.scale(-1f, 1f, 1f);
		float s = VIEW_SCALE * (0.3f + 0.7f * a);
		view.scale(s, s, s);
		view.translate(0f, -GRIP / 16f, 0f);
		model.render(view, collector, light, BbModel.glow(a));
	}
}
