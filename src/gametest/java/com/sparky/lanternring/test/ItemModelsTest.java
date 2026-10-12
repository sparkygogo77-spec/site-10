package com.sparky.lanternring.test;

import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;

/**
 * Photographs the lantern and rings everywhere the plain item models show them: the hotbar and
 * inventory, the player held in the inventory preview and in third person, placed lanterns,
 * dropped items and item frames.
 */
public class ItemModelsTest implements FabricClientGameTest {
	private static final LabSettings.RingModel[] MODELS = {
			LabSettings.RingModel.FORGED, LabSettings.RingModel.CREST, LabSettings.RingModel.CREST_GOLD, LabSettings.RingModel.BEACON,
			LabSettings.RingModel.EMBLEM};

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			world.getServer().runCommand("item replace entity @a hotbar.1 with lanternring:power_battery");
			world.getServer().runCommand("item replace entity @a hotbar.2 with minecraft:lantern");
			world.getServer().runCommand("item replace entity @a inventory.0 with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a inventory.1 with lanternring:power_battery");
			ctx.waitTicks(60);
			LabSettings lab = LabSettings.get();
			lab.handPose = LabSettings.HandPose.KNUCKLES_IN;

			// The world in front: placed lanterns, dropped items and item frames on a wall.
			world.getServer().runCommand("execute at @p run fill ~-6 ~ ~1 ~6 ~5 ~8 air");
			world.getServer().runCommand("execute at @p run fill ~-6 ~ ~7 ~6 ~4 ~7 minecraft:stone");
			world.getServer().runCommand("execute at @p run setblock ~-1 ~ ~3 lanternring:power_battery");
			world.getServer().runCommand("execute at @p run setblock ~1 ~ ~3 minecraft:lantern");
			world.getServer().runCommand("execute at @p run summon minecraft:item ~-2 ~ ~5 {Item:{id:\"lanternring:power_battery\",count:1},PickupDelay:32767,Age:-32768}");
			world.getServer().runCommand("execute at @p run summon minecraft:item ~2 ~ ~5 {Item:{id:\"lanternring:power_ring\",count:1},PickupDelay:32767,Age:-32768}");
			world.getServer().runCommand("execute at @p run summon minecraft:item_frame ~-1 ~2 ~6 {Facing:2,Item:{id:\"lanternring:power_battery\",count:1}}");
			world.getServer().runCommand("execute at @p run summon minecraft:item_frame ~1 ~2 ~6 {Facing:2,Item:{id:\"lanternring:power_ring\",count:1}}");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 25f);
			ctx.waitTicks(20);
			for (LabSettings.RingModel model : MODELS) {
				lab.ringModel = model;
				ctx.waitTicks(2);
				ctx.takeScreenshot("items_world_" + model.name().toLowerCase());
			}

			lab.ringModel = LabSettings.RingModel.CREST;
			ctx.setScreen(() -> new InventoryScreen(Minecraft.getInstance().player));
			ctx.waitTicks(5);
			for (LabSettings.RingModel model : MODELS) {
				lab.ringModel = model;
				ctx.waitTicks(2);
				ctx.takeScreenshot("items_inventory_" + model.name().toLowerCase());
			}
			ctx.setScreen(() -> null);

			// A lantern in each hand: the main hand shows the right-hand transform.
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_battery");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 0 0");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("items_third_person_front");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(150f, 10f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("items_third_person_side");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
		}
	}
}
