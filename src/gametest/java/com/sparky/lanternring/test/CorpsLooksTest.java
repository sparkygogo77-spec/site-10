package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
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
 * J's per-corps construct looks from the Blender kits (Ring Lab rows Red, Yellow, Violet and Blue constructs):
 * six 6 x 6 panels (Red construct and Wall brick, Yellow, Violet, Blue construct and brick) with each set of
 * picks, a green panel with each round 6 pick, then the placed Red Lantern and Blue Lantern from the front and the back.
 */
public class CorpsLooksTest implements FabricClientGameTest {
	private static final Object[][] PANELS = {
			{ModRegistry.LIGHT_CONSTRUCT, Corps.RED}, {ModRegistry.CONSTRUCT_BRICK, Corps.RED},
			{ModRegistry.LIGHT_CONSTRUCT, Corps.YELLOW}, {ModRegistry.LIGHT_CONSTRUCT, Corps.VIOLET},
			{ModRegistry.LIGHT_CONSTRUCT, Corps.BLUE}, {ModRegistry.CONSTRUCT_BRICK, Corps.BLUE},
			{ModRegistry.LIGHT_CONSTRUCT, Corps.GREEN}};

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			List<BlockPos> centre = new ArrayList<>();
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getAbilities().flying = true;
				BlockPos b = p.blockPosition().above(4);
				centre.add(b);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-30, -3, -24), b.offset(30, 20, 30))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				for (int i = 0; i < PANELS.length; i++) {
					for (int x = 0; x < 6; x++) {
						for (int y = 0; y < 6; y++) {
							BlockPos pos = new BlockPos(b.getX() - 23 + i * 8 + x, b.getY() + y, b.getZ() + 12);
							p.level().setBlock(pos, ((Block) PANELS[i][0]).defaultBlockState().setValue(Corps.PROPERTY, (Corps) PANELS[i][1]),
									Block.UPDATE_CLIENTS | Block.UPDATE_SKIP_ON_PLACE);
						}
					}
				}
				p.teleportTo(b.getX() + 0.5, b.getY() + 3, b.getZ() - 14);
			});
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("corps_looks_defaults");
			pick(ctx, LabSettings.RedLook.R2, LabSettings.YellowLook.Y2, LabSettings.VioletLook.V3, LabSettings.BlueLook.B2);
			ctx.takeScreenshot("corps_looks_r2_y2_v3_b2");
			pick(ctx, LabSettings.RedLook.R1, LabSettings.YellowLook.Y3, LabSettings.VioletLook.V1, LabSettings.BlueLook.B3);
			ctx.takeScreenshot("corps_looks_r1_y3_v1_b3");
			for (LabSettings.YellowLook y : new LabSettings.YellowLook[] {LabSettings.YellowLook.W1, LabSettings.YellowLook.H1, LabSettings.YellowLook.HW}) {
				pick(ctx, LabSettings.RedLook.R1, y, LabSettings.VioletLook.V1, LabSettings.BlueLook.H1);
				ctx.takeScreenshot("corps_looks_yellow_" + y.name().toLowerCase());
			}
			for (LabSettings.ConstructLook look : new LabSettings.ConstructLook[] {LabSettings.ConstructLook.X5_EMERALD,
					LabSettings.ConstructLook.X5_NEON, LabSettings.ConstructLook.X3_EMERALD, LabSettings.ConstructLook.X1_EMERALD}) {
				ctx.runOnClient(mc -> LabSettings.get().constructLook = look);
				ctx.waitTicks(40);
				ctx.takeScreenshot("corps_looks_green_" + look.name().toLowerCase());
			}
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(20);
			ctx.takeScreenshot("corps_looks_night");
			// Close on the Red construct panel at night with R2 bloodfire (J: faster, finer lines), two moments apart.
			ctx.runOnClient(mc -> LabSettings.get().redLook = LabSettings.RedLook.R2);
			BlockPos red = centre.get(0);
			world.getServer().runCommand("tp @p " + (red.getX() - 20) + " " + (red.getY() + 2.5) + " " + (red.getZ() + 7) + " 0 0");
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("corps_looks_r2_close_a");
			ctx.waitTicks(15);
			ctx.takeScreenshot("corps_looks_r2_close_b");
			world.getServer().runCommand("time set 6000");

			// The two fixed lantern models, placed, from the front and from the back.
			BlockPos b = centre.get(0);
			for (Corps corps : new Corps[] {Corps.RED, Corps.BLUE}) {
				String name = corps.getSerializedName();
				world.getServer().runCommand("setblock " + b.getX() + " " + b.getY() + " " + (b.getZ() - 4)
						+ " lanternring:power_battery[corps=" + name + "]");
				world.getServer().runCommand("tp @p " + (b.getX() + 0.5) + " " + (b.getY() + 0.3) + " " + (b.getZ() - 6.5) + " 0 15");
				ctx.getInput().lookAt(0f, 15f);
				ctx.waitTicks(30);
				ctx.takeScreenshot("corps_looks_" + name + "_lantern_front");
				world.getServer().runCommand("tp @p " + (b.getX() + 0.5) + " " + (b.getY() + 0.3) + " " + (b.getZ() - 1.5) + " 180 15");
				ctx.getInput().lookAt(180f, 15f);
				ctx.waitTicks(30);
				ctx.takeScreenshot("corps_looks_" + name + "_lantern_back");
				world.getServer().runCommand("setblock " + b.getX() + " " + b.getY() + " " + (b.getZ() - 4) + " air");
			}
		}
	}

	private static void pick(ClientGameTestContext ctx, LabSettings.RedLook r, LabSettings.YellowLook y,
			LabSettings.VioletLook v, LabSettings.BlueLook bl) {
		ctx.runOnClient(mc -> {
			LabSettings s = LabSettings.get();
			s.redLook = r;
			s.yellowLook = y;
			s.violetLook = v;
			s.blueLook = bl;
		});
		ctx.waitTicks(40);
	}
}
