package com.sparky.lanternring.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Camera;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * The Shrine charge style: once both clicks have been held long enough, the lantern is set down on
 * the ground in front of you, you kneel (crouch) and bow your head to it, and the ring docks on it
 * while the light builds and the oath is spoken; then it returns to your hand. The server charges
 * exactly as with the lantern in hand (it stays in the off hand), so this is all drawn here.
 */
public final class LanternShrine {
	/** How far ahead of your feet the lantern stands, in blocks. */
	private static final double AHEAD = 1.3;
	/** The lantern's size on the ground, like a placed lantern block. */
	private static final float SIZE = 0.8f;
	/** How far your head bows toward the lantern while it charges, 0..1 per tick. */
	private static final float BOW = 0.2f;
	private static final int FULL_BRIGHT = 0xF000F0;

	/** Where the lantern stands, and which way its front faces (radians about Y), while it's set down. */
	private static Vec3 at;
	private static float facing;
	private static Corps corps = Corps.GREEN;
	/** True while we hold the sneak key down for the kneel. */
	private static boolean kneeling;

	private LanternShrine() {
	}

	/** True while the lantern stands on the ground as a shrine. */
	static boolean active() {
		return at != null;
	}

	public static void tick(Minecraft mc) {
		LocalPlayer player = mc.player;
		boolean shrine = LabSettings.get().chargeStyle == LabSettings.ChargeStyle.SHRINE;
		float t = LanternFirstPerson.held(0f);
		boolean charging = player != null && shrine && t >= LanternCharge.hold() && t < LanternCharge.done() + LanternCharge.SETTLE;
		boolean afterglow = at != null && LanternGlare.after(0f) >= 0;
		if (player == null || !shrine || (!charging && !afterglow)) {
			at = null;
			stand(mc);
			return;
		}
		if (at == null) {
			// Set it down just ahead of your feet, its front turned to you.
			Vec3 look = player.getViewVector(1f);
			Vec3 flat = new Vec3(look.x, 0, look.z);
			flat = flat.lengthSqr() < 1.0e-4 ? new Vec3(0, 0, 1) : flat.normalize();
			at = player.position().add(flat.scale(AHEAD));
			facing = (float) Math.atan2(flat.x, flat.z);
			ItemStack off = player.getOffhandItem();
			if (off.is(ModRegistry.POWER_BATTERY_ITEM)) corps = Corps.ofLantern(off);
			burst(mc, at.add(0, 0.4, 0), 14);
		}
		if (charging) {
			// Kneel and bow your head to it.
			mc.options.keyShift.setDown(true);
			kneeling = true;
			Vec3 port = portWorld();
			Vec3 d = port.subtract(player.getEyePosition());
			float pitch = (float) Math.toDegrees(-Math.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)));
			player.setXRot(Mth.lerp(BOW, player.getXRot(), Mth.clamp(pitch, -45f, 45f)));
		} else {
			stand(mc);
		}
		if (!mc.isPaused() && mc.level != null && t >= LanternCharge.hold() + LanternCharge.REACH && t < LanternCharge.done()) {
			// Light drawn up out of the lantern into the ring.
			RandomSource r = mc.level.getRandom();
			Vec3 port = portWorld();
			Vec3 from = port.add((r.nextDouble() - 0.5) * 0.4, -0.2 + r.nextDouble() * 0.3, (r.nextDouble() - 0.5) * 0.4);
			LabFx.spawn(ModParticles.MOTE, from, port.subtract(from).scale(0.15).add(0, 0.02, 0), 0.3f);
		}
	}

	/** Lets go of the kneel, if we were holding it. */
	private static void stand(Minecraft mc) {
		if (!kneeling) return;
		kneeling = false;
		mc.options.keyShift.setDown(false);
		// Back to whatever the keyboard really says (in case sneak is held for real).
		KeyMapping.setAll();
	}

	private static void burst(Minecraft mc, Vec3 where, int count) {
		if (mc.level == null) return;
		RandomSource r = mc.level.getRandom();
		for (int i = 0; i < count; i++) {
			Vec3 v = new Vec3(r.nextGaussian(), r.nextGaussian() * 0.5 + 0.4, r.nextGaussian()).scale(0.06);
			LabFx.spawn(ModParticles.MOTE, where, v, 0.35f);
		}
	}

	/** The lantern's own space: standing at {@link #at}, its front turned toward you, at block size. */
	private static Matrix4f frame() {
		// The model's front is -z; turning it by facing points it back toward you.
		return new Matrix4f().translate((float) at.x, (float) at.y, (float) at.z).rotateY(facing).scale(SIZE);
	}

	/** Where the ring docks on the lantern, in the world. */
	private static Vec3 portWorld() {
		Vector3f dock = dockLocal();
		Vector3f w = frame().transformPosition(dock, new Vector3f());
		return new Vec3(w.x, w.y, w.z);
	}

	/** The dock in the lantern's own space (blocks before {@link #SIZE}). */
	private static Vector3f dockLocal() {
		LanternFirstPerson.Look look = LanternFirstPerson.look(corps);
		Vector3f port = look.port();
		float plate = look.socket() != null ? 0.25f : 0f;
		return new Vector3f(port.x / 16f, port.y / 16f, (port.z - plate) / 16f);
	}

	public static void render(LevelRenderContext ctx) {
		if (at == null) return;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		PoseStack pose = ctx.poseStack();
		pose.pushPose();
		pose.translate(at.x - cam.x, at.y - cam.y, at.z - cam.z);
		pose.rotateDegrees(Axis.YP, (float) Math.toDegrees(facing));
		pose.scale(SIZE, SIZE, SIZE);
		float glow = LanternFirstPerson.glow(ctx.levelState().worldPartialTicks);
		LanternFirstPerson.drawLantern(pose, ctx.submitNodeCollector(), FULL_BRIGHT, LanternFirstPerson.look(corps), corps, glow);
		pose.popPose();
	}

	/**
	 * Called while drawing the first-person hands: tells the ring hand (and the glare on screen)
	 * where the shrine's dock is, turned into hand space so it lines up on screen at any field of view.
	 */
	static void aimRing() {
		Minecraft mc = Minecraft.getInstance();
		Camera camera = mc.gameRenderer.mainCamera();
		Quaternionf toView = new Quaternionf(camera.rotation()).conjugate();
		Vec3 port = portWorld();
		Vec3 cam = camera.position();
		Vector3f view = toView.transform(new Vector3f((float) (port.x - cam.x), (float) (port.y - cam.y), (float) (port.z - cam.z)));
		// The hand is drawn at a fixed field of view: shift the point so it lands on the same spot on screen.
		float k = (float) (Math.tan(Math.toRadians(camera.getFov()) / 2) / Math.tan(Math.toRadians(RingFirstPerson.HAND_FOV) / 2));
		view.x /= k;
		view.y /= k;
		Matrix4f fromView = new Matrix4f(RenderSystem.getModelViewStack()).invert();
		Vector3f target = fromView.transformPosition(new Vector3f(view));
		Vector3f out = new Vector3f((float) Math.sin(facing), 0f, (float) Math.cos(facing)).negate();
		Vector3f normal = fromView.transformDirection(toView.transform(out)).normalize();
		LanternFirstPerson.dockAt(target, normal, view);
	}
}
