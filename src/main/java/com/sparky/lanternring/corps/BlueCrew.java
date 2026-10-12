package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A Blue Lantern building crew: a leader (the village founder) and two more Blue villagers who
 * plan and build together. The leader ticks it; it runs one order at a time through these phases:
 * <ol>
 * <li><b>IDLE</b>: nothing to do; everyone lives as a normal villager. A queued order is planned
 * here (its site picked and claimed so no other crew builds on top of it).</li>
 * <li><b>MUSTER</b>: the crew is gathered (idle Blue villagers nearby first, new ones called in
 * only if there aren't enough) and all three rise to meet above the leader.</li>
 * <li><b>TRAVEL</b>: the leader flies to the site over the terrain (see {@link SkyPath}), the other
 * two following off its shoulders.</li>
 * <li><b>FORM</b>: they take their places in a wide U round the site and wait for each other
 * (or give up waiting on a straggler after a few seconds).</li>
 * <li><b>BUILD</b>: the construct forms while all three pour light into it, the U rising with it.
 * When it's done the crew's suits form (the first time) and everyone flies home.</li>
 * </ol>
 * Crew members are remembered by UUID (saved by the leader), so a crew survives a reload; an
 * order in progress doesn't (the founder plans its step again).
 */
public final class BlueCrew {
	public enum Phase { IDLE, MUSTER, TRAVEL, FORM, BUILD }

	/** How many build together, leader included. */
	public static final int SIZE = 3;
	private static final int MUSTER_WAIT = 100, FORM_WAIT = 80;
	private static final double RECRUIT_RANGE = 48;

	private final CorpsVillager leader;
	private final List<CorpsVillager> members = new ArrayList<>();
	private final List<UUID> savedIds = new ArrayList<>();
	private final Deque<BuildOrder> orders = new ArrayDeque<>();
	private Phase phase = Phase.IDLE;
	private BuildOrder.@Nullable Site site;
	@Nullable
	private AABB claim;
	private SkyBuilds.@Nullable Job job;
	private int phaseTicks;
	/** Where the crew meets before setting off. */
	private Vec3 meet = Vec3.ZERO;
	private int finished;

	BlueCrew(CorpsVillager leader) {
		this.leader = leader;
	}

	// ---- API for other features -----------------------------------------------------------------

	/** Queues something to build; the crew gets to it once it's done with what it's doing. */
	public void order(BuildOrder order) {
		orders.add(order);
	}

	/** Whether it's working on something or has something queued. */
	public boolean busy() {
		return phase != Phase.IDLE || !orders.isEmpty();
	}

	public Phase phase() {
		return phase;
	}

	public CorpsVillager leader() {
		return leader;
	}

	/** The other members (not the leader), alive ones only. */
	public List<CorpsVillager> members() {
		members.removeIf(v -> !v.isAlive());
		return List.copyOf(members);
	}

	/** How many builds this crew has finished (in this session). */
	public int finished() {
		return finished;
	}

	/** Where the current build is, while it has one. */
	@Nullable
	public AABB site() {
		return claim;
	}

	// ---- the state machine ----------------------------------------------------------------------

	void tick(ServerLevel level) {
		phaseTicks++;
		switch (phase) {
			case IDLE -> {
				if (orders.isEmpty()) return;
				BuildOrder next = orders.poll();
				BuildOrder.Site planned = next.plan(level, this);
				if (planned == null || planned.blocks().isEmpty()) return;
				site = planned;
				claim = bounds(planned.blocks());
				Claims.claim(level, claim);
				recruit(level);
				meet = leader.position().add(0, 3, 0);
				enter(Phase.MUSTER);
			}
			case MUSTER -> {
				leader.follow(meet);
				for (int i = 0; i < members.size(); i++) members.get(i).follow(meet.add(offset(i)));
				boolean gathered = members().stream().allMatch(v -> v.distanceToSqr(leader) < 5 * 5);
				if (gathered && phaseTicks > 20 || phaseTicks > MUSTER_WAIT) enter(Phase.TRAVEL);
			}
			case TRAVEL -> {
				Vec3 base = slots(level)[0];
				leader.follow(base);
				// The other two keep off its shoulders.
				for (int i = 0; i < members.size(); i++) members.get(i).follow(leader.position().add(offset(i)));
				if (leader.position().distanceToSqr(base) < 3 * 3 || phaseTicks > 600) enter(Phase.FORM);
			}
			case FORM -> {
				Vec3[] slots = slots(level);
				Vec3 look = look();
				boolean ready = place(leader, slots[0], look, false);
				for (int i = 0; i < members.size(); i++) ready &= place(members.get(i), slots[i + 1], look, false);
				if (ready && phaseTicks > 10 || phaseTicks > FORM_WAIT) {
					job = SkyBuilds.start(level, site.blocks(), site.ticks(), Corps.BLUE, site.force(), leader);
					job.crew(members());
					enter(Phase.BUILD);
				}
			}
			case BUILD -> {
				if (SkyBuilds.running(job)) {
					Vec3[] slots = slots(level);
					Vec3 look = look();
					place(leader, slots[0], look, true);
					for (int i = 0; i < members.size(); i++) place(members.get(i), slots[i + 1], look, true);
					return;
				}
				// Done: the suits form on the first one, and everyone heads home.
				finished++;
				leader.suitUp(level);
				for (CorpsVillager v : members()) v.suitUp(level);
				leader.goHome();
				for (CorpsVillager v : members()) v.goHome();
				if (claim != null) Claims.release(level, claim);
				claim = null;
				site = null;
				job = null;
				enter(Phase.IDLE);
			}
		}
	}

	private void enter(Phase next) {
		phase = next;
		phaseTicks = 0;
	}

	/** Flies to its place and reports whether it's there. */
	private static boolean place(CorpsVillager v, Vec3 slot, Vec3 look, boolean building) {
		v.holdSlot(slot, look, building);
		return v.position().distanceToSqr(slot) < 1.5 * 1.5;
	}

	/** Followers' places off the leader's shoulders while gathering and travelling. */
	private Vec3 offset(int i) {
		float yaw = leader.getYRot() * (float) (Math.PI / 180);
		double side = i == 0 ? 2.2 : -2.2;
		return new Vec3(-Math.cos(yaw) * side + Math.sin(yaw) * 1.5, 0.6, -Math.sin(yaw) * side - Math.cos(yaw) * 1.5);
	}

	/**
	 * The wide U round the build: the leader at the bottom of the U, on the side toward home, and
	 * the other two at its arms, reaching a little past the middle a block higher. All rise with
	 * the build (a few blocks over the layer forming now) and are lifted clear of any blocks.
	 */
	private Vec3[] slots(Level level) {
		AABB box = claim;
		Vec3 c = box.getBottomCenter();
		double r = Math.max(6, Math.max(box.getXsize(), box.getZsize()) / 2 + 4);
		double y = Math.max((job != null ? job.current().getY() : box.minY) + 3.5, c.y + 2);
		BlockPos home = leader.homePos();
		Vec3 toHome = new Vec3(home.getX() + 0.5 - c.x, 0, home.getZ() + 0.5 - c.z);
		Vec3 back = toHome.lengthSqr() < 1 ? new Vec3(0, 0, 1) : toHome.normalize();
		Vec3 across = new Vec3(-back.z, 0, back.x);
		Vec3[] out = {
				new Vec3(c.x, y, c.z).add(back.scale(r)),
				new Vec3(c.x, y + 1, c.z).add(across.scale(r)).subtract(back.scale(r * 0.45)),
				new Vec3(c.x, y + 1, c.z).add(across.scale(-r)).subtract(back.scale(r * 0.45)),
		};
		for (int i = 0; i < out.length; i++) out[i] = clear(level, out[i]);
		return out;
	}

	/** The point raised until a villager fits there. */
	private static Vec3 clear(Level level, Vec3 at) {
		BlockPos p = BlockPos.containing(at);
		for (int up = 0; up < 8; up++) {
			if (level.getBlockState(p.above(up)).isAir() && level.getBlockState(p.above(up + 1)).isAir()) return at.add(0, up, 0);
		}
		return at.add(0, 8, 0);
	}

	private Vec3 look() {
		Vec3 c = claim.getBottomCenter();
		return new Vec3(c.x, (job != null ? job.current().getY() : claim.minY) + 1, c.z);
	}

	private static AABB bounds(Map<BlockPos, ?> blocks) {
		int x0 = Integer.MAX_VALUE, y0 = Integer.MAX_VALUE, z0 = Integer.MAX_VALUE;
		int x1 = Integer.MIN_VALUE, y1 = Integer.MIN_VALUE, z1 = Integer.MIN_VALUE;
		for (BlockPos p : blocks.keySet()) {
			x0 = Math.min(x0, p.getX());
			y0 = Math.min(y0, p.getY());
			z0 = Math.min(z0, p.getZ());
			x1 = Math.max(x1, p.getX());
			y1 = Math.max(y1, p.getY());
			z1 = Math.max(z1, p.getZ());
		}
		return new AABB(x0, y0, z0, x1 + 1, y1 + 1, z1 + 1);
	}

	// ---- crew members ---------------------------------------------------------------------------

	/**
	 * Fills the crew up to three: members it already had (alive, or found again by UUID after a
	 * reload), then idle Blue villagers nearby that aren't in another crew, and only then new ones
	 * called down in a flash of light.
	 */
	private void recruit(ServerLevel level) {
		members.removeIf(v -> !v.isAlive());
		for (UUID id : savedIds) {
			if (members.size() >= SIZE - 1) break;
			if (level.getEntity(id) instanceof CorpsVillager v && v.isAlive() && !members.contains(v)) join(v);
		}
		savedIds.clear();
		for (CorpsVillager v : CorpsVillager.near(level, leader.blockPosition(), RECRUIT_RANGE)) {
			if (members.size() >= SIZE - 1) break;
			if (v != leader && v.corps() == Corps.BLUE && !v.isBaby() && !v.leads() && v.crewOf() == null && !members.contains(v)) join(v);
		}
		while (members.size() < SIZE - 1) {
			CorpsVillager v = CorpsMobs.CORPS_VILLAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (v == null) return;
			v.setCorps(Corps.BLUE);
			v.settle(leader.homePos());
			double a = level.getRandom().nextDouble() * Math.PI * 2;
			v.snapTo(leader.getX() + Math.cos(a) * 2, leader.getY() + 0.5, leader.getZ() + Math.sin(a) * 2, level.getRandom().nextFloat() * 360f, 0f);
			level.addFreshEntity(v);
			CorpsShots.summon(level, v.position(), v.getBbHeight(), 1f, Corps.BLUE);
			join(v);
		}
	}

	private void join(CorpsVillager v) {
		members.add(v);
		v.joinCrew(this);
	}

	List<UUID> memberIds() {
		List<UUID> ids = new ArrayList<>(savedIds);
		for (CorpsVillager v : members()) ids.add(v.getUUID());
		return ids;
	}

	void load(List<UUID> ids) {
		savedIds.clear();
		savedIds.addAll(ids);
	}

	// ---- shared claims: crews don't build on top of each other ------------------------------------

	/** Every site a crew is building on, per level. Also used by site pickers (see BlueSites). */
	public static final class Claims {
		private static final Map<Level, List<AABB>> CLAIMS = new WeakHashMap<>();

		private Claims() {
		}

		static void claim(Level level, AABB box) {
			CLAIMS.computeIfAbsent(level, l -> new ArrayList<>()).add(box);
		}

		static void release(Level level, AABB box) {
			List<AABB> list = CLAIMS.get(level);
			if (list != null) list.remove(box);
		}

		/** Whether the box (grown by {@code gap}) is clear of every claimed site. */
		public static boolean free(Level level, AABB box, double gap) {
			List<AABB> list = CLAIMS.get(level);
			if (list == null) return true;
			AABB grown = box.inflate(gap);
			for (AABB b : list) if (b.intersects(grown)) return false;
			return true;
		}
	}
}
