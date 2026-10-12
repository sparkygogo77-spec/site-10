package com.sparky.lanternring;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import com.sparky.lanternring.item.PowerRingItem;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.util.Mth;

/**
 * Every editable duration in the mod, in seconds, saved to config/lanternring-tuning.json and
 * edited in game from the Ring Lab's Durations page. Code reads a value with {@code ticks()} when
 * it needs it, so edits apply straight away. To add one, declare an {@link Entry} below and add a
 * {@code tuning.lanternring.<key>} line to the lang file; it shows up in the menu by itself.
 *
 * <p>In singleplayer the menu edits the values the integrated server uses. A dedicated server uses
 * its own copy of the file.
 */
public final class RingTuning {
	/** One editable duration. */
	public static final class Entry {
		public final String key;
		public final double defaultSeconds;
		public final double min;
		public final double max;
		/** How much one click of - or + changes it. */
		public final double step;
		private volatile double seconds;

		private Entry(String key, double defaultSeconds, double min, double max, double step) {
			this.key = key;
			this.defaultSeconds = defaultSeconds;
			this.min = min;
			this.max = max;
			this.step = step;
			this.seconds = defaultSeconds;
		}

		public double seconds() {
			return seconds;
		}

		public int ticks() {
			return (int) Math.round(seconds * 20);
		}

		public void set(double value) {
			// Whole ticks only, so repeated clicks don't pile up rounding errors.
			seconds = Mth.clamp(Math.round(value * 20) / 20.0, min, max);
		}

		public void nudge(int clicks) {
			set(seconds + clicks * step);
		}

		public boolean isDefault() {
			return Math.abs(seconds - defaultSeconds) < 1.0e-6;
		}
	}

	private static final List<Entry> ENTRIES = new ArrayList<>();
	private static final Map<RingMode, Entry> COOLDOWNS = new EnumMap<>(RingMode.class);

	/** How long Bridge (and any other unheld) hard-light blocks last before fading. */
	public static final Entry CONSTRUCT_LIFETIME = entry("construct_lifetime", 10, 1, 120, 1);
	/** How long a Blast tunnel keeps glowing and lighting its walls. 0 turns the light off. */
	public static final Entry BLAST_AFTERGLOW = entry("blast_afterglow", 12, 0, 60, 1);
	/** How long a full ring keeps you in the air. */
	public static final Entry FLIGHT_TIME = entry("flight_time",
			PowerRingItem.MAX_CHARGE * 10 / 20.0, 50, 1800, 50);

	static {
		for (RingMode mode : RingMode.values()) {
			COOLDOWNS.put(mode, entry("cooldown." + mode.name().toLowerCase(), mode.cooldown / 20.0, 0, 10, 0.25));
		}
	}

	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

	private RingTuning() {
	}

	private static Entry entry(String key, double seconds, double min, double max, double step) {
		Entry entry = new Entry(key, seconds, min, max, step);
		ENTRIES.add(entry);
		return entry;
	}

	public static List<Entry> entries() {
		return Collections.unmodifiableList(ENTRIES);
	}

	/** Ticks before the ring can be used again after this mode. */
	public static int cooldownTicks(RingMode mode) {
		return COOLDOWNS.get(mode).ticks();
	}

	/** Ticks of flight per point of charge. */
	public static int flightDrainInterval() {
		return Math.max(1, Math.round(FLIGHT_TIME.ticks() / (float) PowerRingItem.MAX_CHARGE));
	}

	public static void resetAll() {
		for (Entry entry : ENTRIES) entry.set(entry.defaultSeconds);
	}

	/** Changed values, one per line, for the Ring Lab report. Empty if nothing was changed. */
	public static String report() {
		StringBuilder out = new StringBuilder();
		for (Entry entry : ENTRIES) {
			if (!entry.isDefault()) {
				out.append("- ").append(entry.key).append(": ").append(format(entry.seconds()))
						.append("s (default ").append(format(entry.defaultSeconds)).append("s)\n");
			}
		}
		return out.toString();
	}

	public static String format(double seconds) {
		String text = String.format(Locale.ROOT, "%.2f", seconds);
		return text.replaceAll("\\.?0+$", "");
	}

	private static Path file() {
		return FabricLoader.getInstance().getConfigDir().resolve("lanternring-tuning.json");
	}

	static void load() {
		Path path = file();
		if (!Files.exists(path)) return;
		try (Reader reader = Files.newBufferedReader(path)) {
			Map<String, Double> values = GSON.fromJson(reader, new TypeToken<Map<String, Double>>() { }.getType());
			if (values == null) return;
			for (Entry entry : ENTRIES) {
				Double value = values.get(entry.key);
				if (value != null && Double.isFinite(value)) entry.set(value);
			}
		} catch (IOException | RuntimeException e) {
			LanternRing.LOGGER.warn("Couldn't read {}, using default durations", path, e);
		}
	}

	public static void save() {
		Map<String, Double> values = new LinkedHashMap<>();
		for (Entry entry : ENTRIES) values.put(entry.key, entry.seconds());
		try (Writer writer = Files.newBufferedWriter(file())) {
			GSON.toJson(values, writer);
		} catch (IOException e) {
			LanternRing.LOGGER.warn("Couldn't save {}", file(), e);
		}
	}
}
