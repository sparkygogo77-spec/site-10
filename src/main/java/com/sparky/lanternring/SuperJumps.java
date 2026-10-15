package com.sparky.lanternring;

import com.mojang.math.Transformation;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import com.sparky.lanternring.net.CraterLiningPayload;
import com.sparky.lanternring.net.SuperJumpPayload;
import java.util.ArrayList;
import java.util.Collections;
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
import net.minecraft.util.Brightness;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.jspecify.annotations.Nullable;

/**
 * Super sprint and super jump (J, 2026-10-13: "a faster sprint and super jump ... a powerful jump
 * animation, a landing, earthquake shockwaves or screen shake ... my landing forces everyone around
 * me up by like a tenth of a block, with some particle dispersion"). Both come with any charged
 * ring you carry, in its corps colour, when you're not flying.
 *
 * <p>Sprinting builds up speed (the Ring Lab's Super sprint row): slow at first, then a surge to top
 * speed over RingTuning super_sprint_build, and it steps straight up single blocks. Sprinting also
 * charges the jump (J: "I want to have to be sprinting"): jump once you've sprinted super_jump_arm
 * and you leap in a long forward arc, up to 30 blocks high after super_jump_charge of sprinting, steering in the air like
 * flight but with gravity untouched (the client launches and steers you, see SuperJumpInput, and
 * tells us here). When you come
 * down, an earthquake rolls out from where you land: a ring of thrown-up dirt and light travels
 * outward, and everything it passes is bounced about a tenth of a block into the air and nudged
 * away. Every client nearby shakes as the wave reaches it (RingShake.quake).
 *
 * <p>J (2026-10-13): the landing kills. Mobs near where you land die, those further out are hurt
 * less the further they are (other players are hurt but never killed outright; villagers, your
 * pets and construct allies are spared). The ground the wave touches is scorched on the spot:
 * plants burn away, grass and dirt char to coarse dirt, and the middle turns to blackstone, sand
 * to glass. Hold left-click in the air for super_jump_prime to prime the ring: a hard-light shell
 * like the ram barrier forms under you, and the landing is bigger, with a crater and a dome.
 *
 * <p>J's Blender picks (2026-10-13, Ring Lab Super crater): every landing blasts a stepped crater
 * shaped by what you land on, carved the tick before touchdown so you land on its floor, and its
 * blocks are thrown up and out. Landing more than DEEP blocks below where you took off makes the
 * deep crater (and on the client the E3 landing and the guard walls; the variant's DEEP bit).
 */
public final class SuperJumps {
	public static final Identifier SPRINT_ID = LanternRing.id("super_sprint");
	private static final Identifier STEP_ID = LanternRing.id("super_sprint_step");
	/** The default Super sprint pick: 60% faster than walking on top of vanilla's sprint. */
	public static final float DEFAULT_SPRINT = 0.6f;
	/** How much higher you can step while super sprinting (vanilla steps 0.6 blocks). */
	private static final double STEP_EXTRA = 0.5;
	/** The landing quake: how fast its wave rolls out (blocks a tick), and its reach for the softest and hardest landing. */
	public static final double WAVE_SPEED = 0.75, MIN_REACH = 5, MAX_REACH = 22;
	/** Heights of a just-armed and a fully charged jump, in blocks (J: 85 went too high, it should be a satisfying arc). */
	public static final double MIN_HEIGHT = 6, MAX_HEIGHT = 30;
	/** A primed landing reaches this much further (and at most PRIMED_MAX_REACH). */
	private static final double PRIMED_SCALE = 1.5, PRIMED_MAX_REACH = 30;
	/** The part of the quake's reach where mobs are killed outright: normal and primed. */
	private static final double KILL_PART = 0.35, KILL_PRIMED = 0.55;
	/** The upward speed the wave gives: a body moves by it, then loses 0.08 to gravity each tick, so it rises about a tenth of a block (J). */
	private static final double LIFT = 0.1;
	/** The outward nudge at the middle of the wave, fading to nothing at its edge. */
	private static final double PUSH = 0.35;
	/** Landing this many blocks below the take-off is the deeper fall. */
	public static final double DEEP = 6;
	/** SUPER_LAND's variant bits: primed, and the deeper fall. */
	public static final int PRIMED_BIT = 1, DEEP_BIT = 2;
	/** SUPER_LAND's variant bit for a power landing (PowerLandings): no stepped crater, pad or landing pose of its own. */
	public static final int POWER_BIT = 4;
	/** Ticks a thrown block takes to shrink away. */
	private static final int DEBRIS_LIFE = 10;

	private static final class Jump {
		final ServerLevel level;
		final Corps corps;
		final double fromY;
		double peakY;
		int ticks;
		/** Left-click held in the air (ticks so far), and whether that has primed the ring. */
		boolean priming, primed;
		int primeTicks;
		/** Last tick's height, whether the crater is already carved, and how the ground turned out. */
		double lastY;
		/** Where they were last tick, across the ground, and how far they moved on the last tick. */
		double lastX, lastZ;
		Vec3 step = Vec3.ZERO;
		boolean carved, deep;

		@Nullable BlockPos ground;
		/** Every block the landing blasted out, for the client to line with the pad. */
		final List<BlockPos> destroyed = new ArrayList<>();

		Jump(ServerLevel level, Corps corps, Vec3 at) {
			this.level = level;
			this.corps = corps;
			this.fromY = at.y;
			this.peakY = at.y;
			this.lastY = at.y;
			this.lastX = at.x;
			this.lastZ = at.z;
		}
	}

	/** A blasted block thrown out of a crater: waits its delay, then flies and shrinks away. */
	private static final class Debris {
		final ServerLevel level;
		final BlockState state;
		Vec3 pos, vel;
		int delay, age;
		final float size;
		Display.@Nullable BlockDisplay body;

		Debris(ServerLevel level, BlockState state, Vec3 pos, Vec3 vel, int delay, float size) {
			this.level = level;
			this.state = state;
			this.pos = pos;
			this.vel = vel;
			this.delay = delay;
			this.size = size;
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
		/** A landing's: mobs inside killReach die, and damage fades from maxDamage there to nothing at the edge. */
		double killReach;
		float maxDamage;
		boolean scorch, primed;

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
	/** Ticks each player has been super sprinting. */
	private static final Map<UUID, Integer> SPRINT_TICKS = new HashMap<>();
	private static final Map<UUID, Jump> JUMPS = new HashMap<>();
	private static final List<Quake> QUAKES = new ArrayList<>();
	private static final List<Debris> DEBRIS = new ArrayList<>();
	/** Each player's Super crater pick: 0 a crater every landing (the default), 1 only when primed. */
	private static final Map<UUID, Integer> CRATER = new HashMap<>();

	private SuperJumps() {
	}

	static void register() {
		PayloadTypeRegistry.serverboundPlay().register(SuperJumpPayload.TYPE, SuperJumpPayload.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(CraterLiningPayload.TYPE, CraterLiningPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(SuperJumpPayload.TYPE, (payload, context) -> {
			ServerPlayer player = context.player();
			if (payload.action() == SuperJumpPayload.SPRINT) {
				SPRINT.put(player.getUUID(), Mth.clamp(payload.value(), 0f, 2f));
			} else if (payload.action() == SuperJumpPayload.JUMP) {
				jump(player, Mth.clamp(payload.value(), 0f, 1f));
			} else if (payload.action() == SuperJumpPayload.PRIME) {
				Jump jump = JUMPS.get(player.getUUID());
				if (jump != null) jump.priming = payload.value() > 0;
			} else if (payload.action() == SuperJumpPayload.CRATER) {
				CRATER.put(player.getUUID(), Math.round(payload.value()));
			} else if (payload.action() == SuperJumpPayload.SLIDE) {
				PowerLandings.pick(player, Math.round(payload.value()));
			}
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			SPRINT.remove(handler.player.getUUID());
			SPRINT_TICKS.remove(handler.player.getUUID());
			JUMPS.remove(handler.player.getUUID());
			CRATER.remove(handler.player.getUUID());
		});
		ServerTickEvents.END_SERVER_TICK.register(SuperJumps::tick);
	}

	/** Whether this player can use the ring's legs: a charged ring carried, not flying or gliding. */
	public static boolean canUse(ServerPlayer player, ItemStack ring) {
		return !ring.isEmpty() && PowerRingItem.getCharge(ring) > 0 && !player.getAbilities().flying
				&& !player.isFallFlying() && !player.isPassenger() && !player.isSpectator();
	}

	/**
	 * 0..1: how far a sprint of this many ticks has built up to top speed. It eases in slowly, surges
	 * through the middle and settles at the top (J: "accelerate satisfyingly").
	 */
	public static float sprintRamp(int ticks) {
		float t = Mth.clamp(ticks / (float) Math.max(1, RingTuning.SUPER_SPRINT_BUILD.ticks()), 0f, 1f);
		return t * t * t * (t * (6 * t - 15) + 10);
	}

	/** 0..1: how charged a jump is after sprinting this many ticks (negative until it's armed). */
	public static float jumpCharge(int ticks) {
		int arm = RingTuning.SUPER_JUMP_ARM.ticks();
		if (ticks < arm) return -1f;
		return Mth.clamp((ticks - arm) / (float) Math.max(1, RingTuning.SUPER_JUMP_CHARGE.ticks() - arm), 0f, 1f);
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
		JUMPS.put(player.getUUID(), new Jump(level, corps, player.position()));
		WhatsNew.done(player, "move.super_jump");
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
			double vy = p.getY() - jump.lastY;
			prime(p, jump, vy < 0);
			jump.lastY = p.getY();
			jump.step = new Vec3(p.getX() - jump.lastX, 0, p.getZ() - jump.lastZ);
			jump.lastX = p.getX();
			jump.lastZ = p.getZ();
			if (jump.ticks < 4) continue;
			if (p.onGround() || p.isInWater() || p.onClimbable()) {
				it.remove();
				if (jump.primed) shell(p, jump, false);
				if (!jump.carved) carve(p, jump, below(p.level(), p.position(), 3));
				land(p, jump);
			} else if (!jump.carved && vy < -1) {
				// Carved the tick before touchdown, so you land on the crater's floor rather than drop into it.
				BlockPos ground = below(p.level(), p.position(), 2 - vy * 1.2);
				if (ground != null && p.getY() - (ground.getY() + 1) <= Math.max(2, -vy * 1.2)) carve(p, jump, ground);
			}
		}

		for (Iterator<Debris> it = DEBRIS.iterator(); it.hasNext(); ) {
			if (!fly(it.next())) it.remove();
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
		float pick = SPRINT.getOrDefault(player.getUUID(), DEFAULT_SPRINT);
		boolean on = pick > 0 && player.isSprinting() && canUse(player, RingFlight.findRing(player));
		int ticks = on ? SPRINT_TICKS.merge(player.getUUID(), 1, Integer::sum) : 0;
		if (!on) SPRINT_TICKS.remove(player.getUUID());
		float ramp = sprintRamp(ticks);
		float boost = Math.round(pick * ramp * 100) / 100f;
		AttributeModifier current = speed.getModifier(SPRINT_ID);
		if (on) {
			if (current == null || current.amount() != boost) {
				speed.removeModifier(SPRINT_ID);
				speed.addTransientModifier(new AttributeModifier(SPRINT_ID, boost, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
			}
			if (step != null && ramp > 0.3f && !step.hasModifier(STEP_ID)) {
				step.addTransientModifier(new AttributeModifier(STEP_ID, STEP_EXTRA, AttributeModifier.Operation.ADD_VALUE));
			}
			// Dirt kicked up behind your heels, and the odd mote of light.
			if (player.onGround() && player.tickCount % (ramp > 0.6f ? 1 : 3) == 0) {
				ServerLevel level = player.level();
				BlockState ground = level.getBlockState(player.getOnPos());
				Vec3 back = player.getDeltaMovement().multiply(-1.5, 0, -1.5);
				if (!ground.isAir()) {
					level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), player.getX() + back.x, player.getY() + 0.05,
							player.getZ() + back.z, 2, 0.15, 0.02, 0.15, 0.05);
				}
				if (player.tickCount % (jumpCharge(ticks) >= 1f ? 2 : 6) == 0) {
					level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.of(RingFlight.findRing(player))), player.getX() + back.x,
							player.getY() + 0.2, player.getZ() + back.z, 1, 0.1, 0.1, 0.1, 0.01);
				}
			}
		} else {
			if (current != null) speed.removeModifier(SPRINT_ID);
			if (step != null && step.hasModifier(STEP_ID)) step.removeModifier(STEP_ID);
		}
	}

	/**
	 * Left-click held in the air primes the ring; so does crouch held on the way down, at once (pass 518 P2: the
	 * locked head-down dive into the 9x9 crater). Once primed the shell stays up until you land.
	 */
	private static void prime(ServerPlayer p, Jump jump, boolean falling) {
		if (!jump.primed) {
			boolean crouch = falling && p.isShiftKeyDown();
			jump.primeTicks = jump.priming ? jump.primeTicks + 1 : 0;
			if (!crouch && jump.primeTicks < Math.max(1, RingTuning.SUPER_JUMP_PRIME.ticks())) return;
			jump.primed = true;
			Corps before = Corps.enter(jump.corps);
			try {
				CombatMoves.send(p.level(), com.sparky.lanternring.net.CombatFxPayload.Kind.PRIMED_DIVE, p.position(), p.position(), 0, 1, p, -1);
			} finally {
				Corps.restore(before);
			}
			p.sendOverlayMessage(net.minecraft.network.chat.Component.translatable("message.lanternring.super_jump_primed")
					.withStyle(net.minecraft.ChatFormatting.GREEN));
			p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.PLAYERS, 1f, 1.4f);
		}
		if (jump.ticks % 2 == 0) shell(p, jump, true);
	}

	/** The primed ring's hard-light shell under the falling player, drawn like the ram barrier (RamBarrierFx). */
	private static void shell(ServerPlayer p, Jump jump, boolean up) {
		Vec3 mid = p.getBoundingBox().getCenter();
		Corps before = Corps.enter(jump.corps);
		try {
			RingFx.send(p.level(), Kind.RAM_BARRIER, mid, mid.add(0, -1, 0), up ? 1f : 0f, p.getId(), null);
		} finally {
			Corps.restore(before);
		}
	}

	/** Touchdown: the harder the fall, the bigger the quake. */
	private static void land(ServerPlayer p, Jump jump) {
		ServerLevel level = p.level();
		double drop = Math.max(0, jump.peakY - p.getY());
		float strength = (float) Mth.clamp(0.25 + drop / 30, 0.25, 2.0);
		double reach = Mth.clamp(MIN_REACH + drop * 0.25, MIN_REACH, MAX_REACH);
		if (jump.primed) {
			strength = Math.min(2.6f, strength + 0.6f);
			reach = Math.min(PRIMED_MAX_REACH, reach * PRIMED_SCALE);
		}
		Vec3 feet = p.position();
		Corps before = Corps.enter(jump.corps);
		try {
			if (jump.primed) {
				// The shell slams down into a dome of hard light and the ground caves in under it.
				RingFx.send(level, Kind.RAM_BREAK, feet, feet, 0f, p.getId(), null);
				RingFx.send(level, Kind.SHOCKWAVE, feet, feet.add(reach * 0.55, 0, 0));
				// Pass 518 P2: the 9x9 opens at once and is lined; left click held sweeps it back (PrimedSlams).
				// From the client's own touchdown spot: the server sees the landing a tick late, a block or so on.
				Vec3 reported = PowerLandings.takeReport(p);
				PrimedSlams.open(p, reported != null && reported.distanceToSqr(feet) < 9 ? reported : feet, PrimedSlams.JUMP_REACH, true);
				WhatsNew.done(p, "slam.primed_jump");
				level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 2f, 0.7f);
			}
			// Unprimed on solid ground: J's power landing (stop dead, or the slide in place of the run-out).
			boolean power = !jump.primed && !p.isInWater() && level.getFluidState(BlockPos.containing(feet.x, feet.y - 0.05, feet.z)).isEmpty();
			int variant = (jump.primed ? PRIMED_BIT : 0) | (jump.deep ? DEEP_BIT : 0) | (power ? POWER_BIT : 0);
			if (power) PowerLandings.landed(p, jump.corps, feet, jump.step, CRATER.getOrDefault(p.getUUID(), 0) == 0);
			// The crater first, so the landing can line it with the pad.
			else CraterLiningPayload.send(level, p.getId(), jump.corps, feet, 0, jump.destroyed);
			RingFx.send(level, Kind.SUPER_LAND, feet, feet.add(reach, 0, 0), strength, variant, p);
			Quake quake = new Quake(level, feet, jump.corps, reach, true, p);
			quake.scorch = true;
			quake.primed = jump.primed;
			quake.killReach = Math.max(3, reach * (jump.primed ? KILL_PRIMED : KILL_PART));
			quake.maxDamage = jump.primed ? 30f : 18f;
			QUAKES.add(quake);
			dust(level, feet, 1.5, 40 + (int) (40 * strength), 0.3 + 0.2 * strength);
			// A few dim motes (J's Blender pass: about 8, not 30).
			level.sendParticles(ModParticles.of(ModParticles.MOTE, jump.corps), feet.x, feet.y + 0.2, feet.z, 8, 1.2, 0.2, 1.2, 0.08);
			level.sendParticles(ModParticles.of(ModParticles.SHARD, jump.corps), feet.x, feet.y + 0.2, feet.z, 14, 0.6, 0.1, 0.6, 0.25);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.PLAYERS, 1.2f + 0.6f * strength, 0.7f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.5f + 0.6f * strength, 0.55f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 1.5f, 0.5f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.FIRECHARGE_USE, SoundSource.PLAYERS, 1.2f, 0.6f);
	}

	/** The top block you'd land on below at (solid, or water), searching down to reach blocks under your feet, or null. */
	private static @Nullable BlockPos below(ServerLevel level, Vec3 at, double reach) {
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		int top = Mth.floor(at.y + 0.5);
		for (int y = top; y >= Mth.floor(at.y - reach - 1); y--) {
			pos.set(Mth.floor(at.x), y, Mth.floor(at.z));
			BlockState state = level.getBlockState(pos);
			if (!state.getFluidState().isEmpty() || !state.getCollisionShape(level, pos).isEmpty()) return pos.immutable();
		}
		return null;
	}

	/** Notes the ground the jump lands on, the tick before touchdown, and whether it was the deeper fall. */
	private static void carve(ServerPlayer p, Jump jump, @Nullable BlockPos top) {
		jump.carved = true;
		if (top == null) return;
		jump.ground = top;
		jump.deep = jump.fromY - (top.getY() + 1) > DEEP;
		// An unprimed landing on the ground is a power landing (PowerLandings), and a primed one opens its own 9x9
		// crater at touchdown (PrimedSlams, pass 518): neither digs the old stepped bowl.
	}

	/** Moves a thrown block one tick: out and up, falling, shrinking away. False once it's gone. */
	private static boolean fly(Debris d) {
		if (d.delay > 0) {
			d.delay--;
			return true;
		}
		if (d.body == null) {
			Display.BlockDisplay body = EntityTypes.BLOCK_DISPLAY.create(d.level, EntitySpawnReason.TRIGGERED);
			if (body == null) return false;
			body.setBlockState(d.state);
			body.setPosRotInterpolationDuration(1);
			body.setTransformationInterpolationDuration(1);
			body.setViewRange(2f);
			body.setPos(d.pos.x, d.pos.y, d.pos.z);
			d.body = body;
			shape(d);
			d.level.addFreshEntity(body);
			return true;
		}
		d.age++;
		if (d.age >= DEBRIS_LIFE || !d.body.isAlive()) {
			d.body.discard();
			return false;
		}
		d.pos = d.pos.add(d.vel);
		d.vel = new Vec3(d.vel.x * 0.98, (d.vel.y - 0.04) * 0.98, d.vel.z * 0.98);
		d.body.setPos(d.pos.x, d.pos.y, d.pos.z);
		shape(d);
		return true;
	}

	/** A thrown block's size now, centred on its position and tumbling a little. */
	private static void shape(Debris d) {
		float s = d.size * (1 - d.age / (float) DEBRIS_LIFE);
		Quaternionf turn = new Quaternionf().rotationXYZ(d.age * 0.25f, d.age * 0.4f, 0f);
		Vector3f centre = turn.transform(new Vector3f(-s / 2, -s / 2, -s / 2));
		d.body.setTransformationInterpolationDelay(0);
		d.body.setTransformation(new Transformation(centre, turn, new Vector3f(s), new Quaternionf()));
	}

	/** Whether a landing spares this: its jumper's pets, construct allies and villagers. */
	private static boolean spared(Entity e, @Nullable Entity owner) {
		if (e instanceof com.sparky.lanternring.ally.ConstructAlly || e instanceof net.minecraft.world.entity.npc.villager.AbstractVillager) return true;
		return e instanceof TamableAnimal pet && owner instanceof LivingEntity o && pet.isOwnedBy(o);
	}

	/**
	 * The landing burns the ground at pos (the top solid block) as the wave reaches it: whatever grows
	 * on it burns away, grass and dirt char to coarse dirt, and in the middle (core) natural ground
	 * turns to blackstone, sand to glass. Builds are left alone: only natural ground changes.
	 */
	private static void scorch(ServerLevel level, BlockPos pos, boolean core) {
		BlockPos above = pos.above();
		BlockState top = level.getBlockState(above);
		if (!top.isAir() && top.canBeReplaced() && top.getFluidState().isEmpty()) level.setBlock(above, Blocks.AIR.defaultBlockState(), 3);
		BlockState state = level.getBlockState(pos);
		BlockState to = null;
		if (state.is(Blocks.ICE) || state.is(Blocks.SNOW_BLOCK)) {
			to = Blocks.WATER.defaultBlockState();
		} else if (state.is(BlockTags.SAND)) {
			if (core) to = Blocks.GLASS.defaultBlockState();
		} else if (state.is(BlockTags.SUBSTRATE_OVERWORLD) || state.is(Blocks.GRAVEL) || state.is(Blocks.FARMLAND) || state.is(Blocks.DIRT_PATH)) {
			to = core ? Blocks.BLACKSTONE.defaultBlockState() : state.is(Blocks.COARSE_DIRT) ? null : Blocks.COARSE_DIRT.defaultBlockState();
		} else if (core && state.is(BlockTags.BASE_STONE_OVERWORLD)) {
			to = Blocks.BLACKSTONE.defaultBlockState();
		}
		if (to != null) level.setBlock(pos, to, 3);
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
		if (q.scorch) {
			// Every bit of ground the wave passes this tick, charred as it arrives.
			int ri = (int) Math.ceil(r);
			RandomSource rand = q.level.getRandom();
			var flame = ParticleTypes.FLAME;
			for (int dx = -ri; dx <= ri; dx++) {
				for (int dz = -ri; dz <= ri; dz++) {
					double d = Math.sqrt(dx * dx + dz * dz);
					if (d > r || d <= from && from > 0) continue;
					double frac = d / q.reach;
					boolean core = frac < (q.primed ? 0.45 : 0.3);
					// Patchier toward the edge, unless primed.
					if (!core && !q.primed && rand.nextDouble() < frac * 0.6) continue;
					BlockPos ground = groundAt(q.level, q.centre.x + dx, q.centre.z + dz, q.centre.y);
					if (ground == null) continue;
					scorch(q.level, ground, core);
					if (rand.nextInt(3) == 0) {
						double x = ground.getX() + rand.nextDouble(), y = ground.getY() + 1.05, z = ground.getZ() + rand.nextDouble();
						q.level.sendParticles(flame, x, y, z, 1, 0.05, 0.02, 0.05, 0.02);
						if (rand.nextInt(2) == 0) q.level.sendParticles(ParticleTypes.LARGE_SMOKE, x, y + 0.2, z, 1, 0.1, 0.05, 0.1, 0.01);
					}
				}
			}
		}
		if (q.lift) {
			double fade = 1 - from / q.reach;
			for (Entity e : q.level.getEntities((Entity) null, new AABB(q.centre, q.centre).inflate(r + 1, 4, r + 1),
					e -> e != q.owner && e.isAlive() && !e.isSpectator() && (e instanceof LivingEntity || e instanceof ItemEntity))) {
				double dx = e.getX() - q.centre.x, dz = e.getZ() - q.centre.z;
				double d = Math.sqrt(dx * dx + dz * dz);
				if (d > r || d < from - 0.01 && from > 0 || !q.hit.add(e.getId())) continue;
				if (q.maxDamage > 0 && e instanceof LivingEntity living && !spared(e, q.owner)) {
					var source = q.owner instanceof LivingEntity o ? q.level.damageSources().indirectMagic(o, o) : q.level.damageSources().magic();
					float damage;
					if (d <= q.killReach && !(e instanceof Player)) damage = living.getMaxHealth() + 1000f;
					else damage = (float) (q.maxDamage * Mth.clamp(1 - (d - q.killReach) / Math.max(1, q.reach - q.killReach), 0.1, 1));
					living.hurtServer(q.level, source, damage);
					if (!living.isAlive()) continue;
				}
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
