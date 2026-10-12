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

	public RingTuningScreen(Screen parent) {
		super(Component.translatable("screen.lanternring.tuning"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		refreshers.clear();
		List<RingTuning.Entry> entries = RingTuning.entries();
		rowsPerColumn = (entries.size() + 1) / 2;
		int left = width / 2 - (COLUMN_W * 2 + GAP) / 2;

		for (int i = 0; i < entries.size(); i++) {
			RingTuning.Entry entry = entries.get(i);
			int x = left + (i / rowsPerColumn) * (COLUMN_W + GAP) + LABEL_W;
			int y = TOP + (i % rowsPerColumn) * ROW;

			EditBox box = new EditBox(font, x + STEP_W + 2, y, BOX_W, 20, label(entry));
			box.setMaxLength(7);
			box.setFilter(text -> text.matches("[0-9]*\\.?[0-9]*"));
			box.setResponder(text -> {
				try {
					if (!text.isEmpty() && !text.equals(".")) entry.set(Double.parseDouble(text));
				} catch (NumberFormatException ignored) {
					// The filter keeps this from happening; leave the value as it was.
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

		int y = TOP + rowsPerColumn * ROW + 8;
		addRenderableWidget(Button.builder(Component.translatable("tuning.lanternring.reset"), b -> {
			RingTuning.resetAll();
			changed();
		}).bounds(width / 2 - 146, y, 144, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("gui.done"), b -> onClose())
				.bounds(width / 2 + 2, y, 144, 20).build());
		refreshers.forEach(Runnable::run);
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
		int left = width / 2 - (COLUMN_W * 2 + GAP) / 2;
		for (int i = 0; i < entries.size(); i++) {
			RingTuning.Entry entry = entries.get(i);
			int x = left + (i / rowsPerColumn) * (COLUMN_W + GAP) + LABEL_W / 2;
			int y = TOP + (i % rowsPerColumn) * ROW + 6;
			graphics.centeredText(font, label(entry).getString(), x, y, entry.isDefault() ? 0xFFFFFFFF : 0xFF55FF55);
		}
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
