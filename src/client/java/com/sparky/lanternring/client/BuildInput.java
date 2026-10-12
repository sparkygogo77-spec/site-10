package com.sparky.lanternring.client;

import com.sparky.lanternring.Builds;
import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
import com.sparky.lanternring.net.BuildAreaPayload;
import com.sparky.lanternring.net.BuildStatePayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * The bearer's side of the Build mode (see Builds): while a build is being chosen, left-click
 * shows the next design (crouch: the one before) instead of mining, the mouse wheel scrolls designs
 * (crouch: their materials); and every client traces the
 * areas it's told about on the ground in glowing motes, like the Anvil's drill bit marker.
 */
public final class BuildInput {
	private static int phase = Builds.NONE;
	private static int cost;

	private BuildInput() {
	}

	static void register() {
		ClientPlayNetworking.registerGlobalReceiver(BuildStatePayload.TYPE, (payload, context) -> {
			phase = payload.phase();
			cost = payload.cost();
		});
		ClientPlayNetworking.registerGlobalReceiver(BuildAreaPayload.TYPE, (payload, context) -> {
			// The outline is only sent to the builder, in their ring's colour.
			Corps before = CorpsTint.enter(Corps.held(context.player()));
			draw(payload);
			CorpsTint.restore(before);
		});
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> phase = Builds.NONE);
		ClientHooks.buildBusy = () -> phase == Builds.CLEAR || phase == Builds.CHOOSE;
	}

	/** What the design showing costs while choosing (0.1% = 1), else 0. */
	public static int designCost() {
		return phase == Builds.CHOOSE ? cost : 0;
	}

	/** True while left-click picks designs: a build is waiting and the Build ring is in hand. */
	public static boolean choosing(Minecraft mc) {
		if (phase != Builds.CHOOSE || mc.player == null || mc.player.isUsingItem()) return false;
		ItemStack main = mc.player.getMainHandItem();
		return main.getItem() instanceof PowerRingItem && PowerRingItem.getMode(main) == RingMode.BUILD;
	}

	/** Before vanilla handles the keys: each left-click is the next (or previous) design. */
	public static void startTick(Minecraft mc) {
		if (!choosing(mc)) return;
		while (mc.options.keyAttack.consumeClick()) {
			if (!ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) continue;
			ClientPlayNetworking.send(new AnvilInputPayload(mc.player.isShiftKeyDown() ? AnvilInputPayload.BUILD_PREV : AnvilInputPayload.BUILD_NEXT));
		}
	}

	private static double scrolled;

	/**
	 * The mouse wheel while choosing (from MouseHandlerMixin): each notch down is the next design
	 * (up, the one before), or with crouch the design's next materials, instead of the hotbar.
	 *
	 * @return true if the scroll was used
	 */
	public static boolean scroll(Minecraft mc, double amount) {
		if (mc.gui.screen() != null || !choosing(mc)) {
			scrolled = 0;
			return false;
		}
		scrolled += amount;
		boolean materials = mc.player.isShiftKeyDown();
		while (Math.abs(scrolled) >= 1) {
			boolean back = scrolled > 0;
			scrolled -= back ? 1 : -1;
			if (!ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) continue;
			int action = materials ? (back ? AnvilInputPayload.BUILD_MATERIAL_PREV : AnvilInputPayload.BUILD_MATERIAL_NEXT)
					: (back ? AnvilInputPayload.BUILD_PREV : AnvilInputPayload.BUILD_NEXT);
			ClientPlayNetworking.send(new AnvilInputPayload(action));
		}
		return true;
	}

	// ---- the outline ------------------------------------------------------------------------------

	private static void draw(BuildAreaPayload area) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Vec3 c = area.center();
		// While sizing, a dense bright line; once chosen, a calmer one.
		float size = area.locked() ? 1.1f : 1.5f;
		int life = area.locked() ? 11 : 3;
		double step = area.locked() ? 0.9 : 0.45;
		RandomSource r = mc.level.getRandom();
		switch (area.shape()) {
			case Builds.SQUARE -> {
				double h = Math.round(area.radius()) + 0.5;
				double[][] corners = {{-h, -h}, {h, -h}, {h, h}, {-h, h}};
				for (int i = 0; i < 4; i++) {
					double[] a = corners[i], b = corners[(i + 1) % 4];
					double len = Math.hypot(b[0] - a[0], b[1] - a[1]);
					for (double t = 0; t < len; t += step) {
						mote(mc.level, c.x + a[0] + (b[0] - a[0]) * t / len, c.z + a[1] + (b[1] - a[1]) * t / len, c.y, size, life);
					}
				}
				sprinkle(mc.level, r, c, h, area.locked());
			}
			case Builds.PAINT -> {
				for (int packed : area.rim()) {
					int dx = packed >> 16, dz = (short) (packed & 0xFFFF);
					mote(mc.level, Math.floor(c.x) + dx + 0.5, Math.floor(c.z) + dz + 0.5, c.y, size, life);
				}
			}
			default -> {
				double rad = area.radius() + 0.5;
				int n = Math.max(12, (int) (rad * Math.PI * 2 / step));
				for (int i = 0; i < n; i++) {
					double a = i * Math.PI * 2 / n;
					mote(mc.level, c.x + Math.cos(a) * rad, c.z + Math.sin(a) * rad, c.y, size, life);
				}
				sprinkle(mc.level, r, c, rad * 0.7, area.locked());
			}
		}
	}

	private static void sprinkle(Level level, RandomSource r, Vec3 c, double half, boolean locked) {
		if (locked) return;
		for (int i = 0; i < LabFx.count(4); i++) {
			double x = c.x + (r.nextDouble() * 2 - 1) * half, z = c.z + (r.nextDouble() * 2 - 1) * half;
			double y = groundAt(level, x, z, c.y);
			LabFx.spawn(ModParticles.MOTE, new Vec3(x, y + 0.1, z), new Vec3(0, 0.03, 0), 0.7f);
		}
	}

	/** One glowing mote on the ground at (x, z), resting on whatever is there near height nearY. */
	private static void mote(Level level, double x, double z, double nearY, float size, int life) {
		double y = groundAt(level, x, z, nearY);
		ConstructParticle p = LabFx.spawn(ModParticles.MOTE, new Vec3(x, y + 0.08, z), Vec3.ZERO, size);
		if (p != null) p.lasting(life);
	}

	/** The top of the ground at (x, z), searched from a little above nearY down. */
	private static double groundAt(Level level, double x, double z, double nearY) {
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos(Mth.floor(x), Mth.floor(nearY) + 6, Mth.floor(z));
		for (int i = 0; i < 24; i++, pos.move(0, -1, 0)) {
			if (!level.getBlockState(pos).canBeReplaced()) return pos.getY() + 1;
		}
		return nearY;
	}
}
