package com.sparky.lanternring.block;

import java.util.Locale;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.level.block.state.properties.EnumProperty;

/**
 * Which lantern a placed Power Battery shows: the one picked in the Ring Lab when it was set down
 * (the same names as LabSettings.LanternModel), so it stays the lantern the player was holding.
 * Corps with a lantern of their own (red, blue, yellow, violet) show that one whatever this says.
 */
public enum LanternStyle implements StringRepresentable {
	STONE, CLASSIC, TORUS, NEBULA, COMPACT, DARK, KEYCHAIN;

	public static final EnumProperty<LanternStyle> PROPERTY = EnumProperty.create("style", LanternStyle.class);

	@Override
	public String getSerializedName() {
		return name().toLowerCase(Locale.ROOT);
	}

	/** The style with this name, or STONE (the default lantern) for anything unknown. */
	public static LanternStyle byName(String name) {
		for (LanternStyle style : values()) {
			if (style.name().equalsIgnoreCase(name)) return style;
		}
		return STONE;
	}
}
