package com.sparky.lanternring.client;

import com.sparky.lanternring.RingTuning;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/**
 * Ring Lab's Durations page: every value in RingTuning, in seconds, as a box to type in with - and +
 * either side. Changes apply straight away and are saved to config/lanternring-tuning.json.
 */
public class RingTuningScreen extends Screen {
	private static final int ROW = 22;
	private static final int LABEL_W = 112;
	private static final int STEP_W = 16;
	private static final int BOX_W = 40;
	private static final int COLUMN_W = LABEL_W + STEP_W + 2 + BOX_W + 2 + STEP_W;
	private static final int GAP = 10;
	private static final int TOP = 34;

	private final Screen parent;
	private final List<Runnable> refreshers = new ArrayList<>();
	private int rowsPerColumn;
	private int columns = 2;
	private int shownRows;
	private int scroll;
	private int maxScroll;

	public RingTuningScreen(Screen parent) {
		super(Component.translatable("screen.lanternring.tuning"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		refreshers.clear();
		List<RingTuning.Entry> entries = RingTuning.entries();
		// As many columns as fit, and the rows scroll so Reset and Done always stay on screen.
		columns = Math.clamp((width + GAP) / (COLUMN_W + GAP), 1, 3);
		rowsPerColumn = (entries.size() + columns - 1) / columns;
		shownRows = Math.clamp((height - 44 - TOP) / ROW, 1, rowsPerColumn);
		maxScroll = rowsPerColumn - shownRows;
		scroll = Math.clamp(scroll, 0, maxScroll);
		int left = left();

		for (int i = 0; i < entries.size(); i++) {
			int row = i % rowsPerColumn - scroll;
			if (row < 0 || row >= shownRows) continue;
			RingTuning.Entry entry = entries.get(i);
			int x = left + (i / rowsPerColumn) * (COLUMN_W + GAP) + LABEL_W;
			int y = TOP + row * ROW;

			EditBox box = new EditBox(font, x + STEP_W + 2, y, BOX_W, 20, label(entry));
			box.setMaxLength(7);
			box.setResponder(text -> {
				try {
					if (!text.isEmpty() && !text.equals(".")) entry.set(Double.parseDouble(text));
				} catch (NumberFormatException ignored) {
					// Not a number (yet); keep the value as it was.
				}
			});
			addRenderableWidget(Button.builder(Component.literal("-"), b -> {
				entry.nudge(-1);
				changed();
			}).bounds(x, y, STEP_W, 20).build());
			addRenderableWidget(box);
			addRenderableWidget(Button.builder(Component.literal("+"), b -> {
				entry.nudge(1);
				changed();
			}).bounds(x + STEP_W + 2 + BOX_W + 2, y, STEP_W, 20).build());
			refreshers.add(() -> box.setValue(RingTuning.format(entry.seconds())));
		}

		int y = TOP + shownRows * ROW + 6;
		addRenderableWidget(Button.builder(Component.translatable("tuning.lanternring.reset"), b -> {
			RingTuning.resetAll();
			changed();
		}).bounds(width / 2 - 146, y, 144, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("gui.done"), b -> onClose())
				.bounds(width / 2 + 2, y, 144, 20).build());
		refreshers.forEach(Runnable::run);
	}

	private int left() {
		return width / 2 - (COLUMN_W * columns + GAP * (columns - 1)) / 2;
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		int next = Math.clamp(scroll - 3L * (long) Math.signum(scrollY), 0, maxScroll);
		if (next == scroll) return super.mouseScrolled(mouseX, mouseY, scrollX, scrollY);
		scroll = next;
		rebuildWidgets();
		return true;
	}

	private static Component label(RingTuning.Entry entry) {
		return Component.translatable("tuning.lanternring." + entry.key);
	}

	private void changed() {
		RingTuning.save();
		refreshers.forEach(Runnable::run);
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, title.getString(), width / 2, 10, 0xFF55FF77);
		graphics.centeredText(font, Component.translatable("tuning.lanternring.hint").getString(), width / 2, 21, 0xFFAAAAAA);
		List<RingTuning.Entry> entries = RingTuning.entries();
		int left = left();
		for (int i = 0; i < entries.size(); i++) {
			int row = i % rowsPerColumn - scroll;
			if (row < 0 || row >= shownRows) continue;
			RingTuning.Entry entry = entries.get(i);
			int x = left + (i / rowsPerColumn) * (COLUMN_W + GAP) + LABEL_W / 2;
			int y = TOP + row * ROW + 6;
			String text = label(entry).getString();
			int color = entry.isDefault() ? 0xFFFFFFFF : 0xFF55FF55;
			// Long names shrink to fit beside the - button instead of running under it.
			float fit = Math.min(1f, (LABEL_W - 4f) / font.width(text));
			if (fit >= 1f) {
				graphics.centeredText(font, text, x, y, color);
			} else {
				graphics.pose().pushMatrix();
				graphics.pose().translate(x, y + 4.5f * (1 - fit));
				graphics.pose().scale(fit, fit);
				graphics.centeredText(font, text, 0, 0, color);
				graphics.pose().popMatrix();
			}
		}
		if (scroll > 0) graphics.text(font, "\u25B2", left - 10, TOP + 6, 0xFFAAAAAA);
		if (scroll < maxScroll) graphics.text(font, "\u25BC", left - 10, TOP + (shownRows - 1) * ROW + 6, 0xFFAAAAAA);
		graphics.centeredText(font, Component.translatable("tuning.lanternring.footer").getString(), width / 2, height - 12, 0xFF777777);
	}

	@Override
	public void onClose() {
		RingTuning.save();
		minecraft.setScreenAndShow(parent);
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
