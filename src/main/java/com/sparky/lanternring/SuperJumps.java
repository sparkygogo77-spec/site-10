package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import com.sparky.lanternring.net.SuperJumpPayload;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Super sprint and super jump (J, 2026-10-13: "a faster sprint and super jump ... a powerful jump
 * animation, a landing, earthquake shockwaves or screen shake ... my landing forces everyone around
 * me up by like a tenth of a block, with some particle dispersion"). Both come with any charged
 * ring you carry, in its corps colour, when you're not flying.
 *
 * <p>Sprinting is faster (the Ring Lab's Super sprint row) and steps straight up single blocks.
 * Crouch on the ground to wind up a jump, then press jump: the higher the charge, the higher and
 * further you go (the client launches you, see SuperJumpInput, and tells us here). When you come
 * down, an earthquake rolls out from where you land: a ring of thrown-up dirt and light travels
 * outward, and everything it passes is bounced about a tenth of a block into the air and nudged
 * away. Every client nearby shakes as the wave reaches it (RingShake.quake). No damage.
 */
public final class SuperJumps {
	private static final Identifier SPRINT_ID = LanternRing.id("super_sprint");
	private static final Identifier STEP_ID = LanternRing.id("super_sprint_step");
	/** The default Super sprint pick: 60% faster than walking on top of vanilla's sprint. */
	public static final float DEFAULT_SPRINT = 0.6f;
	/** How much higher you can step while super sprinting (vanilla steps 0.6 blocks). */
	private static final double STEP_EXTRA = 0.5;
	/** The landing quake: how fast its wave rolls out (blocks a tick), and its reach for the softest and hardest landing. */
	public static final double WAVE_SPEED = 0.75, MIN_REACH = 5, MAX_REACH = 14;
	/** The upward speed the wave gives: a body moves by it, then loses 0.08 to gravity each tick, so it rises about a tenth of a block (J). */
	private static final double LIFT = 0.1;
	/** The outward nudge at the middle of the wave, fading to nothing at its edge. */
	private static final double PUSH = 0.35;

	private static final class Jump {
		final ServerLevel level;
		final Corps corps;
		final double fromY;
		double peakY;
		int ticks;

		Jump(ServerLevel level, Corps corps, double y) {
			this.level = level;
			this.corps = corps;
			this.fromY = y;
			this.peakY = y;
		}
	}

	private static final class Quake {
		final ServerLevel level;
		final Vec3 centre;
		final Corps corps;
		final double reach;
		final boolean lift;
		final @Nullable Entity owner;
		final Set<Integer> hit = new HashSet<>();
		double radius;

		Quake(ServerLevel level, Vec3 centre, Corps corps, double reach, boolean lift, @Nullable Entity owner) {
			this.level = level;
			this.centre = centre;
			this.corps = corps;
			this.reach = reach;
			this.lift = lift;
			this.owner = owner;
		}
	}

	private static final Map<UUID, Float> SPRINT = new HashMap<>();
	private static final Map<UUID, Jump> JUMPS = new HashMap<>();
	private static final List<Quake> QUAKES = new ArrayList<>();

	private SuperJumps() {
	}

	static void register() {
		PayloadTypeRegistry.serverboundPlay().register(SuperJumpPayload.TYPE, SuperJumpPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(SuperJumpPayload.TYPE, (payload, context) -> {
			ServerPlayer player = context.player();
			if (payload.action() == SuperJumpPayload.SPRINT) {
				SPRINT.put(player.getUUID(), Mth.clamp(payload.value(), 0f, 2f));
			} else if (payload.action() == SuperJumpPayload.JUMP) {
				jump(player, Mth.clamp(payload.value(), 0f, 1f));
			}
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			SPRINT.remove(handler.player.getUUID());
			JUMPS.remove(handler.player.getUUID());
		});
		ServerTickEvents.END_SERVER_TICK.register(SuperJumps::tick);
	}

	/** Whether this player can use the ring's legs: a charged ring carried, not flying or gliding. */
	public static boolean canUse(ServerPlayer player, ItemStack ring) {
		return !ring.isEmpty() && PowerRingItem.getCharge(ring) > 0 && !player.getAbilities().flying
				&& !player.isFallFlying() && !player.isPassenger() && !player.isSpectator();
	}

	/** The charge a jump takes from the ring, out of PowerRingItem.MAX_CHARGE. */
	static int cost(float charge) {
		return Math.round(8 + 22 * charge);
	}

	/** The client launched this player; take the charge and show it. */
	static void jump(ServerPlayer player, float charge) {
		ItemStack ring = RingFlight.findRing(player);
		if (!canUse(player, ring) || JUMPS.containsKey(player.getUUID())) return;
		PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - cost(charge));
		ServerLevel level = player.level();
		Corps corps = Corps.of(ring);
		JUMPS.put(player.getUUID(), new Jump(level, corps, player.getY()));
		Vec3 feet = player.position();
		Corps before = Corps.enter(corps);
		try {
			RingFx.send(level, Kind.SUPER_JUMP, feet, feet, charge, 0, player);
			// The take-off cracks the ground a little too, but bounces nobody.
			QUAKES.add(new Quake(level, feet, corps, 1.5 + 2 * charge, false, player));
			dust(level, feet, 1.2, 20 + (int) (30 * charge), 0.25 + 0.2 * charge);
			level.sendParticles(ModParticles.of(ModParticles.MOTE, corps), feet.x, feet.y + 0.1, feet.z, 16 + (int) (20 * charge), 0.5, 0.05, 0.5, 0.08);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.PLAYERS, 0.7f + 0.5f * charge, 0.75f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.MACE_SMASH_AIR, SoundSource.PLAYERS, 0.8f, 0.7f + 0.3f * charge);
	}

	private static void tick(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) sprint(player);

		for (Iterator<Map.Entry<UUID, Jump>> it = JUMPS.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Jump> e = it.next();
			ServerPlayer p = server.getPlayerList().getPlayer(e.getKey());
			Jump jump = e.getValue();
			if (p == null || !p.isAlive() || p.level() != jump.level || jump.ticks > 600 || p.getAbilities().flying || p.isFallFlying()) {
				it.remove();
				continue;
			}
			jump.ticks++;
			jump.peakY = Math.max(jump.peakY, p.getY());
			p.resetFallDistance();
			if (jump.ticks < 4) continue;
			if (p.onGround() || p.isInWater() || p.onClimbable()) {
				it.remove();
				if (!p.isInWater()) land(p, jump);
			}
		}

		for (Iterator<Quake> it = QUAKES.iterator(); it.hasNext(); ) {
			Quake q = it.next();
			if (!wave(q)) it.remove();
		}
	}

	/** Super sprint: extra speed and a higher step while a ring-bearer sprints on foot. */
	private static void sprint(ServerPlayer player) {
		AttributeInstance speed = player.getAttribute(Attributes.MOVEMENT_SPEED);
		AttributeInstance step = player.getAttribute(Attributes.STEP_HEIGHT);
		if (speed == null) return;
		float boost = SPRINT.getOrDefault(player.getUUID(), DEFAULT_SPRINT);
		boolean on = boost > 0 && player.isSprinting() && canUse(player, RingFlight.findRing(player));
		AttributeModifier current = speed.getModifier(SPRINT_ID);
		if (on) {
			if (current == null || current.amount() != boost) {
				speed.removeModifier(SPRINT_ID);
				speed.addTransientModifier(new AttributeModifier(SPRINT_ID, boost, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
			}
			if (step != null && !step.hasModifier(STEP_ID)) {
				step.addTransientModifier(new AttributeModifier(STEP_ID, STEP_EXTRA, AttributeModifier.Operation.ADD_VALUE));
			}
			// Dirt kicked up behind your heels, and the odd mote of light.
			if (player.onGround() && player.tickCount % 2 == 0) {
				ServerLevel level = player.level();
				BlockState ground = level.getBlockState(player.getOnPos());
				Vec3 back = player.getDeltaMovement().multiply(-1.5, 0, -1.5);
				if (!ground.isAir()) {
					level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), player.getX() + back.x, player.getY() + 0.05,
							player.getZ() + back.z, 2, 0.15, 0.02, 0.15, 0.05);
				}
				if (player.tickCount % 6 == 0) {
					level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.of(RingFlight.findRing(player))), player.getX() + back.x,
							player.getY() + 0.2, player.getZ() + back.z, 1, 0.1, 0.1, 0.1, 0.01);
				}
			}
		} else {
			if (current != null) speed.removeModifier(SPRINT_ID);
			if (step != null && step.hasModifier(STEP_ID)) step.removeModifier(STEP_ID);
		}
	}

	/** Touchdown: the harder the fall, the bigger the quake. */
	private static void land(ServerPlayer p, Jump jump) {
		ServerLevel level = p.level();
		double drop = Math.max(0, jump.peakY - p.getY());
		float strength = (float) Mth.clamp(0.25 + drop / 20, 0.25, 1.5);
		double reach = Mth.clamp(MIN_REACH + drop * 0.4, MIN_REACH, MAX_REACH);
		Vec3 feet = p.position();
		Corps before = Corps.enter(jump.corps);
		try {
			RingFx.send(level, Kind.SUPER_LAND, feet, feet.add(reach, 0, 0), strength, 0, p);
			QUAKES.add(new Quake(level, feet, jump.corps, reach, true, p));
			dust(level, feet, 1.5, 40 + (int) (40 * strength), 0.3 + 0.2 * strength);
			level.sendParticles(ModParticles.of(ModParticles.MOTE, jump.corps), feet.x, feet.y + 0.2, feet.z, 30, 1.2, 0.2, 1.2, 0.15);
			level.sendParticles(ModParticles.of(ModParticles.SHARD, jump.corps), feet.x, feet.y + 0.2, feet.z, 14, 0.6, 0.1, 0.6, 0.25);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.PLAYERS, 1.2f + 0.6f * strength, 0.7f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.5f + 0.6f * strength, 0.55f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 1.5f, 0.5f);
	}

	/** Moves a quake's wave out one tick: dirt thrown up along its edge, and everything it passes bounced. False once it's gone. */
	private static boolean wave(Quake q) {
		double from = q.radius;
		q.radius = Math.min(q.reach, q.radius + WAVE_SPEED);
		double r = q.radius;
		int points = Math.max(8, (int) (r * 5));
		double spin = q.level.getRandom().nextDouble() * Math.PI * 2;
		var mote = ModParticles.of(ModParticles.MOTE, q.corps);
		for (int i = 0; i < points; i++) {
			double a = spin + i * Math.PI * 2 / points;
			double x = q.centre.x + Math.cos(a) * r, z = q.centre.z + Math.sin(a) * r;
			BlockPos ground = groundAt(q.level, x, z, q.centre.y);
			if (ground == null) continue;
			BlockState state = q.level.getBlockState(ground);
			double y = ground.getY() + 1.02;
			// Fainter as it spreads.
			int count = r < q.reach * 0.6 ? 3 : 2;
			q.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), x, y, z, count, 0.2, 0.02, 0.2, 0.18);
			if (i % 3 == 0) q.level.sendParticles(mote, x, y + 0.1, z, 1, 0.1, 0.05, 0.1, 0.03);
		}
		if (q.lift) {
			double fade = 1 - from / q.reach;
			for (Entity e : q.level.getEntities((Entity) null, new AABB(q.centre, q.centre).inflate(r + 1, 4, r + 1),
					e -> e != q.owner && e.isAlive() && !e.isSpectator() && (e instanceof LivingEntity || e instanceof ItemEntity))) {
				double dx = e.getX() - q.centre.x, dz = e.getZ() - q.centre.z;
				double d = Math.sqrt(dx * dx + dz * dz);
				if (d > r || d < from - 0.01 && from > 0 || !q.hit.add(e.getId())) continue;
				if (!e.onGround() && !(e instanceof ItemEntity)) continue;
								Vec3 out = d < 1e-3 ? Vec3.ZERO : new Vec3(dx / d, 0, dz / d);
				Vec3 v = e.getDeltaMovement();
				e.setDeltaMovement(v.x + out.x * PUSH * fade, Math.max(v.y, LIFT), v.z + out.z * PUSH * fade);
				RingPowers.syncVelocity(e);
			}
		}
		return q.radius < q.reach;
	}

	/** Dirt of whatever the ground is, thrown up round "at". */
	private static void dust(ServerLevel level, Vec3 at, double spread, int count, double speed) {
		BlockState ground = level.getBlockState(BlockPos.containing(at.x, at.y - 0.5, at.z));
		if (ground.isAir()) return;
		level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), at.x, at.y + 0.1, at.z, count, spread, 0.1, spread, speed);
	}

	/** The top solid block near height y at x, z (from two above to four below), or null over a drop. */
	static @Nullable BlockPos groundAt(ServerLevel level, double x, double z, double y) {
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		int top = Mth.floor(y) + 2;
		for (int by = top; by >= top - 6; by--) {
			pos.set(Mth.floor(x), by, Mth.floor(z));
			BlockState state = level.getBlockState(pos);
			if (!state.isAir() && !state.canBeReplaced() && state.getFluidState().isEmpty()
					&& level.getBlockState(pos.above()).canBeReplaced()) {
				return pos.immutable();
			}
		}
		return null;
	}
}
