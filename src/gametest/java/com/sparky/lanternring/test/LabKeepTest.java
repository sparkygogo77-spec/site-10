package com.sparky.lanternring.test;

import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.RingLabScreen;
import com.sparky.lanternring.client.RowNoteScreen;
import java.nio.file.Files;
import java.nio.file.Path;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.fabricmc.loader.api.FabricLoader;

/**
 * J's Ring Lab settings survive new jars (issue #323): an old (version 11) file keeps every value, rows become touched,
 * a take this jar lacks is reported as reset, a moved pick shows "★ new" instead of switching, notes reach the report,
 * and Save / Load my profile round-trips. Shots: the Ring tab with the badge and a note, and the note box.
 */
public class LabKeepTest implements FabricClientGameTest {
	private static void check(boolean ok, String what) {
		if (!ok) throw new AssertionError("Ring Lab keep: " + what);
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		Path config = FabricLoader.getInstance().getConfigDir();
		ctx.runOnClient(mc -> {
			try {
				Files.deleteIfExists(config.resolve("lanternring-profile-J.json"));
				Files.writeString(config.resolve("lanternring-lab.json"), """
						{"ringModel":"N04","handPose":"KNUCKLES_IN","lanternModel":"DARK","constructLook":"H1_NEON",
						 "yellowLook":"W1","blueLook":"BR1","constructOpacity":"P30","drillModel":"D9_GONE","screenShake":"SUBTLE",
						 "version":11,"ratings":{"ring_model.N04":"KEEP","yellow_look.Y1":"DROP"}}
						""");
			} catch (Exception e) {
				throw new RuntimeException(e);
			}
			LabSettings s = LabSettings.reload();
			check(s.ringModel == LabSettings.RingModel.N04 && s.handPose == LabSettings.HandPose.KNUCKLES_IN
					&& s.lanternModel == LabSettings.LanternModel.DARK && s.constructLook == LabSettings.ConstructLook.H1_NEON
					&& s.blueLook == LabSettings.BlueLook.BR1 && s.constructOpacity == LabSettings.ConstructOpacity.P30, "old values kept");
			check(s.touched.contains("ring_model") && s.touched.contains("hand_pose"), "rows touched");
			String report = s.report();
			check(report.contains("reset: ") && report.contains("D9_GONE no longer exists"), "reset listed:\n" + report);
			check(s.rating("ring_model.N04") == LabSettings.Rating.KEEP, "rating kept");

			// A touched row whose pick moved on: badge, no switch, even after a reload.
			s.ringModel = LabSettings.RingModel.FORGED;
			s.seenPicks.put("ring_model", "P03");
			s.setNote("ring_model.FORGED", "band too thick\nface too dark");
			s.save();
			s = LabSettings.reload();
			check(s.ringModel == LabSettings.RingModel.FORGED, "touched row not switched: " + s.ringModel);
			LabSettings.Option<?> ring = LabSettings.OPTIONS.stream().filter(o -> o.key().equals("ring_model")).findFirst().orElseThrow();
			check(ring.newPickAvailable(s), "new pick badge");
			report = s.report();
			check(report.contains("| note: band too thick / face too dark") && report.contains("new ★ pick available: N04"), "note in report:\n" + report);
			s.labTab = LabSettings.Group.RING;
			s.labRow = 0;
		});
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			ctx.waitTicks(20);
			RingLabScreen lab = ctx.computeOnClient(mc -> new RingLabScreen(null));
			ctx.setScreen(() -> lab);
			ctx.waitTicks(4);
			ctx.takeScreenshot("lab_keep_ring_badge");
			ctx.setScreen(() -> new RowNoteScreen(lab, LabSettings.OPTIONS.stream().filter(o -> o.key().equals("ring_model")).findFirst().orElseThrow()));
			ctx.waitTicks(4);
			ctx.takeScreenshot("lab_keep_note");
			ctx.setScreen(() -> null);

			ctx.runOnClient(mc -> {
				LabSettings s = LabSettings.get();
				check(s.saveProfile(), "profile saved");
				s.ringModel = LabSettings.RingModel.SLIM;
				s.setNote("ring_model.FORGED", "");
				check(s.loadProfile() != null, "profile loaded");
				check(s.ringModel == LabSettings.RingModel.FORGED && s.note("ring_model.FORGED").startsWith("band"), "profile round trip");
				try {
					Files.deleteIfExists(config.resolve("lanternring-profile-J.json"));
				} catch (Exception e) {
					throw new RuntimeException(e);
				}
				// With no profile saved, Load reads J's 2.1.647 report from the jar.
				s.ringModel = LabSettings.RingModel.SLIM;
				check("2.1.647 report".equals(s.loadProfile()), "bundled report");
				check(s.ringModel == LabSettings.RingModel.N04 && s.chargeStyle == LabSettings.ChargeStyle.HIP
						&& s.rating("construct_look.H2_NEON") == LabSettings.Rating.DROP
						&& Math.abs(com.sparky.lanternring.RingTuning.CHARGE_TIME.seconds() - 1.5) < 1e-6, "J's report applied");
				System.out.println("[labkeep] all checks passed");
			});
		}
	}
}
