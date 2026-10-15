package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;

/**
 * Pass 844 S3b: the construct sword in first person. It extrudes out of the ring fist when you switch to it, rests in the
 * ring hand, and a swing is the stepping wide sweep pair, whose backswing hits again (SwordSweeps).
 */
public class SwordSwingTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set noon");
			server.runCommand("gamemode survival @a");
			ctx.waitTicks(40);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.getInventory().clearContent();
				BlockPos b = p.blockPosition();
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-6, 0, -6), b.offset(6, 4, 6))) p.level().setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
				p.teleportTo(b.getX() + 0.5, b.getY(), b.getZ() + 0.5);
				ItemStack ring = Corps.GREEN.ring();
				PowerRingItem.setCharge(ring, 500);
				ring.set(ModComponents.MODE, RingMode.TOOLS.ordinal());
				p.getInventory().setItem(0, ring);
				p.getInventory().setSelectedSlot(0);
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(180f, 5f);
			ctx.waitTicks(10);
			ctx.getInput().pressKey(o -> o.keyUse);   // the tools come into the hotbar; slot 1 is the sword
			ctx.waitTicks(10);
			ctx.runOnClient(mc -> mc.player.getInventory().setSelectedSlot(1));
			ctx.waitTicks(8);
			ctx.takeScreenshot("sword_s3b_forming");
			ctx.waitTicks(12);
			ctx.takeScreenshot("sword_s3b_rest");
			// One husk ahead (the first hit) and one off to the left (the backswing reaches it).
			server.runCommand("execute at @p run summon husk ~ ~ ~-2 {NoAI:1b}");
			server.runCommand("execute at @p run summon husk ~-1.6 ~ ~-1.6 {NoAI:1b}");
			ctx.waitTicks(5);
			float[] hp = new float[2];
			server.runOnServer(s -> hp[0] = total(s.getPlayerList().getPlayers().get(0)));
			ctx.getInput().pressKey(o -> o.keyAttack);
			for (int t = 1; t <= 15; t += 2) {
				ctx.takeScreenshot("sword_s3b_swing_" + t);
				ctx.waitTicks(2);
			}
			ctx.waitTicks(10);
			server.runOnServer(s -> hp[1] = total(s.getPlayerList().getPlayers().get(0)));
			System.out.println("[SwordSwingTest] husk health before " + hp[0] + " after " + hp[1]);
			server.runCommand("kill @e[type=husk]");
		}
	}

	private static float total(ServerPlayer p) {
		float sum = 0;
		for (LivingEntity e : p.level().getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(6), e -> e != p)) sum += e.getHealth();
		return sum;
	}
}
