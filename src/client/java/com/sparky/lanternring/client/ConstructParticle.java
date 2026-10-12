package com.sparky.lanternring.client;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.SingleQuadParticle;
import net.minecraft.client.particle.SpriteSet;

/** Hard-light particle: full-bright green, tinted per spawn. */
public class ConstructParticle extends SingleQuadParticle {
	public enum Behavior { MOTE, DRIP, SHARD, SPARK }

	private static final int FULL_BRIGHT = 0xF000F0;

	private final Behavior behavior;
	private float baseSize;
	private float spin;
	private int hangTicks;
	private boolean landed;

	public ConstructParticle(ClientLevel level, double x, double y, double z, double vx, double vy, double vz,
			SpriteSet sprites, Behavior behavior) {
		super(level, x, y, z, sprites.get(level.getRandom()));
		this.behavior = behavior;
		this.xd = vx;
		this.yd = vy;
		this.zd = vz;
		this.hasPhysics = false;
		this.gravity = 0;
		this.friction = 0.92f;
		this.alpha = 1f;
		setColor(0.3f, 1f, 0.4f);
		switch (behavior) {
			case MOTE -> {
				lifetime = 18 + random.nextInt(22);
				baseSize = 0.05f + random.nextFloat() * 0.05f;
			}
			case DRIP -> {
				lifetime = 80;
				baseSize = 0.045f + random.nextFloat() * 0.02f;
				hangTicks = 8 + random.nextInt(25);
				hasPhysics = true;
				friction = 0.98f;
			}
			case SHARD -> {
				lifetime = 14 + random.nextInt(18);
				baseSize = 0.07f + random.nextFloat() * 0.07f;
				spin = (random.nextFloat() - 0.5f) * 0.6f;
				roll = random.nextFloat() * (float) Math.PI;
				oRoll = roll;
				gravity = 0.4f;
				friction = 0.9f;
			}
			case SPARK -> {
				lifetime = 4 + random.nextInt(5);
				baseSize = 0.1f + random.nextFloat() * 0.08f;
				friction = 0.75f;
			}
		}
		quadSize = baseSize;
	}

	/** Multiplies size; used by the strength setting and bigger effects. */
	public ConstructParticle sized(float scale) {
		baseSize *= scale;
		quadSize = baseSize;
		return this;
	}

	public ConstructParticle tinted(float r, float g, float b) {
		setColor(r, g, b);
		return this;
	}

	public ConstructParticle lasting(int ticks) {
		lifetime = ticks;
		return this;
	}

	@Override
	protected Layer getLayer() {
		return Layer.TRANSLUCENT;
	}

	@Override
	protected int getLightCoords(float partialTick) {
		return FULL_BRIGHT;
	}

	@Override
	public void tick() {
		if (behavior == Behavior.DRIP && !landed) {
			if (age < hangTicks) {
				// Cling and swell, like a tear on crying obsidian.
				xo = x;
				yo = y;
				zo = z;
				xd = yd = zd = 0;
				quadSize = baseSize * (0.6f + 0.4f * age / (float) hangTicks);
				age++;
				return;
			}
			gravity = 0.9f;
		}
		super.tick();
		float life = age / (float) lifetime;
		switch (behavior) {
			case MOTE -> {
				alpha = life < 0.2f ? life / 0.2f : 1f - (life - 0.2f) / 0.8f;
				quadSize = baseSize * (1f - life * 0.4f);
			}
			case DRIP -> {
				if (onGround && !landed) {
					landed = true;
					gravity = 0;
					xd = yd = zd = 0;
					lifetime = age + 6;
				}
				if (landed) {
					quadSize = baseSize * (1.6f - 0.15f * (lifetime - age));
					alpha = (lifetime - age) / 6f;
				}
			}
			case SHARD -> {
				oRoll = roll;
				roll += spin;
				alpha = 1f - life * life;
			}
			case SPARK -> {
				quadSize = baseSize * (1f - life);
				alpha = 1f - life;
			}
		}
	}
}
