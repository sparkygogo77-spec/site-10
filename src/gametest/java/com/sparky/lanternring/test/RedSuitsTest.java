package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.corps.CorpsGolem;
import com.sparky.lanternring.corps.CorpsMobs;
import com.sparky.lanternring.corps.RageCat;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.block.Blocks;

/** The sanctuary's four suits side by side, front and back: raider, warden, cat and Blood Iron golem. */
public class RedSuitsTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("difficulty hard");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			List<Mob> mobs = new ArrayList<>();
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				var level = p.level();
				BlockPos o = p.blockPosition();
				for (int x = -8; x <= 8; x++)
					for (int y = 0; y <= 6; y++)
						for (int z = -4; z <= 10; z++)
							level.setBlock(o.offset(x, y, z), y == 0 ? Blocks.POLISHED_BLACKSTONE.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				Mob raider = CorpsMobs.SKY_RAIDER.create(level, EntitySpawnReason.COMMAND);
				Mob warden = CorpsMobs.RAGE_WARDEN.create(level, EntitySpawnReason.COMMAND);
				RageCat cat = CorpsMobs.RAGE_CAT.create(level, EntitySpawnReason.COMMAND);
				CorpsGolem golem = CorpsMobs.CORPS_GOLEM.create(level, EntitySpawnReason.COMMAND);
				golem.setup(Corps.RED, o);
				raider.setItemSlot(EquipmentSlot.MAINHAND, Corps.RED.ring());
				double[] xs = {-4.5, -1.5, 1.2, 4.0};
				Mob[] all = {raider, warden, cat, golem};
				for (int i = 0; i < 4; i++) {
					Mob m = all[i];
					m.setNoAi(true);
					m.setPersistenceRequired();
					m.snapTo(o.getX() + 0.5 + xs[i], o.getY() + 1, o.getZ() + 5.5, 180f, 0f);
					m.setYHeadRot(180f);
					m.setYBodyRot(180f);
					level.addFreshEntity(m);
					mobs.add(m);
				}
				p.teleportTo(o.getX() + 0.5, o.getY() + 2.2, o.getZ() - 3.5);
			});
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("red_suits_front");
			world.getServer().runOnServer(server -> {
				for (Mob m : mobs) {
					m.setYRot(0f);
					m.setYHeadRot(0f);
					m.setYBodyRot(0f);
				}
			});
			ctx.waitTicks(20);
			ctx.takeScreenshot("red_suits_back");
		}
	}
}
