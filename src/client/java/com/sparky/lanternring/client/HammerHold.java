package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.net.RingFxPayload;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;

/**
 * The Hammer mode's construct hammer (J, 2026-10-13: a solid hard-light hammer in your hand): a
 * sledgehammer of see-through hard light in the corps colour, like the Shield's glass, with a bright
 * rim on the head. It forms in the ring hand as you leap, is hauled up behind your head on the way
 * up, swung down over it as you land (both arms on the handle), and fades a moment after the smash.
 * The server announces each leap (RingFxPayload HAMMER_LEAP: value is the leap's ticks), so every
 * client draws everyone's. Third person draws it on the arm ({@link #pose}, {@link #submitOnArm}),
 * first person in front of you ({@link #submitFirstPerson}).
 */
public final class HammerHold {
	private static final Identifier GLASS = LanternRing.id("textures/entity/shockwave_glass.png");
	private static final int FULL_BRIGHT = 0xF000F0;
	/** Ticks the hammer stays down on the ground after the smash, fading over the last of them. */
	private static final int LINGER = 10;
	/** The hammer, in blocks: handle length and half-thickness, the head's half sizes (its long side along the swing). */
	private static final float HANDLE = 1.35f, GRIP_BELOW = 0.15f, HANDLE_HALF = 0.055f;
	private static final float HEAD_HALF_LONG = 0.42f, HEAD_HALF = 0.24f;
	/** The faces are see-through, the head's edges glow solid. */
	private static final float FACE_ALPHA = 0.55f, RIM_ALPHA = 0.95f;
	private static final float[] JADE = {0.80f, 1f, 0.85f};
	private static final float[] EDGE = {0.85f, 1f, 0.9f};
	/** Third person arm angle (xRot): raised up and back behind the head, and swung down in front. */
	private static final float WIND = -Mth.PI - 0.55f, STRUCK = -0.45f;
	/** First person: where the hammer's grip is in hand space, and its tilt back (raised) and forward (struck). */
	private static final float[] VIEW_GRIP = {0.12f, -0.35f, -1.1f};
	private static final float VIEW_WIND = 0.9f, VIEW_STRUCK = -1.5f;
	private static final float VIEW_SCALE = 0.7f;

	private record Leap(long start, int ticks, Corps corps) {
	}

	private static final Int2ObjectMap<Leap> LEAPS = new Int2ObjectOpenHashMap<>();

	private HammerHold() {
	}

	/** HAMMER_LEAP: the bearer has just jumped, landing in value ticks. */
	public static void handle(RingFxPayload fx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || fx.bearer() < 0) return;
		LEAPS.put(fx.bearer(), new Leap(mc.level.getGameTime(), Math.max(1, Math.round(fx.value())), fx.corps()));
	}

	/** How far through the leap this player is: 0 to 1 in the air, above 1 after landing, -1 for no hammer. */
	private static float progress(Player player, float partial) {
		Minecraft mc = Minecraft.getInstance();
		Leap leap = player == null || mc.level == null ? null : LEAPS.get(player.getId());
		if (leap == null) return -1f;
		float age = mc.level.getGameTime() - leap.start + partial;
		if (age > leap.ticks + LINGER || age < 0) {
			if (age > leap.ticks + LINGER + 20 || age < -20) LEAPS.remove(player.getId());
			return -1f;
		}
		return age / leap.ticks;
	}

	/**
	 * Where the swing is: -1 to 0 while it's hauled up (from in front at -1 to wound up behind the
	 * head at 0, by the top of the arc), 0 to 1 as it's swung down over the head to the strike at
	 * the landing, faster and faster.
	 */
	private static float swing(float t) {
		if (t < 0.5f) {
			float u = t * 2;
			return -(1 - u) * (1 - u);
		}
		float u = Math.min(1f, (t - 0.5f) * 2);
		return u * u;
	}

	/** How solid the hammer is: forms over the first part of the leap, fades after the smash. */
	private static float alpha(Player player, float t) {
		Leap leap = LEAPS.get(player.getId());
		float form = Mth.clamp(t * 5f, 0f, 1f);
		float fade = t <= 1f || leap == null ? 1f : 1f - Mth.clamp((t - 1f) * leap.ticks / LINGER, 0f, 1f);
		return form * fade;
	}

	/** The arm angle for swing s (-1 lifting in front, 0 wound up behind the head, 1 struck). */
	private static float armAngle(float s) {
		return s <= 0 ? Mth.lerp(s + 1, -0.6f, WIND) : Mth.lerp(s, WIND, STRUCK);
	}

	private static Corps corps(Player player) {
		Leap leap = LEAPS.get(player.getId());
		return leap == null ? Corps.GREEN : leap.corps;
	}

	/** Third person: both arms on the handle, hauled up and back and swung down over the head. */
	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player)) return;
		float t = progress(player, mc.getDeltaTracker().getGameTimeDeltaPartialTick(false));
		if (t < 0f) return;
		float x = armAngle(swing(Math.min(t, 1f)));
		boolean right = player.getMainArm() == HumanoidArm.RIGHT;
		// The ring arm holds the end of the handle, the other hand just above it, both turned in.
		model.rightArm.xRot = x;
		model.leftArm.xRot = x;
		model.rightArm.yRot = right ? -0.12f : -0.35f;
		model.leftArm.yRot = right ? 0.35f : 0.12f;
		model.rightArm.zRot = 0f;
		model.leftArm.zRot = 0f;
	}

	/** Third person: the hammer in the ring hand, its handle running on out of the fist along the arm. */
	public static void submitOnArm(PoseStack pose, SubmitNodeCollector collector, ModelPart armPart, boolean right, Player player, float partial) {
		float t = progress(player, partial);
		if (t < 0f || (player.getMainArm() == HumanoidArm.RIGHT) != right) return;
		float a = alpha(player, t);
		if (a <= 0.01f) return;
		pose.pushPose();
		armPart.translateAndRotate(pose);
		// In the fist, across towards the other hand a touch.
		pose.translate((right ? 1 : -1) * 1f / 16f, 10f / 16f, 0f);
		// Model space runs y down the arm, so the handle carries on along +y past the fist.
		submit(pose, collector, corps(player), a, player, 1f);
		pose.popPose();
	}

	/** First person: the hammer comes over from behind your head and down in front of you. */
	public static void submitFirstPerson(PoseStack pose, SubmitNodeCollector collector, InteractionHand hand, float partial) {
		Player player = Minecraft.getInstance().player;
		if (player == null || hand != InteractionHand.MAIN_HAND) return;
		float t = progress(player, partial);
		if (t < 0f) return;
		float a = alpha(player, t);
		if (a <= 0.01f) return;
		float s = swing(Math.min(t, 1f));
		// Tilt: 0 is the handle straight up; plus leans it back over your head, minus forward and down.
		float tilt = s <= 0 ? Mth.lerp(s + 1, -0.6f, VIEW_WIND) : Mth.lerp(s, VIEW_WIND, VIEW_STRUCK);
		float f = player.getMainArm() == HumanoidArm.RIGHT ? 1f : -1f;
		pose.pushPose();
		pose.translate(f * VIEW_GRIP[0], VIEW_GRIP[1], VIEW_GRIP[2]);
		pose.rotateDegrees(Axis.YP, f * 4f);
		pose.rotateDegrees(Axis.XP, (float) Math.toDegrees(tilt));
		pose.scale(VIEW_SCALE, VIEW_SCALE, VIEW_SCALE);
		submit(pose, collector, corps(player), a, player, 0.75f);
		pose.popPose();
	}

	/** The hammer with its grip at the origin and the handle along +y, the head across its end. */
	private static void submit(PoseStack pose, SubmitNodeCollector collector, Corps corps, float a, Player player, float faceAlpha) {
		float[] face = CorpsTint.apply(corps, JADE[0], JADE[1], JADE[2]);
		float[] edge = CorpsTint.apply(corps, EDGE[0], EDGE[1], EDGE[2]);
		RenderType glass = RenderTypes.entityTranslucentEmissive(CorpsTint.texture(GLASS, corps));
		float now = player.tickCount + Minecraft.getInstance().getDeltaTracker().getGameTimeDeltaPartialTick(false);
		// The Shield's smoke animation: 64 frames in an 8x8 grid, 3 ticks each.
		int frame = Math.floorMod((int) (now / 3), 64);
		float cell = 1f / 8, fu = (frame % 8) * cell, fv = (frame / 8) * cell;
		collector.submitCustomGeometry(pose, glass, (p, vc) -> {
			float[] uv = {fu, fv, cell};
			// The handle, with a brighter grip.
			box(p, vc, uv, -HANDLE_HALF, -GRIP_BELOW, -HANDLE_HALF, HANDLE_HALF, HANDLE, HANDLE_HALF, edge, a * RIM_ALPHA);
			// The head: a see-through block with a solid band round each end.
			float hy = HANDLE + HEAD_HALF * 0.6f;
			box(p, vc, uv, -HEAD_HALF, hy - HEAD_HALF, -HEAD_HALF_LONG + 0.08f, HEAD_HALF, hy + HEAD_HALF, HEAD_HALF_LONG - 0.08f, face, a * faceAlpha);
			for (int s = -1; s <= 1; s += 2) {
				float z0 = s < 0 ? -HEAD_HALF_LONG : HEAD_HALF_LONG - 0.08f;
				box(p, vc, uv, -HEAD_HALF - 0.02f, hy - HEAD_HALF - 0.02f, z0, HEAD_HALF + 0.02f, hy + HEAD_HALF + 0.02f, z0 + 0.08f, edge, a * RIM_ALPHA);
			}
		});
	}

	/** An axis-aligned box, every face drawn both ways round so it shows from inside and out. */
	private static void box(PoseStack.Pose pose, VertexConsumer vc, float[] uv, float x0, float y0, float z0, float x1, float y1, float z1,
			float[] tint, float alpha) {
		float[][] c = {{x0, y0, z0}, {x1, y0, z0}, {x1, y1, z0}, {x0, y1, z0}, {x0, y0, z1}, {x1, y0, z1}, {x1, y1, z1}, {x0, y1, z1}};
		int[][] faces = {{0, 3, 2, 1}, {4, 5, 6, 7}, {0, 4, 7, 3}, {1, 2, 6, 5}, {0, 1, 5, 4}, {3, 7, 6, 2}};
		float[][] normals = {{0, 0, -1}, {0, 0, 1}, {-1, 0, 0}, {1, 0, 0}, {0, -1, 0}, {0, 1, 0}};
		float[][] corners = {{0, 0}, {0, 1}, {1, 1}, {1, 0}};
		float inset = 0.5f / 1024f, span = uv[2] - 2 * inset;
		for (int f = 0; f < 6; f++) {
			for (int side = 0; side < 2; side++) {
				float sign = side == 0 ? 1 : -1;
				for (int k = 0; k < 4; k++) {
					int i = side == 0 ? k : 3 - k;
					float[] p = c[faces[f][i]];
					vc.addVertex(pose, p[0], p[1], p[2])
							.setColor(tint[0], tint[1], tint[2], alpha)
							.setUv(uv[0] + inset + span * corners[i][0], uv[1] + inset + span * corners[i][1])
							.setOverlay(OverlayTexture.NO_OVERLAY)
							.setLight(FULL_BRIGHT)
							.setNormal(pose, sign * normals[f][0], sign * normals[f][1], sign * normals[f][2]);
				}
			}
		}
	}
}
