package com.sparky.lanternring.client;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.RingTuning;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.BiConsumer;
import java.util.function.Function;
import net.fabricmc.loader.api.FabricLoader;

/**
 * Ring Lab: which version of each look is active, and how the player rated each version.
 * Saved to config/lanternring-lab.json. Later these become the mod's real settings.
 */
public final class LabSettings {
	public enum RingModel { FORGED, CREST, CREST_GOLD, BEACON, EMBLEM, SIGNET, SLIM, LANTERN, CROWN, SQUARE }
	/** The Power Battery's look: the Torus Core, Nebula and Compact Unit concepts, the Dark Lantern or J's keychain lantern. */
	public enum LanternModel { STONE, CLASSIC, TORUS, NEBULA, COMPACT, DARK, KEYCHAIN }
	/** How the lantern is carried and used to charge the ring (see LanternFirstPerson and LanternShrine). */
	public enum ChargeStyle {
		HAND, SHRINE, FLOAT, HIP, SUMMON;

		/** True when the off hand holds the lantern by its handle. */
		public boolean inHand() {
			return this == HAND || this == HIP || this == SHRINE;
		}
	}
	public enum HandPose { RING_FORWARD, KNUCKLES_IN, FIST_DOWN, KNUCKLES_FORWARD, FLAT_ITEM }
	public enum RingGlow { OFF, MOTES, DRIPS, AURA }
	/** What the ring looks like as it charges in the lantern (see BeamChargeGlow.renderSun). */
	public enum LanternSun { INFLOW, SUN }
	public enum UseFx { LINE, HELIX, HELIX_RECALL, SHARDS }
	public enum BlastFx { RINGS, BEAM, SCORCH }
	public enum FlightFx { OFF, TRAIL, JETS, HALO }
	public enum BlockGlow { OFF, CONSTRUCTS, NEARBY }
	public enum Strength { SUBTLE, NORMAL, INTENSE }
	public enum Rating { NONE, KEEP, IMPROVE, DROP }
	/**
	 * J's construct texture picks (Blender rounds, 2026-10-13): which animated strip each kind of construct
	 * shows (see ConstructLooks). {@code strip} names textures/block/construct_ripples_&lt;strip&gt;; null keeps
	 * the construct's own model (R2 K1 from the jade pack, or the classic glass and bricks).
	 */
	public enum ConstructLook {
		W1_NEON("w1_neon"), R2K1(null), H1_NEON("h1_neon"), H2_NEON("h2_neon"), HW_EMERALD("hw_emerald"),
		D1_NEON("d1_neon"), W1_EMERALD("w1_emerald"),
		// Round 6 picks to test (2026-10-13): X5 quantum ripple, X3 power aura, X1 cosmic dust
		X5_EMERALD("green_x5_emerald"), X5_NEON("green_x5_neon"), X3_EMERALD("green_x3_emerald"), X1_EMERALD("green_x1_emerald");

		public final String strip;

		ConstructLook(String strip) {
			this.strip = strip;
		}
	}
	public enum WallLook {
		BR1_JADE("br1_jade"), BR1_EMERALD("br1_emerald"), BR1_LIME("br1_lime"), BR1_NEON("br1_neon"),
		BR1_FOREST("br1_forest"), BRD_NEON("brd_neon"), CLASSIC(null);

		public final String strip;

		WallLook(String strip) {
			this.strip = strip;
		}
	}
	/**
	 * The Blue Lantern's constructs. B1-B3 are J's Blender picks to test (2026-10-13) and cover Walls too;
	 * with H1 the Walls take BR1 blue; CLASSIC is the hue-shifted glass and bricks.
	 */
	public enum BlueLook {
		B1("blue_b1"), B2("blue_b2"), B3("blue_b3"), H1("h1_blue"), BR1("br1_blue"), CLASSIC(null);

		public final String strip;

		BlueLook(String strip) {
			this.strip = strip;
		}
	}
	/** How see-through constructs are (J: about half; the Blue hex Dome is the reference). */
	public enum ConstructOpacity {
		P20(0.2f), P30(0.3f), P40(0.4f), P50(0.5f), P60(0.6f), P70(0.7f), P80(0.8f), P90(0.9f), P100(1f);

		public final float alpha;

		ConstructOpacity(float alpha) {
			this.alpha = alpha;
		}
	}
	/** Yellow constructs and Walls; Y1-Y3 are J's Blender picks (2026-10-13): "all 3 yellow walls as options for now". */
	public enum YellowLook {
		Y1("yellow_y1"), Y2("yellow_y2"), Y3("yellow_y3"), G2N("g2ng_yellow"), G2N_AMBER("g2ng_amber"), N3("n3_yellow"), N3_AMBER("n3_amber"), CLASSIC(null);

		public final String strip;

		YellowLook(String strip) {
			this.strip = strip;
		}
	}
	/** Red constructs and Walls (J's Blender picks, 2026-10-13): R1 magma, R2 bloodfire. */
	public enum RedLook {
		R1("red_r1"), R2("red_r2"), CLASSIC(null);

		public final String strip;

		RedLook(String strip) {
			this.strip = strip;
		}
	}
	/** Violet constructs and Walls (J's Blender picks, 2026-10-13): V1 crystal, V3 silk. */
	public enum VioletLook {
		V1("violet_v1"), V3("violet_v3"), CLASSIC(null);

		public final String strip;

		VioletLook(String strip) {
			this.strip = strip;
		}
	}
	public enum SoulSightMode { PLAYERS_AND_MOBS, PLAYERS, OFF }
	/** The light building on the ring hand while the Beam charges (see BeamChargeGlow). */
	public enum ChargeGlow {
		SWIRL_AND_MOTES, SWIRL, MOTES, OFF;

		public boolean swirl() {
			return this == SWIRL_AND_MOTES || this == SWIRL;
		}

		public boolean motes() {
			return this == SWIRL_AND_MOTES || this == MOTES;
		}
	}
	/** The HUD meter of what each use costs (see ChargeMeter). */
	public enum ChargeMeter { LEVELS, BAR, OFF }
	/** How hard the camera kicks when a shot fires (see RingShake). */
	public enum ScreenShake {
		NORMAL(1f), STRONG(1.6f), SUBTLE(0.5f), OFF(0f);

		private final float amount;

		ScreenShake(float amount) {
			this.amount = amount;
		}

		public float amount() {
			return amount;
		}
	}

	/** How big a hole the ram barrier leaves in a wall it hits (sent to the server, see RamBarrier.Hole; same order). */
	public enum RamHole { DENT, CRATER, TOUCHING }
	/** How much faster a ring-bearer sprints on foot (sent to the server, see SuperJumps): the extra speed on top of walking. */
	public enum SuperSprint {
		FAST(0.6f), BLUR(1.2f), OFF(0f);

		private final float boost;

		SuperSprint(float boost) {
			this.boost = boost;
		}

		public float boost() {
			return boost;
		}
	}
	/** J's Blender picks for the super jump (2026-10-13): the ring arm on the way down (D1A at the ground, D1B ahead, D1C down and out). */
	public enum SuperFallArm { D1A, D1B, D1C }
	/** The landing: E1 three-point landing, E2 the wide slam. */
	public enum SuperLanding { E1, E2 }
	/** The low construct wall round the landing pad: W2 3 x 8 px, W1 8 x 8 px, W3 1.5 x 6 px, or none. */
	public enum SuperWall {
		W2(3, 8), W1(8, 8), W3(1.5f, 6), OFF(0, 0);

		/** Thickness and height in pixels. */
		public final float thick, high;

		SuperWall(float thick, float high) {
			this.thick = thick;
			this.high = high;
		}
	}
	/** Server side: a crater on every landing, shaped by the ground, or only on a primed one. */
	public enum SuperCrater { SURFACE, PRIMED_ONLY }

	public RingModel ringModel = RingModel.FORGED;     // J only uses the forged ring (see the v6 migration)
	public LanternModel lanternModel = LanternModel.STONE;
	public ChargeStyle chargeStyle = ChargeStyle.HAND;
	public HandPose handPose = HandPose.RING_FORWARD;
	public RingGlow ringGlow = RingGlow.AURA;
	public UseFx useFx = UseFx.HELIX;
	public BlastFx blastFx = BlastFx.SCORCH;
	public FlightFx flightFx = FlightFx.TRAIL;
	public BlockGlow blockGlow = BlockGlow.CONSTRUCTS;
	public Strength strength = Strength.NORMAL;
	public ChargeGlow chargeGlow = ChargeGlow.SWIRL_AND_MOTES;
	public LanternSun lanternSun = LanternSun.INFLOW;
	public ChargeMeter chargeMeter = ChargeMeter.LEVELS;
	public ScreenShake screenShake = ScreenShake.NORMAL;
	public RamHole ramHole = RamHole.DENT;
	public SuperSprint superSprint = SuperSprint.FAST;
	public SuperFallArm superFallArm = SuperFallArm.D1A;
	public SuperLanding superLanding = SuperLanding.E1;
	public SuperWall superWall = SuperWall.W2;
	public SuperCrater superCrater = SuperCrater.SURFACE;
	public SoulSightMode soulSight = SoulSightMode.PLAYERS_AND_MOBS;
	public ConstructLook constructLook = ConstructLook.W1_NEON;   // J: every construct should read like W1 neon from afar
	public WallLook wallLook = WallLook.BR1_JADE;
	public BlueLook blueLook = BlueLook.B1;
	public YellowLook yellowLook = YellowLook.Y1;
	public RedLook redLook = RedLook.R1;
	public VioletLook violetLook = VioletLook.V1;
	public ConstructOpacity constructOpacity = ConstructOpacity.P50;
	/** Bumped when a new default should replace what older saved files picked. */
	public int version;
	/** "option.VALUE" -> rating, e.g. "ring_model.SIGNET" -> KEEP. */
	public Map<String, Rating> ratings = new TreeMap<>();

	/** One row of the Ring Lab menu. */
	public record Option<E extends Enum<E>>(String key, Class<E> type, Function<LabSettings, E> get, BiConsumer<LabSettings, E> set) {
		public E current(LabSettings s) {
			return get.apply(s);
		}

		public void cycle(LabSettings s, int step) {
			E[] values = type.getEnumConstants();
			set.accept(s, values[Math.floorMod(current(s).ordinal() + step, values.length)]);
		}

		void fillFrom(LabSettings s, LabSettings defaults) {
			if (current(s) == null) set.accept(s, current(defaults));
		}

		public String ratingKey(LabSettings s) {
			return key + "." + current(s).name();
		}
	}

	public static final List<Option<?>> OPTIONS = List.of(
			new Option<>("ring_model", RingModel.class, s -> s.ringModel, (s, v) -> s.ringModel = v),
			new Option<>("lantern_model", LanternModel.class, s -> s.lanternModel, (s, v) -> s.lanternModel = v),
			new Option<>("charge_style", ChargeStyle.class, s -> s.chargeStyle, (s, v) -> s.chargeStyle = v),
			new Option<>("hand_pose", HandPose.class, s -> s.handPose, (s, v) -> s.handPose = v),
			new Option<>("ring_glow", RingGlow.class, s -> s.ringGlow, (s, v) -> s.ringGlow = v),
			new Option<>("use_fx", UseFx.class, s -> s.useFx, (s, v) -> s.useFx = v),
			new Option<>("blast_fx", BlastFx.class, s -> s.blastFx, (s, v) -> s.blastFx = v),
			new Option<>("flight_fx", FlightFx.class, s -> s.flightFx, (s, v) -> s.flightFx = v),
			new Option<>("block_glow", BlockGlow.class, s -> s.blockGlow, (s, v) -> s.blockGlow = v),
			new Option<>("strength", Strength.class, s -> s.strength, (s, v) -> s.strength = v),
			new Option<>("charge_glow", ChargeGlow.class, s -> s.chargeGlow, (s, v) -> s.chargeGlow = v),
			new Option<>("lantern_sun", LanternSun.class, s -> s.lanternSun, (s, v) -> s.lanternSun = v),
			new Option<>("charge_meter", ChargeMeter.class, s -> s.chargeMeter, (s, v) -> s.chargeMeter = v),
			new Option<>("screen_shake", ScreenShake.class, s -> s.screenShake, (s, v) -> s.screenShake = v),
			new Option<>("ram_hole", RamHole.class, s -> s.ramHole, (s, v) -> s.ramHole = v),
			new Option<>("super_sprint", SuperSprint.class, s -> s.superSprint, (s, v) -> s.superSprint = v),
			new Option<>("super_fall_arm", SuperFallArm.class, s -> s.superFallArm, (s, v) -> s.superFallArm = v),
			new Option<>("super_landing", SuperLanding.class, s -> s.superLanding, (s, v) -> s.superLanding = v),
			new Option<>("super_wall", SuperWall.class, s -> s.superWall, (s, v) -> s.superWall = v),
			new Option<>("super_crater", SuperCrater.class, s -> s.superCrater, (s, v) -> s.superCrater = v),
			new Option<>("soul_sight", SoulSightMode.class, s -> s.soulSight, (s, v) -> s.soulSight = v),
			new Option<>("construct_look", ConstructLook.class, s -> s.constructLook, (s, v) -> s.constructLook = v),
			new Option<>("wall_look", WallLook.class, s -> s.wallLook, (s, v) -> s.wallLook = v),
			new Option<>("blue_look", BlueLook.class, s -> s.blueLook, (s, v) -> s.blueLook = v),
			new Option<>("yellow_look", YellowLook.class, s -> s.yellowLook, (s, v) -> s.yellowLook = v),
			new Option<>("red_look", RedLook.class, s -> s.redLook, (s, v) -> s.redLook = v),
			new Option<>("violet_look", VioletLook.class, s -> s.violetLook, (s, v) -> s.violetLook = v),
			new Option<>("construct_opacity", ConstructOpacity.class, s -> s.constructOpacity, (s, v) -> s.constructOpacity = v));

	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static LabSettings instance;

	public static LabSettings get() {
		if (instance == null) instance = load();
		return instance;
	}

	public float amount() {
		return switch (strength) {
			case SUBTLE -> 0.5f;
			case NORMAL -> 1f;
			case INTENSE -> 2f;
		};
	}

	public Rating rating(String key) {
		return ratings.getOrDefault(key, Rating.NONE);
	}

	public void rate(String key, Rating rating) {
		if (rating == Rating.NONE) ratings.remove(key);
		else ratings.put(key, rating);
	}

	/** A plain-text summary the player can paste back to whoever is building the mod. */
	public String report() {
		StringBuilder out = new StringBuilder("Lantern Ring - Ring Lab report\n");
		for (Option<?> option : OPTIONS) {
			out.append("- ").append(option.key()).append(": using ").append(option.current(this).name());
			StringBuilder rated = new StringBuilder();
			for (Enum<?> value : option.type().getEnumConstants()) {
				Rating r = rating(option.key() + "." + value.name());
				if (r != Rating.NONE) rated.append(rated.isEmpty() ? "" : ", ").append(value.name()).append('=').append(r.name());
			}
			if (!rated.isEmpty()) out.append(" | rated ").append(rated);
			out.append('\n');
		}
		String durations = RingTuning.report();
		if (!durations.isEmpty()) out.append("Durations changed:\n").append(durations);
		return out.toString();
	}

	private static Path file() {
		return FabricLoader.getInstance().getConfigDir().resolve("lanternring-lab.json");
	}

	private static LabSettings load() {
		Path path = file();
		if (Files.exists(path)) {
			try (Reader reader = Files.newBufferedReader(path)) {
				LabSettings loaded = GSON.fromJson(reader, LabSettings.class);
				if (loaded != null) {
					loaded.fillMissing();
					return loaded;
				}
			} catch (IOException | RuntimeException e) {
				LanternRing.LOGGER.warn("Couldn't read {}, using defaults", path, e);
			}
		}
		LabSettings fresh = new LabSettings();
		fresh.version = 10;
		return fresh;
	}

	/** Old or hand-edited files may lack newer fields; fall back to defaults for those. */
	private void fillMissing() {
		LabSettings defaults = new LabSettings();
		if (version < 2) {
			// The Blockbench ring replaced the earlier drafts; show it once even if another was picked.
			ringModel = RingModel.EMBLEM;
			version = 2;
		}
		if (version < 3) {
			// J's signet rings and the knuckles-in hand: show them once over earlier picks.
			ringModel = RingModel.CREST;
			handPose = HandPose.KNUCKLES_IN;
			version = 3;
		}
		if (version < 4) {
			// J: the ring faces forward, on the front of the fist, rather than up.
			handPose = HandPose.RING_FORWARD;
			version = 4;
		}
		if (version < 5) {
			// J's forged carbon ring with the gold and emerald face: show it once over earlier picks.
			ringModel = RingModel.FORGED;
			version = 5;
		}
		if (version < 6) {
			// J only uses the forged ring; and show the new Dark Lantern once over the keychain one.
			ringModel = RingModel.FORGED;
			lanternModel = LanternModel.DARK;
			version = 6;
		}
		if (version < 7) {
			// J picked the Torus Core battery with the ring handle: show it once over earlier picks.
			lanternModel = LanternModel.TORUS;
			version = 7;
		}
		if (version < 8) {
			// J's stone lantern from the two face sheets: show it once over earlier picks.
			lanternModel = LanternModel.STONE;
			version = 8;
		}
		if (version < 9) {
			// J's round-4 hand-off: W1 neon (dark, rich, translucent) is how constructs should look; show it once.
			constructLook = ConstructLook.W1_NEON;
			version = 9;
		}
		if (version < 10) {
			// J's per-corps construct picks from the Blender kits: show the new Blue and Yellow ones once.
			blueLook = BlueLook.B1;
			yellowLook = YellowLook.Y1;
			version = 10;
		}
		// A value an older jar doesn't know loads as null; every menu row falls back to its default.
		for (Option<?> option : OPTIONS) option.fillFrom(this, defaults);
		if (ratings == null) ratings = new TreeMap<>();
		ratings.values().removeIf(r -> r == null || r == Rating.NONE);
	}

	public void save() {
		try (Writer writer = Files.newBufferedWriter(file())) {
			GSON.toJson(this, writer);
		} catch (IOException e) {
			LanternRing.LOGGER.warn("Couldn't save {}", file(), e);
		}
	}
}
