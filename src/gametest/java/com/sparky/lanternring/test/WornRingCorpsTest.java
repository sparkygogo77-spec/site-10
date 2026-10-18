package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.RingSlot;
import com.sparky.lanternring.client.CorpsTint;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;

/**
 * J's bug (2026-10-16): a worn Yellow ring kept a green gem, because the square, crown and round-face
 * rings ship green textures only. Each corps' worn ring should show its own colour: photographs P03 (the
 * default) worn on an empty hand for every corps, in first and third person.
 */
public class WornRingCorpsTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		Identifier p03 = LanternRing.id("textures/entity/bb/ring_sq_p03.png");
		Identifier yellow = ctx.computeOnClient(mc -> CorpsTint.textureOrMade(p03, Corps.YELLOW));
		if (yellow.equals(p03)) throw new AssertionError("The Yellow P03 ring should get a recoloured texture, not the green one");
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(40);
			// An empty main hand (the What's New book lands in the hotbar on join).
			world.getServer().runCommand("clear @a");
			LabSettings lab = LabSettings.get();
			lab.handPose = LabSettings.HandPose.KNUCKLES_IN;
			lab.ringModel = LabSettings.RingModel.P03;
			ctx.getInput().lookAt(0f, 15f);
			for (CameraType camera : new CameraType[] {CameraType.FIRST_PERSON, CameraType.THIRD_PERSON_FRONT}) {
				ctx.runOnClient(mc -> mc.options.setCameraType(camera));
				for (Corps corps : new Corps[] {Corps.GREEN, Corps.YELLOW, Corps.RED, Corps.BLUE, Corps.VIOLET, Corps.ORANGE}) {
					world.getServer().runOnServer(server -> RingSlot.setWorn(player(server), corps.ring()));
					ctx.waitTicks(50);
					ctx.takeScreenshot("worn_ring_" + corps.getSerializedName() + (camera == CameraType.FIRST_PERSON ? "_fp" : "_tp"));
				}
				ctx.getInput().lookAt(0f, 0f);
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
		}
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
