package com.sparky.lanternring.client;

import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.MultiLineEditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/**
 * Ring Lab ✎: a note on one take of one row ("ring_model.N04"), saved in lanternring-lab.json next to its rating and
 * sent in the Copy report and Send to Claude. The note saves as you type, so closing the box any way keeps it.
 */
public class RowNoteScreen extends Screen {
	private final Screen parent;
	private final LabSettings.Option<?> option;
	private final String key;
	private final String take;
	private MultiLineEditBox text;

	public RowNoteScreen(Screen parent, LabSettings.Option<?> option) {
		super(Component.translatable("lab.lanternring.note.title"));
		this.parent = parent;
		this.option = option;
		LabSettings s = LabSettings.get();
		this.key = option.ratingKey(s);
		this.take = option.valueLabel(option.current(s));
	}

	@Override
	protected void init() {
		LabSettings s = LabSettings.get();
		int left = width / 2 - 150;
		int boxH = Math.max(40, Math.min(100, height - 40 - 60));
		text = MultiLineEditBox.builder().setX(left).setY(40)
				.setPlaceholder(Component.translatable("lab.lanternring.note.hint").withStyle(ChatFormatting.DARK_GRAY))
				.build(font, 300, boxH, Component.translatable("lab.lanternring.note.title"));
		text.setCharacterLimit(1000);
		text.setValue(s.note(key));
		text.setValueListener(v -> {
			s.setNote(key, v);
			s.save();
		});
		addRenderableWidget(text);
		setInitialFocus(text);
		int y = 40 + boxH + 10;
		addRenderableWidget(Button.builder(Component.translatable("gui.done"), b -> onClose()).bounds(left, y, 146, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.note.clear"), b -> text.setValue(""))
				.bounds(left + 154, y, 146, 20).build());
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, title.getString(), width / 2, 10, 0xFF55FF77);
		graphics.centeredText(font, font.plainSubstrByWidth(option.label() + ": " + take, width - 10), width / 2, 24, 0xFFCCCCCC);
	}

	@Override
	public void onClose() {
		LabSettings s = LabSettings.get();
		s.setNote(key, text.getValue());
		s.save();
		minecraft.setScreenAndShow(parent);
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
