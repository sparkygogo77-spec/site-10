package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.SelectModePayload;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;

/**
 * The mode wheel: hold the wheel key (R) with a ring in hand and every mode that ring's corps has
 * is laid out in a circle. Move the mouse towards one and let go of the key (or click) to switch
 * straight to it, instead of crouch + right-clicking through them one by one. Escape cancels.
 * <p>
 * Caps Lock (J, 2026-10-16) opens it {@link #cycling cycling}: each press switches straight to the next mode and the
 * wheel shows it. It stays up without holding the key, closing on a click, Escape, or a short pause with the mouse
 * left in the middle.
 */
public class ModeWheelScreen extends Screen {
	/** The mouse has to be this far from the middle before a mode is picked. */
	private static final int DEAD_ZONE = 22;

	private final KeyMapping key;
	private final Corps corps;
	private final List<RingMode> modes = new ArrayList<>();
	private RingMode current;
	private int hovered = -1;
	/** Opened by the mode-cycle key: it doesn't close when that key is let go. */
	private final boolean cycling;
	/** Ticks left before a cycling wheel left alone closes by itself. */
	private int idle;
	/** How long a cycling wheel stays up after the last press while the mouse stays in the middle (1.5 s). */
	private static final int IDLE_CLOSE = 30;

	public ModeWheelScreen(KeyMapping key, ItemStack ring) {
		this(key, ring, false);
	}

	private ModeWheelScreen(KeyMapping key, ItemStack ring, boolean cycling) {
		super(Component.translatable("screen.lanternring.mode_wheel"));
		this.key = key;
		this.corps = Corps.of(ring);
		this.current = PowerRingItem.getMode(ring);
		this.cycling = cycling;
		modes.addAll(corps.modes());
	}

	/** The mode-cycle key was pressed: switches the ring to its next mode and opens the wheel showing it. */
	public static ModeWheelScreen cycling(KeyMapping key, ItemStack ring) {
		ModeWheelScreen screen = new ModeWheelScreen(key, ring, true);
		screen.cycle();
		return screen;
	}

	/** Switches to the next mode after the one shown. */
	private void cycle() {
		idle = IDLE_CLOSE;
		if (modes.size() < 2) return;
		current = corps.next(current);
		if (ClientPlayNetworking.canSend(SelectModePayload.TYPE)) ClientPlayNetworking.send(new SelectModePayload(current.ordinal()));
	}

	@Override
	public void tick() {
		super.tick();
		// Left alone with the mouse in the middle, a cycling wheel goes away by itself.
		if (cycling && hovered < 0 && --idle <= 0) onClose();
		else if (cycling && hovered >= 0) idle = IDLE_CLOSE;
	}

	@Override
	public boolean keyPressed(KeyEvent event) {
		if (cycling && key.matches(event)) {
			cycle();
			return true;
		}
		return super.keyPressed(event);
	}

	private int radius() {
		return Math.max(50, Math.min(width, height) * 3 / 10);
	}

	/**
	 * Where mode i's label sits: on an oval that uses the screen's width, with every other label
	 * pulled in a little when there are many (the green ring has around twenty).
	 */
	private int[] spot(int i) {
		double a = i * Math.PI * 2 / modes.size() - Math.PI / 2;
		double rx = Math.max(radius(), width * 0.36), ry = Math.max(50, height * 0.36);
		double k = modes.size() > 10 && i % 2 == 1 ? 0.72 : 1.0;
		return new int[] {width / 2 + (int) Math.round(Math.cos(a) * rx * k), height / 2 + (int) Math.round(Math.sin(a) * ry * k)};
	}

	private int indexAt(double mx, double my) {
		double dx = mx - width / 2.0, dy = my - height / 2.0;
		if (dx * dx + dy * dy < DEAD_ZONE * DEAD_ZONE || modes.isEmpty()) return -1;
		// Slot 0 is at the top, going clockwise; measured on the oval, squashed back to a circle.
		double rx = Math.max(radius(), width * 0.36), ry = Math.max(50, height * 0.36);
		double a = Math.atan2(dy / ry, dx / rx) + Math.PI / 2;
		double step = Math.PI * 2 / modes.size();
		return Math.floorMod((int) Math.round(a / step), modes.size());
	}

	@Override
	public void extractBackground(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		graphics.fill(0, 0, width, height, 0x66000000);
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		hovered = indexAt(mouseX, mouseY);
		int cx = width / 2, cy = height / 2;
		int colour = 0xFF000000 | corps.rgb;

		// A faint disc in the middle and a ring of dots round the wheel.
		disc(graphics, cx, cy, DEAD_ZONE + 6, 0x99000000);
		// A pointer from the middle to the mode under the mouse.
		if (hovered >= 0) {
			int[] to = spot(hovered);
			double len = Math.hypot(to[0] - cx, to[1] - cy);
			for (double d = DEAD_ZONE; d < len - 10; d += 3) {
				int x = cx + (int) Math.round((to[0] - cx) * d / len), y = cy + (int) Math.round((to[1] - cy) * d / len);
				graphics.fill(x - 1, y - 1, x + 1, y + 1, colour);
			}
		}

		for (int i = 0; i < modes.size(); i++) {
			RingMode mode = modes.get(i);
			int[] at = spot(i);
			int x = at[0], y = at[1];
			Component name = corps.modeName(mode);
			int w = font.width(name) + 10;
			int x0 = x - w / 2, y0 = y - 8;
			boolean on = i == hovered;
			graphics.fill(x0, y0, x0 + w, y0 + 16, on ? colour : 0xCC101010);
			graphics.outline(x0, y0, w, 16, mode == current ? 0xFFFFFFFF : colour);
			int textColour = on ? 0xFF000000 : (mode == current ? 0xFFFFFFFF : colour);
			graphics.text(font, name, x - font.width(name) / 2, y0 + 4, textColour, !on);
		}

		// The middle says what the picked mode does.
		RingMode shown = hovered >= 0 ? modes.get(hovered) : current;
		graphics.centeredText(font, corps.modeName(shown), cx, cy - 10, colour);
		graphics.centeredText(font, Component.translatable(cycling ? "screen.lanternring.mode_wheel.cycle_hint" : "screen.lanternring.mode_wheel.hint"), cx, cy + 2, 0xFFAAAAAA);
		List<net.minecraft.util.FormattedCharSequence> lines = font.split(corps.modeDescription(shown), Math.min(260, width - 20));
		// Along the top, clear of the hotbar and the action bar.
		int ty = 4;
		for (net.minecraft.util.FormattedCharSequence line : lines) {
			graphics.centeredText(font, line, cx, ty, 0xFFDDDDDD);
			ty += 10;
		}
	}

	private static void disc(GuiGraphicsExtractor graphics, int cx, int cy, int r, int argb) {
		for (int dy = -r; dy <= r; dy++) {
			int half = (int) Math.sqrt(r * r - dy * dy);
			graphics.fill(cx - half, cy + dy, cx + half, cy + dy + 1, argb);
		}
	}

	/** Picks the mode under the mouse (if any) and closes. */
	public void choose(double mouseX, double mouseY) {
		int i = indexAt(mouseX, mouseY);
		if (i >= 0 && modes.get(i) != current && ClientPlayNetworking.canSend(SelectModePayload.TYPE)) {
			ClientPlayNetworking.send(new SelectModePayload(modes.get(i).ordinal()));
		}
		onClose();
	}

	@Override
	public boolean keyReleased(KeyEvent event) {
		if (key.matches(event) && !cycling) {
			double[] m = mouse();
			choose(m[0], m[1]);
			return true;
		}
		return super.keyReleased(event);
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		choose(event.x(), event.y());
		return true;
	}

	private double[] mouse() {
		var mc = minecraft;
		double sx = mc.mouseHandler.xpos() * width / mc.getWindow().getScreenWidth();
		double sy = mc.mouseHandler.ypos() * height / mc.getWindow().getScreenHeight();
		return new double[] {sx, sy};
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
