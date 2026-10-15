package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.HitEffects;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.client.HitFx;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;

/**
 * Blender pass 815's hit effects: F1, a ring bearer punches a construct wall and it shatters from the punch
 * outward into construct pixels; F3, a zombie punched by a green, then a yellow ring flashes its outline.
 */
public class HitEffectsTest implements FabricClientGameTest {
	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(server -> {
			var level = player(server).level();
			int left = 0;
			for (BlockPos pos : BlockPos.betweenClosed(o.offset(-4, 0, 2), o.offset(4, 6, 4))) {
				if (HitEffects.isConstruct(level.getBlockState(pos))) left++;
			}
			System.out.println("[hit] " + when + ": construct blocks left=" + left + " shattering=" + HitEffects.shattering());
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("effect give @a resistance infinite 255 true");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring());
				BlockPos o = p.blockPosition().above(10);
				origin[0] = o;
				var level = p.level();
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-12, -3, -12), o.offset(12, 10, 12))) {
					level.setBlock(pos, pos.getY() < o.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				// A 7 wide, 5 high construct wall 2 blocks ahead.
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-3, 0, 2), o.offset(3, 4, 2))) {
					level.setBlock(pos, Corps.GREEN.tint(ModRegistry.LIGHT_CONSTRUCT.defaultBlockState()), 3);
				}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			world.getServer().runCommand("kill @e[type=!player]");
			BlockPos o = origin[0];
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("hit_shatter_before");
			report(world, o, "before");
			ctx.getInput().pressKey(opt -> opt.keyAttack);
			ctx.waitTicks(4);
			ctx.takeScreenshot("hit_shatter_t4");
			ctx.runOnClient(mc -> System.out.println("[hit] pixels flying at t4: " + HitFx.bits()));
			ctx.waitTicks(5);
			ctx.takeScreenshot("hit_shatter_t9");
			ctx.waitTicks(25);
			report(world, o, "after 34 ticks");

			// F3: a still zombie punched by a green ring, then a yellow one.
			world.getServer().runCommand("summon husk " + (o.getX() + 0.5) + " " + o.getY() + " " + (o.getZ() + 2.5)
					+ " {NoAI:1b,Health:200f,Attributes:[{id:\"max_health\",base:200}]}");
			ctx.waitTicks(25);
			ctx.getInput().pressKey(opt -> opt.keyAttack);
			ctx.waitTicks(2);
			ctx.takeScreenshot("hit_flash_green_t2");
			ctx.runOnClient(mc -> System.out.println("[hit] flashing at green t2: " + HitFx.flashes()));
			ctx.waitTicks(25);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.YELLOW.ring());
			});
			ctx.waitTicks(25);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				var zombie = p.level().getEntities(p, p.getBoundingBox().inflate(5), e -> e instanceof net.minecraft.world.entity.monster.zombie.Husk);
				if (!zombie.isEmpty()) p.attack(zombie.getFirst());
			});
			ctx.waitTicks(2);
			ctx.takeScreenshot("hit_flash_yellow_3p_t2");
			ctx.runOnClient(mc -> System.out.println("[hit] flashing at yellow t2: " + HitFx.flashes()));
			ctx.waitTicks(4);
			ctx.takeScreenshot("hit_flash_yellow_3p_t6");
		}
	}
}
