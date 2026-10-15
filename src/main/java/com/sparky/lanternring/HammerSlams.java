package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.CraterLiningPayload;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Hammer mode: the Blue squad warrior's hammer leap for the player (J, 2026-10-13: "pick my
 * drop like an aerial and i commit to the jump and construct smash"). Hold right-click to aim the
 * landing ring (up to {@link RingTuning#HAMMER_RANGE} blocks, 24 by default, 40 at most), let go:
 * you leap in an arc with a construct hammer raised behind your head (drawn by each client, see
 * HammerHold), swing it down as you land,
 * and smash the ground. Monsters and players in the middle are driven into the dirt, those at the
 * edge are blown away, and a small crater is knocked out. Any corps can use it, in its colour.
 * It's free and you take no fall damage from the leap.
 */
public final class HammerSlams {
	/** The shockwave's reach and the inner part where things are smashed down instead of blown away. */
	static final double SMASH_REACH = 5.5, SMASH_CORE = 2.6;
	/** Twice the warrior's hammer (J picked double). */
	static final float SMASH_DAMAGE = 28f, EDGE_DAMAGE = 12f;
	/** Ticks the crater's construct lining stays before it dissolves. */
	private static final int LINING_HOLD = 30;
	/** The crater's radius and how deep its middle goes. */
	static final double CRATER = 2.6;
	static final int CRATER_DEPTH = 2;
	/** Ticks of no fall damage after landing, in case the client lands a moment later than the server. */
	private static final int SAFE_AFTER = 20;

	private static final class Leap {
		final ServerLevel level;
		final Vec3 from, to, dir;
		final int ticks;
		final double peak;
		final Corps corps;
		int t;

		Leap(ServerLevel level, Vec3 from, Vec3 to, Corps corps) {
			this.level = level;
			this.from = from;
			this.to = to;
			this.corps = corps;
			Vec3 flat = new Vec3(to.x - from.x, 0, to.z - from.z);
			this.dir = flat.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : flat.normalize();
			double span = from.distanceTo(to);
			this.ticks = (int) Math.round(12 + span * 0.5);
			this.peak = 3 + span * 0.25 + Math.max(0, to.y - from.y);
		}

		/** Where you are t ticks in: a straight line from take-off to landing, lifted by an arc. */
		Vec3 at(int t) {
			double f = Math.min(1, t / (double) ticks);
			return from.lerp(to, f).add(0, 4 * peak * f * (1 - f), 0);
		}
	}

	private static final Map<UUID, BlockPos> AIMS = new HashMap<>();
	private static final Map<UUID, Leap> LEAPS = new HashMap<>();
	/** Players just landed from a leap, and the ticks left before they can take fall damage again. */
	private static final Map<UUID, Integer> SAFE = new HashMap<>();

	private HammerSlams() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(HammerSlams::tick);
	}

	/** Whether this player is in the air on a hammer leap. */
	public static boolean leaping(Player player) {
		return LEAPS.containsKey(player.getUUID());
	}

	/** Every tick right-click is held in Hammer mode: moves the landing ring. */
	public static void aimTick(ServerPlayer player, ItemStack ring) {
		if (leaping(player) || player.getCooldowns().isOnCooldown(ring)) return;
		ServerLevel level = player.level();
		BlockPos mark = findMark(level, player);
		if (mark == null) {
			AIMS.remove(player.getUUID());
			return;
		}
		AIMS.put(player.getUUID(), mark);
		if (level.getGameTime() % 2 == 0) {
			Vec3 at = Vec3.atBottomCenterOf(mark);
			Corps before = Corps.enter(Corps.of(ring));
			try {
				RingFx.send(level, Kind.DELUGE_MARK, at, at.add(SMASH_REACH, 0, 0), 0f, 0, player);
			} finally {
				Corps.restore(before);
			}
		}
	}

	/** The block you'd land on: where you look, within range, dropped down to the ground. */
	public static @Nullable BlockPos findMark(ServerLevel level, Player player) {
		Vec3 eye = player.getEyePosition();
		double range = RingTuning.HAMMER_RANGE.seconds();
		BlockHitResult hit = level.clip(new ClipContext(eye, eye.add(player.getLookAngle().scale(range)),
				ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		if (hit.getType() == HitResult.Type.MISS) return null;
		BlockPos pos = hit.getBlockPos().relative(hit.getDirection());
		for (int i = 0; i < 24 && pos.getY() > level.getMinY(); i++) {
			BlockState below = level.getBlockState(pos.below());
			if (!below.canBeReplaced()) return pos;
			pos = pos.below();
		}
		return null;
	}

	/** Right-click let go: you commit to the jump. */
	public static void release(ServerPlayer player, ItemStack ring) {
		BlockPos mark = AIMS.remove(player.getUUID());
		if (mark == null || leaping(player)) return;
		start(player, Vec3.atBottomCenterOf(mark), Corps.of(ring));
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.HAMMER));
	}

	/** Springs at {@code land} with the hammer forming over your head. */
	public static void start(ServerPlayer player, Vec3 land, Corps corps) {
		ServerLevel level = player.level();
		Leap leap = new Leap(level, player.position(), land, corps);
		LEAPS.put(player.getUUID(), leap);
		// Every client draws the construct hammer forming in your hand and swinging (HammerHold).
		Corps before = Corps.enter(corps);
		try {
			RingFx.send(level, Kind.HAMMER_LEAP, leap.from, leap.to, leap.ticks, 0, player);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.MACE_SMASH_AIR, SoundSource.PLAYERS, 1f, 0.8f);
		level.sendParticles(ModParticles.of(ModParticles.MOTE, corps), player.getX(), player.getY() + 0.1, player.getZ(), 14, 0.4, 0.05, 0.4, 0.05);
	}

	public static void cancel(Player player) {
		AIMS.remove(player.getUUID());
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Integer>> it = SAFE.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Integer> e = it.next();
			ServerPlayer p = server.getPlayerList().getPlayer(e.getKey());
			if (p != null) p.resetFallDistance();
			if (p == null || e.getValue() <= 1) it.remove();
			else e.setValue(e.getValue() - 1);
		}
		for (Iterator<Map.Entry<UUID, Leap>> it = LEAPS.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Leap> e = it.next();
			ServerPlayer p = server.getPlayerList().getPlayer(e.getKey());
			Leap leap = e.getValue();
			if (p == null || !p.isAlive() || p.level() != leap.level) {
				it.remove();
				continue;
			}
			leap.t++;
			p.resetFallDistance();
			if (leap.t >= leap.ticks) {
				it.remove();
				// Land exactly on the mark, then smash.
				p.teleportTo(leap.to.x, leap.to.y, leap.to.z);
				p.setDeltaMovement(Vec3.ZERO);
				RingPowers.syncVelocity(p);
				SAFE.put(p.getUUID(), SAFE_AFTER);
				Corps before = Corps.enter(leap.corps);
				try {
					smash(leap.level, p, leap.to, leap.dir, leap.corps);
					WhatsNew.done(p, "mode.hammer.smash");
				} finally {
					Corps.restore(before);
				}
				continue;
			}
			// Steer along the arc: the velocity that takes you from here to where the arc is next tick.
			Vec3 next = leap.at(leap.t + 1);
			p.setDeltaMovement(next.subtract(p.position()));
			RingPowers.syncVelocity(p);
		}
	}

	/**
	 * The hammer lands: everything right in front is smashed down into the dirt (hard hit, pinned
	 * slow), everything out at the shockwave's edge is blown away, and a small crater is knocked out.
	 */
	static void smash(ServerLevel level, Player owner, Vec3 land, Vec3 dir, Corps corps) {
		Vec3 centre = land.add(dir.scale(1.6));
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(centre, centre).inflate(SMASH_REACH, 3, SMASH_REACH),
				e -> e != owner && e.isAlive() && !e.isSpectator())) {
			Vec3 off = new Vec3(e.getX() - centre.x, 0, e.getZ() - centre.z);
			double r = off.length();
			if (r > SMASH_REACH) continue;
			if (r <= SMASH_CORE) {
				e.hurtServer(level, level.damageSources().indirectMagic(owner, owner), SMASH_DAMAGE);
				e.setDeltaMovement(0, -1.2, 0);
				e.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 4));
			} else {
				e.hurtServer(level, level.damageSources().indirectMagic(owner, owner), EDGE_DAMAGE);
				Vec3 out = r < 1e-3 ? dir : off.normalize();
				double power = 1.1 + (r - SMASH_CORE) / (SMASH_REACH - SMASH_CORE) * 0.8;
				e.setDeltaMovement(out.x * power, 0.75, out.z * power);
			}
			RingPowers.syncVelocity(e);
		}
		RingFx.send(level, Kind.SHOCKWAVE, centre, centre.add(SMASH_REACH, 0, 0));
		BlockState ground = level.getBlockState(BlockPos.containing(centre.x, centre.y - 0.5, centre.z));
		List<BlockPos> blasted = new ArrayList<>();
		crater(level, owner, centre, blasted);
		// Lined with the construct pad like every landing's crater (J), for as long as the slam's dust settles.
		CraterLiningPayload.send(level, owner.getId(), corps, centre, LINING_HOLD, blasted);
		// Dirt thrown up in a ring and a burst of the ground's own block.
		if (!ground.isAir()) {
			var dust = new BlockParticleOption(ParticleTypes.BLOCK, ground);
			level.sendParticles(dust, centre.x, centre.y + 0.1, centre.z, 60, 1.2, 0.1, 1.2, 0.35);
			for (int i = 0; i < 24; i++) {
				double a = i * Math.PI * 2 / 24;
				level.sendParticles(dust, centre.x + Math.cos(a) * SMASH_REACH * 0.8, centre.y + 0.1, centre.z + Math.sin(a) * SMASH_REACH * 0.8, 3, 0.2, 0.05, 0.2, 0.15);
			}
		}
		level.sendParticles(ModParticles.of(ModParticles.MOTE, corps), centre.x, centre.y + 0.4, centre.z, 40, 1.5, 0.3, 1.5, 0.12);
		level.playSound(null, centre.x, centre.y, centre.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.PLAYERS, 1.4f, 0.8f);
		level.playSound(null, centre.x, centre.y, centre.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.6f);
	}

	/** A small bowl knocked out of the ground where the hammer hit. Unbreakable blocks and containers stay. */
	static int crater(ServerLevel level, Player owner, Vec3 centre, List<BlockPos> blasted) {
		int broken = 0;
		BlockPos c = BlockPos.containing(centre.x, centre.y - 0.5, centre.z);
		int r = (int) Math.ceil(CRATER);
		for (int dx = -r; dx <= r; dx++) {
			for (int dz = -r; dz <= r; dz++) {
				double d2 = (dx * dx + dz * dz) / (CRATER * CRATER);
				if (d2 > 1) continue;
				int depth = (int) Math.round(CRATER_DEPTH * (1 - d2) + 0.3);
				for (int dy = 0; dy < depth; dy++) {
					BlockPos pos = c.offset(dx, -dy, dz);
					BlockState state = level.getBlockState(pos);
					if (state.isAir() || !state.getFluidState().isEmpty() || state.getDestroySpeed(level, pos) < 0
							|| state.hasBlockEntity() || state.is(ModRegistry.LIGHT_CONSTRUCT)) continue;
					if (level.destroyBlock(pos, false, owner)) {
						broken++;
						blasted.add(pos.immutable());
					}
				}
			}
		}
		return broken;
	}
}
