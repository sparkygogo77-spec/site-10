package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

/**
 * The Red Lantern's material takes (Ring Lab "Red Lantern material", tools/red_lantern_materials.py): the held
 * battery in each, M0 today's. Without a shader pack this shows the colours and which part is which; the shine itself
 * needs the patched pack.
 */
public class RedMaterialTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> LabSettings.get().redLantern = LabSettings.RedLantern.NEW);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.RED.lantern());
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, -35f);   // looking up, as in J's screenshot
			ctx.waitTicks(30);
			for (LabSettings.RedMaterial m : LabSettings.RedMaterial.values()) {
				ctx.runOnClient(mc -> LabSettings.get().redMaterial = m);
				ctx.waitTicks(5);
				ctx.takeScreenshot("red_material_" + m.name().toLowerCase(java.util.Locale.ROOT));
			}
			ctx.runOnClient(mc -> LabSettings.get().redMaterial = LabSettings.RedMaterial.M0);
		}
	}
}
