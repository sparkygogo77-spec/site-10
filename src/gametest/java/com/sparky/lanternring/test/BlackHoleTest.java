package com.sparky.lanternring.test;

import com.sparky.lanternring.BlackHoles;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import com.sparky.lanternring.client.BlackHoleFx;

/** The Black Hole opening over a patch of sand and leaves with cows and dropped items about, by day and night. */
public class BlackHoleTest implements FabricClientGameTest {
	private static BlockPos feet;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.BLACK_HOLE.ordinal());
				feet = p.blockPosition();
			});
			RingTuning.BLACK_HOLE_TIME.set(6);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// Size 2, by day, from the bearer's eyes.
			scene(world);
			ctx.getInput().lookAt(0f, 5f);
			ctx.waitTicks(20);
			open(ctx, world, 1, "day");

			// Size 3 at night, seen from the side in third person.
			world.getServer().runCommand("time set 18000");
			scene(world);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 5f);
			ctx.waitTicks(20);
			open(ctx, world, 2, "night");

			// Size 1, close up.
			world.getServer().runCommand("time set 6000");
			scene(world);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 12f);
			ctx.waitTicks(20);
			open(ctx, world, 0, "small");

			// Size 3 opened a few blocks away and left to feed: the core hides what falls in, the
			// screen round it goes dark and its light grows brighter as it lives and eats.
			RingTuning.BLACK_HOLE_TIME.set(10);
			scene(world);
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(20);
			close(ctx, world);
		}
	}

	/** Holds right-click, left-clicks clicks times to pick the size, lets go and watches it through. */
	private static void open(ClientGameTestContext ctx, TestSingleplayerContext world, int clicks, String name) {
		world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.BLACK_HOLE_SIZE, 1));
		ctx.waitTicks(2);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(2);
		for (int i = 0; i < clicks; i++) {
			ctx.getInput().pressKey(o -> o.keyAttack);
			ctx.waitTicks(2);
		}
		ctx.waitTicks(12);
		ctx.takeScreenshot(name + "_aim");
		ctx.getInput().releaseKey(o -> o.keyUse);
		int[] at = {3, 12, 25, 45, 70, 100, 130};
		int waited = 0;
		for (int t : at) {
			ctx.waitTicks(t - waited);
			waited = t;
			ctx.takeScreenshot(name + "_t" + t);
			mobs(world, name + " t" + t);
		}
		int end = BlackHoles.GROW + RingTuning.BLACK_HOLE_TIME.ticks() + BlackHoles.COLLAPSE;
		ctx.waitTicks(end - waited - 4);
		ctx.takeScreenshot(name + "_collapsing");
		ctx.waitTicks(6);
		ctx.takeScreenshot(name + "_flash");
		ctx.waitTicks(40);
		ctx.takeScreenshot(name + "_after");
		mobs(world, name + " after");
	}

	private static void close(ClientGameTestContext ctx, TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.BLACK_HOLE_SIZE, 1));
		ctx.waitTicks(2);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(2);
		for (int i = 0; i < 2; i++) {
			ctx.getInput().pressKey(o -> o.keyAttack);
			ctx.waitTicks(2);
		}
		ctx.waitTicks(10);
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(5);
		Vec3 center = ctx.computeOnClient(mc -> BlackHoleFx.nearestCenter(mc.player.position()));
		// Stand back 12 blocks, facing it, then come up to 5 blocks away.
		standOff(world, center, 12);
		int[] at = {25, 90, 160, 210};
		int waited = 5;
		for (int t : at) {
			ctx.waitTicks(t - waited);
			waited = t;
			ctx.takeScreenshot("close_t" + t);
			if (t == 90) standOff(world, center, 5);
		}
		mobs(world, "close");
	}

	/** Puts the player dist blocks back from center (toward -z, a little above), looking at it. */
	private static void standOff(TestSingleplayerContext world, Vec3 center, double dist) {
		if (center == null) return;
		Vec3 eye = center.add(0, dist * 0.15, -dist);
		world.getServer().runCommand(String.format(java.util.Locale.ROOT, "tp @p %.2f %.2f %.2f facing %.2f %.2f %.2f",
				eye.x, eye.y - 1.62, eye.z, center.x, center.y, center.z));
	}

	/** A flat patch of grass with sand and leaves ahead, cows standing about and some dropped items. */
	private static void scene(TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = player(server);
			var level = p.level();
			for (var e : level.getEntitiesOfClass(net.minecraft.world.entity.Entity.class, new AABB(feet).inflate(60), e -> !(e instanceof ServerPlayer))) e.discard();
			for (int x = -20; x <= 20; x++) {
				for (int z = 0; z <= 40; z++) {
					for (int y = 0; y < 12; y++) level.setBlock(feet.offset(x, y, z), Blocks.AIR.defaultBlockState(), 2);
					level.setBlock(feet.offset(x, -1, z), (x * x + (z - 18) * (z - 18) < 20) ? Blocks.SAND.defaultBlockState() : Blocks.GRASS_BLOCK.defaultBlockState(), 2);
					if ((x + z) % 7 == 0 && Math.abs(x) > 3) level.setBlock(feet.offset(x, 0, z), Blocks.SHORT_GRASS.defaultBlockState(), 2);
				}
			}
			for (int x = 5; x <= 7; x++) for (int y = 0; y <= 2; y++) for (int z = 14; z <= 16; z++) level.setBlock(feet.offset(x, y, z), Blocks.OAK_LEAVES.defaultBlockState(), 2);
			level.setBlock(feet.offset(-6, 0, 20), Blocks.STONE.defaultBlockState(), 2);
		});
		world.getServer().runCommand("execute at @p run summon cow ~-4 ~ ~14");
		world.getServer().runCommand("execute at @p run summon cow ~3 ~ ~22");
		world.getServer().runCommand("execute at @p run summon pig ~-2 ~ ~20");
		world.getServer().runCommand("execute at @p run summon zombie ~6 ~ ~24 {NoAI:0b,PersistenceRequired:1b}");
		world.getServer().runCommand("execute at @p run summon item ~1 ~ ~16 {Item:{id:\"minecraft:diamond\",count:3}}");
		world.getServer().runCommand("execute at @p run summon item ~-3 ~ ~19 {Item:{id:\"minecraft:apple\",count:5}}");
	}

	private static void mobs(TestSingleplayerContext world, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = player(server);
			StringBuilder out = new StringBuilder();
			for (LivingEntity e : p.level().getEntitiesOfClass(LivingEntity.class, new AABB(feet).inflate(60), e -> e != p)) {
				out.append(String.format(" %s@%.1f,%.1f,%.1f hp%.0f;", e.getType().toShortString(), e.getX() - feet.getX(), e.getY() - feet.getY(), e.getZ() - feet.getZ(), e.getHealth()));
			}
			int eaten = 0;
			for (int x = -20; x <= 20; x++) for (int z = 0; z <= 40; z++) for (int y = -4; y <= -1; y++) {
				if (p.level().getBlockState(feet.offset(x, y, z)).isAir()) eaten++;
			}
			System.out.println("[black-hole] " + when + ": ground blocks gone " + eaten + ";" + out);
		});
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
