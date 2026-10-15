package com.sparky.lanternring.test;

import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.WhatsNew;
import com.sparky.lanternring.client.LabSettings;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;

/**
 * The What's New book: handed out when a new jar first loads, page 1 shows the version and what's left to try, a power
 * used ticks its entry (and moves it to the back), a Ring Lab pick ticks from the client, and Mark done ticks the rest.
 */
public class WhatsNewTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);

			// Given on joining with a new jar.
			boolean given = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				return p.getInventory().contains(WhatsNew::isBook) && LanternRing.version().equals(WhatsNew.progress(p).bookVersion());
			});
			if (!given) throw new AssertionError("A new jar should hand out the What's New book on joining");
			if (WhatsNew.entries().size() < 30) throw new AssertionError("The What's New list should load, got " + WhatsNew.entries().size());

			// Page 1: the version and the newest untried entry first.
			String first = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				p.getInventory().clearContent();
				p.setItemInHand(InteractionHand.MAIN_HAND, WhatsNew.book(p));
				return pages(p.getMainHandItem()).getFirst();
			});
			if (!first.contains("What's New") || !first.contains(LanternRing.version()) || !first.contains("☐ " + WhatsNew.entries().getFirst().title())) {
				throw new AssertionError("Page 1 should show the version and the newest entry first, got: " + first);
			}
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(15);
			boolean open = ctx.computeOnClient(mc -> mc.screen != null && mc.screen.getClass().getSimpleName().contains("Book"));
			if (!open) throw new AssertionError("Using the book should open it");
			ctx.takeScreenshot("whats_new_page1");
			ctx.runOnClient(mc -> mc.setScreenAndShow(null));

			// A power used ticks its entry: the sonic boom ticks hyper speed (and ground flight).
			boolean ticked = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				WhatsNew.done(p, "flight.boom");
				List<String> pages = pages(p.getMainHandItem());
				boolean back = false;
				for (int i = 1; i < pages.size(); i++) if (pages.get(i).contains("☑ Shift hyper speed")) back = true;
				return WhatsNew.isDone(p, "hyper_speed") && WhatsNew.isDone(p, "ground_flight") && back && !pages.getFirst().contains("☐ Shift hyper speed");
			});
			if (!ticked) throw new AssertionError("The sonic boom should tick Shift hyper speed and move it to the Done pages");

			// A Ring Lab pick ticks from the client.
			ctx.runOnClient(mc -> LabSettings.OPTIONS.stream().filter(o -> o.key().equals("beam_look")).findFirst().orElseThrow()
					.cycle(LabSettings.get(), 1));
			ctx.waitTicks(10);
			boolean lab = world.getServer().computeOnServer(server -> WhatsNew.isDone(player(server), "lasers_836"));
			if (!lab) throw new AssertionError("Picking a pass 836 laser in the Ring Lab should tick Eight test lasers");

			// Mark done, for entries with no trigger.
			world.getServer().runCommand("execute as @p run whatsnew done construct_rays");
			ctx.waitTicks(5);
			boolean marked = world.getServer().computeOnServer(server -> WhatsNew.isDone(player(server), "construct_rays"));
			if (!marked) throw new AssertionError("Mark done should tick the entry");

			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(15);
			ctx.takeScreenshot("whats_new_after_ticks");
			ctx.runOnClient(mc -> mc.setScreenAndShow(null));
		}
	}

	private static List<String> pages(ItemStack book) {
		var content = book.get(DataComponents.WRITTEN_BOOK_CONTENT);
		if (content == null) throw new AssertionError("The book has no pages");
		return content.pages().stream().map(p -> p.raw().getString()).toList();
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
