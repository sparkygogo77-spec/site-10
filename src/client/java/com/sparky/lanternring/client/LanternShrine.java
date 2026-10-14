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
	/** The Shoulder lean style: the lantern stands tall at your ring side and you lean on it (LeanPoses). */
	private static boolean lean;
	/** In the lean, how far ahead and how far to the ring side the ring meets the lantern, in blocks. */
	private static final double LEAN_AHEAD = 0.85, LEAN_SIDE = 0.4;
	/** In the lean, how high the port stands, about where the leaning ring hand reaches. */
	private static final float LEAN_PORT_HEIGHT = 1.05f;
	/** The lean turns the body this far toward the ring side (J's L3 take), radians. */
	private static final float LEAN_BODY_YAW = 0.4887f;
	private static float size = SIZE;

	/** J's charge takes (ChargeTakes): L1c, the lean into the port on a block, or K3c, kneel and lift; null for the older styles. */
	private static ChargeTakes.Take take;
	/** Where your feet were, and which way you faced (degrees, Minecraft yaw), when the take began. */
	private static Vec3 origin;
	private static float yaw;
	/** Mirror for a left-handed player (the takes are for the ring on the right arm). */
	private static float mirror = 1f;
	/** The take's Blender tick this game tick and the last, and how much of it is on the body. */
	private static float k, kO, weight, weightO;
	private static final ChargeTakes.Rock ROCK = new ChargeTakes.Rock();
	private static final ChargeTakes.Carry CARRY = new ChargeTakes.Carry();
	/** K3c: where the lantern stands on the floor (rig px, right-handed), under the hand at the grab. */
	private static Vector3f spot;
	private static final int FULL_BRIGHT_LIGHT = 0xF000F0;

	private LanternShrine() {
	}

	/** The take being played now, or null. */
	static ChargeTakes.Take take() {
		return at != null ? take : null;
	}

	/** The take's pose this frame (8 parts, right-handed), or null. */
	static float[][] takePose(float partialTick) {
		if (take() == null) return null;
		return ChargeTakes.pose(ChargeTakes.data(take), Mth.lerp(partialTick, kO, k));
	}

	static float takeWeight(float partialTick) {
		return take() == null ? 0f : Mth.lerp(partialTick, weightO, weight);
	}

	/** True while the lantern stands on the ground as a shrine. */
	static boolean active() {
		return at != null;
	}

	/** True while the lantern stands set down for the Shoulder lean. */
	static boolean leaning() {
		return at != null && lean;
	}

	public static void tick(Minecraft mc) {
		LocalPlayer player = mc.player;
		// The summoned lantern (key R) floats; only the one in the off hand is set down as a shrine.
		lean = LabSettings.get().chargeStyle == LabSettings.ChargeStyle.LEAN;
		ChargeTakes.Take want = switch (LabSettings.get().chargeStyle) {
			case PUSH -> ChargeTakes.Take.L1C;
			case KNEEL -> ChargeTakes.Take.K3C;
			default -> null;
		};
		boolean shrine = LabSettings.get().chargeStyle.grounded()
				&& (player == null || !LanternCharge.lanternOut(player));
		float t = LanternFirstPerson.held(0f);
		// The takes start straight away (L1c eases into the port, K3c kneels while the clicks are held).
		int start = want != null ? 0 : LanternCharge.hold();
		boolean charging = player != null && shrine && t >= start && t < LanternCharge.done() + LanternCharge.SETTLE;
		boolean afterglow = at != null && LanternGlare.after(0f) >= 0;
		if (player == null || !shrine || (!charging && !afterglow) || at != null && take != want) {
			at = null;
			take = null;
			stand(mc);
			return;
		}
		if (at == null && want != null) {
			setDown(mc, player, want);
		} else if (at == null) {
			// Set it down just ahead of your feet, its front turned to you.
			Vec3 look = player.getViewVector(1f);
			Vec3 flat = new Vec3(look.x, 0, look.z);
			flat = flat.lengthSqr() < 1.0e-4 ? new Vec3(0, 0, 1) : flat.normalize();
			ItemStack off = player.getOffhandItem();
			if (off.is(ModRegistry.POWER_BATTERY_ITEM)) corps = Corps.ofLantern(off);
			if (lean) {
				// Tall enough that its port meets the leaning hand, standing ahead at your ring side,
				// with the port facing back toward you.
				float portY = Math.max(dockLocal().y, 0.2f);
				size = Mth.clamp(LEAN_PORT_HEIGHT / portY, 0.8f, 1.6f);
				Vec3 side = new Vec3(-flat.z, 0, flat.x).scale(player.getMainArm() == net.minecraft.world.entity.HumanoidArm.RIGHT ? 1 : -1);
				Vector3f dock = dockLocal();
				at = player.position().add(flat.scale(LEAN_AHEAD - dock.z * size)).add(side.scale(LEAN_SIDE));
			} else {
				size = SIZE;
				at = player.position().add(flat.scale(AHEAD));
			}
			facing = (float) Math.atan2(flat.x, flat.z);
			burst(mc, at.add(0, 0.4, 0), 14);
		}
		if (take != null) {
			tickTake(mc, player, charging ? t : -1f);
		} else if (charging && lean) {
			// Lean on it: the body turns its ring shoulder in (the pose itself is LeanPoses).
			float turn = (float) Math.toDegrees(LEAN_BODY_YAW) * (player.getMainArm() == net.minecraft.world.entity.HumanoidArm.RIGHT ? -1 : 1);
			player.setYBodyRot(player.getYRot() + turn);
			player.yBodyRotO = player.yBodyRot;
		} else if (charging) {
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
		if (!mc.isPaused() && mc.level != null && t >= LanternCharge.hold() + LanternCharge.reach() && t < LanternCharge.done()) {
			// Light drawn up out of the lantern into the ring.
			RandomSource r = mc.level.getRandom();
			Vec3 port = portWorld();
			Vec3 from = port.add((r.nextDouble() - 0.5) * 0.4, -0.2 + r.nextDouble() * 0.3, (r.nextDouble() - 0.5) * 0.4);
			Corps before = CorpsTint.enter(corps);
			LabFx.spawn(ModParticles.MOTE, from, port.subtract(from).scale(0.15).add(0, 0.02, 0), 0.3f);
			CorpsTint.restore(before);
		}
	}

	/** Starts one of J's takes: the lantern set down on its block (L1c) or the floor (K3c) in front of you. */
	private static void setDown(Minecraft mc, LocalPlayer player, ChargeTakes.Take want) {
		take = want;
		origin = player.position();
		yaw = player.getYRot();
		mirror = player.getMainArm() == net.minecraft.world.entity.HumanoidArm.RIGHT ? 1f : -1f;
		facing = (float) Math.toRadians(-yaw);
		ItemStack off = player.getOffhandItem();
		if (off.is(ModRegistry.POWER_BATTERY_ITEM)) corps = Corps.ofLantern(off);
		k = kO = 0f;
		weight = weightO = 0f;
		ROCK.reset();
		ChargeTakes.Data data = ChargeTakes.data(want);
		// K3c: the lantern stands on the floor right under where the hand takes the handle.
		Vector3f grab = ChargeTakes.fist(ChargeTakes.pose(data, Math.max(data.carry(), 0)));
		spot = new Vector3f(grab.x, ChargeTakes.GROUND, grab.z);
		CARRY.reset(spot);
		at = origin;
		Vec3 base = toWorld(rig(origin), lanternRig(0f).transformPosition(new Vector3f()));
		at = base;
		burst(mc, base.add(0, 0.4, 0), 14);
	}

	/** One game tick of a take: where on its timeline we are, the lantern's rocking or swinging, the kneel. */
	private static void tickTake(Minecraft mc, LocalPlayer player, float t) {
		float after = LanternGlare.after(0f);
		// A charge still running isn't in an earlier charge's afterglow.
		if (t >= 0 && t < LanternCharge.done()) after = -1f;
		else if (after < 0 && t < 0) after = 0f;
		ChargeTakes.Data data = ChargeTakes.data(take);
		kO = k;
		weightO = weight;
		k = ChargeTakes.tick(take, t, after);
		weight = ChargeTakes.weight(take, t, after);
		// Square on to the lantern, whichever way you look.
		player.setYBodyRot(yaw);
		player.yBodyRotO = yaw;
		if (take == ChargeTakes.Take.L1C) {
			ROCK.tick(ChargeTakes.tilt(data, k));
		} else {
			if (k >= data.carry()) CARRY.tick(ChargeTakes.fist(ChargeTakes.pose(data, k)));
			// The kneel: hold sneak so the camera goes down with you (the body's pose is the take's).
			boolean down = k >= 4f && k < 57f;
			if (down) {
				mc.options.keyShift.setDown(true);
				kneeling = true;
			} else {
				stand(mc);
			}
		}
	}

	/** The rig (model px, y down, -z ahead, feet at y 24) of a player standing at {@code feet} facing {@link #yaw}, in world space. */
	private static Matrix4f rig(Vec3 feet) {
		return new Matrix4f().translate((float) feet.x, (float) feet.y, (float) feet.z)
				.rotateY((float) Math.toRadians(180f - yaw)).scale(-0.9375f, -0.9375f, 0.9375f)
				.translate(0f, -1.501f, 0f).scale(1f / 16f);
	}

	private static Vec3 toWorld(Matrix4f rig, Vector3f p) {
		Vector3f w = rig.transformPosition(new Vector3f(p));
		return new Vec3(w.x, w.y, w.z);
	}

	/**
	 * The lantern's own space (its model units, standing on 0,0,0, its front turned to you) in rig px at this
	 * frame: on its block, tipped by the push (L1c), or on the floor and then hanging from the ring hand (K3c).
	 */
	private static Matrix4f lanternRig(float partialTick) {
		LanternFirstPerson.Look look = LanternFirstPerson.look(corps);
		// The lantern stands as tall as Blender's (16 rig px with its handle), whatever the look.
		float s = 16f * ChargeTakes.LANTERN_HEIGHT / look.handleTop();
		Matrix4f m = new Matrix4f();
		if (take == ChargeTakes.Take.L1C) {
			// Its port lands where the fist does: the port's centre, Blender's 52% up the body, on the front face.
			Vector3f dock = dockLocal();
			Vector3f port = new Vector3f(0f, ChargeTakes.GROUND - ChargeTakes.BLOCK_HEIGHT - ChargeTakes.PORT_UP, -ChargeTakes.PORT_AHEAD);
			Vector3f base = port.sub(dock.x * s, -dock.y * s, -dock.z * s, new Vector3f());
			// Tipped away from you about its far bottom edge.
			float edge = Math.abs(dock.z) * s + 0.5f;
			m.translate(base.x * mirror, base.y, base.z - edge).rotateX(ROCK.at(partialTick)).translate(0f, 0f, edge);
		} else {
			ChargeTakes.Data data = ChargeTakes.data(take);
			float kk = Mth.lerp(partialTick, kO, k);
			if (kk < data.carry()) {
				m.translate(spot.x * mirror, spot.y, spot.z);
			} else {
				Vector3f grip = ChargeTakes.fist(ChargeTakes.pose(data, kk));
				m.translate(grip.x * mirror, grip.y, grip.z).rotateZ(mirror * CARRY.x(partialTick)).rotateX(CARRY.z(partialTick))
						.translate(0f, ChargeTakes.GRIP, 0f);
			}
		}
		// The model stands up (rig y is down) with its front (-z) turned back to you (+z).
		return m.rotateX(Mth.PI).scale(s);
	}

	/** Where your feet are for the take's lantern: where you stood, or where you are once you carry it. */
	private static Vec3 takeFeet(float partialTick) {
		LocalPlayer player = Minecraft.getInstance().player;
		boolean carried = take == ChargeTakes.Take.K3C && Mth.lerp(partialTick, kO, k) >= ChargeTakes.data(take).carry();
		return carried && player != null ? player.getPosition(partialTick) : origin;
	}

	/** The take's lantern in world space this frame. */
	private static Matrix4f takeFrame(float partialTick) {
		return rig(takeFeet(partialTick)).mul(lanternRig(partialTick));
	}

	/** L1c: the hard-light block the lantern stands on, drawn in the corps' construct look. */
	private static void block(LevelRenderContext ctx, Vec3 cam) {
		float top = ChargeTakes.GROUND - ChargeTakes.BLOCK_HEIGHT;
		Matrix4f base = lanternRig(0f);
		top = base.transformPosition(new Vector3f()).y;
		float half = 8f * 0.98f;
		float z = -ChargeTakes.BLOCK_AHEAD;
		Matrix4f m = rig(origin).translateLocal((float) -cam.x, (float) -cam.y, (float) -cam.z);
		net.minecraft.client.renderer.texture.TextureAtlasSprite sprite = ConstructLooks.lightSprite(corps);
		if (sprite == null) {
			sprite = Minecraft.getInstance().getAtlasManager().getAtlasOrThrow(net.minecraft.data.AtlasIds.BLOCKS)
					.getSprite(net.minecraft.resources.Identifier.withDefaultNamespace("block/smooth_stone"));
		}
		net.minecraft.client.renderer.texture.TextureAtlasSprite tex = sprite;
		float x0 = -half, x1 = half, y0 = top, y1 = ChargeTakes.GROUND, z0 = z - half, z1 = z + half;
		PoseStack pose = ctx.poseStack();
		pose.pushPose();
		pose.mulPose(m);
		ctx.submitNodeCollector().submitCustomGeometry(pose,
				net.minecraft.client.renderer.rendertype.RenderTypes.entityCutout(net.minecraft.client.renderer.texture.TextureAtlas.LOCATION_BLOCKS),
				(p, vc) -> {
					// A strip spans four blocks: one block's face is a quarter of it each way.
					float u0 = tex.getU0(), u1 = tex.getU0() + (tex.getU1() - tex.getU0()) * (ConstructLooks.lightSprite(corps) != null ? 0.25f : 1f);
					float v0 = tex.getV0(), v1 = tex.getV0() + (tex.getV1() - tex.getV0()) * (ConstructLooks.lightSprite(corps) != null ? 0.25f : 1f);
					float[][][] faces = {
							{{x0, y0, z0}, {x1, y0, z0}, {x1, y0, z1}, {x0, y0, z1}}, {{x0, y1, z0}, {x0, y1, z1}, {x1, y1, z1}, {x1, y1, z0}},
							{{x0, y0, z0}, {x0, y1, z0}, {x1, y1, z0}, {x1, y0, z0}}, {{x0, y0, z1}, {x1, y0, z1}, {x1, y1, z1}, {x0, y1, z1}},
							{{x0, y0, z0}, {x0, y0, z1}, {x0, y1, z1}, {x0, y1, z0}}, {{x1, y0, z0}, {x1, y1, z0}, {x1, y1, z1}, {x1, y0, z1}}};
					float[][] normals = {{0, -1, 0}, {0, 1, 0}, {0, 0, -1}, {0, 0, 1}, {-1, 0, 0}, {1, 0, 0}};
					float[][] uv = {{u0, v0}, {u1, v0}, {u1, v1}, {u0, v1}};
					for (int f = 0; f < 6; f++) {
						for (int i = 0; i < 4; i++) {
							float[] c = faces[f][i];
							vc.addVertex(p, c[0], c[1], c[2]).setColor(255, 255, 255, 255).setUv(uv[i][0], uv[i][1])
									.setOverlay(net.minecraft.client.renderer.texture.OverlayTexture.NO_OVERLAY).setLight(FULL_BRIGHT_LIGHT)
									.setNormal(p, normals[f][0], normals[f][1], normals[f][2]);
						}
					}
				});
		pose.popPose();
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
		Corps before = CorpsTint.enter(corps);
		for (int i = 0; i < count; i++) {
			Vec3 v = new Vec3(r.nextGaussian(), r.nextGaussian() * 0.5 + 0.4, r.nextGaussian()).scale(0.06);
			LabFx.spawn(ModParticles.MOTE, where, v, 0.35f);
		}
		CorpsTint.restore(before);
	}

	/** The lantern's own space: standing at {@link #at}, its front turned toward you, at block size. */
	private static Matrix4f frame() {
		// The model's front is -z; turning it by facing points it back toward you.
		return new Matrix4f().translate((float) at.x, (float) at.y, (float) at.z).rotateY(facing).scale(size);
	}

	/** Where the ring docks on the lantern, in the world: its port, or K3c's handle. */
	private static Vec3 portWorld() {
		if (take != null) {
			Vector3f dock = take == ChargeTakes.Take.K3C ? new Vector3f(0f, LanternFirstPerson.look(corps).handleTop() / 16f, 0f) : dockLocal();
			Vector3f w = takeFrame(Minecraft.getInstance().getDeltaTracker().getGameTimeDeltaPartialTick(false)).transformPosition(dock);
			return new Vec3(w.x, w.y, w.z);
		}
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
		if (take != null) {
			float partial = ctx.levelState().worldPartialTicks;
			if (take == ChargeTakes.Take.L1C) block(ctx, cam);
			PoseStack lantern = ctx.poseStack();
			lantern.pushPose();
			lantern.mulPose(takeFrame(partial).translateLocal((float) -cam.x, (float) -cam.y, (float) -cam.z));
			LanternFirstPerson.drawLantern(lantern, ctx.submitNodeCollector(), FULL_BRIGHT, LanternFirstPerson.look(corps), corps,
					LanternFirstPerson.glow(partial));
			lantern.popPose();
			return;
		}
		PoseStack pose = ctx.poseStack();
		pose.pushPose();
		pose.translate(at.x - cam.x, at.y - cam.y, at.z - cam.z);
		pose.rotateDegrees(Axis.YP, (float) Math.toDegrees(facing));
		pose.scale(size, size, size);
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
