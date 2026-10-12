package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.CorpsGolem;
import com.sparky.lanternring.corps.RageCat;
import com.sparky.lanternring.corps.RageWarden;
import com.sparky.lanternring.corps.RedSanctuary;
import com.sparky.lanternring.corps.SkyRaider;
import java.util.Map;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;

/** A level 4 red Deluge: the blood orb, the Rage Spire forming top to bottom under blood, its residents, then the dissolve. */
public class RedSanctuaryTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(server -> {
			var level = server.getPlayerList().getPlayers().get(0).level();
			BlockPos anchor = o.above(RedSanctuary.FLOAT);
			int placed = 0, blood = 0, total = 0;
			for (Map.Entry<BlockPos, BlockState> e : RedSanctuary.plan(anchor).entrySet()) {
				total++;
				BlockState now = level.getBlockState(e.getKey());
				if (now.is(e.getValue().getBlock())) placed++;
				if (now.is(RedSanctuary.BLOOD_COAT)) blood++;
			}
			AABB box = new AABB(anchor).inflate(40);
			System.out.println("[sanctuary] " + when + ": placed=" + placed + "/" + total + " blood=" + blood
					+ " raiders=" + level.getEntitiesOfClass(SkyRaider.class, box).size()
					+ " wardens=" + level.getEntitiesOfClass(RageWarden.class, box).size()
					+ " cats=" + level.getEntitiesOfClass(RageCat.class, box).size()
					+ " golems=" + level.getEntitiesOfClass(CorpsGolem.class, box).size()
					+ " sites=" + RedSanctuary.Data.get(level).all().size());
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("difficulty hard");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> {
				mc.options.setCameraType(CameraType.FIRST_PERSON);
				mc.options.renderDistance().set(12);
			});

			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.RED.ring());
				BlockPos o = p.blockPosition();
				origin[0] = o;
				var level = p.level();
				for (int x = -20; x <= 20; x++)
					for (int y = 1; y <= 90; y++)
						for (int z = -20; z <= 20; z++) level.setBlock(o.offset(x, y, z), Blocks.AIR.defaultBlockState(), 2);
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
				p.teleportTo(o.getX() + 0.5, o.getY() + 28, o.getZ() - 60.5);
				System.out.println("[sanctuary] raised=" + RedSanctuary.raise(level, p, o));
			});
			ctx.getInput().lookAt(0f, -4f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("sanctuary_orb_forming");
			ctx.waitTicks(30);
			ctx.takeScreenshot("sanctuary_orb_falls");
			for (int i = 0; i < 5; i++) {
				ctx.waitTicks(110);
				report(world, origin[0], "build " + i);
				ctx.takeScreenshot("sanctuary_build_" + i);
			}
			ctx.waitTicks(80);
			report(world, origin[0], "standing");
			ctx.takeScreenshot("sanctuary_standing");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("sanctuary_night");
			world.getServer().runCommand("time set 6000");
			// On the plaza with the residents.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos plaza = RedSanctuary.plaza(origin[0].above(RedSanctuary.FLOAT));
				p.teleportTo(plaza.getX() + 0.5, plaza.getY() + 2, plaza.getZ() - 9.5);
			});
			ctx.getInput().lookAt(0f, 12f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("sanctuary_plaza");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(5);
			ctx.takeScreenshot("sanctuary_plaza_behind");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			// Break the core lantern: the spire dissolves back into blood.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos core = RedSanctuary.core(origin[0].above(RedSanctuary.FLOAT));
				System.out.println("[sanctuary] core is lantern=" + p.level().getBlockState(core).is(ModRegistry.POWER_BATTERY));
				p.level().setBlock(core, Blocks.AIR.defaultBlockState(), 3);
				p.teleportTo(origin[0].getX() + 0.5, origin[0].getY() + 28, origin[0].getZ() - 60.5);
			});
			ctx.getInput().lookAt(0f, -4f);
			ctx.waitTicks(150);
			report(world, origin[0], "dissolving");
			ctx.takeScreenshot("sanctuary_dissolving");
			ctx.waitTicks(400);
			report(world, origin[0], "dissolved");
			ctx.takeScreenshot("sanctuary_dissolved");
		}
	}
}
