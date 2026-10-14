package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Dismissal;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.client.LabSettings;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

/**
 * J's construct texture picks (Ring Lab rows Constructs, Wall bricks, Blue and Yellow constructs): five
 * 8 x 8 panels side by side, green constructs, green Wall bricks, Blue constructs, Blue bricks and Yellow
 * constructs. Shots with the defaults, with other picks, then the green panel dismissed mid-dissolve.
 */
public class ConstructPicksTest implements FabricClientGameTest {
	private static final Object[][] PANELS = {
			{ModRegistry.LIGHT_CONSTRUCT, Corps.GREEN}, {ModRegistry.CONSTRUCT_BRICK, Corps.GREEN},
			{ModRegistry.LIGHT_CONSTRUCT, Corps.BLUE}, {ModRegistry.CONSTRUCT_BRICK, Corps.BLUE},
			{ModRegistry.LIGHT_CONSTRUCT, Corps.YELLOW}};

	/** (Re)places the panels. */
	private static void build(TestSingleplayerContext world, List<BlockPos> green, List<BlockPos> others) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			List<BlockPos> all = new ArrayList<>(green);
			all.addAll(others);
			for (int k = 0; k < all.size(); k++) {
				Object[] panel = PANELS[k < green.size() ? 0 : 1 + (k - green.size()) / 64];
				p.level().setBlock(all.get(k), Blocks.AIR.defaultBlockState(), 2);
				// skip onPlace: no lifetime, these aren't a real power's (a brick checks for its wall)
				p.level().setBlock(all.get(k), ((Block) panel[0]).defaultBlockState().setValue(Corps.PROPERTY, (Corps) panel[1]),
						Block.UPDATE_CLIENTS | Block.UPDATE_SKIP_ON_PLACE);
			}
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			List<BlockPos> green = new ArrayList<>(), others = new ArrayList<>();
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getAbilities().flying = true;
				BlockPos b = p.blockPosition().above(4);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-30, -3, -24), b.offset(30, 20, 30))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				for (int i = 0; i < PANELS.length; i++) {
					for (int x = 0; x < 8; x++) {
						for (int y = 0; y < 8; y++) {
							BlockPos pos = new BlockPos(b.getX() - 23 + i * 9 + x, b.getY() + y, b.getZ() + 12);
							(i == 0 ? green : others).add(pos);
						}
					}
				}
				p.teleportTo(b.getX() + 0.5, b.getY() + 4, b.getZ() - 14);
			});
			build(world, green, others);
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("construct_picks_default");
			ctx.waitTicks(40);
			ctx.takeScreenshot("construct_picks_default_later");
			build(world, green, others);
			pick(ctx, LabSettings.ConstructLook.H1_NEON, LabSettings.WallLook.BR1_LIME, LabSettings.BlueLook.BR1, LabSettings.YellowLook.N3);
			ctx.takeScreenshot("construct_picks_h1_lime_br1_n3");
			build(world, green, others);
			pick(ctx, LabSettings.ConstructLook.H2_NEON, LabSettings.WallLook.BRD_NEON, LabSettings.BlueLook.CLASSIC, LabSettings.YellowLook.G2N_AMBER);
			ctx.takeScreenshot("construct_picks_h2_brd_classic_amber");
			build(world, green, others);
			pick(ctx, LabSettings.ConstructLook.HW_EMERALD, LabSettings.WallLook.BR1_EMERALD, LabSettings.BlueLook.H1, LabSettings.YellowLook.N3_AMBER);
			ctx.takeScreenshot("construct_picks_hw_emerald");
			// Close up on the HW panel, then dismiss it into the player: it dissolves piece by piece.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos c = green.get(green.size() / 2);
				p.teleportTo(c.getX() + 0.5, c.getY() + 0.5, c.getZ() - 7);
			});
			build(world, green, others);
			ctx.waitTicks(20);
			ctx.takeScreenshot("construct_picks_hw_close");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				Dismissal.blocks(p.level(), p, green, s -> s.is(ModRegistry.LIGHT_CONSTRUCT));
			});
			ctx.waitTicks(5);
			ctx.takeScreenshot("construct_picks_dissolve_a");
			ctx.waitTicks(6);
			ctx.takeScreenshot("construct_picks_dissolve_b");
			ctx.waitTicks(30);
			ctx.takeScreenshot("construct_picks_dissolved");
			pick(ctx, LabSettings.ConstructLook.W1_NEON, LabSettings.WallLook.BR1_JADE, LabSettings.BlueLook.H1, LabSettings.YellowLook.G2N);
			ctx.takeScreenshot("construct_picks_w1_half_opacity");

			// The Anvil falls as stretched block displays: the strip keeps its size and no block grid shows.
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.ANVIL.ordinal());
				BlockPos c = green.get(0);
				p.teleportTo(c.getX() + 4.5, c.getY() + 2, c.getZ() - 20);
			});
			ctx.getInput().lookAt(0f, 20f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(12);
			ctx.getInput().releaseKey(o -> o.keyUse);
			for (int i = 1; i <= 3; i++) {
				ctx.waitTicks(5);
				ctx.takeScreenshot("construct_picks_anvil_drop_" + i);
			}
			ctx.waitTicks(30);
			ctx.takeScreenshot("construct_picks_anvil_landed");

			// J's X3D1 glass aura (2026-10-14) on the drill tank: cut out like glass, and the turned drill
			// pieces drawn as one shell instead of full block models.
			pick(ctx, LabSettings.ConstructLook.X3D1_EMERALD, LabSettings.WallLook.BR1_JADE, LabSettings.BlueLook.H1, LabSettings.YellowLook.G2N);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getMainHandItem().set(ModComponents.ANVIL_SIZE, 3);
				BlockPos c = green.get(0);
				p.teleportTo(c.getX() + 24.5, c.getY() + 2, c.getZ() - 20);
			});
			ctx.getInput().lookAt(0f, 7f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(12);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().lookAt(0f, -12f);
			ctx.waitTicks(15);
			ctx.takeScreenshot("construct_picks_x3d1_tank_building");
			for (int i = 1; i <= 4; i++) {
				ctx.waitTicks(8);
				ctx.takeScreenshot("construct_picks_x3d1_tank_drop_" + i);
			}
			ctx.waitTicks(30);
			ctx.takeScreenshot("construct_picks_x3d1_tank_landed");

			// A held Dome seen from inside, by day and night: see-through, not a washed-out glowing blob.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.DOME.ordinal());
				BlockPos c = green.get(0);
				p.teleportTo(c.getX() + 4.5, c.getY(), c.getZ() - 6);
			});
			ctx.getInput().lookAt(0f, -10f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(25);
			ctx.takeScreenshot("construct_picks_dome_day");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("construct_picks_dome_night");
			ctx.getInput().releaseKey(o -> o.keyUse);
		}
	}

	private static void pick(ClientGameTestContext ctx, LabSettings.ConstructLook c, LabSettings.WallLook w,
			LabSettings.BlueLook b, LabSettings.YellowLook y) {
		ctx.runOnClient(mc -> {
			LabSettings s = LabSettings.get();
			s.constructLook = c;
			s.wallLook = w;
			s.blueLook = b;
			s.yellowLook = y;
		});
		ctx.waitTicks(40);
	}
}
