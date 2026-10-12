package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Ring Lab's Updates page: paste the GitHub token once, check for a newer jar and download it. */
public class UpdateScreen extends Screen {
	private static final String[] HELP = {
			"One-time setup: on github.com open Settings > Developer settings >",
			"Personal access tokens > Fine-grained tokens > Generate new token.",
			"Repository access: Only select repositories > site-10.",
			"Permissions: Contents > Read-only (and Issues > Read and write for Send to Claude).",
			"Generate, copy, paste it below.",
			"After that the ring checks for new versions when you join a world."
	};

	private final Screen parent;
	private EditBox tokenBox;
	private Button downloadButton;

	private static final String SAVED_HINT = "(token saved; paste a new one to replace it)";

	public UpdateScreen(Screen parent) {
		super(Component.translatable("screen.lanternring.updates"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		int top = 34 + HELP.length * 11 + 8;
		tokenBox = new EditBox(font, width / 2 - 150, top, 300, 20, Component.translatable("updates.lanternring.token"));
		tokenBox.setMaxLength(400);
		// The "saved" note is a hint, not text in the box, so a pasted token replaces it cleanly.
		if (RingUpdater.hasToken()) tokenBox.setHint(Component.literal(SAVED_HINT));
		addRenderableWidget(tokenBox);
		int y = top + 26;
		addRenderableWidget(Button.builder(Component.translatable("updates.lanternring.check"), b -> {
			saveToken();
			RingUpdater.check();
		}).bounds(width / 2 - 150, y, 96, 20).build());
		downloadButton = addRenderableWidget(Button.builder(Component.translatable("updates.lanternring.download"),
				b -> RingUpdater.download()).bounds(width / 2 - 48, y, 96, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("gui.done"), b -> onClose())
				.bounds(width / 2 + 54, y, 96, 20).build());
	}

	/** Saves what's in the box as the new token, if anything was pasted. */
	private void saveToken() {
		String text = tokenBox.getValue().trim();
		if (text.isEmpty()) return;
		RingUpdater.setToken(text);
		tokenBox.setValue("");
		tokenBox.setHint(Component.literal(SAVED_HINT));
	}

	@Override
	public void tick() {
		super.tick();
		downloadButton.active = RingUpdater.state() == RingUpdater.State.AVAILABLE;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, title.getString() + "  (you have v" + LanternRing.version() + ")", width / 2, 10, 0xFF55FF77);
		for (int i = 0; i < HELP.length; i++) {
			graphics.centeredText(font, HELP[i], width / 2, 34 + i * 11, 0xFFAAAAAA);
		}
		String message = RingUpdater.message();
		if (!message.isEmpty()) {
			int y = 34 + HELP.length * 11 + 8 + 56;
			graphics.centeredText(font, font.plainSubstrByWidth(message, width - 20), width / 2, y, 0xFF55FF55);
		}
	}

	@Override
	public void onClose() {
		saveToken();
		minecraft.setScreenAndShow(parent);
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}
}
