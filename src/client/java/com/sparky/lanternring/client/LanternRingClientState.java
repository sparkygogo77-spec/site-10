package com.sparky.lanternring.client;

/** A preview picked in the Ring Lab plays a few ticks after the menu closes. */
final class LanternRingClientState {
	private static String pendingPreview;
	private static int delay;

	static void queuePreview(String what) {
		pendingPreview = what;
		delay = 3;
	}

	static void tick() {
		if (pendingPreview != null && --delay <= 0) {
			LabFx.preview(pendingPreview);
			pendingPreview = null;
		}
	}

	private LanternRingClientState() {
	}
}
