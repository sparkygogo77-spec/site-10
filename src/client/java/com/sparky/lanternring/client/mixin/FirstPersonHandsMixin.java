package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.client.CorpsTint;
import com.sparky.lanternring.item.PowerBatteryItem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.client.LanternFirstPerson;
import com.sparky.lanternring.client.RingFirstPerson;
import com.sparky.lanternring.client.RiotShields;
import net.minecraft.client.renderer.FirstPersonHandsAndItemsRenderer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.state.level.FirstPersonHandsAndItemsRenderState;
import net.minecraft.client.renderer.state.level.PlayerRenderState;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(FirstPersonHandsAndItemsRenderer.class)
public abstract class FirstPersonHandsMixin {
	@Inject(method = "submitArmWithItem", at = @At("HEAD"), cancellable = true)
	private void lanternring$ringAndLantern(PlayerRenderState playerState, FirstPersonHandsAndItemsRenderState handsState,
			float partialTick, float xRot, InteractionHand hand, float swing, ItemStack stack, float equip,
			PoseStack poseStack, SubmitNodeCollector collector, int light, CallbackInfo ci) {
		// The raised ring Shield, in front of the hand holding the ring.
		RiotShields.submitFirstPerson(poseStack, collector, hand, partialTick);
		// The Hammer mode's construct hammer, swung down in front of you.
		com.sparky.lanternring.client.HammerHold.submitFirstPerson(poseStack, collector, hand, partialTick);
		// The lantern summoned from its own slot floats on the off-hand side, whatever that hand holds.
		if (hand == InteractionHand.OFF_HAND) LanternFirstPerson.renderSlot(playerState, poseStack, collector, light, partialTick);
		// The ring and lantern are drawn in their corps' colour (see CorpsTint).
		Corps before = CorpsTint.enter(stack.getItem() instanceof PowerBatteryItem ? Corps.ofLantern(stack) : Corps.of(stack));
		boolean drawn;
		try {
			drawn = RingFirstPerson.render(playerState, hand, swing, equip, stack, poseStack, collector, light, partialTick)
					|| LanternFirstPerson.render(playerState, hand, swing, equip, stack, poseStack, collector, light, partialTick);
		} finally {
			CorpsTint.restore(before);
		}
		if (drawn) {
			ci.cancel();
		}
	}
}
