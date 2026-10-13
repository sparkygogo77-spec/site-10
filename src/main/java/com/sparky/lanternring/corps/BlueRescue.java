package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.animal.fish.WaterAnimal;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Blue Lantern rescue (J, 2026-10-13), once its squad has cleared the monsters round its lantern:
 * <ol>
 * <li>the squad picks a safe spot near the lantern (flat, dry, open; J: 10c) and clears its
 * plants away,</li>
 * <li>the flyers fetch every animal and every villager that isn't a Blue Lantern from the clearing,
 * one each, lifting it in a lasso bubble and setting it down gently in the middle (no momentum and
 * no fall damage; a bubble dropped when its flyer falls lands under Slow Falling),</li>
 * <li>a ring of hard-light walls stands round the spot, a dome forms over the rescued once
 * nobody's being carried in, and the squad guards it: the flyers circle overhead, the warrior
 * walks the walls and the ravager prowls round them (J: 11d, all three).</li>
 * </ol>
 * The walls and dome are construct blocks: they fade like any construct and the squad raises them
 * again while it's out. Monsters coming back still come first (BlueSquad), except for a flyer
 * already carrying someone, which finishes setting them down.
 *
 * <p>Still to decide with J: whether players are lifted too and how, and how the rescued are let
 * out when it's over (J: the player decides). Sites aren't saved: after a restart the squad picks
 * its spot again.
 */
final class BlueRescue {
	/** How far from the lantern the spot can be. */
	private static final int SITE_RANGE = 14;
	/** The rescued rest inside this radius; the dome and walls stand round it. */
	static final double SAFE = 6, DOME = 7.5, WALLS = 11;
	/** Ticks the clearing has to be quiet before the rescue starts. */
	private static final int QUIET = 40;
	/** A flyer lassos its mob from this close, carries it this far below itself, and gives up after this long. */
	private static final double CATCH = 7, HANG = 2.6;
	private static final int CARRY_LIMIT = 900;
	/** How near a flyer a player has to crouch to be lifted in (across the ground; flyers keep high). */
	private static final double ASK = 24;
	/** Ticks between re-raising faded walls, and the quiet after the last carry before the dome forms. */
	private static final int REPAIR = 100, DOME_WAIT = 60;

	enum Stage {
		FETCH, CARRY, LOWER
	}

	static final class Carry {
		final LivingEntity mob;
		Stage stage = Stage.FETCH;
		final long started;
		final Vec3 slot;

		Carry(LivingEntity mob, long started, Vec3 slot) {
			this.mob = mob;
			this.started = started;
			this.slot = slot;
		}
	}

	static final class Site {
		final BlockPos lantern;
		@Nullable
		BlockPos centre;
		long quietSince = -1, lastCarry, lastRepair = -REPAIR, lastTick = -1;
		/** A player told the warrior to let everyone out (J: 15a); a new danger starts a new rescue. */
		boolean released;
		int setDown;
		final Map<UUID, Carry> carrying = new HashMap<>();
		final List<BlockPos> dome = new ArrayList<>();
		/** Mobs a flyer couldn't reach in time (indoors, say): left where they are. */
		final Set<UUID> skipped = new HashSet<>();

		Site(BlockPos lantern) {
			this.lantern = lantern;
		}
	}

	private static final Map<BlockPos, Site> SITES = new HashMap<>();
	/** Tag on everyone the squad has lifted: they never take fall damage afterwards (J: no fall damage bubbles). */
	private static final String LIFTED = "lanternring.blue_lifted";
	/** Players lifted in, and the game time until which they take no fall damage. */
	private static final Map<UUID, Long> PLAYERS_SAFE = new HashMap<>();
	/** How long after being set down a player stays safe from falls. */
	private static final int PLAYER_SAFE_TICKS = 100;

	private BlueRescue() {
	}

	static void register() {
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			SITES.clear();
			PLAYERS_SAFE.clear();
		});
		net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
				!(source.is(net.minecraft.tags.DamageTypeTags.IS_FALL) && (entity.entityTags().contains(LIFTED)
						|| PLAYERS_SAFE.getOrDefault(entity.getUUID(), Long.MIN_VALUE) >= entity.level().getGameTime())));
	}

	static Site site(BlockPos lantern) {
		return SITES.computeIfAbsent(lantern, Site::new);
	}

	/** Whether this villager is carrying someone in (it finishes before it fights). */
	static boolean carrying(CorpsVillager v) {
		BlockPos post = v.squadPost();
		if (post == null) return false;
		Site s = SITES.get(post);
		Carry c = s == null ? null : s.carrying.get(v.getUUID());
		return c != null && c.stage != Stage.FETCH;
	}

	/** Who the squad lifts to safety: animals and villagers, never monsters, Blue Lanterns, golems or fish. */
	static boolean needsRescue(LivingEntity e) {
		if (!(e instanceof Mob) || !e.isAlive() || e instanceof Enemy || ConstructAlly.isBadMob(e)) return false;
		if (e instanceof CorpsVillager cv && (cv.inSquad() || cv.corps() == Corps.BLUE)) return false;
		if (e instanceof WaterAnimal || e.isPassenger() || e.isVehicle() || Lasso.isCaught(e)) return false;
		return e instanceof Animal || e instanceof AbstractVillager;
	}

	/**
	 * Once per tick per lantern (any squad member may call it): notices the quiet, picks the spot,
	 * keeps the walls up and forms the dome.
	 */
	static void tickSite(ServerLevel level, Site s, boolean threat) {
		long now = level.getGameTime();
		if (s.lastTick == now) return;
		s.lastTick = now;
		if (threat) {
			s.quietSince = -1;
			s.released = false;
			return;
		}
		if (s.released) return;
		if (s.quietSince < 0) s.quietSince = now;
		if (now - s.quietSince < QUIET) return;
		if (s.centre == null) {
			s.centre = pickSpot(level, s.lantern);
			clearPlants(level, s.centre);
			level.playSound(null, s.centre, SoundEvents.BEACON_ACTIVATE, SoundSource.NEUTRAL, 1.2f, 1.2f);
		}
		if (now - s.lastRepair >= REPAIR) {
			s.lastRepair = now;
			walls(level, s.centre);
		}
		boolean lowering = s.carrying.values().stream().anyMatch(c -> c.stage == Stage.LOWER);
		if (lowering) {
			openDome(level, s);
		} else if (s.setDown > 0 && now - s.lastCarry > DOME_WAIT && (s.dome.isEmpty() || now % REPAIR == 0)) {
			raiseDome(level, s);
		}
	}

	/**
	 * A flyer with no monster to fight: fetches the next one in need, or circles over the spot.
	 * Returns false when there's no rescue for it to do (it then circles as BlueSquad says).
	 */
	static boolean flyer(ServerLevel level, CorpsVillager v, Site s) {
		if (s.centre == null || s.released && !s.carrying.containsKey(v.getUUID())) return false;
		Vec3 centre = Vec3.atBottomCenterOf(s.centre);
		long now = level.getGameTime();
		Carry c = s.carrying.get(v.getUUID());
		if (c != null && (!c.mob.isAlive() || now - c.started > CARRY_LIMIT || c.stage != Stage.FETCH && Lasso.npcCaught(v) != c.mob)) {
			// Gone, taking too long, or the bubble burst: put it down here and try the next.
			if (Lasso.npcCaught(v) == c.mob) Lasso.npcSetDown(v);
			else if (c.stage == Stage.FETCH) s.skipped.add(c.mob.getUUID());
			s.carrying.remove(v.getUUID());
			c = null;
		}
		if (c == null) {
			LivingEntity mob = nextInNeed(level, s, centre, v.position());
			if (mob == null) return false;
			c = new Carry(mob, now, slot(centre, s.setDown + s.carrying.size()));
			s.carrying.put(v.getUUID(), c);
		}
		switch (c.stage) {
			case FETCH -> {
				Vec3 over = c.mob.position().add(0, c.mob.getBbHeight() + HANG + 0.5, 0);
				v.squadFly(over, c.mob.getEyePosition());
				if (v.distanceToSqr(c.mob) < CATCH * CATCH && v.hasLineOfSight(c.mob) && Lasso.npcCatch(level, v, c.mob, true)) {
					c.stage = Stage.CARRY;
					// Animals and villagers keep the no-fall-damage mark for good; a player just floats down under Slow Falling.
					if (!(c.mob instanceof net.minecraft.world.entity.player.Player)) c.mob.addTag(LIFTED);
					else PLAYERS_SAFE.put(c.mob.getUUID(), Long.MAX_VALUE);
					// If its flyer is struck down, the bubble lets it float down instead of falling.
					c.mob.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, CARRY_LIMIT, 0, false, false));
					Vec3 from = CorpsVillager.ringPos(v, 1f, c.mob.getBoundingBox().getCenter());
					Corps before = Corps.enter(Corps.BLUE);
					try {
						RingFx.send(level, RingFxPayload.Kind.TETHER, from, c.mob.getBoundingBox().getCenter());
					} finally {
						Corps.restore(before);
					}
					v.fired();
				}
			}
			case CARRY -> {
				// Over the walls and the dome, to above its place in the middle.
				Vec3 above = c.slot.add(0, DOME + HANG + 3, 0);
				v.squadFly(above, null);
				v.aimAt(c.mob);
				Lasso.npcHold(v, v.position().subtract(0, HANG, 0));
				if (horizontal(v.position(), above) < 1.5 && Math.abs(v.getY() - above.y) < 1.5) c.stage = Stage.LOWER;
			}
			case LOWER -> {
				// Down slowly through the open top of the dome.
				Vec3 low = c.slot.add(0, c.mob.getBbHeight() + HANG, 0);
				v.squadFly(low, null);
				v.aimAt(c.mob);
				Vec3 bubble = c.mob.position();
				Vec3 hold = new Vec3(c.slot.x, Math.max(c.slot.y + 0.2, bubble.y - 0.15), c.slot.z);
				Lasso.npcHold(v, hold);
				if (bubble.y - c.slot.y < 0.6 && horizontal(bubble, c.slot) < 1.2) {
					Lasso.npcSetDown(v);
					if (PLAYERS_SAFE.containsKey(c.mob.getUUID())) PLAYERS_SAFE.put(c.mob.getUUID(), level.getGameTime() + PLAYER_SAFE_TICKS);
					c.mob.removeEffect(MobEffects.SLOW_FALLING);
					level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), c.mob.getX(), c.mob.getY() + 0.5, c.mob.getZ(), 10, 0.4, 0.4, 0.4, 0.02);
					level.playSound(null, c.mob.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.NEUTRAL, 1f, 1.2f);
					s.carrying.remove(v.getUUID());
					s.setDown++;
					v.countRescue();
					s.lastCarry = level.getGameTime();
					v.aimAt(null);
				}
			}
		}
		return true;
	}

	/**
	 * A player talked to the squad's warrior (J: 15a): the dome and walls fade and the rescued are
	 * free to go. The squad stays on guard; the next monster attack starts a new rescue.
	 */
	static boolean release(ServerLevel level, BlockPos lantern, net.minecraft.world.entity.player.Player by) {
		Site s = SITES.get(lantern);
		if (s == null || s.centre == null || s.released) return false;
		s.released = true;
		openDome(level, s);
		int steps = (int) (WALLS * Math.PI * 2.2);
		for (int i = 0; i < steps; i++) {
			double a = i * Math.PI * 2 / steps;
			int x = (int) Math.floor(s.centre.getX() + 0.5 + Math.cos(a) * WALLS), z = (int) Math.floor(s.centre.getZ() + 0.5 + Math.sin(a) * WALLS);
			for (int y = s.centre.getY() - 4; y <= s.centre.getY() + 6; y++) {
				BlockPos p = new BlockPos(x, y, z);
				if (level.getBlockState(p).is(ModRegistry.LIGHT_CONSTRUCT)) level.removeBlock(p, false);
			}
		}
		Vec3 c = Vec3.atBottomCenterOf(s.centre);
		level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), c.x, c.y + 2, c.z, 40, WALLS / 2, 1.5, WALLS / 2, 0.03);
		level.playSound(null, s.centre, SoundEvents.BEACON_DEACTIVATE, SoundSource.NEUTRAL, 1.2f, 1.3f);
		by.sendOverlayMessage(net.minecraft.network.chat.Component.translatable("message.lanternring.blue_squad_release")
				.withStyle(net.minecraft.ChatFormatting.AQUA));
		s.setDown = 0;
		return true;
	}

	/** Where flyers circle once everyone's in: over the spot, or the lantern before there is one. */
	static Vec3 guardCentre(Site s) {
		return s.centre != null ? Vec3.atBottomCenterOf(s.centre) : Vec3.atCenterOf(s.lantern);
	}

	/** The warrior's beat: round the outside of the walls, one point of eight at a time. */
	static @Nullable Vec3 patrolPoint(ServerLevel level, Site s, CorpsVillager v) {
		if (s.centre == null) return null;
		Vec3 c = Vec3.atBottomCenterOf(s.centre);
		Vec3 off = v.position().subtract(c);
		double a = Math.atan2(off.z, off.x);
		// The next point round from where it is now.
		double next = (Math.floor(a / (Math.PI / 4)) + 1) * (Math.PI / 4);
		double r = WALLS + 2.5;
		int x = (int) Math.floor(c.x + Math.cos(next) * r), z = (int) Math.floor(c.z + Math.sin(next) * r);
		return new Vec3(x + 0.5, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z + 0.5);
	}

	// ---- who and where ---------------------------------------------------------------------------

	private static @Nullable LivingEntity nextInNeed(ServerLevel level, Site s, Vec3 centre, Vec3 from) {
		Set<LivingEntity> taken = new HashSet<>();
		for (Carry c : s.carrying.values()) taken.add(c.mob);
		Vec3 lantern = Vec3.atCenterOf(s.lantern);
		double r = BlueSquad.CLEAR_RADIUS;
		// A player crouching near this flyer is asking to be lifted in (J: 14c), and goes first.
		for (net.minecraft.server.level.ServerPlayer p : level.players()) {
			if (p.isShiftKeyDown() && !p.isSpectator() && p.isAlive() && !taken.contains(p) && !Lasso.isCaught(p) && !p.isPassenger()
					&& horizontal(p.position(), from) < ASK && horizontal(p.position(), centre) > SAFE + 0.5) return p;
		}
		return level.getEntitiesOfClass(LivingEntity.class, new AABB(lantern, lantern).inflate(r),
						e -> needsRescue(e) && !taken.contains(e) && !s.skipped.contains(e.getUUID()) && e.distanceToSqr(lantern) < r * r && horizontal(e.position(), centre) > SAFE + 0.5)
				.stream().min(Comparator.comparingDouble(e -> e.distanceToSqr(from))).orElse(null);
	}

	/** The n-th resting place in the middle: a sunflower spiral, so they spread out evenly. */
	private static Vec3 slot(Vec3 centre, int n) {
		double a = n * 2.39996;
		double r = Math.min(SAFE - 1, 0.8 * Math.sqrt(n + 1));
		return centre.add(Math.cos(a) * r, 0, Math.sin(a) * r);
	}

	/** The flattest dry open patch near the lantern. */
	private static BlockPos pickSpot(ServerLevel level, BlockPos lantern) {
		BlockPos best = lantern;
		double bestScore = Double.MAX_VALUE;
		for (int dx = -SITE_RANGE; dx <= SITE_RANGE; dx += 2) {
			for (int dz = -SITE_RANGE; dz <= SITE_RANGE; dz += 2) {
				int x = lantern.getX() + dx, z = lantern.getZ() + dz;
				// Away from the lantern, so rescued villagers resting there don't take its oath (CorpsMobs).
				if (dx * dx + dz * dz < 10 * 10) continue;
				int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
				double score = 0;
				for (int ox = -5; ox <= 5; ox += 2) {
					for (int oz = -5; oz <= 5; oz += 2) {
						int h = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x + ox, z + oz);
						score += Math.abs(h - y);
						if (!level.getFluidState(new BlockPos(x + ox, h - 1, z + oz)).isEmpty()) score += 6;
						// Trees and buildings in the way.
						if (level.getHeight(Heightmap.Types.MOTION_BLOCKING, x + ox, z + oz) > h + 1) score += 2;
					}
				}
				score += Math.sqrt(dx * dx + dz * dz) * 0.3 + Math.abs(y - lantern.getY()) * 0.5;
				if (score < bestScore) {
					bestScore = score;
					best = new BlockPos(x, y, z);
				}
			}
		}
		return best;
	}

	/** Clears grass, flowers and snow off the spot (the land itself is shaped later, with construct tools). */
	private static void clearPlants(ServerLevel level, BlockPos centre) {
		int r = (int) WALLS;
		for (BlockPos p : BlockPos.betweenClosed(centre.offset(-r, -1, -r), centre.offset(r, 3, r))) {
			if (p.distSqr(new BlockPos(centre.getX(), p.getY(), centre.getZ())) > r * r) continue;
			BlockState st = level.getBlockState(p);
			if (st.isAir() || !st.canBeReplaced() || !st.getFluidState().isEmpty()) continue;
			level.destroyBlock(p, false);
			if (level.getRandom().nextInt(6) == 0) {
				level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5, 2, 0.3, 0.3, 0.3, 0.01);
			}
		}
	}

	// ---- walls and dome --------------------------------------------------------------------------

	private static void walls(ServerLevel level, BlockPos centre) {
		Corps before = Corps.enter(Corps.BLUE);
		try {
			BlockState shell = Corps.state(ModRegistry.LIGHT_CONSTRUCT);
			int steps = (int) (WALLS * Math.PI * 2.2);
			for (int i = 0; i < steps; i++) {
				double a = i * Math.PI * 2 / steps;
				int x = (int) Math.floor(centre.getX() + 0.5 + Math.cos(a) * WALLS), z = (int) Math.floor(centre.getZ() + 0.5 + Math.sin(a) * WALLS);
				int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
				for (int dy = 0; dy < 2; dy++) place(level, new BlockPos(x, y + dy, z), shell.setValue(LightConstructBlock.RIM, dy == 1));
			}
		} finally {
			Corps.restore(before);
		}
	}

	private static void raiseDome(ServerLevel level, Site s) {
		BlockPos base = s.centre;
		if (base == null) return;
		boolean fresh = s.dome.isEmpty();
		s.dome.clear();
		Corps before = Corps.enter(Corps.BLUE);
		try {
			BlockState shell = Corps.state(ModRegistry.LIGHT_CONSTRUCT);
			int r = (int) Math.ceil(DOME);
			for (int dx = -r; dx <= r; dx++) {
				for (int dy = 0; dy <= r; dy++) {
					for (int dz = -r; dz <= r; dz++) {
						double d = Math.sqrt(dx * dx + dy * dy + dz * dz);
						if (d < DOME - 0.6 || d > DOME + 0.4) continue;
						BlockPos p = base.offset(dx, dy, dz);
						place(level, p, shell.setValue(LightConstructBlock.RIM, dy == 0 || d > DOME + 0.2));
						if (level.getBlockState(p).is(ModRegistry.LIGHT_CONSTRUCT)) s.dome.add(p.immutable());
					}
				}
			}
		} finally {
			Corps.restore(before);
		}
		if (fresh) {
			Vec3 top = Vec3.atBottomCenterOf(base).add(0, DOME, 0);
			level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), top.x, top.y, top.z, 30, DOME / 2, 1.5, DOME / 2, 0.03);
			level.playSound(null, base, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.NEUTRAL, 1.5f, 1.1f);
		}
	}

	/** Lets the dome go so a bubble can come down into it (it forms again once they're in). */
	private static void openDome(ServerLevel level, Site s) {
		if (s.dome.isEmpty()) return;
		for (BlockPos p : s.dome) {
			if (level.getBlockState(p).is(ModRegistry.LIGHT_CONSTRUCT)) level.removeBlock(p, false);
		}
		s.dome.clear();
	}

	/** Places a construct block where there's room; true if it went in. */
	private static boolean place(ServerLevel level, BlockPos p, BlockState state) {
		BlockState now = level.getBlockState(p);
		if (now.is(ModRegistry.LIGHT_CONSTRUCT) || !now.canBeReplaced() || !now.getFluidState().isEmpty()) return false;
		level.setBlockAndUpdate(p, state);
		return true;
	}

	private static double horizontal(Vec3 a, Vec3 b) {
		double dx = a.x - b.x, dz = a.z - b.z;
		return Math.sqrt(dx * dx + dz * dz);
	}
}
