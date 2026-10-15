package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.item.ConstructToolItem;
import com.sparky.lanternring.item.ConstructTools;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.item.ItemStackRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.PlayerRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.PlayerModelType;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/**
 * Blender pass 844 S3b (J's KEEP, 2026-10-15), the construct sword in first person: your ring arm holds it (the ring on
 * the punching face), it extrudes out of the fist behind a glowing scan plate when you switch to it (ticks 0-14), and
 * every swing is the stepping wide sweep pair: across to the right, then back across to the left (contacts at ticks 5
 * and 10; the backswing's hit is SwordSweeps on the server). The poses are the take's (tools/fp_sword_poses.py packs
 * them into poses/fp_sword.json) on the 844 rig: the shoulder 0.36 right, 0.42 down and 0.12 ahead of the eye, the arm
 * 12 first-person pixels long, the grip 10.6 px down it.
 */
public final class SwordSwing {
	/** The 844 rig, in Blender eye space (x right, y ahead, z up), metres. */
	private static final float PX = 1f / 16f * 1.05f;
	private static final Vector3f SHOULDER = new Vector3f(0.36f, 0.12f, -0.42f);
	private static final float ARM = 12 * PX;
	private static final Vector3f GRIP = new Vector3f(0f, -1.1f * PX, -10.6f * PX);
	/** The sword item model is its bbmodel scaled by 15/29 into 0.5-15.5 px; Blender draws the bbmodel at 1/32 m a unit. */
	private static final float ITEM_SCALE = (1f / 32f) / (15f / 29f / 16f), ITEM_GRIP_Y = 0.5f / 16f;
	/** Ticks after the swing to ease the sword's twist back to rest. */
	private static final float SETTLE = 6f;
	private static final Identifier GLASS = LanternRing.id("textures/entity/shockwave_glass.png");

	private static float[] rest = {96, 14, 0, 22, 0, 0};
	private static float[][] ticks = {rest};
	private static int form = 14, swingTicks = 15;
	private static boolean loaded;

	private static long formStart = Long.MIN_VALUE / 2, swingStart = Long.MIN_VALUE / 2;
	private static ItemStack last = ItemStack.EMPTY;
	private static final ItemStackRenderState ITEM = new ItemStackRenderState();

	private SwordSwing() {
	}

	private static void load() {
		if (loaded) return;
		loaded = true;
		try (InputStream in = SwordSwing.class.getResourceAsStream("/assets/" + LanternRing.MOD_ID + "/poses/fp_sword.json")) {
			JsonObject o = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("S3B");
			form = o.get("form").getAsInt();
			swingTicks = o.get("swing").getAsInt();
			rest = row(o.getAsJsonArray("rest"));
			JsonArray t = o.getAsJsonArray("ticks");
			ticks = new float[t.size()][];
			for (int i = 0; i < t.size(); i++) ticks[i] = row(t.get(i).getAsJsonArray());
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't read the S3b sword poses", e);
		}
	}

	private static float[] row(JsonArray a) {
		float[] r = new float[a.size()];
		for (int i = 0; i < r.length; i++) r[i] = a.get(i).getAsFloat();
		return r;
	}

	private static boolean isSword(ItemStack stack) {
		return stack.getItem() instanceof ConstructToolItem t && t.tool == ConstructTools.Tool.SWORD;
	}

	/** Every client tick: the sword forms when it comes into your hand, and each swing starts the take. */
	public static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.level == null) return;
		long now = mc.level.getGameTime();
		ItemStack main = p.getMainHandItem();
		if (isSword(main) && !ItemStack.isSameItem(main, last)) formStart = now;
		last = main.copy();
		// A new swing of the main hand: it started since last tick, or restarted (its animation went back).
		boolean swinging = p.isSwinging() && p.getCurrentSwing() != null && p.getCurrentSwing().hand() == InteractionHand.MAIN_HAND;
		float anim = p.getSwingAnimation(1f);
		boolean started = swinging && (!wasSwinging || anim < lastAnim);
		wasSwinging = swinging;
		lastAnim = anim;
		if (isSword(main) && started && now - swingStart >= swingTicks) swingStart = now;
	}

	private static boolean wasSwinging;
	private static float lastAnim;

	/** The pose at time {@code k} into the swing (ticks): pitch, yaw, roll, tilt, reach, twist; rest outside it. */
	static float[] pose(float k) {
		load();
		if (k < 0 || k > swingTicks + SETTLE) return rest;
		if (k <= swingTicks) {
			int i = Math.min(ticks.length - 2, (int) Math.floor(k));
			float w = k - i;
			float[] a = ticks[i], b = ticks[i + 1], out = new float[6];
			for (int j = 0; j < 6; j++) out[j] = Mth.lerp(w, a[j], b[j]);
			return out;
		}
		// Settling: the twist goes back the short way round (the blade is the same either way up, so modulo 180).
		float[] end = ticks[ticks.length - 1], out = rest.clone();
		float d = Mth.positiveModulo(end[5] - rest[5] + 90f, 180f) - 90f;
		out[5] = rest[5] + d * (1f - smooth((k - swingTicks) / SETTLE));
		return out;
	}

	private static float smooth(float t) {
		t = Mth.clamp(t, 0f, 1f);
		return t * t * (3 - 2 * t);
	}

	/** How far the sword has extruded out of the fist: 0 for the first 3 ticks, then up to 1 by the forming's end. */
	static float grown(float since) {
		return since < 3 ? 0.001f : Math.max(0.001f, smooth((since - 3) / (form - 3)));
	}

	/** Blender eye space (x right, y ahead, z up) to view space (x right, y up, -z ahead). */
	private static final Matrix4f BLENDER_TO_VIEW = new Matrix4f(1, 0, 0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 1);

	/** The arm's matrix in Blender eye space: at the shoulder, Euler XYZ (pitch, 0, yaw) then roll about its own Z. */
	private static Matrix4f arm(float[] p) {
		return new Matrix4f().translate(SHOULDER.x, SHOULDER.y + p[4], SHOULDER.z)
				.rotateZ(p[1] * Mth.DEG_TO_RAD).rotateX(p[0] * Mth.DEG_TO_RAD).rotateZ(p[2] * Mth.DEG_TO_RAD);
	}

	/** Draws the arm, ring and sword; false when the main hand isn't holding the construct sword. */
	public static boolean render(PlayerRenderState playerState, InteractionHand hand, ItemStack stack, PoseStack poseStack,
			SubmitNodeCollector collector, int light, float partial) {
		if (hand != InteractionHand.MAIN_HAND || !isSword(stack)) return false;
		Minecraft mc = Minecraft.getInstance();
		AvatarRenderState avatar = playerState.avatarRenderState;
		if (avatar == null || avatar.skin == null || mc.level == null || mc.player == null) return false;
		float now = mc.level.getGameTime() + partial;
		float[] p = pose(now - swingStart);
		float grow = grown(now - formStart);
		boolean right = avatar.mainArm == HumanoidArm.RIGHT;
		boolean slim = avatar.skin.model() == PlayerModelType.SLIM;
		float f = right ? 1f : -1f;
		Matrix4f mirror = new Matrix4f().scale(f, 1, 1);

		// The arm: shoulder to fist along the arm's -Z, the back of the hand (knuckles) its +Y.
		Matrix4f armB = arm(p);
		Matrix4f armView = new Matrix4f(mirror).mul(BLENDER_TO_VIEW).mul(armB);
		Vector3f fist = armView.transformPosition(new Vector3f(0, 0, -ARM));
		Vector3f along = armView.transformDirection(new Vector3f(0, 0, -1)).normalize();
		Vector3f back = armView.transformDirection(new Vector3f(0, 1, 0)).normalize();
		AvatarRenderer<?> renderer = mc.getEntityRenderDispatcher().getRenderer(avatar);
		ModelPart armPart = right ? renderer.getModel().rightArm : renderer.getModel().leftArm;
		armPart.resetPose();
		poseStack.pushPose();
		RingFirstPerson.placeFist(poseStack, armPart, right, slim, fist, along, back);
		Identifier skin = avatar.skin.body().texturePath();
		if (right) renderer.renderRightHand(poseStack, collector, light, skin, avatar.showRightSleeve);
		else renderer.renderLeftHand(poseStack, collector, light, skin, avatar.showLeftSleeve);
		poseStack.pushPose();
		armPart.translateAndRotate(poseStack);
		RingModels.render(poseStack, collector, light, LabSettings.get().ringModel, !right, slim);
		poseStack.popPose();
		poseStack.popPose();

		// The sword: at the grip, tilted forward in the fist, turned about its length, extruding along it.
		Matrix4f tool = new Matrix4f(armB).translate(GRIP).rotateX(-p[3] * Mth.DEG_TO_RAD).rotateY(p[5] * Mth.DEG_TO_RAD);
		Matrix4f toolView = new Matrix4f(mirror).mul(BLENDER_TO_VIEW).mul(tool).mul(mirror);
		poseStack.pushPose();
		poseStack.mulPose(toolView);
		poseStack.pushPose();
		poseStack.scale(1f, grow, 1f);
		poseStack.scale(ITEM_SCALE, ITEM_SCALE, ITEM_SCALE);
		// The item's quads are centred on the block (-0.5 to 0.5): its grip (lowest point) onto the origin, its long axis up +Y.
		poseStack.translate(0f, 0.5f - ITEM_GRIP_Y, 0f);
		mc.getItemModelResolver().updateForTopItem(ITEM, stack, ItemDisplayContext.NONE, mc.level, mc.player, 0);
		ITEM.submit(poseStack, collector, 0xF000F0, OverlayTexture.NO_OVERLAY, 0);
		poseStack.popPose();
		// The scan plate riding the growing tip, as wide as the blade, gone once it has formed.
		float since = now - formStart;
		if (since >= 1 && since <= form + 2) {
			float span = 29f / 32f * grow, w = 4.5f / 32f + 0.02f, d = 1.5f / 32f + 0.02f;
			float a = since > form ? 1f - (since - form) / 2f : 1f;
			float[] c = CorpsTint.apply(CorpsTint.current(), 0.05f, 0.95f, 0.25f);
			collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucentEmissive(GLASS), (pose, vc) ->
					plate(pose, vc, -w, span - 0.006f, -d, w, span + 0.006f, d, c, 0.6f * a));
		}
		poseStack.popPose();
		return true;
	}

	/** A flat glowing box, both sides of each face. */
	private static void plate(PoseStack.Pose pose, VertexConsumer vc, float x0, float y0, float z0, float x1, float y1, float z1, float[] c, float a) {
		float[][] v = {{x0, y0, z0}, {x1, y0, z0}, {x1, y1, z0}, {x0, y1, z0}, {x0, y0, z1}, {x1, y0, z1}, {x1, y1, z1}, {x0, y1, z1}};
		int[][] faces = {{0, 3, 2, 1}, {4, 5, 6, 7}, {0, 4, 7, 3}, {1, 2, 6, 5}, {0, 1, 5, 4}, {3, 7, 6, 2}};
		for (int[] face : faces) {
			for (int side = 0; side < 2; side++) {
				for (int k = 0; k < 4; k++) {
					float[] q = v[face[side == 0 ? k : 3 - k]];
					vc.addVertex(pose, q[0], q[1], q[2]).setColor(c[0], c[1], c[2], a).setUv(0.5f, 0.5f)
							.setOverlay(OverlayTexture.NO_OVERLAY).setLight(0xF000F0).setNormal(pose, 0, 1, 0);
				}
			}
		}
	}
}
