package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;

/** A non-green ring's lasso bubble, rope and body glint are in its own colour, with no green left (on grey stone, at night). */
public class CorpsColourTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(40);
			for (Corps corps : new Corps[] {Corps.VIOLET, Corps.YELLOW}) {
				String name = corps.getSerializedName();
				world.getServer().runOnServer(server -> {
					ServerPlayer p = server.getPlayerList().getPlayers().get(0);
					BlockPos b = p.blockPosition();
					for (BlockPos pos : BlockPos.betweenClosed(b.offset(-12, -2, -4), b.offset(12, 8, 20))) {
						p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.STONE.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
					}
					p.level().getEntitiesOfClass(Mob.class, p.getBoundingBox().inflate(40)).forEach(m -> m.discard());
					ItemStack ring = corps.ring();
					ring.set(ModComponents.MODE, RingMode.TETHER.ordinal());
					p.setItemInHand(InteractionHand.MAIN_HAND, ring);
					p.teleportTo(b.getX() + 0.5, b.getY(), b.getZ() + 0.5);
					Mob pig = EntityTypes.PIG.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
					pig.snapTo(b.getX() + 0.5, b.getY(), b.getZ() + 6.5, 180f, 0f);
					pig.setNoAi(true);
					p.level().addFreshEntity(pig);
				});
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
				ctx.getInput().lookAt(0f, 12f);
				ctx.waitTicks(20);
				ctx.getInput().holdKey(o -> o.keyUse);
				ctx.waitTicks(25);
				ctx.takeScreenshot("corps_lasso_" + name + "_first_person");
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
				ctx.waitTicks(5);
				ctx.takeScreenshot("corps_lasso_" + name + "_third_person");
				ctx.getInput().releaseKey(o -> o.keyUse);
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
				ctx.waitTicks(30);
				ctx.takeScreenshot("corps_aura_" + name + "_front");
			}
		}
	}
}
