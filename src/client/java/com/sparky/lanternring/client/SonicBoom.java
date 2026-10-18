package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.net.RingFxPayload;
import it.unimi.dsi.fastutil.ints.Int2LongMap;
import it.unimi.dsi.fastutil.ints.Int2LongOpenHashMap;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * J's sonic boom (Blender pass 218): once each time the fast glide breaks 1.1 blocks a tick, a ring of
 * light bursts out round the flyer, facing along their flight and growing to about 6 blocks across in
 * 0.4 s. Nearby players hear the double crack and rumble (to about 64 blocks) and their view shakes
 * with distance; the flyer hears a tight whoosh into a crack and gets a fast jitter and a kick of the
 * field of view. The shake follows the Ring Lab's "Sonic boom: screen shake".
 */
public final class SonicBoom {
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/sonic_boom_ring.png");
	static final SoundEvent FAR = SoundEvent.createFixedRangeEvent(LanternRing.id("sonic_boom"), 64f);
	static final SoundEvent CLOSE = SoundEvent.createVariableRangeEvent(LanternRing.id("sonic_boom_close"));
	/** 8 frames, one every tick and a half: 0.4 s. */
	private static final int FRAMES = 8;
	static final float LIFE = 12f;
	/** How wide the ring grows, in blocks. */
	private static final float ACROSS = 6f;
	/** How far away the boom still shakes a camera, in blocks. */
	private static final double SHAKE_RANGE = 24;

	private record Boom(Vec3 at, Vec3 dir, long start, Corps corps) {
	}

	private static final List<Boom> BOOMS = new ArrayList<>();
	/** When each flyer last boomed (game time), so the trail's speed ring gives way to it. */
	private static final Int2LongMap LAST = new Int2LongOpenHashMap();

	private SonicBoom() {
	}

	/** Your own boom: the close sound, the fast jitter and the FOV kick, straight away. */
	static void own(LocalPlayer p, Vec3 dir) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		mc.level.playLocalSound(p.getX(), p.getY(), p.getZ(), CLOSE, SoundSource.PLAYERS, 1f, 1f, false);
		RingShake.boom(true, 1f);
		RingShake.fovKick(4f + ThreadLocalRandom.current().nextFloat() * 2f);
	}

	/** SONIC_BOOM from the server (variant: the flyer), while LabFx has their corps current. */
	static void handle(RingFxPayload fx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || mc.player == null) return;
		long now = mc.level.getGameTime();
		Vec3 dir = fx.to().subtract(fx.from());
		dir = dir.lengthSqr() < 1e-6 ? new Vec3(0, 0, 1) : dir.normalize();
		BOOMS.add(new Boom(fx.from().add(0, 0.9, 0), dir, now, CorpsTint.current()));
		LAST.put(fx.variant(), now);
		if (fx.variant() == mc.player.getId()) return;
		mc.level.playLocalSound(fx.from().x, fx.from().y, fx.from().z, FAR, SoundSource.PLAYERS, 1f, 1f, true);
		double d = mc.player.position().distanceTo(fx.from());
		if (d < SHAKE_RANGE) RingShake.boom(false, (float) (1 - d / SHAKE_RANGE));
	}

	/** True for a moment after this flyer boomed (the trail's own speed ring stays out of the way). */
	static boolean recent(int id, long now) {
		return LAST.containsKey(id) && now - LAST.get(id) < LIFE;
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			BOOMS.clear();
			LAST.clear();
			return;
		}
		long now = mc.level.getGameTime();
		BOOMS.removeIf(b -> now - b.start > LIFE + 1);
		LAST.values().removeIf(t -> now - t > 200);
	}

	public static void render(LevelRenderContext ctx) {
		if (BOOMS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float now = mc.level.getGameTime() + ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		for (Boom b : BOOMS) {
			float age = now - b.start;
			if (age < 0 || age >= LIFE) continue;
			float grow = 1f - (1f - age / LIFE) * (1f - age / LIFE);
			float half = ACROSS / 2f * grow;
			int frame = Math.min(FRAMES - 1, (int) (age / 1.5f));
			ring(ctx, cam, b.at, b.dir, half, frame, FRAMES, b.corps, 1f);
		}
	}

	/**
	 * A ring of light (a frame of sonic_boom_ring.png) at "at", facing along dir, half blocks out from
	 * its middle; drawn from both sides. The flight trail's speed ring uses it too.
	 */
	static void ring(LevelRenderContext ctx, Vec3 cam, Vec3 at, Vec3 dir, float half, int frame, int frames, Corps corps, float alpha) {
		Vec3 up = Math.abs(dir.y) > 0.95 ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0);
		Vec3 right = dir.cross(up).normalize().scale(half);
		Vec3 top = right.cross(dir).normalize().scale(half);
		Vec3 c = at.subtract(cam);
		float v0 = frame / (float) frames, v1 = (frame + 1) / (float) frames;
		float r = corps.red(), g = corps.green(), bl = corps.blue();
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TEXTURE), (pose, vc) -> {
			Vec3[] q = {c.subtract(right).subtract(top), c.add(right).subtract(top), c.add(right).add(top), c.subtract(right).add(top)};
			float[][] uv = {{0, v1}, {1, v1}, {1, v0}, {0, v0}};
			for (int i = 0; i < 4; i++) vertex(pose, vc, q[i], uv[i], r, g, bl, alpha);
			for (int i = 3; i >= 0; i--) vertex(pose, vc, q[i], uv[i], r, g, bl, alpha);
		});
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, Vec3 p, float[] uv, float r, float g, float b, float a) {
		vc.addVertex(pose, (float) p.x, (float) p.y, (float) p.z)
				.setColor(Mth.lerp(0.25f, r, 1f), Mth.lerp(0.25f, g, 1f), Mth.lerp(0.25f, b, 1f), a)
				.setUv(uv[0], uv[1])
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(ShaderGlow.light(0.9f))
				.setNormal(pose, 0, 1, 0);
	}
}
