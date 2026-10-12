package com.sparky.lanternring.city;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.sparky.lanternring.LanternRing;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import org.jspecify.annotations.Nullable;

/**
 * Every sky city in a dimension, saved with the world: where it floats, which pieces stand, and
 * how far the piece being built has got, so building picks up exactly where it stopped after a
 * restart or once its chunks load again.
 */
public final class CityData extends SavedData {
	/** One city. {@code built} is a bit set of {@link BlueCity.Piece} ordinals. */
	public static final class City {
		public final int id;
		public final BlockPos anchor;
		/** Where its village is on the ground (the city counts its people there and overhead). */
		public final BlockPos village;
		long built;
		/** Pieces that have ever stood: one missing from {@code built} again was broken, and is repaired first. */
		long ever;
		/** The piece forming now (-1 none), and how many of its blocks have formed and set. */
		int active = -1, formed, set;
		/** How many builder bursts this city has had, which spreads out the planner's choices. */
		int bursts;

		City(int id, BlockPos anchor, BlockPos village) {
			this.id = id;
			this.anchor = anchor;
			this.village = village;
		}

		public boolean has(BlueCity.Piece p) {
			return (built & (1L << p.ordinal())) != 0;
		}

		void mark(BlueCity.Piece p, boolean on) {
			if (on) {
				built |= 1L << p.ordinal();
				ever |= 1L << p.ordinal();
			} else {
				built &= ~(1L << p.ordinal());
			}
		}

		/** How many blocks of the active piece have formed (saved, so building resumes there). */
		public int formed() {
			return formed;
		}

		public boolean broken(BlueCity.Piece p) {
			return !has(p) && (ever & (1L << p.ordinal())) != 0;
		}

		public BlueCity.@Nullable Piece active() {
			return active < 0 ? null : BlueCity.Piece.values()[active];
		}

		public boolean complete() {
			for (BlueCity.Piece p : BlueCity.Piece.values()) {
				if (!has(p)) return false;
			}
			return true;
		}

		private static final Codec<City> CODEC = RecordCodecBuilder.create(i -> i.group(
				Codec.INT.fieldOf("id").forGetter(c -> c.id),
				BlockPos.CODEC.fieldOf("anchor").forGetter(c -> c.anchor),
				BlockPos.CODEC.fieldOf("village").forGetter(c -> c.village),
				Codec.LONG.optionalFieldOf("built", 0L).forGetter(c -> c.built),
				Codec.LONG.optionalFieldOf("ever", 0L).forGetter(c -> c.ever),
				Codec.INT.optionalFieldOf("active", -1).forGetter(c -> c.active),
				Codec.INT.optionalFieldOf("formed", 0).forGetter(c -> c.formed),
				Codec.INT.optionalFieldOf("set", 0).forGetter(c -> c.set),
				Codec.INT.optionalFieldOf("bursts", 0).forGetter(c -> c.bursts)
		).apply(i, (id, anchor, village, built, ever, active, formed, set, bursts) -> {
			City c = new City(id, anchor, village);
			c.built = built;
			c.ever = ever | built;
			c.active = active < BlueCity.Piece.values().length ? active : -1;
			c.formed = formed;
			c.set = set;
			c.bursts = bursts;
			return c;
		}));
	}

	final List<City> cities = new ArrayList<>();
	int nextId = 1;

	private static final Codec<CityData> CODEC = RecordCodecBuilder.create(i -> i.group(
			City.CODEC.listOf().optionalFieldOf("cities", List.of()).forGetter(d -> d.cities),
			Codec.INT.optionalFieldOf("next_id", 1).forGetter(d -> d.nextId)
	).apply(i, (cities, nextId) -> {
		CityData d = new CityData();
		d.cities.addAll(cities);
		d.nextId = nextId;
		return d;
	}));

	// The datafix type only matters for vanilla's own keys, none of which are in here.
	static final SavedDataType<CityData> TYPE = new SavedDataType<>(LanternRing.id("sky_cities"), CityData::new, CODEC,
			DataFixTypes.SAVED_DATA_COMMAND_STORAGE);

	public static CityData get(ServerLevel level) {
		return level.getDataStorage().computeIfAbsent(TYPE);
	}

	@Nullable
	public City byId(int id) {
		for (City c : cities) {
			if (c.id == id) return c;
		}
		return null;
	}

	/** The city whose village or anchor is within {@code r} blocks (across) of {@code at}. */
	@Nullable
	public City near(BlockPos at, int r) {
		City best = null;
		double bestD = (double) r * r;
		for (City c : cities) {
			for (BlockPos p : new BlockPos[] {c.village, c.anchor}) {
				double dx = p.getX() - at.getX(), dz = p.getZ() - at.getZ();
				double d = dx * dx + dz * dz;
				if (d <= bestD) {
					bestD = d;
					best = c;
				}
			}
		}
		return best;
	}

	City add(BlockPos anchor, BlockPos village) {
		City c = new City(nextId++, anchor, village);
		cities.add(c);
		setDirty();
		return c;
	}
}
