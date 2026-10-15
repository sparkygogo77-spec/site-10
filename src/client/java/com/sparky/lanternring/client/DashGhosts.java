package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * The dash strike's afterimages (Blender pass 505, R3a-3): three see-through construct copies of the bearer, 2, 4 and
 * 6 ticks behind in the pose they had then, from the dash's first tick until 8 ticks after it (as the Blender take
 * keys them, 25% opaque). Every client draws them for every dash (CombatFx DASH, or CombatInput for your own), in the
 * corps colour of the ring, shader-safe: entityTranslucentEmissive with ShaderGlow light, as CombatFx draws.
 */
public final class DashGhosts {
	/** How many afterimages, each this many ticks further behind; shown until this long after the dash; their opacity. */
	private static final int GHOSTS = 3, BEHIND = 2, AFTER = 8;
	private static final float ALPHA = 0.25f;
	/** The player model's scale and the drop from its root to the feet (LivingEntityRenderer), in blocks. */
	private static final float SCALE = 0.9375f, ROOT = 1.501f;
	/** Each part's box in its own space (px): centre and half sizes, right-handed; head, body, ring arm, free arm, ring leg, free leg. */
	private static final float[][] CENTRE = {{0, -4, 0}, {0, 6, 0}, {-1, 4, 0}, {1, 4, 0}, {0, 6, 0}, {0, 6, 0}};
	private static final float[][] HALF = {{4, 4, 4}, {4, 6, 2}, {2, 6, 2}, {2, 6, 2}, {2, 6, 2}, {2, 6, 2}};

	private record Frame(Vec3 pos, float yaw, float index) {
	}

	private static final class Dash {
		final Corps corps;
		final long start;
		final int windup, time;
		final boolean right;
		/** Newest first, one a tick. */
		final List<Frame> frames = new ArrayList<>();

		Dash(Corps corps, long start, int windup, int time, boolean right) {
			this.corps = corps;
			this.start = start;
			this.windup = windup;
			this.time = time;
			this.right = right;
		}
	}

	private static final Int2ObjectMap<Dash> DASHES = new Int2ObjectOpenHashMap<>();

	private DashGhosts() {
	}

	/** A dash strike by player id started this tick (lean and dash in ticks). */
	static void start(int id, Corps corps, int windup, int time) {
		Minecraft mc = Minecraft.getInstance();
		Player p = RingEmit.bearer(id);
		if (mc.level == null || p == null) return;
		DASHES.put(id, new Dash(corps, mc.level.getGameTime(), Math.max(0, windup), Math.max(1, time), RingEmit.ringArm(p) == HumanoidArm.RIGHT));
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			DASHES.clear();
			return;
		}
		if (mc.isPaused()) return;
		long now = mc.level.getGameTime();
		for (Iterator<Int2ObjectMap.Entry<Dash>> it = DASHES.int2ObjectEntrySet().iterator(); it.hasNext(); ) {
			Int2ObjectMap.Entry<Dash> e = it.next();
			Dash d = e.getValue();
			Player p = RingEmit.bearer(e.getIntKey());
			long age = now - d.start;
			if (p == null || age > d.windup + d.time + AFTER || age < 0) {
				it.remove();
				continue;
			}
			d.frames.add(0, new Frame(p.position(), p.yBodyRot, CombatPoses.dashIndex(d.windup, d.time, age)));
			while (d.frames.size() > BEHIND * GHOSTS + 1) d.frames.remove(d.frames.size() - 1);
		}
	}

	public static void render(LevelRenderContext ctx) {
		if (DASHES.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		long now = mc.level.getGameTime();
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS), (pose, vc) -> {
			for (Dash d : DASHES.values()) {
				long age = now - d.start;
				if (age < d.windup || age >= d.windup + d.time + AFTER) continue;
				TextureAtlasSprite s = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, d.corps);
				float[] col = PowerLandingFx.bright(PowerLandingFx.tint(d.corps), 0.1f);
				// The last 3 ticks fade them out.
				float alpha = ALPHA * Mth.clamp((d.windup + d.time + AFTER - age) / 3f, 0f, 1f);
				int light = ShaderGlow.light(0.8f);
				for (int g = 1; g <= GHOSTS; g++) {
					int k = g * BEHIND;
					if (k >= d.frames.size()) break;
					Frame f = d.frames.get(k);
					float[][] parts = CombatPoses.dashPose(f.index());
					if (parts == null) return;
					Quaternionf body = new Quaternionf().rotationY((180f - f.yaw()) * Mth.DEG_TO_RAD).rotateZ(Mth.PI);
					float m = d.right ? 1f : -1f;
					for (int i = 0; i < 6; i++) {
						float[] q = parts[i];
						float[] home = SuperJumpPoses.HOME[i];
						Quaternionf turn = new Quaternionf().rotationZYX(m * q[2], m * q[1], q[0]);
						Vector3f c = turn.transform(new Vector3f(m * CENTRE[i][0], CENTRE[i][1], CENTRE[i][2]))
								.add(m * (home[0] + q[3]), home[1] + q[4], home[2] + q[5]).div(16f).sub(0f, ROOT, 0f).mul(SCALE);
						body.transform(c);
						Quaternionf world = new Quaternionf(body).mul(turn);
						PowerLandingFx.cube(pose, vc, cam, f.pos().add(c.x, c.y, c.z), world, HALF[i][0] * SCALE / 16f, HALF[i][1] * SCALE / 16f,
								HALF[i][2] * SCALE / 16f, s, 0f, 0f, 0.5f, col, alpha, light);
					}
				}
			}
		});
	}
}
