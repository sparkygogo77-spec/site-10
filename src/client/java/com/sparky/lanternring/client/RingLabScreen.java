package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/**
 * Ring Lab: flip between versions of each look, rate them Keep / Improve / Drop, and copy a report
 * of your picks. Later this becomes the mod's settings screen.
 */
public class RingLabScreen extends Screen {
	private static final int ROW = 22;
	private static final int[] RATING_COLORS = {0xAAAAAA, 0x55FF55, 0xFFFF55, 0xFF5555};

	private final Screen parent;
	private final List<Runnable> refreshers = new ArrayList<>();
	private Component status = Component.empty();

	public RingLabScreen(Screen parent) {
		super(Component.translatable("screen.lanternring.lab"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		refreshers.clear();
		LabSettings s = LabSettings.get();
		int choiceW = 190;
		int rateW = 90;
		int left = width / 2 - (choiceW + 4 + rateW) / 2;
		int top = 34;

		for (int i = 0; i < LabSettings.OPTIONS.size(); i++) {
			LabSettings.Option<?> option = LabSettings.OPTIONS.get(i);
			int y = top + i * ROW;
			Button choice = addRenderableWidget(Button.builder(Component.empty(), b -> {
				option.cycle(s, 1);
				changed();
			}).bounds(left, y, choiceW, 20).build());
			Button rate = addRenderableWidget(Button.builder(Component.empty(), b -> {
				String key = option.ratingKey(s);
				LabSettings.Rating[] all = LabSettings.Rating.values();
				s.rate(key, all[(s.rating(key).ordinal() + 1) % all.length]);
				changed();
			}).bounds(left + choiceW + 4, y, rateW, 20).build());
			refreshers.add(() -> {
				choice.setMessage(Component.translatable("lab.lanternring." + option.key())
						.append(": ")
						.append(Component.translatable("lab.lanternring." + option.key() + "." + option.current(s).name().toLowerCase())
								.withStyle(ChatFormatting.GREEN)));
				LabSettings.Rating r = s.rating(option.ratingKey(s));
				rate.setMessage(Component.translatable("lab.lanternring.rating." + r.name().toLowerCase())
						.withColor(RATING_COLORS[r.ordinal()]));
			});
		}

		int y = top + LabSettings.OPTIONS.size() * ROW + 8;
		int w = 70;
		int x = width / 2 - (w * 4 + 12) / 2;
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.preview.blast"), b -> preview("blast")).bounds(x, y, w, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.preview.use"), b -> preview("use")).bounds(x + w + 4, y, w, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.preview.push"), b -> preview("push")).bounds(x + 2 * (w + 4), y, w, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.preview.charge"), b -> preview("charge")).bounds(x + 3 * (w + 4), y, w, 20).build());

		y += 24;
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.copy"), b -> {
			minecraft.keyboardHandler.setClipboard(s.report());
			status = Component.translatable("lab.lanternring.copied").withStyle(ChatFormatting.GREEN);
		}).bounds(width / 2 - 146, y, 96, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.durations"),
				b -> minecraft.setScreenAndShow(new RingTuningScreen(this))).bounds(width / 2 - 48, y, 96, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("gui.done"), b -> onClose()).bounds(width / 2 + 50, y, 96, 20).build());
		refreshers.forEach(Runnable::run);
	}

	private void changed() {
		LabSettings.get().save();
		refreshers.forEach(Runnable::run);
	}

	/** Close the menu so the effect can be seen, then play it in front of the player. */
	private void preview(String what) {
		onClose();
		LanternRingClientState.queuePreview(what);
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, title.getString() + "  v" + LanternRing.version(), width / 2, 10, 0xFF55FF77);
		graphics.centeredText(font, Component.translatable("lab.lanternring.hint").getString(), width / 2, 21, 0xFFAAAAAA);
		graphics.centeredText(font, status.getString(), width / 2, height - 12, 0xFF55FF55);
	}

	@Override
	public void onClose() {
		LabSettings.get().save();
		minecraft.setScreenAndShow(parent);
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
