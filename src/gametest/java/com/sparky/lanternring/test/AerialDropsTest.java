package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.Terror;
import com.sparky.lanternring.city.CityBlocks;
import com.sparky.lanternring.corps.FearNuke;
import com.sparky.lanternring.corps.HopeDrop;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ambient.Bat;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** The Blue Hope Drop (a container round a mob and a dome), then the Yellow Fear Nuke: fear building, the orb, the blast, Dread. */
public class AerialDropsTest implements FabricClientGameTest {
	private static ServerPlayer player(TestSingleplayerContext world) {
		ServerPlayer[] p = new ServerPlayer[1];
		world.getServer().runOnServer(s -> p[0] = s.getPlayerList().getPlayers().get(0));
		return p[0];
	}

	private static void count(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(s -> {
			ServerLevel level = s.getPlayerList().getPlayers().get(0).level();
			int bricks = 0, walls = 0, panes = 0;
			for (BlockPos p : BlockPos.betweenClosed(o.offset(-30, -2, -30), o.offset(30, 12, 30))) {
				var st = level.getBlockState(p);
				if (st.is(CityBlocks.HOPE_BRICKS)) bricks++;
				else if (st.is(CityBlocks.HOPE_BRICK_WALL)) walls++;
				else if (st.is(Blocks.STAINED_GLASS_PANE.blue())) panes++;
			}
			System.out.println("[aerial] " + when + ": hope bricks=" + bricks + " walls=" + walls + " panes=" + panes);
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode creative @a");
			server.runCommand("difficulty normal");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(60);
			server.runCommand("execute at @p run fill ~-40 ~-1 ~-40 ~40 ~-1 ~40 grass_block");
			server.runCommand("execute at @p run fill ~-40 ~ ~-40 ~40 ~30 ~40 air");
			server.runCommand("kill @e[type=!player]");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				ItemStack ring = Corps.BLUE.ring();
				ring.set(ModComponents.MODE, RingMode.AERIAL.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			ctx.getInput().lookAt(0f, 20f);
			ctx.waitTicks(10);

			// ---- Blue: a container round a zombie, and a dome.
			server.runCommand("execute at @p run summon zombie ~-6 ~ ~14 {NoAI:1b}");
			ctx.waitTicks(5);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				Mob zombie = p.level().getEntitiesOfClass(Mob.class, new AABB(p.blockPosition()).inflate(30)).getFirst();
				System.out.println("[aerial] cage=" + HopeDrop.drop(p.level(), p, zombie.blockPosition(), true));
				System.out.println("[aerial] dome=" + HopeDrop.drop(p.level(), p, o[0].offset(8, 0, 16), false));
			});
			ctx.waitTicks(14);
			ctx.takeScreenshot("hope_drop_falling");
			ctx.waitTicks(30);
			ctx.takeScreenshot("hope_drop_hard_light");
			ctx.waitTicks(40);
			ctx.takeScreenshot("hope_drop_setting");
			ctx.waitTicks(60);
			count(world, o[0], "blue set");
			ctx.takeScreenshot("hope_drop_set");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.teleportTo(o[0].getX() + 8.5, o[0].getY(), o[0].getZ() + 15.5);
			});
			ctx.getInput().lookAt(0f, -15f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("hope_drop_inside_dome");

			// ---- Yellow: frighten a crowd, kill some, then the nuke (on a fresh field next door).
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = o[0].offset(80, 0, 0);
				p.teleportTo(o[0].getX() + 0.5, o[0].getY(), o[0].getZ() + 0.5);
			});
			ctx.waitTicks(20);
			server.runCommand("execute at @p run fill ~-30 ~-1 ~-10 ~30 ~-1 ~40 grass_block");
			server.runCommand("execute at @p run fill ~-30 ~ ~-10 ~30 ~12 ~15 air");
			server.runCommand("execute at @p run fill ~-30 ~ ~16 ~30 ~12 ~40 air");
			server.runCommand("kill @e[type=!player]");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.teleportTo(o[0].getX() + 0.5, o[0].getY(), o[0].getZ() + 0.5);
				ItemStack ring = Corps.YELLOW.ring();
				ring.set(ModComponents.MODE, RingMode.AERIAL.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			for (int i = 0; i < 10; i++) {
				server.runCommand("execute at @p run summon zombie ~" + (i * 3 - 14) + " ~ ~" + (14 + i % 3 * 2) + " {NoAI:1b}");
			}
			server.runCommand("execute at @p run summon bat ~4 ~6 ~22 {NoAI:1b}");
			// Out near the edge of the blast's reach: one flier to be flung, one walker to get Dread.
			server.runCommand("execute at @p run summon bat ~25 ~7 ~34 {NoAI:1b,Tags:[\"edge\"]}");
			server.runCommand("execute at @p run summon zombie ~-25 ~ ~30 {NoAI:1b,Tags:[\"edge\"]}");
			server.runCommand("execute at @p run summon bat ~-4 ~8 ~26 {NoAI:1b}");
			ctx.waitTicks(5);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				for (LivingEntity e : p.level().getEntitiesOfClass(LivingEntity.class, new AABB(p.blockPosition()).inflate(40), e -> e != p)) {
					Terror.frighten(p.level(), e, p.getUUID(), 600);
				}
			});
			ctx.getInput().lookAt(0f, 25f);
			ctx.waitTicks(80);
			server.runOnServer(s -> System.out.println("[aerial] fear after holding=" + FearNuke.fear(s.getPlayerList().getPlayers().get(0).getMainHandItem())));
			// Three die afraid: their fear streams to the bearer.
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				int n = 0;
				for (Mob m : p.level().getEntitiesOfClass(Mob.class, new AABB(p.blockPosition()).inflate(40), m -> !(m instanceof Bat) && !m.entityTags().contains("edge"))) {
					if (n++ < 3) m.hurtServer(p.level(), p.damageSources().playerAttack(p), 1000f);
				}
			});
			ctx.waitTicks(6);
			ctx.takeScreenshot("fear_wisps");
			ctx.waitTicks(30);
			server.runOnServer(s -> System.out.println("[aerial] fear after kills=" + FearNuke.fear(s.getPlayerList().getPlayers().get(0).getMainHandItem())));
			ctx.takeScreenshot("fear_smoke");

			// The nuke, 24 blocks out, watched from behind.
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				System.out.println("[aerial] nuke=" + FearNuke.drop(p.level(), p, p.getMainHandItem(), o[0].offset(0, 0, 24)));
			});
			ctx.getInput().lookAt(0f, 5f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("fear_nuke_forming");
			ctx.waitTicks(25);
			ctx.takeScreenshot("fear_nuke_dropped");
			ctx.waitTicks(40);
			ctx.takeScreenshot("fear_nuke_consuming");
			ctx.waitTicks(30);
			ctx.takeScreenshot("fear_nuke_bright");
			ctx.waitTicks(28);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				for (Entity e : p.level().getEntitiesOfClass(Entity.class, new AABB(p.blockPosition()).inflate(80), e -> e.entityTags().contains("edge"))) {
					System.out.println("[aerial] just after the blast " + e.getType().toShortString() + " at " + e.blockPosition() + " v=" + e.getDeltaMovement()
							+ " dread=" + ((LivingEntity) e).hasEffect(ModEffects.DREAD) + " health=" + ((LivingEntity) e).getHealth());
				}
			});
			ctx.takeScreenshot("fear_nuke_blast");
			ctx.waitTicks(10);
			ctx.takeScreenshot("fear_nuke_cloud");
			ctx.waitTicks(60);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				for (Entity e : p.level().getEntitiesOfClass(Entity.class, new AABB(p.blockPosition()).inflate(80), e -> e != p && e instanceof LivingEntity)) {
					System.out.println("[aerial] after blast " + e.getType().toShortString() + " at " + e.blockPosition() + " v=" + e.getDeltaMovement()
							+ " dread=" + ((LivingEntity) e).hasEffect(ModEffects.DREAD));
				}
			});
			ctx.takeScreenshot("fear_nuke_crater");
			count(world, o[0], "after the nuke (air check below)");
			server.runOnServer(s -> {
				ServerLevel level = s.getPlayerList().getPlayers().get(0).level();
				int gone = 0;
				for (BlockPos p : BlockPos.betweenClosed(o[0].offset(-12, -3, 12), o[0].offset(12, -1, 36))) {
					if (level.getBlockState(p).isAir()) gone++;
				}
				System.out.println("[aerial] ground blown away round the nuke: " + gone + " blocks");
			});

			// Dread on the player: yellow hearts.
			server.runCommand("gamemode survival @a");
			server.runCommand("effect give @a lanternring:dread 30");
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("dread_hearts");
		}
	}
}
