package com.sparky.lanternring.city;

import com.sparky.lanternring.city.BlueCity.Piece;
import com.sparky.lanternring.city.CityData.City;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.phys.AABB;
import org.jspecify.annotations.Nullable;

/**
 * Decides what a sky city builds next, from what it already has and what its people need:
 * <ul>
 * <li>a piece can only go up once what it stands on is there (the disc before the spire, the spire
 * before anything hung off it, each tower after the one below it in the spiral);</li>
 * <li>a piece that was built and has since been broken (its keystone gone) is repaired first;</li>
 * <li>then needs are weighed: beds for everyone plus room to grow (towers), food for everyone
 * (gardens), a way up once the city is tall (lifts), somewhere for fliers to land once it has a
 * few towers (ports), and the vault last, as the city's crown.</li>
 * </ul>
 */
public final class CityPlanner {
	/** People each tower houses (a bed on each of its two floors, with a spare), and each garden feeds. */
	static final int PER_TOWER = 2, PER_GARDEN = 6;
	/** The city plans for this many more people than it has, so it keeps growing. */
	static final int GROWTH = 2;

	/** What the city has, and needs, right now. */
	public record Needs(int people, int beds, int food, int towers, int gardens, boolean tall) {
		public int housing() {
			return people + GROWTH - beds;
		}

		public int hunger() {
			return people - food;
		}
	}

	public static Needs needs(ServerLevel level, City city) {
		int towers = 0, gardens = 0;
		for (Piece p : Piece.values()) {
			if (!city.has(p)) continue;
			if (BlueCity.isTower(p)) towers++;
			if (p == Piece.GARDEN_EAST || p == Piece.GARDEN_WEST) gardens++;
		}
		return new Needs(people(level, city), towers * PER_TOWER, gardens * PER_GARDEN, towers, gardens, towers >= 3);
	}

	/** Villagers living in the city or in the village under it. */
	static int people(ServerLevel level, City city) {
		AABB box = new AABB(city.village).inflate(48, 8, 48).minmax(new AABB(city.anchor).inflate(32, BlueCity.HEIGHT, 32));
		return level.getEntitiesOfClass(Villager.class, box, Villager::isAlive).size();
	}

	/** Whether everything the piece rests on or hangs from is built. */
	static boolean ready(City city, Piece p) {
		return switch (p) {
			case FOUNDATION -> true;
			case SPIRE, GARDEN_EAST, GARDEN_WEST -> city.has(Piece.FOUNDATION);
			case LIFTS -> city.has(Piece.SPIRE);
			case PORTS -> city.has(Piece.SPIRE) && towerCount(city) >= 2;
			case CROWN -> city.has(Piece.PORTS) && towerCount(city) == 6;
			default -> {
				int i = BlueCity.towerIndex(p);
				yield city.has(Piece.SPIRE) && (i == 0 || city.has(BlueCity.tower(i - 1)));
			}
		};
	}

	static int towerCount(City city) {
		int n = 0;
		for (int i = 0; i < 6; i++) {
			if (city.has(BlueCity.tower(i))) n++;
		}
		return n;
	}

	/** How much the city wants the piece now (higher first); only pieces that are ready and not built count. */
	static double score(Piece p, Needs n) {
		return switch (p) {
			case FOUNDATION -> 1000;
			case SPIRE -> 900;
			case GARDEN_EAST, GARDEN_WEST -> 20 + Math.max(0, n.hunger()) * 12 - n.gardens() * 5;
			case LIFTS -> n.tall() ? 45 : 8;
			case PORTS -> n.towers() >= 3 ? 40 : 10;
			case CROWN -> 5;
			// The lowest open tower is the next one in the spiral.
			default -> 30 + Math.max(0, n.housing()) * 10;
		};
	}

	/** The piece to build next, or null when the city is complete. Re-checks what stands first. */
	@Nullable
	public static Piece choose(ServerLevel level, City city) {
		refresh(level, city);
		// Repairs come first: a piece that stood and has been broken, lowest first.
		for (Piece p : Piece.values()) {
			if (city.broken(p) && ready(city, p)) return p;
		}
		Piece best = null;
		double bestScore = Double.NEGATIVE_INFINITY;
		Needs n = needs(level, city);
		for (Piece p : Piece.values()) {
			if (city.has(p) || !ready(city, p)) continue;
			double s = score(p, n);
			if (s > bestScore) {
				bestScore = s;
				best = p;
			}
		}
		return best;
	}

	/**
	 * Updates which pieces stand from the world, for pieces whose chunks are loaded: one finished
	 * while away, or one broken by players or raiders, which then gets rebuilt.
	 */
	static void refresh(ServerLevel level, City city) {
		for (Piece p : Piece.values()) {
			if (city.active() == p) continue;
			Boolean stands = BlueCity.stands(level, city.anchor, p);
			if (stands != null && stands != city.has(p)) {
				city.mark(p, stands);
				CityData.get(level).setDirty();
			}
		}
	}

	/** A readable summary of the plan (for tests and the log). */
	public static String describe(ServerLevel level, City city) {
		Needs n = needs(level, city);
		List<String> have = new ArrayList<>();
		for (Piece p : Piece.values()) {
			if (city.has(p)) have.add(p.name().toLowerCase());
		}
		Map<Piece, Double> open = new EnumMap<>(Piece.class);
		for (Piece p : Piece.values()) {
			if (!city.has(p) && ready(city, p)) open.put(p, score(p, n));
		}
		return "city " + city.id + " at " + city.anchor.toShortString() + ": people " + n.people() + ", beds " + n.beds()
				+ ", food " + n.food() + "; built " + have + "; open " + open;
	}

	private CityPlanner() {
	}
}
