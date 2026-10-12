package com.sparky.lanternring.corps;

import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Something a Blue Lantern crew is asked to build (see {@link BlueCrew#order}). The site is planned
 * when the crew gets to it, not when it's ordered, so it can dodge whatever was built or claimed
 * in the meantime. Other features (the floating city, the flier highway) plug in by queueing
 * their own orders on a crew.
 */
public interface BuildOrder {
	/** What it is, for logs and messages ("house", "island", "spire"...). */
	String name();

	/** Picks where it goes and what blocks it is, or null to give up on it (no room anywhere). */
	@Nullable
	Site plan(ServerLevel level, BlueCrew crew);

	/**
	 * A planned build: its blocks, how many ticks it takes to form, and whether it may knock out
	 * terrain in the way (a house on the ground) or only fill air (anything in the sky).
	 */
	record Site(Map<BlockPos, BlockState> blocks, int ticks, boolean force) {
	}

	/**
	 * For a build that runs its own job (the sky city's pieces): {@link #plan} returns null and
	 * this gives the area the crew forms its U round. Null as well means there's nothing to build.
	 */
	default @Nullable AABB area(ServerLevel level, BlueCrew crew) {
		return null;
	}

	/** Starts that job once the crew is in its U, all of {@code builders} pouring light in. */
	default @Nullable Started start(ServerLevel level, BlueCrew crew, List<CorpsVillager> builders) {
		return null;
	}

	/** A build running its own job: where the crew faces, the block forming now, and whether it's still going. */
	interface Started {
		Vec3 focus();

		BlockPos current();

		boolean running();
	}

	/** An order whose blocks are already decided. */
	static BuildOrder fixed(String name, Map<BlockPos, BlockState> blocks, int ticks, boolean force) {
		Site site = new Site(blocks, ticks, force);
		return new BuildOrder() {
			@Override
			public String name() {
				return name;
			}

			@Override
			public Site plan(ServerLevel level, BlueCrew crew) {
				return site;
			}
		};
	}
}
