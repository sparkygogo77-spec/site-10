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
	public enum RingModel { FORGED, CREST, CREST_GOLD, BEACON, EMBLEM, SIGNET, SLIM, LANTERN }
	public enum HandPose { RING_FORWARD, KNUCKLES_IN, FIST_DOWN, KNUCKLES_FORWARD, FLAT_ITEM }
	public enum RingGlow { OFF, MOTES, DRIPS, AURA }
	public enum UseFx { LINE, HELIX, HELIX_RECALL, SHARDS }
	public enum BlastFx { RINGS, BEAM, SCORCH }
	public enum FlightFx { OFF, TRAIL, JETS, HALO }
	public enum BlockGlow { OFF, CONSTRUCTS, NEARBY }
	public enum Strength { SUBTLE, NORMAL, INTENSE }
	public enum Rating { NONE, KEEP, IMPROVE, DROP }
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

	public RingModel ringModel = RingModel.FORGED;
	public HandPose handPose = HandPose.RING_FORWARD;
	public RingGlow ringGlow = RingGlow.AURA;
	public UseFx useFx = UseFx.HELIX;
	public BlastFx blastFx = BlastFx.SCORCH;
	public FlightFx flightFx = FlightFx.TRAIL;
	public BlockGlow blockGlow = BlockGlow.CONSTRUCTS;
	public Strength strength = Strength.NORMAL;
	public ChargeGlow chargeGlow = ChargeGlow.SWIRL_AND_MOTES;
	public ChargeMeter chargeMeter = ChargeMeter.LEVELS;
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

		public String ratingKey(LabSettings s) {
			return key + "." + current(s).name();
		}
	}

	public static final List<Option<?>> OPTIONS = List.of(
			new Option<>("ring_model", RingModel.class, s -> s.ringModel, (s, v) -> s.ringModel = v),
			new Option<>("hand_pose", HandPose.class, s -> s.handPose, (s, v) -> s.handPose = v),
			new Option<>("ring_glow", RingGlow.class, s -> s.ringGlow, (s, v) -> s.ringGlow = v),
			new Option<>("use_fx", UseFx.class, s -> s.useFx, (s, v) -> s.useFx = v),
			new Option<>("blast_fx", BlastFx.class, s -> s.blastFx, (s, v) -> s.blastFx = v),
			new Option<>("flight_fx", FlightFx.class, s -> s.flightFx, (s, v) -> s.flightFx = v),
			new Option<>("block_glow", BlockGlow.class, s -> s.blockGlow, (s, v) -> s.blockGlow = v),
			new Option<>("strength", Strength.class, s -> s.strength, (s, v) -> s.strength = v),
			new Option<>("charge_glow", ChargeGlow.class, s -> s.chargeGlow, (s, v) -> s.chargeGlow = v),
			new Option<>("charge_meter", ChargeMeter.class, s -> s.chargeMeter, (s, v) -> s.chargeMeter = v));

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
		fresh.version = 5;
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
		if (ringModel == null) ringModel = defaults.ringModel;
		if (handPose == null) handPose = defaults.handPose;
		if (ringGlow == null) ringGlow = defaults.ringGlow;
		if (useFx == null) useFx = defaults.useFx;
		if (blastFx == null) blastFx = defaults.blastFx;
		if (flightFx == null) flightFx = defaults.flightFx;
		if (blockGlow == null) blockGlow = defaults.blockGlow;
		if (strength == null) strength = defaults.strength;
		if (chargeGlow == null) chargeGlow = defaults.chargeGlow;
		if (chargeMeter == null) chargeMeter = defaults.chargeMeter;
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
