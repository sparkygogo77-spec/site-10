package com.sparky.lanternring.client;

import java.nio.file.Path;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.MultiLineEditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/**
 * Ring Lab > Send to Claude: pick Redo / Retry, Approve, Remove or Note, type an optional message and
 * send it as a GitHub issue (see {@link RingInbox}). Claude picks those up and passes them on.
 */
public class SendToClaudeScreen extends Screen {
	private static final String[] HELP = {
			"Sends Claude a GitHub issue with your note, version, ring and report.",
			"Uses the Updates token, which also needs Issues: Read and write.",
			"For a screenshot, press F2 in game first; the newest one is sent."
	};
	private static final int[] ACTION_COLORS = {0xFFFF55, 0x55FF55, 0xFF5555, 0x55FFFF};

	private final Screen parent;
	private RingInbox.Action action = RingInbox.Action.NOTE;
	private boolean screenshot;
	private boolean sending;
	private MultiLineEditBox text;
	private Button actionButton;
	private Button shotButton;
	private Button sendButton;
	private Component status = Component.empty();

	public SendToClaudeScreen(Screen parent) {
		super(Component.translatable("screen.lanternring.inbox"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		int top = 30 + HELP.length * 11 + 6;
		int left = width / 2 - 150;
		actionButton = addRenderableWidget(Button.builder(Component.empty(), b -> {
			RingInbox.Action[] all = RingInbox.Action.values();
			action = all[(action.ordinal() + 1) % all.length];
			refresh();
		}).bounds(left, top, 146, 20).build());
		shotButton = addRenderableWidget(Button.builder(Component.empty(), b -> {
			screenshot = !screenshot;
			refresh();
		}).bounds(left + 154, top, 146, 20).build());
		int boxH = Math.max(40, Math.min(100, height - top - 26 - 64));
		text = MultiLineEditBox.builder().setX(left).setY(top + 26)
				.setPlaceholder(Component.translatable("inbox.lanternring.placeholder").withStyle(ChatFormatting.DARK_GRAY))
				.build(font, 300, boxH, Component.translatable("inbox.lanternring.text"));
		text.setCharacterLimit(4000);
		// The draft lives in lanternring-lab.json, so leaving the panel (Back, Esc, another menu) never loses it (issue #323).
		text.setValue(LabSettings.get().inboxDraft);
		text.setValueListener(v -> LabSettings.get().inboxDraft = v);
		addRenderableWidget(text);
		int y = top + 26 + boxH + 14;
		sendButton = addRenderableWidget(Button.builder(Component.translatable("inbox.lanternring.send"), b -> send())
				.bounds(left, y, 146, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("gui.back"), b -> onClose()).bounds(left + 154, y, 146, 20).build());
		refresh();
	}

	private void refresh() {
		actionButton.setMessage(Component.translatable("inbox.lanternring.action")
				.append(Component.literal(action.label).withColor(ACTION_COLORS[action.ordinal()])));
		Path shot = RingInbox.latestScreenshot();
		Component shotState = !screenshot ? Component.translatable("options.off").withStyle(ChatFormatting.GRAY)
				: shot == null ? Component.translatable("inbox.lanternring.screenshot.none").withStyle(ChatFormatting.RED)
				: Component.translatable("inbox.lanternring.screenshot.latest").withStyle(ChatFormatting.GREEN);
		shotButton.setMessage(Component.translatable("inbox.lanternring.screenshot").append(shotState));
		sendButton.active = !sending;
	}

	private void send() {
		if (sending) return;
		sending = true;
		status = Component.translatable("inbox.lanternring.sending").withStyle(ChatFormatting.GRAY);
		refresh();
		String note = text.getValue();
		LabSettings.get().inboxDraft = note;
		LabSettings.get().save();
		RingInbox.send(action, note, screenshot).whenComplete((url, error) -> minecraft.execute(() -> {
			sending = false;
			if (error == null) {
				status = Component.translatable("inbox.lanternring.sent", url).withStyle(ChatFormatting.GREEN);
				LabSettings.get().inboxDraft = "";
				LabSettings.get().save();
				if (text != null) text.setValue("");
			} else {
				Throwable cause = error.getCause() != null ? error.getCause() : error;
				String why = cause.getMessage() == null ? cause.getClass().getSimpleName() : cause.getMessage();
				status = Component.literal(why).withStyle(ChatFormatting.RED);
			}
			refresh();
		}));
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, title.getString(), width / 2, 10, 0xFF55FF77);
		for (int i = 0; i < HELP.length; i++) {
			graphics.centeredText(font, font.plainSubstrByWidth(HELP[i], width - 10), width / 2, 30 + i * 11, 0xFFAAAAAA);
		}
		graphics.centeredText(font, font.plainSubstrByWidth(status.getString(), width - 10), width / 2, height - 14,
				0xFF000000 | (status.getStyle().getColor() == null ? 0x55FF55 : status.getStyle().getColor().getValue()));
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
