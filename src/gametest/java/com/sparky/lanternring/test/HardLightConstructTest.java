package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Hope;
import com.sparky.lanternring.corps.CorpsGolem;
import com.sparky.lanternring.corps.CorpsMobs;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/** The Blue Lantern's hard light constructs from J's sheets: villager constructs and golems, front and back, day and night. */
public class HardLightConstructTest implements FabricClientGameTest {
	private static <T extends Mob> T place(ServerPlayer p, T mob, Vec3 at, float yaw) {
		mob.snapTo(at.x, at.y, at.z, yaw, 0f);
		mob.setYHeadRot(yaw);
		mob.setYBodyRot(yaw);
		mob.setNoAi(true);
		p.level().addFreshEntity(mob);
		return mob;
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos b = p.blockPosition().above(6);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-30, -3, -30), b.offset(30, 30, 30))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				Vec3 o = Vec3.atBottomCenterOf(b);
				p.teleportTo(o.x, o.y + 0.6, o.z);
				// Villager constructs (front and back) on the left, the golems (front and back) on the right.
				for (int i = 0; i < 2; i++) {
					// A Villager Spark builder: a villager with the Blue Lantern's mark, still a construct.
					Villager v = EntityTypes.VILLAGER.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
					v.setAttached(Hope.MARK, new Hope.Mark(p.level().getGameTime(), false, b));
					place(p, v, o.add(3.2 - i * 1.2, 0, 4.0), i == 0 ? 0f : 180f);
				}
				IronGolem g = EntityTypes.IRON_GOLEM.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
				g.setAttached(Hope.MARK, new Hope.Mark(p.level().getGameTime(), true, b));
				place(p, g, o.add(0.2, 0, 5.0), 0f);
				CorpsGolem cg = CorpsMobs.CORPS_GOLEM.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
				cg.setup(Corps.BLUE, b);
				cg.setCustomName(null);
				place(p, cg, o.add(-3.0, 0, 5.5), 180f);
			});
			ctx.getInput().lookAt(0f, 14f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("hard_light_constructs_day");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("hard_light_constructs_night");
		}
	}
}
