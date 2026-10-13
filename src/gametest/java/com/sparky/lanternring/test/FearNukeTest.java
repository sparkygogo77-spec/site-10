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
 * The Fear Nuke rework (J, 2026-10-13): built on the raised ring hand (first and third person), sent
 * out to airburst over a field 70 blocks off, the 4x crater, no damage, the Fear Frenzy with yellow
 * construct weapons; then the 1911.
 */
public class FearNukeTest implements FabricClientGameTest {
	private static final int AHEAD = 70;

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
			RingTuning.FEAR_NUKE_BUILD.set(3);
			RingTuning.FEAR_NUKE_ORB.set(2);
			RingTuning.FEAR_NUKE_CONSUME.set(1.5);
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

			// ---- Straying too far: start forming it, then go 40 blocks back; it breaks apart.
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 1.3f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o2 -> o2.keyUse);
			ctx.waitTicks(20);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				System.out.println("[nuke] forming at " + FearNuke.forming(p) + " strayed=" + FearNuke.strayed(p));
				p.teleportTo(o[0].getX() + 0.5, o[0].getY(), o[0].getZ() - 39.5);
			});
			ctx.getInput().lookAt(0f, -16f);
			ctx.waitTicks(5);
			ctx.takeScreenshot("nuke_strayed_scatter");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				System.out.println("[nuke] after straying broken=" + FearNuke.broken(p) + " building=" + FearNuke.building(p));
			});
			ctx.waitTicks(10);
			server.runOnServer(s -> System.out.println("[nuke] still broken while held=" + FearNuke.broken(s.getPlayerList().getPlayers().get(0))
					+ " building=" + FearNuke.building(s.getPlayerList().getPlayers().get(0))));
			ctx.getInput().releaseKey(o2 -> o2.keyUse);
			server.runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o[0].getX() + 0.5, o[0].getY(), o[0].getZ() + 0.5));
			ctx.getInput().lookAt(0f, 1.3f);
			ctx.waitTicks(30);

			// ---- Forming it in the sky, tethered to the raised ring.
			ctx.getInput().holdKey(o2 -> o2.keyUse);
			ctx.waitTicks(25);
			ctx.getInput().lookAt(0f, -36f);
			ctx.waitTicks(2);
			ctx.takeScreenshot("nuke_forming_fp");
			server.runOnServer(s -> System.out.println("[nuke] building=" + FearNuke.building(s.getPlayerList().getPlayers().get(0))));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(4);
			ctx.takeScreenshot("nuke_forming_3p_back");
			ctx.waitTicks(40);
			ctx.takeScreenshot("nuke_built_3p_back");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().lookAt(0f, 1.3f);
			ctx.waitTicks(4);
			ctx.takeScreenshot("nuke_built_3p_front");
			ctx.runOnClient(mc -> System.out.println("[nuke] client raise=" + NukeHold.raise(mc.player, 0f) + " formed=" + FearNukeFx.formed(mc.player)));
			server.runOnServer(s -> System.out.println("[nuke] built=" + FearNuke.built(s.getPlayerList().getPlayers().get(0))));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(2);

			// ---- Let go: it flies out, hangs, airbursts.
			ctx.getInput().releaseKey(o2 -> o2.keyUse);
			ctx.waitTicks(12);
			ctx.takeScreenshot("nuke_flying");
			server.runOnServer(s -> System.out.println("[nuke] busy after release=" + FearNuke.busy(s.getPlayerList().getPlayers().get(0))));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, -8f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("nuke_hanging");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				for (Mob m : p.level().getEntitiesOfClass(Mob.class, new AABB(o[0]).inflate(120))) {
					System.out.println("[nuke] before " + m.getType().toShortString() + " health=" + m.getHealth());
				}
			});
			ctx.waitTicks(20);
			ctx.takeScreenshot("nuke_airburst");
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
		}
	}
}
