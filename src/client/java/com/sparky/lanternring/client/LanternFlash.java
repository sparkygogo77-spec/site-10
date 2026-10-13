package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.LanternFlashPayload;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * The lantern flashbang. While someone charges their ring at a lantern, the light escaping round
 * the ring is a sun (drawn on the hand, see BeamChargeGlow.renderSun) and anyone looking at them is
 * blinded: their screen floods with bright light in the corps' colour for as long as they look,
 * and it only clears once they look away (over RingTuning.LANTERN_FLASH_FADE). The charger
 * themself isn't blinded by their own light (the lantern's own glare is LanternGlare).
 */
public final class LanternFlash {
	/** Ticks a sun keeps its last brightness after the server's last word (it repeats every other tick). */
	private static final int LAPSE = 3;
	/** Ticks the sun takes to shrink back into the ring after the burst. */
	private static final float SETTLE = 14f;
	/** Within this many blocks the flash is at full strength; it's gone by FAR. */
	private static final double NEAR = 5;
	private static final double FAR = 28;

	/** A ring pouring out light, by bearer entity id. */
	private static final class Source {
		float power;
		long at;
		Corps corps;
	}

	private static final Map<Integer, Source> SOURCES = new HashMap<>();
	/** How blinded this screen is, 0 = not at all, about 1 = white-out; last tick and this one. */
	private static float flash;
	private static float prevFlash;
	/** The colour of the light that blinded us last. */
	private static Corps flashCorps = Corps.GREEN;

	private LanternFlash() {
	}

	public static void register() {
		ClientPlayNetworking.registerGlobalReceiver(LanternFlashPayload.TYPE, (payload, context) -> handle(payload));
		HudElementRegistry.addFirst(LanternRing.id("lantern_flash"), LanternFlash::extract);
	}

	public static void handle(LanternFlashPayload payload) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Source s = SOURCES.computeIfAbsent(payload.bearer(), k -> new Source());
		s.power = payload.power();
		s.at = mc.level.getGameTime();
		Corps[] all = Corps.values();
		s.corps = all[Mth.clamp(payload.corps(), 0, all.length - 1)];
	}

	private static float smooth(float x) {
		x = Mth.clamp(x, 0f, 1f);
		return x * x * (3 - 2 * x);
	}

	/**
	 * How bright the sun on this player's ring is: about 0.25 as the ring meets the lens, 1 just
	 * before it fills, {@link com.sparky.lanternring.LanternFlash#BURST} at the burst, then back
	 * down into the ring. 0 when they aren't charging. Your own follows your charge directly.
	 */
	public static float sun(Player player, float partialTick) {
		Minecraft mc = Minecraft.getInstance();
		if (player == mc.player) {
			// The Dark Lantern (G3): the light comes from the lantern itself, so no sun on the ring.
			if (LanternFirstPerson.g3()) return 0f;
			float k = 1f;
			float t = LanternFirstPerson.held(partialTick);
			int contact = LanternCharge.hold() + LanternCharge.reach();
			int done = LanternCharge.done();
			if (t >= contact && t < done) {
				float x = (t - contact) / Math.max(1, done - contact);
				return k * (0.25f + 0.75f * (float) Math.pow(x, 1.5));
			}
			float a = LanternGlare.after(partialTick);
			if (a >= 0 && a < SETTLE) return k * com.sparky.lanternring.LanternFlash.BURST * (1f - smooth(a / SETTLE));
			return 0f;
		}
		return sun(player.getId(), partialTick);
	}

	/** The sun on another bearer's ring, as the server last told us. */
	private static float sun(int bearer, float partialTick) {
		Minecraft mc = Minecraft.getInstance();
		Source s = SOURCES.get(bearer);
		if (s == null || mc.level == null) return 0f;
		float age = mc.level.getGameTime() - s.at + partialTick;
		if (age <= LAPSE) return s.power;
		return s.power * (1f - smooth((age - LAPSE) / SETTLE));
	}

	/** Other bearers whose ring is pouring out light right now (the server still repeats it), for {@link SunDim}. */
	static void forEachCharger(Minecraft mc, java.util.function.Consumer<Entity> action) {
		if (mc.level == null) return;
		long now = mc.level.getGameTime();
		for (Map.Entry<Integer, Source> e : SOURCES.entrySet()) {
			if (e.getValue().power <= 0f || now - e.getValue().at > LAPSE) continue;
			Entity bearer = mc.level.getEntity(e.getKey());
			if (bearer != null && bearer != mc.player) action.accept(bearer);
		}
	}

	/** Every client tick: how much each ring's light is blinding us, and dropping stale suns. */
	public static void tick(Minecraft mc) {
		prevFlash = flash;
		LocalPlayer me = mc.player;
		if (me == null || mc.level == null) {
			SOURCES.clear();
			flash = prevFlash = 0f;
			return;
		}
		long now = mc.level.getGameTime();
		float target = 0f;
		Corps strongest = null;
		for (Iterator<Map.Entry<Integer, Source>> it = SOURCES.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<Integer, Source> e = it.next();
			Source s = e.getValue();
			if (now - s.at > LAPSE + SETTLE || now < s.at) {
				it.remove();
				continue;
			}
			Entity bearer = mc.level.getEntity(e.getKey());
			if (bearer == null || bearer == me) continue;
			float b = blinding(mc, me, bearer, sun(e.getKey(), 0f));
			if (b > target) {
				target = b;
				strongest = s.corps;
			}
		}
		if (strongest != null) flashCorps = strongest;
		if (target > flash) {
			// Light hits at once...
			flash += (target - flash) * 0.75f;
		} else {
			// ...and the eyes take a while to recover once you look away.
			float fade = Math.max(1, RingTuning.LANTERN_FLASH_FADE.ticks());
			flash = Math.max(target, flash - 1.2f / fade);
		}
	}

	/** How much a ring this bright at {@code bearer} blinds {@code me}: facing it, near it, seeing it. */
	static float blinding(Minecraft mc, Player me, Entity bearer, float power) {
		if (power <= 0.01f) return 0f;
		Vec3 eye = me.getEyePosition();
		// The light is at the ring, held up in front of the chest.
		Vec3 light = bearer.getEyePosition().add(bearer.getViewVector(1f).scale(0.5)).add(0, -0.4, 0);
		Vec3 to = light.subtract(eye);
		double dist = to.length();
		if (dist > FAR) return 0f;
		float near = dist < 1e-3 ? 1f : 1f - smooth((float) ((dist - NEAR) / (FAR - NEAR)));
		float dot = dist < 1e-3 ? 1f : (float) me.getViewVector(1f).dot(to.scale(1 / dist));
		// Looking straight at it is a white-out; at the edge of your view it's a glare; behind you, nothing much.
		float facing = smooth((dot - 0.25f) / 0.6f);
		float spill = 0.08f;
		boolean seen = mc.level.clip(new ClipContext(eye, light, ClipContext.Block.VISUAL, ClipContext.Fluid.NONE, me)).getType() == HitResult.Type.MISS;
		float b = power * near * (spill + (1f - spill) * facing);
		return seen ? b : b * 0.15f;
	}

	/** Test hook: how blinded the screen is right now. */
	public static float flash() {
		return flash;
	}

	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null) return;
		float partial = delta.getGameTimeDeltaPartialTick(false);
		float f = Mth.lerp(partial, prevFlash, flash);
		if (f <= 0.004f) return;
		int w = graphics.guiWidth();
		int h = graphics.guiHeight();
		float time = mc.level == null ? 0 : mc.level.getGameTime() + partial;
		// Like Darkness, but light: the glare throbs a little while it lasts.
		float pulse = 0.94f + 0.06f * Mth.sin(time * 0.45f);
		// The corps' colour, pale and bright, burning toward white the harder it hits.
		int pale = lerpRgb(flashCorps.rgb, 0xFFFFFF, 0.45f);
		int rgb = lerpRgb(pale, 0xFFFFFF, 0.55f * smooth((f - 0.75f) / 0.6f));
		float alpha = Mth.clamp((float) Math.pow(Math.min(f, 1.2f) / 1.05f, 0.8) * pulse, 0f, 0.97f);
		graphics.fill(0, 0, w, h, Math.round(255 * alpha) << 24 | rgb);
	}

	private static int lerpRgb(int from, int to, float t) {
		int r = Math.round(Mth.lerp(t, from >> 16 & 0xFF, to >> 16 & 0xFF));
		int g = Math.round(Mth.lerp(t, from >> 8 & 0xFF, to >> 8 & 0xFF));
		int b = Math.round(Mth.lerp(t, from & 0xFF, to & 0xFF));
		return r << 16 | g << 8 | b;
	}
}
