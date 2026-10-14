package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.TakePoses;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.player.PlayerModel;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Knees for the player model: each leg (and its pants) gets a thigh and a shin, hidden unless a charge take kneels (TakePoses). */
@Mixin(PlayerModel.class)
public abstract class PlayerMeshMixin {
	@Inject(method = "createMesh", at = @At("RETURN"))
	private static void lanternring$knees(CubeDeformation deformation, boolean slim, CallbackInfoReturnable<MeshDefinition> cir) {
		// Only the skin model: armour meshes are built the same way with a bigger deformation.
		if (deformation == CubeDeformation.NONE) TakePoses.addKnees(cir.getReturnValue());
	}
}
