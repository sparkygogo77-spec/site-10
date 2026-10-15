package com.sparky.lanternring;

import com.google.gson.Gson;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.sparky.lanternring.net.WhatsNewPayload;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.Filterable;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.WrittenBookContent;

/**
 * The What's New book (J, 2026-10-15: "a checklist of what's new and untested as a book that checks them once I've done
 * them and how to get to them"). The entries live in lanternring/whats_new.json; each has the steps to reach it and the
 * trigger ids that tick it. Feature code calls {@link #done(Player, String)} when the player actually does the thing (the
 * client sends its own ones, like Ring Lab picks, as a {@link WhatsNewPayload}). What each player has done is saved on
 * the player, so it survives restarts and new jars. The book is a written book that is rewritten every time it is opened:
 * untried entries first, newest first, then the done ones at the back. A new jar hands out a fresh copy on joining.
 */
public final class WhatsNew {
	/** The marker in a What's New book's custom data. */
	private static final String MARK = "lanternring_whats_new";
	/** Book pages are 114 px wide and 14 lines tall; keep a little slack since widths here are estimated. */
	private static final int PAGE_WIDTH = 110;
	private static final int PAGE_LINES = 13;

	public record Entry(String id, String date, String pass, String title, List<String> steps, List<String> triggers) {
		boolean manual() {
			return triggers == null || triggers.isEmpty();
		}

		boolean matches(String trigger) {
			if (triggers == null) return false;
			for (String t : triggers) {
				if (t.endsWith("*") ? trigger.startsWith(t.substring(0, t.length() - 1)) : t.equals(trigger)) return true;
			}
			return false;
		}
	}

	private record Data(List<Entry> entries) {
	}

	/** Which entries a player has done, and the jar whose book they were last given. */
	public record Progress(List<String> done, String bookVersion) {
		public static final Codec<Progress> CODEC = RecordCodecBuilder.create(i -> i.group(
				Codec.STRING.listOf().fieldOf("done").forGetter(Progress::done),
				Codec.STRING.optionalFieldOf("book", "").forGetter(Progress::bookVersion)
		).apply(i, Progress::new));
		static final Progress EMPTY = new Progress(List.of(), "");
	}

	public static final AttachmentType<Progress> PROGRESS = AttachmentRegistry.create(LanternRing.id("whats_new"),
			b -> b.persistent(Progress.CODEC).copyOnDeath());

	private static List<Entry> entries;

	private WhatsNew() {
	}

	/** Every entry, newest first (the file's order within a date). */
	public static List<Entry> entries() {
		if (entries == null) {
			List<Entry> list = new ArrayList<>();
			try (InputStream in = WhatsNew.class.getResourceAsStream("/lanternring/whats_new.json")) {
				if (in != null) list.addAll(new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), Data.class).entries());
			} catch (Exception e) {
				LanternRing.LOGGER.warn("Couldn't read the What's New list", e);
			}
			// Stable sort: newest date first, the file's order within a date.
			list.sort(Comparator.comparing(Entry::date).reversed());
			entries = List.copyOf(list);
		}
		return entries;
	}

	static void register() {
		PayloadTypeRegistry.serverboundPlay().register(WhatsNewPayload.TYPE, WhatsNewPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(WhatsNewPayload.TYPE, (payload, context) -> {
			String what = payload.trigger();
			if (what.length() > 120) return;
			if (what.equals(WhatsNewPayload.GIVE_BOOK)) give(context.player());
			else done(context.player(), what);
		});
		// A new jar hands out its book once.
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
			ServerPlayer player = handler.getPlayer();
			if (!LanternRing.version().equals(progress(player).bookVersion())) give(player);
		});
		// Rewrite the book just before it opens, so it shows today's ticks.
		UseItemCallback.EVENT.register((player, level, hand) -> {
			ItemStack stack = player.getItemInHand(hand);
			if (player instanceof ServerPlayer sp && isBook(stack)) {
				write(sp, stack);
				sp.containerMenu.broadcastChanges();
			}
			return InteractionResult.PASS;
		});
		// The book's Mark done / Undo links.
		CommandRegistrationCallback.EVENT.register((dispatcher, registries, environment) -> dispatcher.register(Commands.literal("whatsnew")
				.executes(c -> {
					give(c.getSource().getPlayerOrException());
					return 1;
				})
				.then(Commands.literal("done").then(Commands.argument("id", StringArgumentType.word()).executes(c -> {
					mark(c.getSource().getPlayerOrException(), StringArgumentType.getString(c, "id"), true);
					return 1;
				})))
				.then(Commands.literal("undo").then(Commands.argument("id", StringArgumentType.word()).executes(c -> {
					mark(c.getSource().getPlayerOrException(), StringArgumentType.getString(c, "id"), false);
					return 1;
				})))));
	}

	public static Progress progress(Player player) {
		Progress p = player.getAttached(PROGRESS);
		return p == null ? Progress.EMPTY : p;
	}

	public static boolean isDone(Player player, String id) {
		return progress(player).done().contains(id);
	}

	/**
	 * The player just did something: ticks every entry whose trigger it is. Safe to call from either side and as often as
	 * it happens; only the server records it, and only the first time says so.
	 */
	public static void done(net.minecraft.world.entity.Entity player, String trigger) {
		if (!(player instanceof ServerPlayer sp) || sp.hasDisconnected()) return;
		Set<String> done = new LinkedHashSet<>(progress(sp).done());
		List<Entry> ticked = new ArrayList<>();
		for (Entry e : entries()) {
			if (e.matches(trigger) && done.add(e.id())) ticked.add(e);
		}
		if (ticked.isEmpty()) return;
		save(sp, done);
		for (Entry e : ticked) {
			sp.sendSystemMessage(Component.literal("☑ What's New: ").withStyle(ChatFormatting.GREEN)
					.append(Component.literal(e.title()).withStyle(ChatFormatting.WHITE))
					.append(e.pass().isEmpty() ? Component.empty() : Component.literal("  " + e.pass()).withStyle(ChatFormatting.DARK_GRAY)));
		}
		refreshBooks(sp);
	}

	/** Mark done (or undo) from the book. */
	static void mark(ServerPlayer player, String id, boolean on) {
		Entry entry = entries().stream().filter(e -> e.id().equals(id)).findFirst().orElse(null);
		if (entry == null) return;
		Set<String> done = new LinkedHashSet<>(progress(player).done());
		if (on ? !done.add(id) : !done.remove(id)) return;
		save(player, done);
		player.sendSystemMessage(Component.literal((on ? "☑ " : "☐ ") + "What's New: ").withStyle(on ? ChatFormatting.GREEN : ChatFormatting.GRAY)
				.append(Component.literal(entry.title()).withStyle(ChatFormatting.WHITE)));
		done(player, "book.mark_done");
		refreshBooks(player);
		// Open the book again so the click shows straight away.
		for (InteractionHand hand : InteractionHand.values()) {
			if (isBook(player.getItemInHand(hand))) {
				player.openItemGui(player.getItemInHand(hand), hand);
				break;
			}
		}
	}

	private static void save(ServerPlayer player, Set<String> done) {
		player.setAttached(PROGRESS, new Progress(List.copyOf(done), progress(player).bookVersion()));
	}

	public static boolean isBook(ItemStack stack) {
		if (!stack.is(Items.WRITTEN_BOOK)) return false;
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		return data != null && data.copyTag().contains(MARK);
	}

	/** A fresh book for this player. */
	public static ItemStack book(ServerPlayer player) {
		ItemStack stack = new ItemStack(Items.WRITTEN_BOOK);
		CompoundTag tag = new CompoundTag();
		tag.putBoolean(MARK, true);
		stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
		stack.set(DataComponents.ITEM_MODEL, LanternRing.id("whats_new_book"));
		stack.set(DataComponents.CUSTOM_NAME, Component.literal("What's New").withStyle(s -> s.withItalic(false).withColor(ChatFormatting.GREEN)));
		write(player, stack);
		return stack;
	}

	/** Gives a new book, taking back any old copies so there's only ever one. */
	public static void give(ServerPlayer player) {
		var inv = player.getInventory();
		for (int i = 0; i < inv.getContainerSize(); i++) {
			if (isBook(inv.getItem(i))) inv.setItem(i, ItemStack.EMPTY);
		}
		ItemStack book = book(player);
		if (!inv.add(book)) player.drop(book, false);
		player.setAttached(PROGRESS, new Progress(progress(player).done(), LanternRing.version()));
		player.sendSystemMessage(Component.literal("📖 What's New for v" + LanternRing.version() + " is in your inventory").withStyle(ChatFormatting.GREEN));
	}

	private static void refreshBooks(ServerPlayer player) {
		var inv = player.getInventory();
		for (int i = 0; i < inv.getContainerSize(); i++) {
			if (isBook(inv.getItem(i))) write(player, inv.getItem(i));
		}
	}

	/** Writes the book's pages for this player's progress. */
	public static void write(ServerPlayer player, ItemStack stack) {
		stack.set(DataComponents.WRITTEN_BOOK_CONTENT, new WrittenBookContent(Filterable.passThrough("What's New"), "Lantern Ring", 0,
				pages(progress(player).done()).stream().map(Filterable::passThrough).toList(), true));
	}

	/** The book's pages: contents, then untried entries newest first, then the done ones. */
	public static List<Component> pages(List<String> doneIds) {
		Set<String> done = Set.copyOf(doneIds);
		List<Entry> todo = entries().stream().filter(e -> !done.contains(e.id())).toList();
		List<Entry> finished = entries().stream().filter(e -> done.contains(e.id())).toList();
		List<List<List<Component>>> todoPages = todo.stream().map(e -> entryPages(e, false)).toList();
		List<List<List<Component>>> donePages = finished.stream().map(e -> entryPages(e, true)).toList();

		// The contents' links need its own length; guess one page and redo until it agrees.
		List<List<Component>> contents = contents(todo, finished, todoPages, donePages, 1);
		for (int tries = 0; tries < 4; tries++) {
			List<List<Component>> again = contents(todo, finished, todoPages, donePages, contents.size());
			if (again.size() == contents.size()) {
				contents = again;
				break;
			}
			contents = again;
		}
		List<List<Component>> out = new ArrayList<>(contents);
		for (List<List<Component>> e : todoPages) out.addAll(e);
		if (!finished.isEmpty()) {
			out.add(List.of(Component.literal("Done").withStyle(ChatFormatting.DARK_GREEN, ChatFormatting.BOLD), Component.empty(),
					Component.literal(finished.size() + " tried. Undo on a page puts it back in front.").withStyle(ChatFormatting.DARK_GRAY)));
			for (List<List<Component>> e : donePages) out.addAll(e);
		}
		return out.stream().limit(WrittenBookContent.MAX_PAGES).map(WhatsNew::join).toList();
	}

	/** Page 1 on: the version, the counts and a link to every entry, assuming the contents take {@code length} pages. */
	private static List<List<Component>> contents(List<Entry> todo, List<Entry> finished, List<List<List<Component>>> todoPages,
			List<List<List<Component>>> donePages, int length) {
		List<Component> lines = new ArrayList<>();
		lines.add(Component.literal("What's New").withStyle(ChatFormatting.DARK_GREEN, ChatFormatting.BOLD));
		lines.add(Component.literal("v" + LanternRing.version()).withStyle(ChatFormatting.DARK_GRAY));
		lines.add(Component.literal(todo.size() + " to try · " + finished.size() + " done").withStyle(ChatFormatting.BLACK));
		lines.add(Component.empty());
		// Book pages count from 1.
		int page = length + 1;
		for (int i = 0; i < todo.size(); i++) {
			lines.addAll(link("☐ ", todo.get(i).title(), page, ChatFormatting.BLACK));
			page += todoPages.get(i).size();
		}
		if (!finished.isEmpty()) {
			int doneStart = page;
			lines.add(Component.empty());
			lines.add(Component.literal("Done").withStyle(s -> s.withBold(true).withColor(ChatFormatting.DARK_GREEN)
					.withClickEvent(new ClickEvent.ChangePage(doneStart))));
			page++;
			for (int i = 0; i < finished.size(); i++) {
				// One line each so the contents stays short.
				lines.add(link("☑ ", cut(finished.get(i).title(), PAGE_WIDTH - 12), page, ChatFormatting.DARK_GRAY).getFirst());
				page += donePages.get(i).size();
			}
		}
		List<List<Component>> pages = new ArrayList<>();
		paginate(lines, pages);
		return pages;
	}

	/** One entry: box and title, pass label, date, how to get there, then Mark done / Undo. */
	private static List<List<Component>> entryPages(Entry e, boolean isDone) {
		List<Component> lines = new ArrayList<>();
		for (String l : wrap((isDone ? "☑ " : "☐ ") + e.title(), true)) {
			lines.add(Component.literal(l).withStyle(isDone ? ChatFormatting.DARK_GREEN : ChatFormatting.BLACK, ChatFormatting.BOLD));
		}
		if (!e.pass().isEmpty()) for (String l : wrap(e.pass(), false)) lines.add(Component.literal(l).withStyle(ChatFormatting.DARK_GREEN));
		lines.add(Component.literal(e.date().substring(5) + (isDone ? " · done" : e.manual() ? " · tick it yourself" : " · ticks itself"))
				.withStyle(ChatFormatting.DARK_GRAY));
		lines.add(Component.literal("How to get there:").withStyle(ChatFormatting.DARK_BLUE));
		for (String step : e.steps()) {
			List<String> wrapped = wrap("• " + step, false);
			for (int i = 0; i < wrapped.size(); i++) lines.add(Component.literal((i == 0 ? "" : "  ") + wrapped.get(i)).withStyle(ChatFormatting.BLACK));
		}
		String command = "/whatsnew " + (isDone ? "undo " : "done ") + e.id();
		lines.add(Component.literal(isDone ? "[Undo]" : "[Mark done]").withStyle(s -> s.withColor(isDone ? ChatFormatting.DARK_GRAY : ChatFormatting.BLUE)
				.withUnderlined(true).withClickEvent(new ClickEvent.RunCommand(command))
				.withHoverEvent(new HoverEvent.ShowText(Component.literal(isDone ? "Put it back with the untried ones" : "Tick it now")))));
		List<List<Component>> pages = new ArrayList<>();
		paginate(lines, pages);
		return pages;
	}

	private static List<Component> link(String box, String title, int page, ChatFormatting colour) {
		List<Component> out = new ArrayList<>();
		for (String l : wrap(box + title, false)) {
			out.add(Component.literal(l).withStyle(s -> s.withColor(colour).withClickEvent(new ClickEvent.ChangePage(page))
					.withHoverEvent(new HoverEvent.ShowText(Component.literal("Page " + page)))));
		}
		return out;
	}

	private static void paginate(List<Component> lines, List<List<Component>> pages) {
		List<Component> page = new ArrayList<>();
		for (Component line : lines) {
			if (page.size() == PAGE_LINES) {
				pages.add(page);
				page = new ArrayList<>();
			}
			page.add(line);
		}
		if (!page.isEmpty() || pages.isEmpty()) pages.add(page);
	}

	private static Component join(List<Component> lines) {
		MutableComponent page = Component.empty();
		for (int i = 0; i < lines.size(); i++) {
			if (i > 0) page.append("\n");
			page.append(lines.get(i));
		}
		return page;
	}

	/** Word-wraps to the page width, using the default font's widths. */
	static List<String> wrap(String text, boolean bold) {
		List<String> lines = new ArrayList<>();
		StringBuilder line = new StringBuilder();
		for (String word : text.split(" ")) {
			String next = line.isEmpty() ? word : line + " " + word;
			if (width(next, bold) <= PAGE_WIDTH || line.isEmpty()) {
				line.setLength(0);
				line.append(next);
			} else {
				lines.add(line.toString());
				line.setLength(0);
				line.append(word);
			}
		}
		if (!line.isEmpty()) lines.add(line.toString());
		return lines;
	}

	private static String cut(String text, int max) {
		if (width(text, false) <= max) return text;
		String t = text;
		while (!t.isEmpty() && width(t + "…", false) > max) t = t.substring(0, t.length() - 1);
		return t.strip() + "…";
	}

	static int width(String text, boolean bold) {
		int w = 0;
		for (int i = 0; i < text.length(); i++) w += width(text.charAt(i)) + (bold ? 1 : 0);
		return w;
	}

	/** Advance of one character in the default font, spacing included (wide guesses for symbols). */
	private static int width(char c) {
		if ("i.,:;|!'".indexOf(c) >= 0 || c == '·') return 2;
		if (c == 'l' || c == '`') return 3;
		if ("It[] ".indexOf(c) >= 0) return 4;
		if ("fk<>\"()*{}".indexOf(c) >= 0 || c == '°') return 5;
		if (c == '@' || c == '~') return 7;
		if (c < 128) return 6;
		return 9;
	}
}
