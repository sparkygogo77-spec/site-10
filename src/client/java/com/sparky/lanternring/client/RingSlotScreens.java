package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.RingSlot;
import com.sparky.lanternring.client.mixin.AbstractContainerScreenAccessor;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.resources.Identifier;
import net.minecraft.world.inventory.Slot;

/** Draws the frame behind the ring slot (RingSlot), which the inventory textures don't have. */
public final class RingSlotScreens {
	private static final Identifier FRAME = LanternRing.id("container/ring_slot");

	private RingSlotScreens() {
	}

	static void register() {
		ScreenEvents.AFTER_INIT.register((client, screen, width, height) -> {
			if (!(screen instanceof AbstractContainerScreen<?> container)) return;
			ScreenEvents.afterBackground(screen).register((s, graphics, mouseX, mouseY, partial) -> {
				AbstractContainerScreenAccessor pos = (AbstractContainerScreenAccessor) container;
				for (Slot slot : container.getMenu().slots) {
					if (!(slot.container instanceof RingSlot.Worn) || !slot.isActive() || slot.x < 0) continue;
					graphics.blitSprite(RenderPipelines.GUI_TEXTURED, FRAME, pos.lanternring$leftPos() + slot.x - 1, pos.lanternring$topPos() + slot.y - 1, 18, 18);
				}
			});
		});
	}
}
