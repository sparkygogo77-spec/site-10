package com.sparky.lanternring.test;

import com.sparky.lanternring.Avarice;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** The Orange Lantern ring: ring and lantern in hand, Hoard pulling in loot, Steal, and Avarice copies. */
public class OrangeLanternTest implements FabricClientGameTest {
	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.ORANGE.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.ORANGE.lantern());
				BlockPos o = p.blockPosition().above(10);
				origin[0] = o;
				var level = p.level();
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-25, -3, -25), o.offset(25, 12, 25))) {
					level.setBlock(pos, pos.getY() < o.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			world.getServer().runCommand("kill @e[type=!player]");
			ctx.getInput().lookAt(0f, 20f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("orange_ring_and_lantern");

			// Hoard: loot scattered around the field.
			String[] loot = {"diamond", "gold_ingot", "emerald", "iron_ingot", "apple", "bone", "string", "rotten_flesh"};
			for (int i = 0; i < 16; i++) {
				double a = i * Math.PI / 8, r = 6 + (i % 4) * 3;
				world.getServer().runCommand("summon item " + (origin[0].getX() + Math.sin(a) * r) + " " + (origin[0].getY() + 1) + " "
						+ (origin[0].getZ() + Math.cos(a) * r) + " {Item:{id:\"minecraft:" + loot[i % loot.length] + "\",count:8}}");
			}
			world.getServer().runCommand("summon experience_orb " + origin[0].getX() + " " + (origin[0].getY() + 1) + " " + (origin[0].getZ() + 10) + " {Value:20}");
			ctx.waitTicks(20);
			ctx.takeScreenshot("orange_hoard_before");
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.MODE, RingMode.HOARD.ordinal()));
			ctx.waitTicks(5);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(12);
			ctx.takeScreenshot("orange_hoard_pulling");
			ctx.waitTicks(30);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				int left = p.level().getEntitiesOfClass(ItemEntity.class, new AABB(origin[0]).inflate(30)).size();
				System.out.println("[orange] after hoard: items left on ground=" + left + " charge=" + p.getMainHandItem().get(ModComponents.CHARGE));
			});
			ctx.takeScreenshot("orange_hoard_done");

			// Steal: a zombie with a sword and armour in front of us.
			world.getServer().runCommand("summon zombie " + origin[0].getX() + " " + origin[0].getY() + " " + (origin[0].getZ() + 5)
					+ " {NoAI:1b,equipment:{mainhand:{id:\"minecraft:diamond_sword\"},head:{id:\"minecraft:golden_helmet\"}}}");
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.MODE, RingMode.STEAL.ordinal()));
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("orange_steal_before");
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("orange_steal_after");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				System.out.println("[orange] steal: inventory has sword=" + p.getInventory().contains(new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.DIAMOND_SWORD)));
			});
			world.getServer().runCommand("kill @e[type=!player]");

			// Avarice: copies of slain zombies, skeletons and a spider rise and go for a husk.
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(Avarice.SLAIN,
					List.of(Identifier.withDefaultNamespace("zombie"), Identifier.withDefaultNamespace("skeleton"), Identifier.withDefaultNamespace("spider"))));
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.MODE, RingMode.AVARICE.ordinal()));
			world.getServer().runCommand("summon husk " + origin[0].getX() + " " + origin[0].getY() + " " + (origin[0].getZ() + 14));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(10);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(15);
			ctx.takeScreenshot("orange_avarice_summon");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(60);
			ctx.takeScreenshot("orange_avarice_fight");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("orange_avarice_night");
			world.getServer().runOnServer(server -> {
				var level = player(server).level();
				long copies = level.getEntitiesOfClass(net.minecraft.world.entity.Mob.class, new AABB(origin[0]).inflate(40),
						m -> m.entityTags().contains("lanternring.avarice_copy")).size();
				long husks = level.getEntitiesOfClass(net.minecraft.world.entity.monster.zombie.Husk.class, new AABB(origin[0]).inflate(40)).size();
				System.out.println("[orange] avarice: copies=" + copies + " husksLeft=" + husks);
			});
		}
	}
}
