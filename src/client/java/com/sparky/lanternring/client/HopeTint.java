package com.sparky.lanternring.client;

import com.sparky.lanternring.Hope;
import net.fabricmc.fabric.api.client.rendering.v1.RenderStateDataKey;
import net.minecraft.world.entity.LivingEntity;

/** Tints the Blue Lantern's villagers and golems blue (see Hope.Mark); villagers fade back to normal. */
public final class HopeTint {
	public static final RenderStateDataKey<Float> KEY = RenderStateDataKey.create(() -> "lanternring:hope");
	/** The blue they start at, 0xRRGGBB. */
	private static final int BLUE = 0x4FA0FF;

	private HopeTint() {
	}

	public static float strength(LivingEntity entity) {
		Hope.Mark mark = entity.getAttached(Hope.MARK);
		return mark == null ? 0f : mark.blue(entity.level().getGameTime());
	}

	/** {@code argb} multiplied towards blue by {@code t} (0 to 1). */
	public static int apply(int argb, float t) {
		int r = Math.round(255 + ((BLUE >> 16 & 0xFF) - 255) * t);
		int g = Math.round(255 + ((BLUE >> 8 & 0xFF) - 255) * t);
		int b = Math.round(255 + ((BLUE & 0xFF) - 255) * t);
		return argb & 0xFF000000
				| ((argb >> 16 & 0xFF) * r / 255) << 16
				| ((argb >> 8 & 0xFF) * g / 255) << 8
				| (argb & 0xFF) * b / 255;
	}
}
