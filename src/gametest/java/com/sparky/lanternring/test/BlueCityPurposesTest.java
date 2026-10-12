package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.city.BlueCity;
import com.sparky.lanternring.city.CityBlocks;
import com.sparky.lanternring.city.CityData;
import com.sparky.lanternring.corps.CorpsMobs;
import com.sparky.lanternring.corps.CorpsVillager;
import com.sparky.lanternring.corps.DivingHawk;
import com.sparky.lanternring.corps.FlierHighway;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;

/**
 * The Blue sky city's purposes for the player (J, 2026-10-12, "start all of it"): taming a hawk,
 * the Hawk Whistle, Blue trades, the crown's charging station and Hope boost, a hawk flying you
 * along the highway on autopilot, and domes over the villagers in a Red raid. Prints "PURPOSE ..."
 * lines and throws on anything that doesn't work.
 */
public class BlueCityPurposesTest implements FabricClientGameTest {
	private static void log(String s) {
		System.out.println("PURPOSE " + s);
	}

	private static void check(boolean ok, String what) {
		log((ok ? "ok   " : "FAIL ") + what);
		if (!ok) throw new AssertionError(what);
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer s) {
		return s.getPlayerList().getPlayers().get(0);
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode creative @a");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(40);
			DivingHawk[] hawk = new DivingHawk[1];

			// 1. Taming: feed a wild hawk raw chicken until it takes to you.
			server.runOnServer(s -> {
				ServerPlayer p = player(s);
				DivingHawk h = FlierHighway.DIVING_HAWK.create(p.level(), EntitySpawnReason.COMMAND);
				h.snapTo(p.getX() + 2, p.getY(), p.getZ() + 2, 0f, 0f);
				p.level().addFreshEntity(h);
				p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.CHICKEN, 64));
				for (int i = 0; i < 40 && !h.tamed(); i++) h.mobInteract(p, InteractionHand.MAIN_HAND);
				check(h.tamed() && h.isOwner(p), "a fed hawk takes to its feeder");
				p.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
				hawk[0] = h;
				p.teleportTo(p.getX() + 25, p.getY(), p.getZ());
			});
			ctx.getInput().lookAt(0f, -30f);
			ctx.waitTicks(100);
			server.runOnServer(s -> {
				double d = hawk[0].distanceTo(player(s));
				check(d < 12, "the tamed hawk follows its owner (" + Math.round(d) + " blocks)");
			});
			ctx.takeScreenshot("purpose_tamed_hawk");

			// 2. The whistle: far away it comes as light, and the old hawk goes.
			server.runOnServer(s -> {
				ServerPlayer p = player(s);
				p.teleportTo(p.getX() + 600, p.getY() + 40, p.getZ());
			});
			ctx.waitTicks(40);
			server.runOnServer(s -> {
				ServerPlayer p = player(s);
				ItemStack whistle = new ItemStack(FlierHighway.HAWK_WHISTLE);
				p.setItemInHand(InteractionHand.MAIN_HAND, whistle);
				whistle.getItem().use(p.level(), p, InteractionHand.MAIN_HAND);
			});
			ctx.waitTicks(60);
			server.runOnServer(s -> {
				ServerPlayer p = player(s);
				List<DivingHawk> mine = p.level().getEntitiesOfClass(DivingHawk.class, p.getBoundingBox().inflate(20), h -> h.isOwner(p));
				check(mine.size() == 1, "the whistle brings exactly one hawk (" + mine.size() + ")");
				hawk[0] = mine.getFirst();
			});

			// 3. Blue trades: building blocks from every Blue villager, the whistle in a city with ports.
			BlockPos[] anchor = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = player(s);
				ServerLevel level = p.level();
				CityData.City city = BlueCity.cityFor(level, p.blockPosition());
				BlueCity.buildAll(level, city);
				anchor[0] = city.anchor;
				FlierHighway.buildNow(level, city.anchor);
				CorpsVillager v = CorpsMobs.CORPS_VILLAGER.create(level, EntitySpawnReason.COMMAND);
				v.setCorps(Corps.BLUE);
				v.snapTo(p.getX() + 1, p.getY(), p.getZ(), 0f, 0f);
				level.addFreshEntity(v);
				v.mobInteract(p, InteractionHand.MAIN_HAND);
				p.closeContainer();
				var offers = v.getOffers();
				check(offers.stream().anyMatch(o -> o.getResult().is(CityBlocks.HOPE_QUARTZ_BRICKS.asItem())), "Blue villagers sell Hope Quartz");
				check(offers.stream().anyMatch(o -> o.getResult().is(CityBlocks.SKYSTONE_BRICKS.asItem())), "Blue villagers sell Skystone");
				check(offers.stream().anyMatch(o -> o.getResult().is(CityBlocks.HOPE_LAMP.asItem())), "Blue villagers sell Hope Lamps");
				check(offers.stream().anyMatch(o -> o.getResult().is(FlierHighway.HAWK_WHISTLE)), "a city villager sells the Hawk Whistle");
				v.discard();
			});

			// 4. The crown's charging station: a Red ring charges, a Green ring gets a Hope boost.
			server.runOnServer(s -> {
				ServerPlayer p = player(s);
				ServerLevel level = p.level();
				BlockPos lantern = anchor[0].offset(0, 45, -2);
				check(level.getBlockState(lantern).is(ModRegistry.POWER_BATTERY), "the crown has its Blue lantern");
				p.teleportTo(lantern.getX() + 0.5, lantern.getY(), lantern.getZ() + 1.5);
				BlockHitResult hit = new BlockHitResult(Vec3.atCenterOf(lantern), Direction.SOUTH, lantern, false);
				ItemStack red = Corps.RED.ring();
				PowerRingItem.setCharge(red, 100);
				p.setItemInHand(InteractionHand.MAIN_HAND, red);
				level.getBlockState(lantern).useItemOn(red, level, p, InteractionHand.MAIN_HAND, hit);
				check(PowerRingItem.getCharge(red) == PowerRingItem.MAX_CHARGE, "the crown lantern charges a Red ring");
				ItemStack green = Corps.GREEN.ring();
				PowerRingItem.setCharge(green, 100);
				p.setItemInHand(InteractionHand.MAIN_HAND, green);
				level.getBlockState(lantern).useItemOn(green, level, p, InteractionHand.MAIN_HAND, hit);
				check(PowerRingItem.hopeReserve(green) == PowerRingItem.MAX_CHARGE, "a Green ring gets a full Hope boost");
				PowerRingItem.setCharge(green, PowerRingItem.getCharge(green) - 300);
				check(PowerRingItem.getCharge(green) == PowerRingItem.MAX_CHARGE && PowerRingItem.hopeReserve(green) == PowerRingItem.MAX_CHARGE - 300,
						"spending draws on the boost first");
			});
			ctx.getInput().lookAt(180f, 30f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("purpose_crown_lantern");

			// 5. Autopilot: from a port pad, a city hawk flies you to the port you look toward.
			BlockPos[] ports = new BlockPos[4];
			server.runOnServer(s -> {
				ServerPlayer p = player(s);
				ServerLevel level = p.level();
				List<BlockPos> list = BlueCity.ports(anchor[0]);
				for (int i = 0; i < 4; i++) ports[i] = list.get(i);
				BlockPos pad = ports[0];
				p.teleportTo(pad.getX() + 0.5, pad.getY() + 1, pad.getZ() + 0.5);
				Vec3 to = Vec3.atCenterOf(ports[2]).subtract(p.position());
				p.setYRot((float) Math.toDegrees(Math.atan2(-to.x, to.z)));
				CityData.City city = CityData.get(level).near(anchor[0], 10);
				int hawks = level.getEntitiesOfClass(DivingHawk.class, new AABB(anchor[0]).inflate(120), h -> !h.tamed()).size();
				log("city hawks: " + hawks);
				check(FlierHighway.requestRide(level, p, city), "a city hawk answers a ride request");
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			boolean rode = false, arrived = false;
			for (int i = 0; i < 40 && !arrived; i++) {
				ctx.waitTicks(20);
				boolean riding = server.computeOnServer(s -> player(s).getVehicle() instanceof DivingHawk);
				if (riding && !rode) ctx.takeScreenshot("purpose_autopilot_ride");
				rode |= riding;
				if (rode && !riding) arrived = true;
			}
			check(rode, "the hawk picks the player up");
			double off = server.computeOnServer(s -> Math.sqrt(player(s).blockPosition().distSqr(ports[2].above())));
			check(arrived && off < 6, "the hawk sets the player down at the far port (" + Math.round(off) + " blocks off)");
			ctx.takeScreenshot("purpose_autopilot_arrived");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// 6. A Red raid: Blue villagers raise domes over the villagers who can't fight.
			BlockPos[] ground = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = player(s);
				ServerLevel level = p.level();
				BlockPos g = new BlockPos(anchor[0].getX() + 90, 0, anchor[0].getZ());
				g = level.getHeightmapPos(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING, g);
				ground[0] = g;
				for (BlockPos pos : BlockPos.betweenClosed(g.offset(-12, 0, -12), g.offset(12, 12, 12))) level.setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
				CorpsVillager blue = CorpsMobs.CORPS_VILLAGER.create(level, EntitySpawnReason.COMMAND);
				blue.setCorps(Corps.BLUE);
				blue.snapTo(g.getX() + 3.5, g.getY(), g.getZ() + 0.5, 0f, 0f);
				level.addFreshEntity(blue);
				Villager plain = EntityTypes.VILLAGER.create(level, EntitySpawnReason.COMMAND);
				plain.snapTo(g.getX() - 3.5, g.getY(), g.getZ() + 0.5, 0f, 0f);
				plain.setNoAi(true);
				level.addFreshEntity(plain);
				var raider = CorpsMobs.SKY_RAIDER.create(level, EntitySpawnReason.COMMAND);
				raider.snapTo(g.getX(), g.getY() + 14, g.getZ() + 20, 0f, 0f);
				level.addFreshEntity(raider);
				p.teleportTo(g.getX() + 0.5, g.getY() + 6, g.getZ() - 14);
			});
			ctx.getInput().lookAt(0f, 20f);
			ctx.waitTicks(50);
			ctx.takeScreenshot("purpose_raid_dome");
			server.runOnServer(s -> {
				ServerLevel level = player(s).level();
				BlockPos c = ground[0].offset(-4, 0, 0);
				int shell = 0;
				for (BlockPos pos : BlockPos.betweenClosed(c.offset(-4, 0, -4), c.offset(4, 4, 4))) {
					if (level.getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) shell++;
				}
				check(shell > 20, "a dome of blue light covers the villager in the raid (" + shell + " blocks)");
			});
			server.runCommand("kill @e[type=lanternring:sky_raider]");
			log("PASS all city purposes work");
		}
	}
}
