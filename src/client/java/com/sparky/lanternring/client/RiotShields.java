package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.ShieldReflect;
import com.sparky.lanternring.item.PowerRingItem;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
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
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix4f;

/**
 * The Shield construct: a riot shield of hard light in the ring's corps colour (see ShieldReflect
 * for its outline and what it reflects). It is a see-through slab with smoke swirling inside (the
 * Shockwave's animated glass sheet), bright edges and a slight thickness. Holding right-click
 * raises it like a vanilla shield: the ring arm swings up across the body and the shield grows out
 * of the ring as it's pulled in for cover, then drops away when you let go. Third person draws it
 * on the arm (see {@link #submitOnArm} and {@link #pose}), first person in front of the fist (see
 * {@link #submitFirstPerson}). Every client tracks every bearer's raise, so it needs no packets.
 */
public final class RiotShields {
	private static final Identifier GLASS = LanternRing.id("textures/entity/shockwave_glass.png");
	private static final int FULL_BRIGHT = 0xF000F0;
	/** Half the slab's thickness, in outline units. */
	private static final float HALF_THICK = 0.06f;
	/** How wide the bright band along the edge is, on the faces. */
	private static final float RIM = 0.07f;
	/** How much of the way up the shield comes each tick while held, and down once let go. */
	private static final float RAISE_STEP = 0.22f;
	private static final float LOWER_STEP = 0.3f;
	/** The face is see-through so you can watch what you're blocking; the edge glows solid. */
	private static final float FACE_ALPHA = 0.45f;
	/** Your own shield, seen from behind in first person, is fainter so you can aim past it. */
	private static final float FIRST_PERSON_FACE_ALPHA = 0.28f;
	private static final float RIM_ALPHA = 0.95f;
	private static final float[] JADE = {0.80f, 1f, 0.85f};
	private static final float[] EDGE = {0.85f, 1f, 0.9f};
	/** Smoke animation, as ShockwaveDomes: 64 frames in an 8x8 grid, 3 ticks each. */
	private static final int FRAMES = 64;
	private static final int GRID = 8;
	private static final int FRAME_TICKS = 3;
	private static final float INSET = 0.5f / 1024f;
	/** One smoke frame spans this many blocks of shield, so it isn't stretched. */
	private static final float TILE = 2.7f;
	/** The outline's middle height, where the shield is held. */
	private static final float MIDDLE = (float) (ShieldReflect.OUTLINE[0][0] + ShieldReflect.OUTLINE[ShieldReflect.OUTLINE.length - 1][0]) / 2f;
	/** Third person: the shield's size on the arm (the outline is in blocks), about 1.35 blocks tall. */
	private static final float ARM_SCALE = 0.55f;
	/** The ring arm's blocking pose, as vanilla's shield block: raised forward and turned in across the chest. */
	private static final float BLOCK_X = -0.9424779f;
	private static final float BLOCK_Y = Mth.PI / 6f;
	/** First person: the shield's size in front of the fist, and where it sits raised and lowered (right hand; x flips for the left). */
	private static final float VIEW_SCALE = 0.34f;
	private static final float[] VIEW_UP = {0.2f, -0.5f, -0.8f};
	private static final float[] VIEW_DOWN = {0.5f, -1.0f, -0.75f};

	private static final class Track {
		float raise, prevRaise;
		InteractionHand hand = InteractionHand.MAIN_HAND;
		Corps corps = Corps.GREEN;
	}

	private static final Int2ObjectMap<Track> TRACKS = new Int2ObjectOpenHashMap<>();

	private RiotShields() {
	}

	public static void register() {
		ClientTickEvents.END_CLIENT_TICK.register(RiotShields::tick);
	}

	private static boolean holdsShield(Player player) {
		if (!player.isUsingItem()) return false;
		ItemStack used = player.getUseItem();
		return used.getItem() instanceof PowerRingItem && PowerRingItem.getMode(used) == RingMode.SHIELD;
	}

	private static void tick(Minecraft mc) {
		if (mc.level == null || mc.isPaused()) {
			if (mc.level == null) TRACKS.clear();
			return;
		}
		for (Player player : mc.level.players()) {
			boolean up = holdsShield(player);
			Track t = TRACKS.get(player.getId());
			if (t == null) {
				if (!up) continue;
				t = new Track();
				TRACKS.put(player.getId(), t);
			}
			t.prevRaise = t.raise;
			if (up) {
				t.hand = player.getUsedItemHand();
				t.corps = Corps.of(player.getUseItem());
				t.raise = Math.min(1f, t.raise + RAISE_STEP);
			} else {
				t.raise = Math.max(0f, t.raise - LOWER_STEP);
			}
		}
		TRACKS.int2ObjectEntrySet().removeIf(e -> e.getValue().raise <= 0 && e.getValue().prevRaise <= 0
				|| !(mc.level.getEntity(e.getIntKey()) instanceof Player));
	}

	/** 0 = lowered (or no shield), 1 = fully raised for cover, eased so it snaps up and settles. */
	public static float raise(Entity player, float partial) {
		Track t = player == null ? null : TRACKS.get(player.getId());
		if (t == null) return 0f;
		float r = Mth.lerp(partial, t.prevRaise, t.raise);
		return 1f - (1f - r) * (1f - r);
	}

	/** The hand whose ring holds the shield, or null when it's down. */
	public static InteractionHand hand(Player player) {
		Track t = player == null ? null : TRACKS.get(player.getId());
		return t == null ? null : t.hand;
	}

	/** The arm the shield is on, or null when it's down. */
	public static HumanoidArm arm(Player player) {
		Track t = TRACKS.get(player.getId());
		if (t == null) return null;
		return t.hand == InteractionHand.MAIN_HAND ? player.getMainArm() : player.getMainArm().getOpposite();
	}

	/** Third person: swings the shield arm up into the blocking pose (after vanilla and flight poses). */
	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player)) return;
		float r = raise(player, mc.getDeltaTracker().getGameTimeDeltaPartialTick(false));
		HumanoidArm side = arm(player);
		if (r <= 0f || side == null) return;
		boolean right = side == HumanoidArm.RIGHT;
		ModelPart arm = right ? model.rightArm : model.leftArm;
		// Looking up or down tips the shield a little with the gaze, as vanilla's does.
		arm.xRot = Mth.lerp(r, arm.xRot, BLOCK_X + Mth.clamp(model.head.xRot, -1f, 1f) * 0.35f);
		arm.yRot = Mth.lerp(r, arm.yRot, right ? -BLOCK_Y : BLOCK_Y);
		arm.zRot = Mth.lerp(r, arm.zRot, 0f);
	}

	/**
	 * Third person: draws the shield strapped to the outside of {@code armPart}'s forearm. It faces
	 * straight ahead when the arm is in the blocking pose, so as the arm swings up the shield turns
	 * from hanging at the side to covering the body.
	 */
	public static void submitOnArm(PoseStack pose, SubmitNodeCollector collector, ModelPart armPart, boolean right, Player player, float partial) {
		float r = raise(player, partial);
		HumanoidArm side = arm(player);
		if (r <= 0f || side != (right ? HumanoidArm.RIGHT : HumanoidArm.LEFT)) return;
		Track t = TRACKS.get(player.getId());
		float f = right ? 1f : -1f;
		pose.pushPose();
		armPart.translateAndRotate(pose);
		// The forearm, near the wrist.
		pose.translate(-f / 16f, 7f / 16f, 0f);
		// Undo the blocking pose's turn, then flip model space (y down, front -z) to the mesh's (y up, front +z).
		pose.mulPose(new Matrix4f().rotationX(-BLOCK_X).rotateY(right ? BLOCK_Y : -BLOCK_Y).rotateX(Mth.PI));
		// Out in front of the arm and in across the chest, grown out of the ring as it comes up.
		pose.translate(f * 0.22f, 0f, 0.3f);
		float size = ARM_SCALE * (0.35f + 0.65f * r);
		pose.scale(size, size, size);
		pose.translate(0f, -MIDDLE, 0f);
		submit(pose, collector, t.corps, r, FACE_ALPHA, player);
		pose.popPose();
	}

	/**
	 * First person: draws your raised shield in front of the fist, in hand space ({@code pose} is the
	 * first-person hand origin). It comes up from below the screen and turns to face ahead.
	 */
	public static void submitFirstPerson(PoseStack pose, SubmitNodeCollector collector, InteractionHand hand, float partial) {
		Minecraft mc = Minecraft.getInstance();
		Player player = mc.player;
		Track t = player == null ? null : TRACKS.get(player.getId());
		float r = raise(player, partial);
		if (t == null || r <= 0f || t.hand != hand) return;
		float f = arm(player) == HumanoidArm.RIGHT ? 1f : -1f;
		pose.pushPose();
		pose.translate(f * Mth.lerp(r, VIEW_DOWN[0], VIEW_UP[0]), Mth.lerp(r, VIEW_DOWN[1], VIEW_UP[1]), Mth.lerp(r, VIEW_DOWN[2], VIEW_UP[2]));
		// Lowered it lies tipped away and turned out; raised it stands up facing ahead, angled in a touch.
		pose.rotateDegrees(Axis.YP, f * Mth.lerp(r, 40f, 8f));
		pose.rotateDegrees(Axis.XP, Mth.lerp(r, -70f, 0f));
		pose.rotateDegrees(Axis.ZP, f * Mth.lerp(r, -25f, 0f));
		// The mesh's front (+z) faces away from you.
		pose.rotateDegrees(Axis.YP, 180f);
		float size = VIEW_SCALE * (0.35f + 0.65f * r);
		pose.scale(size, size, size);
		pose.translate(0f, -MIDDLE, 0f);
		submit(pose, collector, t.corps, r, FIRST_PERSON_FACE_ALPHA, player);
		pose.popPose();
	}

	private static void submit(PoseStack pose, SubmitNodeCollector collector, Corps corps, float r, float faceAlpha, Player player) {
		float now = player.tickCount + Minecraft.getInstance().getDeltaTracker().getGameTimeDeltaPartialTick(false);
		int frame = Math.floorMod((int) (now / FRAME_TICKS), FRAMES);
		float alpha = 0.4f + 0.6f * r;
		float[] face = CorpsTint.apply(corps, JADE[0], JADE[1], JADE[2]);
		float[] edge = CorpsTint.apply(corps, EDGE[0], EDGE[1], EDGE[2]);
		RenderType glass = RenderTypes.entityTranslucentEmissive(CorpsTint.texture(GLASS, corps));
		collector.submitCustomGeometry(pose, glass, (p, vc) -> mesh(p, vc, frame, alpha, faceAlpha, face, edge));
	}

	private static void mesh(PoseStack.Pose pose, VertexConsumer vc, int frame, float alpha, float faceAlpha, float[] jade, float[] edge) {
		double[][] o = ShieldReflect.OUTLINE;
		float cell = 1f / GRID;
		float fu = (frame % GRID) * cell, fv = (frame / GRID) * cell;
		float[] smoke = {fu, fv, cell};
		for (int i = 1; i < o.length; i++) {
			float y0 = (float) o[i - 1][0], w0 = (float) o[i - 1][1];
			float y1 = (float) o[i][0], w1 = (float) o[i][1];
			// The see-through face, front and back, inset by the rim.
			float iy0 = i == 1 ? y0 + RIM : y0, iy1 = i == o.length - 1 ? y1 - RIM : y1;
			float jw0 = lerpWidth(y0, w0, y1, w1, iy0) - RIM, jw1 = lerpWidth(y0, w0, y1, w1, iy1) - RIM;
			for (float z : new float[] {HALF_THICK, -HALF_THICK}) {
				quad(pose, vc, smoke, -jw0, iy0, jw0, iy0, jw1, iy1, -jw1, iy1, z, jade, alpha * faceAlpha);
			}
			// The bright rim on both faces, down each side.
			for (int s = -1; s <= 1; s += 2) {
				for (float z : new float[] {HALF_THICK, -HALF_THICK}) {
					quad(pose, vc, smoke, s * jw0, iy0, s * w0, y0, s * w1, y1, s * jw1, iy1, z, edge, alpha * RIM_ALPHA);
				}
				// The slab's side wall, joining front and back.
				wall(pose, vc, smoke, s * w0, y0, s * w1, y1, edge, alpha * RIM_ALPHA);
			}
		}
		// Bottom and top: a rim band across each face, and the end walls.
		double[] bottom = o[0], top = o[o.length - 1];
		for (double[] end : new double[][] {bottom, top}) {
			float y = (float) end[0], w = (float) end[1];
			float in = end == bottom ? y + RIM : y - RIM;
			float iw = (float) ShieldReflect.halfWidth(in) - RIM;
			for (float z : new float[] {HALF_THICK, -HALF_THICK}) {
				quad(pose, vc, smoke, -w, y, w, y, iw, in, -iw, in, z, edge, alpha * RIM_ALPHA);
			}
			wall(pose, vc, smoke, -w, y, w, y, edge, alpha * RIM_ALPHA);
		}
	}

	private static float lerpWidth(float y0, float w0, float y1, float w1, float y) {
		return y1 == y0 ? w0 : w0 + (w1 - w0) * (y - y0) / (y1 - y0);
	}

	/** A flat quad on the face at depth z, drawn both ways round so it shows from either side. */
	private static void quad(PoseStack.Pose pose, VertexConsumer vc, float[] smoke, float x0, float y0, float x1, float y1,
			float x2, float y2, float x3, float y3, float z, float[] tint, float alpha) {
		float nz = z >= 0 ? 1 : -1;
		vertex(pose, vc, smoke, x0, y0, z, tint, alpha, 0, 0, nz);
		vertex(pose, vc, smoke, x1, y1, z, tint, alpha, 0, 0, nz);
		vertex(pose, vc, smoke, x2, y2, z, tint, alpha, 0, 0, nz);
		vertex(pose, vc, smoke, x3, y3, z, tint, alpha, 0, 0, nz);
		vertex(pose, vc, smoke, x3, y3, z, tint, alpha, 0, 0, -nz);
		vertex(pose, vc, smoke, x2, y2, z, tint, alpha, 0, 0, -nz);
		vertex(pose, vc, smoke, x1, y1, z, tint, alpha, 0, 0, -nz);
		vertex(pose, vc, smoke, x0, y0, z, tint, alpha, 0, 0, -nz);
	}

	/** The slab's edge between two outline points, across its thickness, both ways round. */
	private static void wall(PoseStack.Pose pose, VertexConsumer vc, float[] smoke, float x0, float y0, float x1, float y1, float[] tint, float alpha) {
		float dx = x1 - x0, dy = y1 - y0;
		float len = Math.max(1e-4f, Mth.sqrt(dx * dx + dy * dy));
		float nx = dy / len, ny = -dx / len;
		vertex(pose, vc, smoke, x0, y0, HALF_THICK, tint, alpha, nx, ny, 0);
		vertex(pose, vc, smoke, x1, y1, HALF_THICK, tint, alpha, nx, ny, 0);
		vertex(pose, vc, smoke, x1, y1, -HALF_THICK, tint, alpha, nx, ny, 0);
		vertex(pose, vc, smoke, x0, y0, -HALF_THICK, tint, alpha, nx, ny, 0);
		vertex(pose, vc, smoke, x0, y0, -HALF_THICK, tint, alpha, -nx, -ny, 0);
		vertex(pose, vc, smoke, x1, y1, -HALF_THICK, tint, alpha, -nx, -ny, 0);
		vertex(pose, vc, smoke, x1, y1, HALF_THICK, tint, alpha, -nx, -ny, 0);
		vertex(pose, vc, smoke, x0, y0, HALF_THICK, tint, alpha, -nx, -ny, 0);
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, float[] smoke, float x, float y, float z,
			float[] tint, float alpha, float nx, float ny, float nz) {
		// The smoke frame is mapped flat across the shield by position, centred on it.
		float span = smoke[2] - 2 * INSET;
		float u = smoke[0] + INSET + span * Mth.clamp(0.5f + x / TILE, 0f, 1f);
		float v = smoke[1] + INSET + span * Mth.clamp(1f - y / TILE, 0f, 1f);
		vc.addVertex(pose, x, y, z)
				.setColor(tint[0], tint[1], tint[2], alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(FULL_BRIGHT)
				.setNormal(pose, nx, ny, nz);
	}
}
