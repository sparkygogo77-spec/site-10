package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.sounds.AbstractTickableSoundInstance;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * The lasso's sounds, two loops per bubble that follow it for as long as it lasts:
 * <ul>
 * <li>HUM: the hard-light rope humming while it is held. The longer the rope, the higher and louder
 * it sings, and it wavers up when the bubble is swung fast. The bearer hears it right at the ring
 * however far out the bubble is; everyone else hears it at the bubble. It fades out on a throw.</li>
 * <li>WIND: the rush of air around the bubble, swelling with its speed, so a swing or a big throw
 * roars and a slow float is silent.</li>
 * </ul>
 */
final class LassoSound extends AbstractTickableSoundInstance {
	private static final SoundEvent HUM = SoundEvent.createVariableRangeEvent(LanternRing.id("lasso_hum"));
	/** Rope length (blocks) at which the hum reaches its highest pitch. */
	private static final double LONG_ROPE = 120;
	private static final int FADE_TICKS = 10;

	private final int target;
	private final boolean hum;
	private Vec3 last;
	private float speed;
	private float pitchNow = 0.6f;
	private int fade = FADE_TICKS;

	private LassoSound(int target, boolean hum, Minecraft mc) {
		super(hum ? HUM : SoundEvents.ELYTRA_FLYING, SoundSource.PLAYERS, mc.level.getRandom());
		this.target = target;
		this.hum = hum;
		this.looping = true;
		this.delay = 0;
		this.volume = 0.01f;
		this.pitch = hum ? 0.6f : 0.8f;
		this.attenuation = SoundInstance.Attenuation.LINEAR;
	}

	/** Starts the hum (or the wind) for the bubble around this mob. */
	static LassoSound start(Minecraft mc, int target, boolean hum) {
		LassoSound sound = new LassoSound(target, hum, mc);
		sound.tick();
		mc.getSoundManager().play(sound);
		return sound;
	}

	@Override
	public boolean canStartSilent() {
		return true;
	}

	@Override
	public void tick() {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || mc.player == null) {
			stop();
			return;
		}
		LassoFx.Bubble b = LassoFx.bubble(target);
		Entity mob = mc.level.getEntity(target);
		Player holder = b != null && mc.level.getEntity(b.holder) instanceof Player p ? p : null;
		boolean alive = mob != null && b != null && (!hum || holder != null);
		if (!alive) {
			// Fade out instead of cutting off.
			volume *= 0.7f;
			if (--fade <= 0 || volume < 0.01f) stop();
			return;
		}
		fade = FADE_TICKS;
		Vec3 center = mob.getBoundingBox().getCenter();
		float moved = last == null ? 0 : (float) center.distanceTo(last);
		last = center;
		speed += (moved - speed) * 0.4f;

		if (hum) {
			Vec3 eye = holder.getEyePosition();
			double length = center.distanceTo(eye);
			float stretch = (float) Mth.clamp(length / LONG_ROPE, 0, 1);
			float targetPitch = 0.55f + 1.2f * (float) Math.sqrt(stretch) + Math.min(0.25f, speed * 0.05f);
			pitchNow += (targetPitch - pitchNow) * 0.25f;
			pitch = Mth.clamp(pitchNow, 0.5f, 2.0f);
			volume = 0.45f + 0.45f * stretch + Math.min(0.3f, speed * 0.06f);
			// The bearer hears the rope at their ring; it would be lost in the distance otherwise.
			Vec3 at = holder == mc.player ? eye.add(center.subtract(eye).normalize().scale(Math.min(length, 2))) : center;
			x = at.x;
			y = at.y;
			z = at.z;
		} else {
			float rush = Mth.clamp((speed - 0.25f) / 2.5f, 0, 1);
			volume = rush * 1.6f;
			pitch = 0.7f + 0.6f * rush;
			x = center.x;
			y = center.y;
			z = center.z;
		}
	}
}
