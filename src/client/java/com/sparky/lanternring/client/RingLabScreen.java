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
 *
 * <p>J (2026-10-14, "optimize the ring lab selection methods"): the rows are grouped by power under
 * tabs along the top (All, Ring, Lantern, Powers, Constructs, Landing, Flight; the last one open is
 * remembered), and each row steps both ways with its own back and forward arrows (clicking the
 * row itself still steps forward). Copy report lists every pick, grouped the same way.
 */
public class RingLabScreen extends Screen {
	private static final int ROW = 22;
	private static final int[] RATING_COLORS = {0xAAAAAA, 0x55FF55, 0xFFFF55, 0xFF5555};

	private final Screen parent;
	private final List<Runnable> refreshers = new ArrayList<>();
	/** Room under the options for the preview, Copy and Send to Claude rows and the status line. */
	private static final int BUTTONS_H = 8 + 3 * 24 + 10;

	private Component status = Component.empty();
	private int scroll;
	private int maxScroll;
	private int listLeft;
	private int listTop;
	private int listBottom;
	private int statusY;

	public RingLabScreen(Screen parent) {
		super(Component.translatable("screen.lanternring.lab"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		refreshers.clear();
		LabSettings s = LabSettings.get();
		// The tabs: All, then one per group.
		LabSettings.Group[] groups = LabSettings.Group.values();
		int tabs = groups.length + 1;
		int tabW = Math.min(64, (width - 20 - (tabs - 1) * 2) / tabs);
		int tabX = width / 2 - (tabs * tabW + (tabs - 1) * 2) / 2;
		for (int i = 0; i < tabs; i++) {
			LabSettings.Group g = i == 0 ? null : groups[i - 1];
			Component name = Component.translatable(g == null ? "lab.lanternring.tab.all" : "lab.lanternring.tab." + g.name().toLowerCase());
			Button tab = addRenderableWidget(Button.builder(g == s.labTab ? name.copy().withStyle(ChatFormatting.GREEN, ChatFormatting.UNDERLINE) : name, b -> {
				s.labTab = g;
				scroll = 0;
				s.save();
				rebuildWidgets();
			}).bounds(tabX + i * (tabW + 2), 32, tabW, 20).build());
			tab.active = g != s.labTab;
		}
		List<LabSettings.Option<?>> shown = LabSettings.OPTIONS.stream().filter(o -> s.labTab == null || o.group() == s.labTab).toList();
		int top = 56;
		int count = shown.size();
		// The three button rows below the options stay on screen; the options scroll if they don't fit.
		int fitRows = Math.max(1, (height - BUTTONS_H - top) / ROW);
		// One column if it fits; otherwise two narrower ones side by side.
		boolean twoColumns = count > fitRows && width >= 2 * 234 + 8;
		int perColumn = twoColumns ? (count + 1) / 2 : count;
		int shownRows = Math.min(perColumn, fitRows);
		scroll = Math.clamp(scroll, 0, perColumn - shownRows);
		maxScroll = perColumn - shownRows;
		int choiceW = twoColumns ? 152 : 190;
		int arrowW = 14;
		int rateW = twoColumns ? 46 : 90;
		int columnW = arrowW + 2 + choiceW + 2 + arrowW + 4 + rateW;
		int totalW = twoColumns ? 2 * columnW + 8 : columnW;
		listLeft = width / 2 - totalW / 2;
		listTop = top;
		listBottom = top + shownRows * ROW;

		for (int i = 0; i < count; i++) {
			int row = i % perColumn - scroll;
			if (row < 0 || row >= shownRows) continue;
			LabSettings.Option<?> option = shown.get(i);
			int left = listLeft + (i / perColumn) * (columnW + 8);
			int y = top + row * ROW;
			addRenderableWidget(Button.builder(Component.literal("\u25C0"), b -> {
				option.cycle(s, -1);
				changed();
			}).bounds(left, y, arrowW, 20).build());
			left += arrowW + 2;
			Button choice = addRenderableWidget(Button.builder(Component.empty(), b -> {
				option.cycle(s, 1);
				changed();
			}).bounds(left, y, choiceW, 20).build());
			addRenderableWidget(Button.builder(Component.literal("\u25B6"), b -> {
				option.cycle(s, 1);
				changed();
			}).bounds(left + choiceW + 2, y, arrowW, 20).build());
			left += choiceW + 2 + arrowW;
			Button rate = addRenderableWidget(Button.builder(Component.empty(), b -> {
				String key = option.ratingKey(s);
				LabSettings.Rating[] all = LabSettings.Rating.values();
				s.rate(key, all[(s.rating(key).ordinal() + 1) % all.length]);
				changed();
			}).bounds(left + 4, y, rateW, 20).build());
			refreshers.add(() -> {
				choice.setMessage(name(option, s.labTab != null)
						.append(": ")
						.append(Component.translatable("lab.lanternring." + option.key() + "." + option.current(s).name().toLowerCase())
								.withStyle(ChatFormatting.GREEN)));
				LabSettings.Rating r = s.rating(option.ratingKey(s));
				rate.setMessage(Component.translatable("lab.lanternring.rating." + r.name().toLowerCase())
						.withColor(RATING_COLORS[r.ordinal()]));
			});
		}

		int y = listBottom + 8;
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
		}).bounds(width / 2 - 150, y, 72, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.durations"),
				b -> minecraft.setScreenAndShow(new RingTuningScreen(this))).bounds(width / 2 - 74, y, 72, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.updates"),
				b -> minecraft.setScreenAndShow(new UpdateScreen(this))).bounds(width / 2 + 2, y, 72, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("gui.done"), b -> onClose()).bounds(width / 2 + 78, y, 72, 20).build());
		y += 24;
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.inbox"),
				b -> minecraft.setScreenAndShow(new SendToClaudeScreen(this))).bounds(width / 2 - 75, y, 150, 20).build());
		statusY = Math.min(y + 24, height - 10);
		refreshers.forEach(Runnable::run);
	}

	/**
	 * A row's name. Under a tab its group prefix ("Super jump: landing" in the Super jump tab) is left
	 * off, so more of the picked version shows.
	 */
	private static net.minecraft.network.chat.MutableComponent name(LabSettings.Option<?> option, boolean tabbed) {
		String full = Component.translatable("lab.lanternring." + option.key()).getString();
		int cut = full.lastIndexOf(": ");
		if (!tabbed || cut < 0) return Component.literal(full);
		String rest = full.substring(cut + 2);
		return Component.literal(rest.isEmpty() ? full : Character.toUpperCase(rest.charAt(0)) + rest.substring(1));
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		int next = Math.clamp(scroll - (int) Math.signum(scrollY), 0, maxScroll);
		if (next == scroll) return super.mouseScrolled(mouseX, mouseY, scrollX, scrollY);
		scroll = next;
		rebuildWidgets();
		return true;
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
		graphics.centeredText(font, status.getString(), width / 2, statusY, 0xFF55FF55);
		if (scroll > 0) graphics.text(font, "\u25B2", listLeft - 10, listTop + 6, 0xFFAAAAAA);
		if (scroll < maxScroll) graphics.text(font, "\u25BC", listLeft - 10, listBottom - 16, 0xFFAAAAAA);
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
