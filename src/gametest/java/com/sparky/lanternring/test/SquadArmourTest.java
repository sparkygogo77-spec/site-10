package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.BlueRavager;
import com.sparky.lanternring.corps.BlueSquad;
import com.sparky.lanternring.corps.CorpsVillager;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** The rescue squad in J's B2 hard-light armour, and the rider's ravager in its R2 shell, close up. */
public class SquadArmourTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			BlockPos[] lantern = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos b = p.blockPosition().above(6);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-30, -3, -30), b.offset(30, 25, 30))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				lantern[0] = b.immutable();
				p.level().setBlock(b, ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, Corps.BLUE), 3);
				p.teleportTo(b.getX() - 12.5, b.getY() + 4, b.getZ() + 0.5);
			});
			ctx.getInput().lookAt(-90f, 15f);
			ctx.waitTicks(20);
			world.getServer().runOnServer(server -> BlueSquad.callOut(server.getPlayerList().getPlayers().get(0).level(), lantern[0]));
			ctx.waitTicks(140);
			ctx.takeScreenshot("squad_armour_wide");
			List<Integer> ids = new ArrayList<>();
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				AABB box = new AABB(lantern[0]).inflate(40);
				for (CorpsVillager v : p.level().getEntitiesOfClass(CorpsVillager.class, box, CorpsVillager::inSquad)) {
					ids.add(v.getId());
					System.out.println("[SquadArmourTest] " + v.squadRole() + (v.flying() ? " flying" : "")
							+ (v.getVehicle() instanceof BlueRavager ? " mounted" : ""));
				}
			});
			for (int i = 0; i < Math.min(ids.size(), 6); i++) {
				int id = ids.get(i);
				for (int side = 0; side < 2; side++) {
					float[] look = new float[2];
					int s = side;
					world.getServer().runOnServer(server -> {
						ServerPlayer p = server.getPlayerList().getPlayers().get(0);
						Entity e = p.level().getEntity(id);
						if (e == null) return;
						Entity target = e.getVehicle() != null ? e.getVehicle() : e;
						float dist = target instanceof BlueRavager ? 6f : 3f;
						// In front, then from the back-right.
						float yaw = target.getYRot() + (s == 0 ? 0 : 140);
						Vec3 dir = Vec3.directionFromRotation(0, yaw);
						Vec3 eye = e.position().add(0, 1.0, 0);
						Vec3 at = eye.add(dir.scale(dist)).add(0, 0.4, 0);
						p.teleportTo(at.x, at.y - p.getEyeHeight(), at.z);
						Vec3 d = eye.subtract(at);
						look[0] = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
						look[1] = (float) (-Mth.atan2(d.y, d.horizontalDistance()) * Mth.RAD_TO_DEG);
					});
					ctx.getInput().lookAt(look[0], look[1]);
					ctx.waitTicks(3);
					ctx.takeScreenshot("squad_armour_" + i + "_" + side);
				}
			}
		}
	}
}
