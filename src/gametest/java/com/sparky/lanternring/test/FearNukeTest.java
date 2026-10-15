package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.AirburstFx;
import com.sparky.lanternring.client.FearGasFx;
import com.sparky.lanternring.client.FearNukeFx;
import com.sparky.lanternring.client.NukeHold;
import com.sparky.lanternring.corps.FearNuke;
import com.sparky.lanternring.item.Pistol1911Item;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;

/**
 * The Fear Nuke (J, 2026-10-15): it drops into place over the raised ring (first and third person), is
 * thrown up and out to airburst with its bottom about 5 blocks over a field, then thrown at a wall it goes off on contact; the 4x crater, no damage, the Fear Frenzy with yellow
 * construct weapons; then the 1911.
 */
public class FearNukeTest implements FabricClientGameTest {
	private static final int AHEAD = 45;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode creative @a");
			server.runCommand("difficulty normal");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(40);
			RingTuning.FEAR_NUKE_BUILD.set(0.5);
			RingTuning.FEAR_NUKE_FLIGHT.set(8);
			// A flat field out to well past the crater, 30 blocks deep and raised off the superflat
			// bedrock so the crater has room: grass on stone, clear sky.
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
				p.teleportTo(p.getX(), p.getY() + 34, p.getZ());
			});
			ctx.waitTicks(5);
			for (int x = -60; x < 60; x += 30) {
				for (int z = -20; z < AHEAD + 60; z += 30) {
					String box = "~" + x + " ~%d ~" + z + " ~" + (x + 29) + " ~%d ~" + (z + 29);
					server.runCommand("execute at @p run fill " + String.format(box, -31, -2) + " stone");
					server.runCommand("execute at @p run fill " + String.format(box, -1, -1) + " grass_block");
				}
			}
			server.runCommand("kill @e[type=!player]");
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				p.getAbilities().flying = false;
				p.onUpdateAbilities();
				p.teleportTo(o[0].getX() + 0.5, o[0].getY(), o[0].getZ() + 0.5);
				ItemStack ring = Corps.YELLOW.ring();
				ring.set(ModComponents.MODE, RingMode.AERIAL.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			// A crowd by the target: villagers, husks, illagers and cows, all with their own AI.
			String[] mobs = {"villager", "villager", "villager", "villager", "husk", "husk", "husk", "pillager", "vindicator", "cow", "cow", "piglin"};
			for (int i = 0; i < mobs.length; i++) {
				server.runCommand("execute at @p run summon " + mobs[i] + " ~" + (i % 4 * 3 - 5) + " ~ ~" + (AHEAD - 4 + i / 4 * 3)
						+ (mobs[i].equals("piglin") ? " {IsImmuneToZombification:1b}" : ""));
			}
			// A house and a tree in the crater, to see them burn.
			server.runCommand("execute at @p run fill ~8 ~ ~" + (AHEAD + 6) + " ~13 ~4 ~" + (AHEAD + 11) + " oak_planks hollow");
			server.runCommand("execute at @p run fill ~-10 ~ ~" + (AHEAD + 4) + " ~-10 ~5 ~" + (AHEAD + 4) + " oak_log");
			server.runCommand("execute at @p run fill ~-12 ~5 ~" + (AHEAD + 2) + " ~-8 ~7 ~" + (AHEAD + 6) + " oak_leaves keep");

			// ---- Hold: it drops out of the sky into place over the raised ring.
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, -36f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o2 -> o2.keyUse);
			ctx.waitTicks(4);
			ctx.takeScreenshot("nuke_dropping_fp");
			server.runOnServer(s -> System.out.println("[nuke] building=" + FearNuke.building(s.getPlayerList().getPlayers().get(0))));
			ctx.waitTicks(10);
			ctx.takeScreenshot("nuke_held_fp");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				System.out.println("[nuke] built=" + FearNuke.built(p) + " held at " + FearNuke.forming(p) + " eye " + p.getEyePosition());
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, -25f);
			ctx.waitTicks(4);
			ctx.takeScreenshot("nuke_held_3p_back");
			ctx.runOnClient(mc -> System.out.println("[nuke] client raise=" + NukeHold.raise(mc.player, 0f) + " formed=" + FearNukeFx.formed(mc.player)));

			// ---- Let go: thrown up and out the way they look, a heavy arc, no hovering; airbursts with its bottom about 5 blocks up.
			ctx.getInput().releaseKey(o2 -> o2.keyUse);
			for (int i = 0; i < 6; i++) {
				ctx.waitTicks(4);
				server.runOnServer(s -> System.out.println("[nuke] flying at " + FearNuke.flying(s.getPlayerList().getPlayers().get(0))));
				if (i == 2) ctx.takeScreenshot("nuke_thrown");
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, -8f);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				for (Mob m : p.level().getEntitiesOfClass(Mob.class, new AABB(o[0]).inflate(120))) {
					System.out.println("[nuke] before " + m.getType().toShortString() + " health=" + m.getHealth());
				}
			});
			for (int i = 0; i < 40 && FearNuke.lastBurst == null; i++) ctx.waitTicks(1);
			ctx.waitTicks(2);
			ctx.takeScreenshot("nuke_airburst");
			System.out.println("[nuke] burst " + FearNuke.lastBurst + " (bottom about 5 over the ground)");
			ctx.runOnClient(mc -> System.out.println("[nuke] flash=" + AirburstFx.flash()));
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				for (Mob m : p.level().getEntitiesOfClass(Mob.class, new AABB(o[0]).inflate(140))) {
					System.out.println("[nuke] just after " + m.getType().toShortString() + " health=" + m.getHealth()
							+ " frenzy=" + m.hasEffect(ModEffects.FRENZY));
				}
			});
			ctx.waitTicks(10);
			ctx.takeScreenshot("nuke_fireball");
			ctx.waitTicks(30);
			ctx.takeScreenshot("nuke_mushroom");
			ctx.waitTicks(40);
			ctx.takeScreenshot("nuke_cloud");
			// Up close with the crowd in the crater, with their weapons out.
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
				p.teleportTo(o[0].getX() + 0.5, o[0].getY() - 2, o[0].getZ() + AHEAD - 12.5);
			});
			ctx.getInput().lookAt(0f, 25f);
			ctx.waitTicks(4);
			ctx.takeScreenshot("frenzy_weapons");
			ctx.runOnClient(mc -> System.out.println("[nuke] gas=" + FearGasFx.strength()));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(20);
			ctx.takeScreenshot("frenzy_fight");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			// The crater from above.
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.teleportTo(o[0].getX() + 0.5, o[0].getY() + 30, o[0].getZ() + AHEAD - 62.5);
			});
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("nuke_crater_above");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				ServerLevel level = p.level();
				BlockPos c = o[0].offset(0, 0, AHEAD);
				int deepest = 0;
				for (int y = 0; y < 30; y++) {
					if (level.getBlockState(c.below(y + 1)).isAir()) deepest = y + 1;
					else break;
				}
				int rim = 0;
				for (int r = 0; r < 120; r++) {
					if (level.getBlockState(c.offset(0, -1, r)).isAir()) rim = r;
				}
				System.out.println("[nuke] crater depth=" + deepest + " radius along +z=" + rim + " (old blast reached about 10)");
				for (Mob m : level.getEntitiesOfClass(Mob.class, new AABB(o[0]).inflate(140))) {
					System.out.println("[nuke] after " + m.getType().toShortString() + " health=" + m.getHealth()
							+ " frenzy=" + m.hasEffect(ModEffects.FRENZY) + " holds=" + m.getItemBySlot(EquipmentSlot.MAINHAND).getItem());
				}
			});
			ctx.takeScreenshot("nuke_crater");

			ctx.waitTicks(200);
			ctx.takeScreenshot("frenzy_later");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				int alive = 0;
				for (Mob m : p.level().getEntitiesOfClass(Mob.class, new AABB(o[0]).inflate(140))) {
					alive++;
					System.out.println("[nuke] later " + m.getType().toShortString() + " health=" + m.getHealth()
							+ " frenzy=" + m.hasEffect(ModEffects.FRENZY) + " holds=" + m.getItemBySlot(EquipmentSlot.MAINHAND).getItem());
				}
				System.out.println("[nuke] alive after the frenzy: " + alive + " of 12");
			});

			// ---- The 1911.
			server.runCommand("kill @e[type=!player]");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.getAbilities().flying = false;
				p.onUpdateAbilities();
				p.teleportTo(o[0].getX() + 20.5, o[0].getY(), o[0].getZ() - 10.5);
				p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(ModRegistry.PISTOL_1911));
			});
			server.runCommand("execute at @p run summon cow ~ ~ ~6 {NoAI:1b}");
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("pistol_1911_fp");
			ctx.getInput().pressKey(o2 -> o2.keyUse);
			ctx.waitTicks(2);
			ctx.takeScreenshot("pistol_1911_fire");
			ctx.waitTicks(6);
			ctx.getInput().pressKey(o2 -> o2.keyUse);
			ctx.waitTicks(6);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				LivingEntity cow = p.level().getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(12), e -> e != p).stream().findFirst().orElse(null);
				System.out.println("[nuke] pistol rounds=" + Pistol1911Item.rounds(p.getMainHandItem()) + " cow health="
						+ (cow == null ? "dead" : cow.getHealth()));
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(4);
			ctx.takeScreenshot("pistol_1911_3p");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// ---- On contact: thrown level at a wall 15 blocks off, it goes off on the wall before it can airburst.
			FearNuke.lastBurst = null;
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.teleportTo(o[0].getX() - 39.5, o[0].getY(), o[0].getZ() - 9.5);
				ItemStack ring = Corps.YELLOW.ring();
				ring.set(ModComponents.MODE, RingMode.AERIAL.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			ctx.waitTicks(2);
			server.runCommand("execute at @p run fill ~-18 ~-1 ~-15 ~-16 ~25 ~15 stone");
			ctx.getInput().lookAt(90f, 0f);
			ctx.waitTicks(30);
			ctx.getInput().holdKey(o2 -> o2.keyUse);
			ctx.waitTicks(14);
			ctx.getInput().releaseKey(o2 -> o2.keyUse);
			for (int i = 0; i < 30 && FearNuke.lastBurst == null; i++) ctx.waitTicks(1);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(3);
			ctx.takeScreenshot("nuke_contact");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			System.out.println("[nuke] contact burst " + FearNuke.lastBurst + " (wall face at x=" + (o[0].getX() - 55) + ", middle stops about 4.3 short)");
		}
	}
}
