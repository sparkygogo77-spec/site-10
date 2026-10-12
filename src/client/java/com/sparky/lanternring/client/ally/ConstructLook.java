package com.sparky.lanternring.client.ally;

import net.minecraft.util.Mth;

/** Shared by the Army construct renderers. */
final class ConstructLook {
	static final int FULL_BRIGHT = 0xF000F0;

	private ConstructLook() {
	}

	/** Solid while it has charge to spare; flickers as the last of it runs out. */
	static int tint(float life, float age) {
		float alpha = 1f;
		if (life < 0.15f) alpha = 0.45f + 0.55f * Math.abs(Mth.sin(age * (0.25f + (0.15f - life) * 4f)));
		return Math.round(alpha * 255) << 24 | 0xFFFFFF;
	}
}
