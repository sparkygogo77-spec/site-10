package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.ally.ConstructAlly;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.entity.EntityTypeTest;

/** Army mode: the Warden, Dragon and Sentry constructs forming and fighting husks, leaving a pig and a villager alone. */
public class ArmyTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode creative @a");
			server.runCommand("difficulty normal");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			server.runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.ARMY.ordinal());
			});
			// A flat field to fight on.
			server.runCommand("execute at @p run fill ~-24 ~-1 ~-24 ~24 ~-1 ~24 grass_block");
			server.runCommand("execute at @p run fill ~-24 ~ ~-24 ~24 ~20 ~24 air");
			server.runCommand("kill @e[type=!player]");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(20);

			// The Warden: hold right-click to aim, let go.
			summon(ctx, 0);
			ctx.waitTicks(8);
			ctx.takeScreenshot("army_warden_forming");
			ctx.waitTicks(30);
			ctx.takeScreenshot("army_warden");
			server.runCommand("execute at @p run summon husk ~3 ~ ~12");
			server.runCommand("execute at @p run summon husk ~-3 ~ ~14");
			server.runCommand("execute at @p run summon pig ~5 ~ ~6");
			server.runCommand("execute at @p run summon villager ~-5 ~ ~6 {NoAI:1b}");
			for (int i = 1; i <= 4; i++) {
				ctx.waitTicks(15);
				ctx.takeScreenshot("army_warden_fight_" + i);
			}
			count(world, "after warden");
			ctx.waitTicks(80);
			count(world, "after warden 80");

			// The Dragon: one left-click while holding picks it.
			summon(ctx, 1);
			ctx.waitTicks(40);
			ctx.getInput().lookAt(0f, -10f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("army_dragon_1");
			ctx.waitTicks(15);
			ctx.takeScreenshot("army_dragon_2");
			server.runCommand("execute at @p run summon husk ~6 ~ ~14");
			server.runCommand("execute at @p run summon husk ~-6 ~ ~16");
			for (int i = 1; i <= 4; i++) {
				ctx.waitTicks(12);
				ctx.takeScreenshot("army_dragon_fight_" + i);
			}
			count(world, "after dragon");

			// The Sentry: guards the spot it forms on.
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(5);
			summon(ctx, 1);
			ctx.waitTicks(30);
			ctx.takeScreenshot("army_sentry");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 15f);
			server.runCommand("execute at @p run summon husk ~2 ~ ~16");
			server.runCommand("execute at @p run summon husk ~-4 ~ ~18");
			for (int i = 1; i <= 6; i++) {
				ctx.waitTicks(8);
				ctx.takeScreenshot("army_sentry_fight_" + i);
			}
			count(world, "after sentry");

			// The Pig (pass 828): wears the Ring Lab's construct pig texture (P2 hex by default).
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(5);
			summon(ctx, 1);
			ctx.waitTicks(30);
			ctx.takeScreenshot("army_pig");
			count(world, "after pig");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().lookAt(180f, 10f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("army_all");
		}
	}

	/** Holds right-click, left-clicks clicks times to step the construct, then lets go. */
	private static void summon(ClientGameTestContext ctx, int clicks) {
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(4);
		for (int i = 0; i < clicks; i++) {
			ctx.getInput().pressKey(o -> o.keyAttack);
			ctx.waitTicks(3);
		}
		ctx.waitTicks(10);
		ctx.takeScreenshot("army_aim_" + clicks);
		ctx.getInput().releaseKey(o -> o.keyUse);
	}

	private static void count(TestSingleplayerContext world, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			StringBuilder out = new StringBuilder();
			for (LivingEntity e : p.level().getEntities(EntityTypeTest.forClass(LivingEntity.class), e -> e != p && e.isAlive())) {
				out.append(e.getType().toShortString()).append(e instanceof ConstructAlly a ? "(life " + a.life() + ")" : "")
						.append(" hp=").append(Math.round(e.getHealth())).append("; ");
			}
			System.out.println("[army] " + when + ": " + out);
		});
	}
}
