package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.CharacterEvent;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import com.mojang.blaze3d.platform.InputConstants;

/**
 * Ring Lab: pick the version (take) of each feature, rate it Keep / Improve / Drop, and copy a report of your picks.
 *
 * <p>J (2026-10-14, "fix up ring lab too, the system should have been worked on to make the options easier to navigate"):
 * <ul>
 * <li>category tabs along the top (Movement, Flight, Combat, Beams, Constructs, Ring, Lantern, Corps, Effects, Updates);
 * <li>one row per feature, stepped with ◀ value ▶, the value naming its take code and pass;
 * <li>J's picks starred (★), with "Reset tab" and "Reset all" back to them;
 * <li>a search box: typing filters the rows across every tab;
 * <li>keys that work on a 60% keyboard: Tab / Shift+Tab change tab, Up / Down pick a row, Left / Right step its value,
 * Enter previews where there is a preview (Ctrl + W A S D do the same as the arrows), Esc clears the search, then closes;
 * <li>superseded takes hidden unless "Old takes" is on;
 * <li>the last tab and row are remembered.
 * </ul>
 */
public class RingLabScreen extends Screen {
	private static final int ROW = 21;
	private static final int[] RATING_COLORS = {0xAAAAAA, 0x55FF55, 0xFFFF55, 0xFF5555};
	private static final int TOP = 54;
	/** Room under the rows for the two button rows and the status line. */
	private static final int BOTTOM_H = 2 * 22 + 12;

	private final Screen parent;
	private final List<Runnable> refreshers = new ArrayList<>();
	private EditBox search;
	private String query = "";
	private List<LabSettings.Option<?>> rows = List.of();
	private Component status = Component.empty();
	private int scroll;
	private int shownRows;
	private int listLeft;
	private int listWidth;
	private int nameWidth;

	public RingLabScreen(Screen parent) {
		super(Component.translatable("screen.lanternring.lab"));
		this.parent = parent;
		WhatsNewClient.tell("lab.opened");
	}

	private static LabSettings.Group tab(LabSettings s) {
		return s.labTab == null ? LabSettings.Group.values()[0] : s.labTab;
	}

	private boolean searching() {
		return !query.isBlank();
	}

	@Override
	protected void init() {
		refreshers.clear();
		LabSettings s = LabSettings.get();
		LabSettings.Group current = tab(s);

		// The search box: always takes typing, so letters never move the selection.
		search = new EditBox(font, width / 2 - 110, 16, 220, 14, Component.translatable("lab.lanternring.search"));
		search.setHint(Component.translatable("lab.lanternring.search.hint").withStyle(EditBox.SEARCH_HINT_STYLE));
		search.setMaxLength(40);
		search.setValue(query);
		search.setResponder(text -> {
			if (text.equals(query)) return;
			query = text;
			scroll = 0;
			if (searching()) s.labRow = 0;
			rebuildWidgets();
		});
		addRenderableWidget(search);
		setInitialFocus(search);

		// The tabs.
		LabSettings.Group[] groups = LabSettings.Group.values();
		// Each tab as wide as its name, shrunk together if the screen is narrow.
		int gap = 2;
		int[] tabW = new int[groups.length];
		int total = (groups.length - 1) * gap;
		for (int i = 0; i < groups.length; i++) {
			tabW[i] = font.width(Component.translatable("lab.lanternring.tab." + groups[i].name().toLowerCase())) + 12;
			total += tabW[i];
		}
		float fit = Math.min(1f, (width - 8f) / total);
		int tabX = width / 2 - Math.round(total * fit) / 2;
		for (int i = 0; i < groups.length; i++) {
			LabSettings.Group g = groups[i];
			Component name = Component.translatable("lab.lanternring.tab." + g.name().toLowerCase());
			boolean on = !searching() && g == current;
			int w = Math.round(tabW[i] * fit);
			Button tab = addRenderableWidget(Button.builder(on ? name.copy().withStyle(ChatFormatting.GREEN, ChatFormatting.UNDERLINE) : name,
					b -> switchTab(g)).bounds(tabX, 34, w, 16).build());
			tab.active = !on;
			tabX += w + Math.round(gap * fit);
		}

		rows = searching() ? s.search(query) : LabSettings.tab(current);
		s.labRow = rows.isEmpty() ? 0 : Math.clamp(s.labRow, 0, rows.size() - 1);
		shownRows = Math.max(1, (height - BOTTOM_H - TOP) / ROW);
		scroll = Math.clamp(scroll, 0, Math.max(0, rows.size() - shownRows));
		if (s.labRow < scroll) scroll = s.labRow;
		if (s.labRow >= scroll + shownRows) scroll = s.labRow - shownRows + 1;

		int arrowW = 14;
		int rateW = 46;
		int noteW = 16;
		listWidth = Math.min(width - 16, 460);
		nameWidth = Math.min(180, listWidth - (arrowW * 2 + 4 + 140 + 4 + rateW + 2 + noteW) - 6);
		int valueW = listWidth - nameWidth - 6 - arrowW * 2 - 4 - 4 - rateW - 2 - noteW;
		listLeft = width / 2 - listWidth / 2;

		if (current == LabSettings.Group.UPDATES && !searching()) {
			int y = TOP + 6;
			addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.updates"),
					b -> minecraft.setScreenAndShow(new UpdateScreen(this))).bounds(width / 2 - 75, y, 150, 20).build());
			addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.durations"),
					b -> minecraft.setScreenAndShow(new RingTuningScreen(this))).bounds(width / 2 - 75, y + 24, 150, 20).build());
			addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.inbox"),
					b -> minecraft.setScreenAndShow(new SendToClaudeScreen(this))).bounds(width / 2 - 75, y + 48, 150, 20).build());
			addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.profile.save"), b -> {
				WhatsNewClient.tell("lab.profile");
				status = s.saveProfile() ? Component.translatable("lab.lanternring.profile.saved").withStyle(ChatFormatting.GREEN)
						: Component.translatable("lab.lanternring.profile.failed").withStyle(ChatFormatting.RED);
			}).bounds(width / 2 - 75, y + 72, 150, 20).build());
			addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.profile.load"), b -> {
				String from = s.loadProfile();
				status = from != null ? Component.translatable("lab.lanternring.profile.loaded", from).withStyle(ChatFormatting.GREEN)
						: Component.translatable("lab.lanternring.profile.failed").withStyle(ChatFormatting.RED);
				changed();
			}).bounds(width / 2 - 75, y + 96, 150, 20).build());
			addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.whats_new"), b -> {
				WhatsNewClient.giveBook();
				status = Component.translatable("lab.lanternring.whats_new.given").withStyle(ChatFormatting.GREEN);
			}).bounds(width / 2 - 75, y + 120, 150, 20).build());
		}

		for (int i = scroll; i < Math.min(rows.size(), scroll + shownRows); i++) {
			LabSettings.Option<?> option = rows.get(i);
			int index = i;
			int y = TOP + (i - scroll) * ROW;
			int x = listLeft + nameWidth + 6;
			addRenderableWidget(Button.builder(Component.literal("◀"), b -> step(index, -1)).bounds(x, y, arrowW, 20).build());
			x += arrowW + 2;
			Button choice = addRenderableWidget(Button.builder(Component.empty(), b -> step(index, 1)).bounds(x, y, valueW, 20).build());
			x += valueW + 2;
			addRenderableWidget(Button.builder(Component.literal("▶"), b -> step(index, 1)).bounds(x, y, arrowW, 20).build());
			x += arrowW + 4;
			Button rate = addRenderableWidget(Button.builder(Component.empty(), b -> {
				s.labRow = index;
				String key = option.ratingKey(s);
				LabSettings.Rating[] all = LabSettings.Rating.values();
				s.rate(key, all[(s.rating(key).ordinal() + 1) % all.length]);
				changed();
			}).bounds(x, y, rateW, 20).build());
			x += rateW + 2;
			Button note = addRenderableWidget(Button.builder(Component.literal("✎"), b -> {
				s.labRow = index;
				minecraft.setScreenAndShow(new RowNoteScreen(this, option));
			}).bounds(x, y, noteW, 20).build());
			refreshers.add(() -> {
				Enum<?> value = option.current(s);
				boolean pick = option.isPick(value);
				net.minecraft.network.chat.MutableComponent text = Component.literal(option.valueLabel(value))
						.withStyle(option.old().contains(value) ? ChatFormatting.GRAY : ChatFormatting.GREEN);
				if (pick) text.append(Component.literal(" ★").withStyle(ChatFormatting.GOLD));
				choice.setMessage(text);
				LabSettings.Rating r = s.rating(option.ratingKey(s));
				rate.setMessage(Component.translatable("lab.lanternring.rating." + r.name().toLowerCase()).withColor(RATING_COLORS[r.ordinal()]));
				boolean hasNote = !s.note(option.ratingKey(s)).isEmpty();
				note.setMessage(Component.literal("✎").withStyle(hasNote ? ChatFormatting.YELLOW : ChatFormatting.GRAY));
				note.setTooltip(net.minecraft.client.gui.components.Tooltip.create(hasNote ? Component.literal(s.note(option.ratingKey(s)))
						: Component.translatable("lab.lanternring.note.add")));
			});
		}

		// Bottom: resets, old takes, report, done; then previews and the other menus.
		int y = height - BOTTOM_H + 2;
		int w = Math.min(80, (width - 16 - 4 * 4) / 5);
		int x = width / 2 - (w * 5 + 16) / 2;
		addRenderableWidget(Button.builder(Component.translatable(searching() ? "lab.lanternring.reset.shown" : "lab.lanternring.reset.tab"), b -> {
			s.resetToPicks(rows);
			status = Component.translatable("lab.lanternring.reset.done").withStyle(ChatFormatting.GOLD);
			changed();
		}).bounds(x, y, w, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.reset.all"), b -> {
			s.resetToPicks(LabSettings.OPTIONS);
			status = Component.translatable("lab.lanternring.reset.done").withStyle(ChatFormatting.GOLD);
			changed();
		}).bounds(x + (w + 4), y, w, 20).build());
		addRenderableWidget(Button.builder(Component.translatable(s.showOld ? "lab.lanternring.old.on" : "lab.lanternring.old.off"), b -> {
			s.showOld = !s.showOld;
			s.save();
			rebuildWidgets();
		}).bounds(x + 2 * (w + 4), y, w, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.copy"), b -> {
			minecraft.keyboardHandler.setClipboard(s.report());
			WhatsNewClient.tell("lab.report");
			status = Component.translatable("lab.lanternring.copied").withStyle(ChatFormatting.GREEN);
		}).bounds(x + 3 * (w + 4), y, w, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("gui.done"), b -> onClose()).bounds(x + 4 * (w + 4), y, w, 20).build());

		y += 22;
		String[] previews = {"blast", "use", "push", "charge"};
		int pw = Math.min(70, (width - 16 - 5 * 4) / 6);
		x = width / 2 - (pw * 6 + 20) / 2;
		for (int i = 0; i < previews.length; i++) {
			String what = previews[i];
			addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.preview." + what), b -> preview(what))
					.bounds(x + i * (pw + 4), y, pw, 20).build());
		}
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.durations"),
				b -> minecraft.setScreenAndShow(new RingTuningScreen(this))).bounds(x + 4 * (pw + 4), y, pw, 20).build());
		addRenderableWidget(Button.builder(Component.translatable("lab.lanternring.inbox"),
				b -> minecraft.setScreenAndShow(new SendToClaudeScreen(this))).bounds(x + 5 * (pw + 4), y, pw, 20).build());
		refreshers.forEach(Runnable::run);
	}

	private void switchTab(LabSettings.Group g) {
		LabSettings s = LabSettings.get();
		if (g != s.labTab) s.labRow = 0;
		s.labTab = g;
		query = "";
		scroll = 0;
		s.save();
		rebuildWidgets();
	}

	private void step(int index, int dir) {
		LabSettings s = LabSettings.get();
		if (index < 0 || index >= rows.size()) return;
		s.labRow = index;
		rows.get(index).cycle(s, dir);
		changed();
	}

	private void moveRow(int dir) {
		LabSettings s = LabSettings.get();
		if (rows.isEmpty()) return;
		s.labRow = Math.floorMod(s.labRow + dir, rows.size());
		if (s.labRow < scroll || s.labRow >= scroll + shownRows) rebuildWidgets();
	}

	@Override
	public boolean keyPressed(KeyEvent event) {
		LabSettings s = LabSettings.get();
		int key = event.key();
		boolean ctrl = event.hasControlDown();
		if (key == InputConstants.KEY_TAB) {
			LabSettings.Group[] groups = LabSettings.Group.values();
			LabSettings.Group next = groups[Math.floorMod(tab(s).ordinal() + (event.hasShiftDown() ? -1 : 1), groups.length)];
			// While searching, Tab first leaves the search for the tab you were on.
			switchTab(searching() ? tab(s) : next);
			return true;
		}
		if (key == InputConstants.KEY_UP || ctrl && key == InputConstants.KEY_W) {
			moveRow(-1);
			return true;
		}
		if (key == InputConstants.KEY_DOWN || ctrl && key == InputConstants.KEY_S) {
			moveRow(1);
			return true;
		}
		if (key == InputConstants.KEY_LEFT || ctrl && key == InputConstants.KEY_A) {
			step(s.labRow, -1);
			return true;
		}
		if (key == InputConstants.KEY_RIGHT || ctrl && key == InputConstants.KEY_D) {
			step(s.labRow, 1);
			return true;
		}
		if (key == InputConstants.KEY_RETURN || key == InputConstants.KEY_NUMPADENTER) {
			if (s.labRow < rows.size() && rows.get(s.labRow).preview() != null) preview(rows.get(s.labRow).preview());
			else status = Component.translatable("lab.lanternring.preview.none").withStyle(ChatFormatting.GRAY);
			return true;
		}
		if (key == InputConstants.KEY_ESCAPE && searching()) {
			search.setValue("");
			return true;
		}
		if (key == InputConstants.KEY_ESCAPE) {
			onClose();
			return true;
		}
		// Everything else (Backspace, Ctrl+A, paste...) edits the search.
		return search.keyPressed(event) || super.keyPressed(event);
	}

	@Override
	public boolean charTyped(CharacterEvent event) {
		if (!search.isFocused()) search.setFocused(true);
		return search.charTyped(event);
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		boolean handled = super.mouseClicked(event, doubleClick);
		// Clicking anywhere on a row picks it.
		int row = (int) Math.floor((event.y() - TOP) / ROW);
		if (event.y() >= TOP && row >= 0 && row < shownRows && scroll + row < rows.size() && event.x() >= listLeft && event.x() <= listLeft + listWidth) {
			LabSettings.get().labRow = scroll + row;
		}
		// Keep typing going to the search box.
		setFocused(search);
		search.setFocused(true);
		return handled;
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		int next = Math.clamp(scroll - (int) Math.signum(scrollY), 0, Math.max(0, rows.size() - shownRows));
		if (next == scroll) return super.mouseScrolled(mouseX, mouseY, scrollX, scrollY);
		scroll = next;
		LabSettings s = LabSettings.get();
		s.labRow = Math.clamp(s.labRow, scroll, scroll + shownRows - 1);
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
		LabSettings s = LabSettings.get();
		// The picked row's highlight goes under its buttons.
		int sel = s.labRow - scroll;
		if (!rows.isEmpty() && sel >= 0 && sel < shownRows) {
			int y = TOP + sel * ROW;
			graphics.fill(listLeft - 3, y - 1, listLeft + listWidth + 3, y + 21, 0x5533FF66);
			graphics.outline(listLeft - 3, y - 1, listWidth + 6, 22, 0xFF55FF77);
		}
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, title.getString() + "  v" + LanternRing.version(), width / 2, 5, 0xFF55FF77);
		for (int i = scroll; i < Math.min(rows.size(), scroll + shownRows); i++) {
			LabSettings.Option<?> option = rows.get(i);
			String name = option.label();
			if (searching()) {
				name = Component.translatable("lab.lanternring.tab." + option.group().name().toLowerCase()).getString() + " · " + name;
			}
			int y = TOP + (i - scroll) * ROW + 6;
			if (option.newPickAvailable(s)) {
				// J set this row himself, so a newer ★ pick is only offered, never switched in.
				String badge = "★ new";
				int bw = font.width(badge);
				graphics.text(font, badge, listLeft + nameWidth - bw, y, 0xFFFFAA00);
				name = font.plainSubstrByWidth(name, nameWidth - bw - 3);
			} else {
				name = font.plainSubstrByWidth(name, nameWidth);
			}
			graphics.text(font, name, listLeft, y, i == s.labRow ? 0xFFFFFFFF : 0xFFCCCCCC);
		}
		if (rows.isEmpty() && !(tab(s) == LabSettings.Group.UPDATES && !searching())) {
			graphics.centeredText(font, Component.translatable(searching() ? "lab.lanternring.search.none" : "lab.lanternring.tab.empty").getString(),
					width / 2, TOP + 8, 0xFFAAAAAA);
		}
		if (scroll > 0) graphics.text(font, "▲", listLeft - 12, TOP + 6, 0xFFAAAAAA);
		if (scroll + shownRows < rows.size()) graphics.text(font, "▼", listLeft - 12, TOP + (shownRows - 1) * ROW + 6, 0xFFAAAAAA);
		int hintY = height - 10;
		graphics.centeredText(font, status.getString().isEmpty() ? Component.translatable("lab.lanternring.hint").getString() : status.getString(),
				width / 2, hintY, status.getString().isEmpty() ? 0xFF888888 : 0xFF55FF55);
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
