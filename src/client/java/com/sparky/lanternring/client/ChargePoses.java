package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;

/**
 * Third person: charging the ring from the lantern. The lantern arm comes up in front of the chest
 * (low, not at shoulder height); the ring arm rises to show the ring, swings in beside the
 * lantern and the port pulls it on, then lets go at 100% (timeline in {@link ChargeMotion}).
 * Angles are model rotations in radians for the right arm; mirrored for the left. Mutable so tests
 * can sweep them.
 */
public final class ChargePoses {
	/** The lantern arm, held up in front: pitch (negative raises it forward), inward turn, and the roll that swings the lantern in to meet the ring. */
	public static float lanternX = -0.85f, lanternY = 0.42f, lanternZ = 0.42f;
	/** The ring arm raised, showing the ring. */
	public static float showX = -2.1f, showY = 0.05f, showZ = 0.25f;
	/** The ring arm lined up just below the lantern's port, coming up from underneath. */
	public static float lineX = -0.9f, lineY = -0.45f, lineZ = 0f;
	/** The ring arm with the ring on the port. */
	public static float pressX = -0.95f, pressY = -0.55f, pressZ = 0f;

	private ChargePoses() {
	}

	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player)) return;
		ChargeMotion.Weights w;
		if (player == mc.player) {
			w = ChargeMotion.local(mc.getDeltaTracker().getGameTimeDeltaPartialTick(false));
		} else {
			if (!LanternCharge.isCharging(player)) return;
			w = ChargeMotion.at(player.getTicksUsingItem() + mc.getDeltaTracker().getGameTimeDeltaPartialTick(false));
		}
		if (w.raise() <= 0f && w.show() <= 0f) return;
		boolean ringRight = player.getMainArm() == HumanoidArm.RIGHT;
		ModelPart ring = ringRight ? model.rightArm : model.leftArm;
		ModelPart lantern = ringRight ? model.leftArm : model.rightArm;
		// Inward is +y for the left arm and -y for the right; -z swings the right arm in.
		float fl = ringRight ? -1f : 1f;
		float fr = ringRight ? 1f : -1f;
		float buzz = ChargeMotion.buzz(ChargeMotion.onPort(player.getTicksUsingItem()), state.ageInTicks) * 6f;
		// Propped on the ring: the lantern hand turns a little more to lean it onto the ring.
		float lean = player == mc.player ? ChargeMotion.lean(LanternFirstPerson.held(mc.getDeltaTracker().getGameTimeDeltaPartialTick(false))) : 0f;
		// On the way up the lantern is lifted clear first, then settles lower into place.
		float lift = -0.45f * Mth.sin(Mth.clamp(w.raise() * 1.15f, 0f, 1f) * Mth.PI);
		set(lantern, w.raise(), lanternX + lift + buzz, -fl * lanternY, fl * -(lanternZ + 0.18f * lean));

		float sx = Mth.lerp(w.line(), showX, lineX), sy = Mth.lerp(w.line(), showY, lineY), sz = Mth.lerp(w.line(), showZ, lineZ);
		sx = Mth.lerp(w.pull(), sx, pressX + buzz);
		sy = Mth.lerp(w.pull(), sy, pressY);
		sz = Mth.lerp(w.pull(), sz, pressZ);
		// Before it lines up the arm comes up through the show pose; afterwards it is the whole target.
		float reach = Math.max(w.show(), w.line());
		set(ring, reach, sx, fr * sy, fr * sz);
	}

	private static void set(ModelPart arm, float w, float x, float y, float z) {
		arm.xRot = Mth.lerp(w, arm.xRot, x);
		arm.yRot = Mth.lerp(w, arm.yRot, y);
		arm.zRot = Mth.lerp(w, arm.zRot, z);
	}
}
