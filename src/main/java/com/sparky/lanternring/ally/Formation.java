package com.sparky.lanternring.ally;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.entity.EntityTypeTest;
import net.minecraft.world.phys.Vec3;

/**
 * Where each construct ally stands around its owner. Every ally type picks a {@link Stance}; the
 * owner's allies with the same stance form one group, ordered by when they were summoned, and each
 * takes the slot for its place in that group. So the shape changes with how many are out: one
 * Warden walks at your right shoulder, two flank you, three close in behind.
 *
 * <p>Nothing here looks at the corps: a Yellow Lantern construct that returns the same stance
 * joins the same formation.
 */
public final class Formation {
	private Formation() {}

	public enum Stance {
		/** Ground guards at your sides (Warden). */
		FLANK,
		/** Overhead: circles above you, or flies in a V when you move fast (Dragon). */
		CANOPY,
		/** Holds a post, or fans out ahead of you while you're at that post (Sentry). */
		PICKET
	}

	/** An ally's place in its group: its index among {@code count} allies. */
	public record Place(int index, int count) {
		public static final Place ALONE = new Place(0, 1);

		/** -1 to 1 across the group, 0 for a lone ally: spreads a line of them evenly. */
		public double spread() {
			return count <= 1 ? 0 : index * 2.0 / (count - 1) - 1;
		}

		/** This ally's share of a circle, so a group spaces itself evenly round it. */
		public double phase() {
			return index * Math.PI * 2 / count;
		}
	}

	/** The owner's allies in the same group as {@code ally} (itself included), oldest first. */
	static List<ConstructAlly> group(ServerLevel level, ConstructAlly ally) {
		List<ConstructAlly> group = new ArrayList<>(level.getEntities(EntityTypeTest.forClass(ConstructAlly.class),
				other -> other.isAlive() && ally.ownerId() != null && ally.ownerId().equals(other.ownerId())
						&& other.stance() == ally.stance() && ally.sameGroup(other)));
		group.sort(Comparator.comparingInt((ConstructAlly a) -> -a.tickCount).thenComparingInt(a -> a.getId()));
		return group;
	}

	/** Which way the owner is facing, flat. */
	public static Vec3 forward(Player owner) {
		float yaw = owner.getYRot() * Mth.DEG_TO_RAD;
		return new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
	}

	/** A point {@code side} blocks to the owner's right, {@code ahead} in front and {@code up} above them. */
	public static Vec3 around(Player owner, Vec3 facing, double side, double ahead, double up) {
		Vec3 right = new Vec3(-facing.z, 0, facing.x);
		return owner.position().add(right.scale(side)).add(facing.scale(ahead)).add(0, up, 0);
	}

	/**
	 * The Warden's guard slot: right shoulder alone; left and right as a pair; a third covers your
	 * back; four make a box. Spacing opens up a little as the group grows.
	 */
	public static Vec3 flankSlot(Player owner, Vec3 facing, Place place) {
		double side = 2.2 + 0.3 * (place.count() - 1);
		return switch (place.count() == 1 ? 0 : place.index()) {
			case 0 -> around(owner, facing, side, -0.6, 0);
			case 1 -> around(owner, facing, -side, -0.6, 0);
			case 2 -> place.count() == 3 ? around(owner, facing, 0, -3.2, 0) : around(owner, facing, side * 0.7, -3.4, 0);
			default -> around(owner, facing, -side * 0.7, -3.4, 0);
		};
	}
}
