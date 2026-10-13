package com.sparky.lanternring.test;

import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.corps.RedRingBearers;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.animal.chicken.Chicken;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.level.block.Blocks;

/**
 * Red rings choosing bearers: a zombie kills a chicken, a red ring streaks down onto it, and it
 * comes out a Red Lantern with double health and rage, then flies up at the player on a pillar.
 */
public class RedRingBearersTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			int[] ids = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				ServerLevel level = p.level();
				// The player stands on a pillar 6 blocks up, so the bearer has to fly.
				BlockPos feet = p.blockPosition();
				for (int y = 0; y < 6; y++) level.setBlockAndUpdate(feet.offset(0, y, 0), Blocks.STONE.defaultBlockState());
				p.teleportTo(feet.getX() + 0.5, feet.getY() + 6, feet.getZ() + 0.5);
				Zombie z = EntityTypes.ZOMBIE.create(level, EntitySpawnReason.COMMAND);
				z.setPos(feet.getX() + 9.5, feet.getY(), feet.getZ() + 0.5);
				z.setNoAi(false);
				level.addFreshEntity(z);
				Chicken c = EntityTypes.CHICKEN.create(level, EntitySpawnReason.COMMAND);
				c.setPos(z.getX() + 1, z.getY(), z.getZ());
				level.addFreshEntity(c);
				RedRingBearers.KILL_CHANCE = 1f;
				c.hurtServer(level, level.damageSources().mobAttack(z), 100);
				return new int[] {z.getId(), (int) z.getMaxHealth()};
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(-90f, 25f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("red_ring_flying_in");
			ctx.waitTicks(30);
			ctx.takeScreenshot("red_ring_bearer");
			String state = world.getServer().computeOnServer(server -> {
				var z = (Zombie) player(server).level().getEntity(ids[0]);
				if (z == null) return "gone";
				return RedRingBearers.bearer(z) + " hp=" + z.getMaxHealth() + " rage=" + z.hasEffect(ModEffects.RAGE) + " y=" + z.getY();
			});
			System.out.println("[red-ring-bearers] crowned: " + state);
			if (!state.startsWith("true") || !state.contains("rage=true")) throw new AssertionError("The zombie should have been chosen: " + state);
			double startY = world.getServer().computeOnServer(server -> player(server).getY() - 6);
			ctx.waitTicks(60);
			ctx.takeScreenshot("red_ring_bearer_flying");
			double y = world.getServer().computeOnServer(server -> {
				var z = player(server).level().getEntity(ids[0]);
				return z == null ? -999 : z.getY();
			});
			System.out.println("[red-ring-bearers] rose " + (y - startY));
			RedRingBearers.KILL_CHANCE = 0.35f;
			if (y - startY < 2.5) throw new AssertionError("The bearer should fly up at the player, rose " + (y - startY));
		}
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
