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
		R2K1(null), H1_NEON("h1_neon"), D1_NEON("d1_neon"), W1_EMERALD("w1_emerald"), W1_NEON("w1_neon");

		public final String strip;

		ConstructLook(String strip) {
			this.strip = strip;
		}
	}
	public enum WallLook {
		BR1_JADE("br1_jade"), BR1_EMERALD("br1_emerald"), BR1_LIME("br1_lime"), BR1_NEON("br1_neon"),
		BR1_FOREST("br1_forest"), CLASSIC(null);

		public final String strip;

		WallLook(String strip) {
			this.strip = strip;
		}
	}
	/** The Blue Lantern's constructs; its Walls take BR1 blue unless this is CLASSIC. */
	public enum BlueLook {
		H1("h1_blue"), BR1("br1_blue"), CLASSIC(null);

		public final String strip;

		BlueLook(String strip) {
			this.strip = strip;
		}
	}
	public enum YellowLook {
		G2N("g2ng_yellow"), G2N_AMBER("g2ng_amber"), N3("n3_yellow"), N3_AMBER("n3_amber"), CLASSIC(null);

		public final String strip;

		YellowLook(String strip) {
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
	public SoulSightMode soulSight = SoulSightMode.PLAYERS_AND_MOBS;
	public ConstructLook constructLook = ConstructLook.R2K1;
	public WallLook wallLook = WallLook.BR1_JADE;
	public BlueLook blueLook = BlueLook.H1;
	public YellowLook yellowLook = YellowLook.G2N;
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
			new Option<>("soul_sight", SoulSightMode.class, s -> s.soulSight, (s, v) -> s.soulSight = v),
			new Option<>("construct_look", ConstructLook.class, s -> s.constructLook, (s, v) -> s.constructLook = v),
			new Option<>("wall_look", WallLook.class, s -> s.wallLook, (s, v) -> s.wallLook = v),
			new Option<>("blue_look", BlueLook.class, s -> s.blueLook, (s, v) -> s.blueLook = v),
			new Option<>("yellow_look", YellowLook.class, s -> s.yellowLook, (s, v) -> s.yellowLook = v));

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
		fresh.version = 8;
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
