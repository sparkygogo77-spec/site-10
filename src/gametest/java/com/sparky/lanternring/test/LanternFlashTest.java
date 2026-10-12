package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.LanternFlash;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.LanternFlashPayload;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.monster.zombie.Zombie;

/**
 * The lantern flashbang: the sun on the ring while charging a Blue ring (first and third person),
 * a zombie looking at the charger gets dazzled, and someone else's flash whites out your screen
 * while you look at them and clears once you look away.
 */
public class LanternFlashTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 18000");
			world.getServer().runOnServer(server -> {
				player(server).setItemInHand(InteractionHand.MAIN_HAND, Corps.BLUE.ring());
				player(server).setItemInHand(InteractionHand.OFF_HAND, Corps.BLUE.lantern());
			});
			ctx.waitTicks(40);
			LabSettings.get().ringModel = LabSettings.RingModel.CREST;
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 10f);
			// A zombie a few blocks ahead, staring at you.
			world.getServer().runCommand("execute as @p at @s run summon zombie ~ ~ ~6 {NoAI:1b,Rotation:[180f,0f],PersistenceRequired:1b,Tags:[\"flashed\"]}");
			ctx.waitTicks(20);
			setCharge(world, 10);

			int contact = LanternCharge.hold() + LanternCharge.reach();
			int build = LanternCharge.done() - contact;
			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(contact + build / 3);
			ctx.takeScreenshot("flash_sun_first_person_early");
			ctx.waitTicks(build / 3);
			ctx.takeScreenshot("flash_sun_first_person_mid");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(build - 2 * (build / 3) - 10);
			ctx.takeScreenshot("flash_sun_third_person_peak");
			boolean dazzled = world.getServer().computeOnServer(server -> player(server).level().getEntitiesOfClass(Zombie.class,
					player(server).getBoundingBox().inflate(12)).stream().anyMatch(z -> z.hasEffect(MobEffects.BLINDNESS)));
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			if (!dazzled) throw new AssertionError("The zombie looking at the charging ring should be dazzled");
			ctx.waitTicks(LanternCharge.DEPLETE + 10);

			// Someone else charging: the zombie stands in for them, with the server's light messages faked.
			int id = world.getServer().computeOnServer(server -> player(server).level().getEntitiesOfClass(Zombie.class,
					player(server).getBoundingBox().inflate(12)).get(0).getId());
			ctx.getInput().lookAt(0f, 10f);
			for (int i = 0; i < 12; i++) {
				float power = i < 10 ? 0.4f + 0.06f * i : com.sparky.lanternring.LanternFlash.BURST;
				ctx.runOnClient(mc -> LanternFlash.handle(new LanternFlashPayload(id, power, Corps.BLUE.ordinal())));
				ctx.waitTicks(2);
				if (i == 4) ctx.takeScreenshot("flash_looking_building");
			}
			float looking = ctx.computeOnClient(mc -> LanternFlash.flash());
			ctx.takeScreenshot("flash_looking_burst");
			if (looking < 0.7f) throw new AssertionError("Looking at the flash should white out the screen, got " + looking);

			// Look away: it clears.
			ctx.runOnClient(mc -> LanternFlash.handle(new LanternFlashPayload(id, 1f, Corps.BLUE.ordinal())));
			ctx.getInput().lookAt(180f, 10f);
			ctx.waitTicks(Math.max(1, RingTuning.LANTERN_FLASH_FADE.ticks()) / 3);
			ctx.takeScreenshot("flash_looked_away_clearing");
			ctx.waitTicks(RingTuning.LANTERN_FLASH_FADE.ticks() + 20);
			float away = ctx.computeOnClient(mc -> LanternFlash.flash());
			ctx.takeScreenshot("flash_looked_away");
			System.out.println("[flash-test] looking=" + looking + " away=" + away);
			if (away > 0.1f) throw new AssertionError("The flash should clear after looking away, got " + away);
		}
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static void setCharge(TestSingleplayerContext world, int charge) {
		world.getServer().runOnServer(server -> PowerRingItem.setCharge(player(server).getMainHandItem(), charge));
	}
}
