package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.ChargePoses;
import com.sparky.lanternring.client.FlightPoses;
import com.sparky.lanternring.client.LanternCarry;
import com.sparky.lanternring.client.RiotShields;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Third person: flight poses for the arms, legs and head, the ring Shield raised on its arm, the lantern carried out in front, and charging from the lantern. */
@Mixin(PlayerModel.class)
public abstract class PlayerModelMixin {
	@Inject(method = "setupAnim(Lnet/minecraft/client/renderer/entity/state/AvatarRenderState;)V", at = @At("TAIL"))
	private void lanternring$flightPose(AvatarRenderState state, CallbackInfo ci) {
		FlightPoses.pose((PlayerModel) (Object) this, state);
		RiotShields.pose((PlayerModel) (Object) this, state);
		LanternCarry.pose((PlayerModel) (Object) this, state);
		ChargePoses.pose((PlayerModel) (Object) this, state);
		// Leaning on the set-down lantern to charge (J's L3 shoulder lean).
		com.sparky.lanternring.client.LeanPoses.pose((PlayerModel) (Object) this, state);
		// J's charge takes: L1c's lean into the port and K3c's kneel and lift (with knees).
		com.sparky.lanternring.client.TakePoses.pose((PlayerModel) (Object) this, state);
		// J's Blender sprint run, rocket takeoff and ground flight (and where the ring fist is, for the trail).
		com.sparky.lanternring.client.MovePoses.pose((PlayerModel) (Object) this, state);
		// Pass 404: in all flight the ring arm points where you are going, ahead of the body.
		com.sparky.lanternring.client.ArmLeadPoses.pose((PlayerModel) (Object) this, state);
		// The super jump: wind-up, launch, in the air, and the superhero landing.
		com.sparky.lanternring.client.SuperJumpPoses.pose((PlayerModel) (Object) this, state);
		// Building the Fear Nuke locks the ring arm straight up, over everything else.
		com.sparky.lanternring.client.NukeHold.pose((PlayerModel) (Object) this, state);
		// Swinging the Hammer mode's construct hammer: both arms on the handle.
		com.sparky.lanternring.client.HammerHold.pose((PlayerModel) (Object) this, state);
		// J's combat moves: the big flight slam, the flying flurry and the absorb.
		com.sparky.lanternring.client.CombatPoses.pose((PlayerModel) (Object) this, state);
	}
}
