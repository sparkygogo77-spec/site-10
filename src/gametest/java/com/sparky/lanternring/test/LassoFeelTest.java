package com.sparky.lanternring.test;

import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.animal.cow.Cow;
import net.minecraft.world.phys.Vec3;

/**
 * Lasso physics and controls, with a cow that has its AI on: the reel-in doesn't overshoot into the
 * bearer, the bubble settles after a swing without wobbling, the client draws the cow where the
 * server put it (not three ticks behind), the mouse wheel moves the catch out and in (the hotbar
 * stays put), jumping keeps the catch, and left-click with a lantern in the off hand pushes the
 * catch out instead of dropping it for a charge.
 */
public class LassoFeelTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("effect give @a resistance 1000 10 true");
			ctx.waitTicks(40);
			world.getServer().runCommand("execute at @p run fill ~-30 ~-1 ~-30 ~30 ~-1 ~60 grass_block");
			world.getServer().runCommand("execute at @p run fill ~-30 ~ ~-30 ~30 ~20 ~60 air");
			world.getServer().runCommand("kill @e[type=!player]");
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.MODE, RingMode.TETHER.ordinal()));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			world.getServer().runCommand("execute at @p run summon minecraft:cow ~ ~ ~10");
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(10);

			// Catch and reel in: the bubble comes to its hold distance without swinging past it.
			ctx.getInput().holdKey(o -> o.keyUse);
			List<Double> reel = new ArrayList<>();
			for (int i = 0; i < 30; i++) {
				ctx.waitTicks(1);
				reel.add(world.getServer().computeOnServer(s -> {
					Vec3 c = Lasso.heldCenter(player(s));
					return c == null ? Double.NaN : horizontal(c.subtract(player(s).getEyePosition()));
				}));
			}
			double rest = reel.get(reel.size() - 1);
			double closest = reel.stream().filter(d -> !d.isNaN()).min(Double::compare).orElse(Double.NaN);
			System.out.println(String.format(Locale.ROOT, "[lasso feel] reel: rest %.2f closest %.2f", rest, closest));
			if (Double.isNaN(rest)) throw new AssertionError("The lasso didn't catch the cow");
			if (rest - closest > 0.35) throw new AssertionError("Reel-in overshot by " + (rest - closest) + " blocks");
			ctx.takeScreenshot("lasso_feel_held");

			// A smooth swing to the right; the client keeps up with the server and it settles quickly.
			double worstLag = 0;
			for (int i = 1; i <= 10; i++) {
				ctx.getInput().lookAt(i * 9f, 0f);
				ctx.waitTicks(1);
				worstLag = Math.max(worstLag, lag(ctx, world));
			}
			ctx.takeScreenshot("lasso_feel_swing");
			List<Vec3> settle = new ArrayList<>();
			for (int i = 0; i < 15; i++) {
				ctx.waitTicks(1);
				settle.add(world.getServer().computeOnServer(s -> Lasso.heldCenter(player(s))));
			}
			Vec3 end = settle.get(settle.size() - 1);
			double wobble = 0;
			for (int i = 5; i < settle.size(); i++) wobble = Math.max(wobble, settle.get(i).distanceTo(end));
			System.out.println(String.format(Locale.ROOT, "[lasso feel] swing: client up to %.0f ticks behind, wobble after 5 ticks %.2f", worstLag, wobble));
			if (worstLag > 2) throw new AssertionError("The client drew the caught cow " + worstLag + " ticks behind the server");
			if (wobble > 0.15) throw new AssertionError("The bubble was still wobbling " + wobble + " blocks after the swing");

			// The mouse wheel: up pushes it out, down pulls it back in, and the hotbar slot doesn't change.
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(15);
			int slot = ctx.computeOnClient(mc -> mc.player.getInventory().getSelectedSlot());
			double before = held(world);
			for (int i = 0; i < 4; i++) {
				ctx.getInput().scroll(1);
				ctx.waitTicks(1);
			}
			ctx.waitTicks(20);
			double out = held(world);
			ctx.takeScreenshot("lasso_feel_scrolled_out");
			for (int i = 0; i < 2; i++) {
				ctx.getInput().scroll(-1);
				ctx.waitTicks(1);
			}
			ctx.waitTicks(20);
			double in = held(world);
			int slotAfter = ctx.computeOnClient(mc -> mc.player.getInventory().getSelectedSlot());
			System.out.println(String.format(Locale.ROOT, "[lasso feel] wheel: %.2f -> out %.2f -> in %.2f, slot %d -> %d", before, out, in, slot, slotAfter));
			if (!(out > before + 3)) throw new AssertionError("Scrolling up didn't push the catch out (" + before + " -> " + out + ")");
			if (!(in < out - 1.5)) throw new AssertionError("Scrolling down didn't pull the catch in (" + out + " -> " + in + ")");
			if (slot != slotAfter) throw new AssertionError("Scrolling with a catch changed the hotbar slot");

			// Jumping keeps the catch where it is.
			ctx.getInput().pressKey(o -> o.keyJump);
			ctx.waitTicks(20);
			ctx.getInput().pressKey(o -> o.keyJump);
			ctx.waitTicks(20);
			double afterJump = held(world);
			System.out.println(String.format(Locale.ROOT, "[lasso feel] jump: %.2f -> %.2f", in, afterJump));
			if (Double.isNaN(afterJump) || Math.abs(afterJump - in) > 0.5) throw new AssertionError("Jumping moved or dropped the catch (" + in + " -> " + afterJump + ")");

			// With the lantern in the off hand, left-click pushes the catch out and keeps it.
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.waitTicks(5);
			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(15);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			ctx.waitTicks(10);
			double pushed = held(world);
			System.out.println(String.format(Locale.ROOT, "[lasso feel] lantern left-click: %.2f -> %.2f", afterJump, pushed));
			if (Double.isNaN(pushed)) throw new AssertionError("Left-click with a lantern in the off hand dropped the catch");
			if (!(pushed > afterJump + 1)) throw new AssertionError("Left-click with a lantern in the off hand didn't push the catch out");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(20);
		}
	}

	private static final List<Vec3> HISTORY = new ArrayList<>();

	/** How many server ticks behind the client draws the cow. */
	private static double lag(ClientGameTestContext ctx, TestSingleplayerContext world) {
		Vec3 server = world.getServer().computeOnServer(s -> {
			for (Entity e : player(s).level().getAllEntities()) if (e instanceof Cow) return e.position();
			return null;
		});
		Vec3 client = ctx.computeOnClient(mc -> {
			for (Entity e : mc.level.entitiesForRendering()) if (e instanceof Cow) return e.position();
			return null;
		});
		if (server == null || client == null) return Double.NaN;
		HISTORY.add(server);
		// Ticks back to the server spot the client is drawing (the test reads the server a tick or so
		// ahead of what has reached the client; vanilla's easing put it three ticks back).
		for (int i = HISTORY.size() - 1; i >= 0; i--) {
			if (HISTORY.get(i).distanceTo(client) < 0.05) return HISTORY.size() - 1 - i;
		}
		return HISTORY.size();
	}

	/** Distance from the bearer's eyes to the held bubble, NaN with nothing held. */
	private static double held(TestSingleplayerContext world) {
		return world.getServer().computeOnServer(s -> {
			Vec3 c = Lasso.heldCenter(player(s));
			return c == null ? Double.NaN : c.distanceTo(player(s).getEyePosition());
		});
	}

	private static double horizontal(Vec3 v) {
		return Math.sqrt(v.x * v.x + v.z * v.z);
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
