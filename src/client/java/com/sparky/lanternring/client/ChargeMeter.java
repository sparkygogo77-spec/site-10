package com.sparky.lanternring.client;

import com.sparky.lanternring.Anvils;
import com.sparky.lanternring.BlackHoles;
import com.sparky.lanternring.BlastDrills;
import com.sparky.lanternring.Builds;
import com.sparky.lanternring.Deluges;
import com.sparky.lanternring.HeldConstructs;
import com.sparky.lanternring.ConstructArmy;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * A small meter beside the hotbar while the ring is held: the mode, what each of its levels costs
 * (the current one lit), the ring's charge with the part the next use will spend flashing at its
 * end, and how many more uses that leaves. While the Beam charges, a thin bar above it fills
 * toward the charged shot.
 */
public final class ChargeMeter {
	static final int WIDTH = 80;
	private static final int NAME = 0xFF55FF77;
	private static final int LIT = 0xFFE6FFE9;
	private static final int DIM = 0xFF5E8A66;
	private static final int FILL = 0xFF2FA84A;

	/** One level of a mode: its label, what it costs (with a unit like "/s"), and whether it's the one in use. */
	record Level(String label, int cost, String unit, boolean current) {
		Level(String label, int cost, boolean current) {
			this(label, cost, "", current);
		}

		String text() {
			return (label.isEmpty() ? "" : label + " ") + percent(cost) + unit;
		}
	}

	/** Text is drawn at this scale so a mode's levels fit beside the hotbar. */
	private static final float TEXT = 0.75f;

	private ChargeMeter() {
	}

	public static void register() {
		HudElementRegistry.attachElementAfter(VanillaHudElements.HOTBAR, LanternRing.id("charge_meter"), ChargeMeter::extract);
	}

	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		Player player = mc.player;
		LabSettings.ChargeMeter style = LabSettings.get().chargeMeter;
		if (player == null || player.isSpectator() || style == LabSettings.ChargeMeter.OFF) return;
		ItemStack ring = player.getMainHandItem();
		if (!(ring.getItem() instanceof PowerRingItem)) ring = player.getOffhandItem();
		if (!(ring.getItem() instanceof PowerRingItem)) return;

		float partial = delta.getGameTimeDeltaPartialTick(false);
		float beam = BeamChargeGlow.progress(player, partial);
		if (beam < 0f) beam = blastProgress(player, partial);
		RingMode mode = PowerRingItem.getMode(ring);
		// In the ring's own colour: the meter's greens become the corps' shades.
		Corps corps = Corps.of(ring);
		List<Level> levels = levels(mode, ring, player, beam);
		Level current = levels.stream().filter(Level::current).findFirst().orElse(levels.get(0));

		Font font = mc.font;
		// Beside the hotbar, past the off-hand slot when that sits on the right.
		int x = graphics.guiWidth() / 2 + 91 + 6;
		if (player.getMainArm() == HumanoidArm.LEFT && !player.getOffhandItem().isEmpty()) x += 29;
		int bottom = graphics.guiHeight();

		// A soft backdrop so it reads over a bright sky or the fist.
		String name = mode.displayName().getString();
		int textW = font.width(name) + 5;
		if (style == LabSettings.ChargeMeter.LEVELS) for (Level level : levels) textW += font.width(level.text()) + 5;
		else textW += font.width(current.text());
		int backW = Math.max(Math.round(textW * TEXT), WIDTH + 22);
		graphics.fill(x - 3, bottom - 23, x + backW + 1, bottom - 1, 0x60000000);

		// The mode and its levels.
		graphics.pose().pushMatrix();
		graphics.pose().translate(x, bottom - 20);
		graphics.pose().scale(TEXT, TEXT);
		graphics.text(font, name, 0, 0, CorpsTint.apply(corps, NAME));
		int tx = font.width(name) + 5;
		if (style == LabSettings.ChargeMeter.LEVELS) {
			for (Level level : levels) {
				graphics.text(font, level.text(), tx, 0, CorpsTint.apply(corps, level.current() ? LIT : DIM));
				tx += font.width(level.text()) + 5;
			}
		} else {
			graphics.text(font, current.text(), tx, 0, CorpsTint.apply(corps, LIT));
		}
		graphics.pose().popMatrix();

		// The ring's charge, with what the next use spends flashing at its end.
		int charge = PowerRingItem.getCharge(ring);
		int by = bottom - 10;
		graphics.fill(x - 1, by - 1, x + WIDTH + 1, by + 5, 0xB0000000);
		int filled = Math.round(WIDTH * charge / (float) PowerRingItem.MAX_CHARGE);
		graphics.fill(x, by, x + filled, by + 4, CorpsTint.apply(corps, FILL));
		int spend = Math.min(filled, Math.max(2, Math.round(WIDTH * current.cost() / (float) PowerRingItem.MAX_CHARGE)));
		float pulse = 0.5f + 0.5f * Mth.sin((player.tickCount + partial) * 0.35f);
		int flash = CorpsTint.apply(corps, 0xFF000000 | lerpRgb(0x7CFF8C, 0xFFFFFF, pulse));
		if (charge < current.cost()) flash = 0xFFFF5555;
		graphics.fill(x + filled - spend, by, x + filled, by + 4, flash);

		// Uses left at this level.
		if (!player.isCreative()) {
			String uses = "x" + (charge / Math.max(1, current.cost()));
			graphics.pose().pushMatrix();
			graphics.pose().translate(x + WIDTH + 3, by - 1);
			graphics.pose().scale(TEXT, TEXT);
			graphics.text(font, uses, 0, 0, charge < current.cost() ? 0xFFFF5555 : CorpsTint.apply(corps, 0xFFB8C8BA));
			graphics.pose().popMatrix();
		}

		// Building the charged Beam: a thin bar that fills toward the charged shot.
		if (beam >= 0f) {
			int w = Math.round(WIDTH * beam);
			graphics.fill(x, by - 3, x + WIDTH, by - 2, 0x80000000);
			graphics.fill(x, by - 3, x + w, by - 2, beam >= 1f ? 0xFFFFFFFF : CorpsTint.apply(corps, 0xFF9CFFAA));
		}
	}

	/** Each level a mode can be used at, and what one use of it costs (0.1% = 1). */
	static List<Level> levels(RingMode mode, ItemStack ring, Player player, float beam) {
		List<Level> out = new ArrayList<>();
		switch (mode) {
			case BEAM -> {
				// Holding builds toward the charged shot; let go early and it's a tap.
				boolean full = beam >= 1f;
				out.add(new Level(tr("tap"), RingMode.BEAM.cost, !full));
				out.add(new Level(tr("charged"), RingPowers.BEAM_CHARGED_COST, full));
			}
			case BLAST -> {
				// Each level at full reach; a tap costs half of that.
				int level = BlastDrills.level(ring);
				for (int l = 1; l <= 3; l++) {
					int w = BlastDrills.width(l);
					out.add(new Level(w + "x" + w, BlastDrills.cost(l, 1f), l == level));
				}
			}
			case ANVIL -> {
				int size = Anvils.size(ring);
				// Levels 1-3: the anvil, the drill bit and the anchor.
				for (int i = 0; i < Anvils.SIZES.length; i++) {
					int s = Anvils.SIZES[i];
					out.add(new Level(String.valueOf(i + 1), Anvils.cost(s), s == size));
				}
			}
			case BLACK_HOLE -> {
				int size = BlackHoles.size(ring);
				for (int s : BlackHoles.SIZES) out.add(new Level(String.valueOf(s), BlackHoles.cost(s), s == size));
			}
			case DELUGE -> {
				int level = Deluges.level(ring);
				for (int i = 0; i < Deluges.RADII.length; i++) out.add(new Level(String.valueOf(i + 1), Deluges.cost(i), i == level));
			}
			case BUILD -> {
				// While choosing, what the design showing costs; before that, the range (1% to 75% by size).
				int design = BuildInput.designCost();
				if (design > 0) {
					out.add(new Level(tr("build_design"), design, true));
				} else {
					out.add(new Level(tr("build_min"), Builds.MIN_COST, true));
					out.add(new Level(tr("build_max"), Builds.MAX_COST, false));
				}
			}
			case DOME -> {
				// Raising it, then every second it's held (1 point a tick).
				boolean holding = player.isUsingItem();
				out.add(new Level("", mode.cost, !holding));
				out.add(new Level(tr("hold"), 20, "/s", holding));
			}
			case SHIELD -> {
				// Raising it, then every second it's held (1 point every HeldConstructs.SHIELD_DRAIN_INTERVAL ticks).
				boolean holding = player.isUsingItem();
				out.add(new Level("", mode.cost, !holding));
				out.add(new Level(tr("hold"), 20 / HeldConstructs.SHIELD_DRAIN_INTERVAL, "/s", holding));
			}
			case TETHER -> {
				boolean holding = player.isUsingItem();
				out.add(new Level("", mode.cost, !holding));
				out.add(new Level(tr("hold"), Math.max(1, 20 / Lasso.HOLD_DRAIN_INTERVAL), "/s", holding));
			}
			case ARMY -> {
				ConstructArmy.Type picked = ConstructArmy.type(ring);
				for (ConstructArmy.Type type : ConstructArmy.Type.values()) {
					out.add(new Level(tr(type.key), type.cost, type == picked));
				}
			}
			default -> out.add(new Level("", mode.cost, true));
		}
		return out;
	}

	/** How far the Blast's reach has built, 0 to 1, while it charges; -1 otherwise. */
	private static float blastProgress(Player player, float partial) {
		if (!player.isUsingItem()) {
			AnvilInput.blastRestart = 0;
			return -1f;
		}
		ItemStack used = player.getUseItem();
		if (!(used.getItem() instanceof PowerRingItem) || PowerRingItem.getMode(used) != RingMode.BLAST) return -1f;
		// A level change restarts the charge (left-click while holding, see AnvilInput).
		float held = player.getTicksUsingItem(partial) - Math.min(AnvilInput.blastRestart, player.getTicksUsingItem());
		return Mth.clamp(held / Math.max(1, RingTuning.BLAST_CHARGE.ticks()), 0f, 1f);
	}

	private static String tr(String key) {
		return Component.translatable("hud.lanternring." + key).getString();
	}

	/** Charge points as a percent of a full ring: 5 -> "0.5%", 10 -> "1%", 35 -> "3.5%". */
	static String percent(int points) {
		return (points % 10 == 0 ? String.valueOf(points / 10) : String.valueOf(points / 10.0)) + "%";
	}

	private static int lerpRgb(int a, int b, float t) {
		int r = (int) Mth.lerp(t, a >> 16 & 0xFF, b >> 16 & 0xFF);
		int g = (int) Mth.lerp(t, a >> 8 & 0xFF, b >> 8 & 0xFF);
		int bl = (int) Mth.lerp(t, a & 0xFF, b & 0xFF);
		return r << 16 | g << 8 | bl;
	}
}
