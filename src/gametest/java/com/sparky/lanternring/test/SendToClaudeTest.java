package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.client.RingInbox;
import com.sparky.lanternring.client.SendToClaudeScreen;
import java.nio.file.Path;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.world.InteractionHand;

/** Ring Lab > Send to Claude: the panel, the screenshot shrinking, and the no-token error. Nothing is sent. */
public class SendToClaudeTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("time set 6000");
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0)
					.setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring()));
			ctx.waitTicks(40);
			ctx.takeScreenshot("inbox_world");
			ctx.runOnClient(mc -> {
				Path shot = RingInbox.latestScreenshot();
				try {
					List<String> chunks = RingInbox.screenshotChunks(shot);
					int total = chunks.stream().mapToInt(String::length).sum();
					System.out.println("[inbox] latest=" + shot.getFileName() + " chunks=" + chunks.size() + " base64=" + total);
				} catch (Exception e) {
					System.out.println("[inbox] chunk error " + e);
				}
				mc.setScreenAndShow(new SendToClaudeScreen(null));
			});
			ctx.waitTicks(5);
			ctx.takeScreenshot("inbox_panel");
			String result = ctx.computeOnClient(mc -> {
				try {
					return "sent " + RingInbox.send(RingInbox.Action.REDO, "test", false).join();
				} catch (Exception e) {
					return "error " + (e.getCause() != null && e.getCause().getMessage() != null ? e.getCause().getMessage() : e.toString());
				}
			});
			System.out.println("[inbox] no-token send: " + result);
			ctx.runOnClient(mc -> mc.setScreenAndShow(null));
		}
	}
}
