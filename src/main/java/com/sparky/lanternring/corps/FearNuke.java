package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import net.minecraft.world.level.block.Block;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.Terror;
import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Yellow Lantern's aerial drop, Sinestro's Fear Nuke (J, 2026-10-12). Its size comes from the fear
 * its bearer has caused on their fear ground, so Sinestro has to hold his ground:
 * <ul>
 * <li>Every mob he keeps frightened within {@link #GROUND} blocks adds fear each second, and every one
 * that dies afraid (or that he kills) adds a lot more. Its fear streams out of the body and flows to
 * him like XP orbs when there's an abundance of levels, and settles on the floor round him as a thin
 * yellow smoke that spreads wider the more fear there is. Walk more than 50 blocks off the ground and
 * the fear slips away.</li>
 * <li>The nuke costs 90% of a full ring with no fear, falling to 75% at full fear (see
 * {@link #cost}). Holding right-click raises the ring arm and the bomb of yellow hard light drops out
 * of the sky into place over it in RingTuning.FEAR_NUKE_BUILD (J, 2026-10-15), tethered to the ring by a
 * line of light while the fear on the ground streams up into it; everyone sees the arm come up (the
 * client's NukeHold). Let go and it's thrown the way the bearer looks, a heavy arc with no hovering
 * and no control, and goes off on contact or once its bottom is {@link #AIRBURST} blocks over the
 * ground ({@link #blast}).</li>
 * <li>The airburst does no damage. Its yellow aura ({@link Burn}) burns out a crater 40 blocks
 * across with no fear up to 80 at full fear (4x the old blast's), and its yellow gas lingers and
 * gives every mob in reach Fear Frenzy: they turn on each other with yellow construct weapons
 * ({@link FearFrenzy}). Yellow ring bearers are spared.</li>
 * </ul>
 * The fear is kept on the ring ({@code lanternring:fear}), so the HUD and tooltip can show it.
 */
public final class FearNuke {
	public static final int FULL = 100;
	/** The fear ground's radius. */
	public static final double GROUND = 50;
	static final float POWER_MIN = 8f, POWER_MAX = 16f;
	/** The orb's radius as it forms (it swells by up to 2 more as it drinks in fear). */
	static final int ORB = 4;
	private static final DustParticleOptions SMOKE = new DustParticleOptions(0xE8C83A, 0.8f);
	private static final DustParticleOptions SPARK = new DustParticleOptions(0xFFE870, 0.9f);
	private static final DustParticleOptions BLAST = new DustParticleOptions(0xFFD21A, 2.5f);

	private FearNuke() {
	}

	// ---- fear on the ring -----------------------------------------------------------------------

	public static int fear(ItemStack ring) {
		return Mth.clamp(ring.getOrDefault(ModComponents.FEAR, 0), 0, FULL);
	}

	/** 90% of a full ring with no fear, down to 75% at full fear. */
	public static int cost(ItemStack ring) {
		return PowerRingItem.MAX_CHARGE * 90 / 100 - PowerRingItem.MAX_CHARGE * 15 / 100 * fear(ring) / FULL;
	}

	public static float power(double fear) {
		return (float) (POWER_MIN + (POWER_MAX - POWER_MIN) * Mth.clamp(fear / FULL, 0, 1));
	}

	/** How many times wider the airburst's crater is than the old ground blast's (J, 2026-10-13: "at least a 4x larger crater"). */
	static final double CRATER_SCALE = 4;

	/** The crater's radius: 40 blocks with no fear, up to 80 at full fear. */
	public static double crater(double fear) {
		return power(fear) * 1.25 * CRATER_SCALE;
	}

	/** How far the yellow gas reaches, and with it the frenzy: a little past the crater's rim. */
	public static double reach(double fear) {
		return crater(fear) + 8;
	}

	public static Component status(ItemStack ring) {
		return Component.translatable("message.lanternring.fear_nuke_status", fear(ring), String.valueOf(cost(ring) / 10),
				String.valueOf(Math.round(crater(fear(ring)))));
	}

	/** The yellow ring this player has on them (hands first), or empty. */
	static ItemStack yellowRing(Player player) {
		for (ItemStack s : new ItemStack[] {player.getMainHandItem(), player.getOffhandItem(), com.sparky.lanternring.RingSlot.worn(player)}) {
			if (s.getItem() instanceof PowerRingItem && Corps.of(s) == Corps.YELLOW) return s;
		}
		for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
			ItemStack s = player.getInventory().getItem(i);
			if (s.getItem() instanceof PowerRingItem && Corps.of(s) == Corps.YELLOW) return s;
		}
		return ItemStack.EMPTY;
	}

	/** Whether {@code e} holds a yellow ring: the nuke spares Sinestro's corps. */
	static boolean spared(Entity e, @Nullable UUID owner) {
		if (owner != null && e.getUUID().equals(owner)) return true;
		if (e instanceof ConstructAlly) return true;
		if (e instanceof Player p && (p.isCreative() || p.isSpectator())) return true;
		if (e instanceof LivingEntity living) {
			for (ItemStack s : new ItemStack[] {living.getMainHandItem(), living.getOffhandItem(), com.sparky.lanternring.RingSlot.worn(living)}) {
				if (s.getItem() instanceof PowerRingItem && Corps.of(s) == Corps.YELLOW) return true;
			}
		}
		return false;
	}

	// ---- the fear ground --------------------------------------------------------------------------

	private static final class Ground {
		@Nullable Vec3 centre;
		@Nullable ResourceKey<Level> dim;
		double fear;
		long slipNote = Long.MIN_VALUE / 2;
		/** Its fear is being drawn into a nuke (built in the hand, or in the air): nothing more is gathered meanwhile. */
		boolean consuming;
	}

	private static final Map<UUID, Ground> GROUNDS = new HashMap<>();

	private static Ground ground(Player player, ItemStack ring) {
		return GROUNDS.computeIfAbsent(player.getUUID(), id -> {
			Ground g = new Ground();
			g.fear = fear(ring);
			return g;
		});
	}

	private static void sync(Ground g, ItemStack ring) {
		int v = (int) Math.round(g.fear);
		if (!ring.isEmpty() && ring.getOrDefault(ModComponents.FEAR, 0) != v) ring.set(ModComponents.FEAR, v);
	}

	private static boolean off(Ground g, Player p) {
		if (g.centre == null) return false;
		if (g.dim != p.level().dimension()) return true;
		double dx = p.getX() - g.centre.x, dz = p.getZ() - g.centre.z;
		return dx * dx + dz * dz > GROUND * GROUND;
	}

	/** Once a second for each player with a yellow ring: fear from the mobs they keep frightened, or fear slipping away if they left. */
	private static void groundTick(ServerPlayer player) {
		ItemStack ring = yellowRing(player);
		if (ring.isEmpty()) return;
		Ground g = ground(player, ring);
		if (g.consuming) return;
		ServerLevel level = player.level();
		if (g.centre == null && g.fear > 0) {
			// Fear kept on the ring from before a restart: the ground is wherever they are now.
			g.centre = player.position();
			g.dim = level.dimension();
		}
		if (off(g, player)) {
			g.fear = Math.max(0, g.fear - 5);
			long now = level.getGameTime();
			if (now - g.slipNote > 60) {
				g.slipNote = now;
				player.sendOverlayMessage(Component.translatable("message.lanternring.fear_ground_slipping").withStyle(ChatFormatting.GOLD));
			}
		} else {
			int feared = Terror.fearedNear(level, g.centre != null ? g.centre : player.position(), GROUND, player.getUUID());
			if (feared > 0) {
				if (g.centre == null) {
					g.centre = player.position();
					g.dim = level.dimension();
				}
				g.fear = Math.min(FULL, g.fear + feared * 0.5);
			}
		}
		if (g.fear <= 0) {
			g.fear = 0;
			g.centre = null;
		}
		sync(g, ring);
	}

	/** Something died: if it died afraid of a yellow bearer (or they killed it) on their ground, its fear flows to them. */
	private static void died(LivingEntity dead, DamageSource source) {
		if (!(dead.level() instanceof ServerLevel level) || dead instanceof Player && ((Player) dead).isSpectator()) return;
		UUID owner = Terror.fearerId(dead);
		ServerPlayer player = owner != null ? level.getServer().getPlayerList().getPlayer(owner) : null;
		if ((player == null || yellowRing(player).isEmpty()) && source.getEntity() instanceof ServerPlayer killer && !yellowRing(killer).isEmpty()) {
			player = killer;
		}
		if (player == null || player == dead || player.level() != level || player.distanceToSqr(dead) > GROUND * GROUND) return;
		ItemStack ring = yellowRing(player);
		if (ring.isEmpty()) return;
		Ground g = ground(player, ring);
		if (g.consuming) return;
		if (g.centre == null || g.dim != level.dimension()) {
			g.centre = player.position();
			g.dim = level.dimension();
		} else if (off(g, player)) {
			return;
		}
		double gain = Mth.clamp(4 + dead.getMaxHealth() / 10, 4, 25);
		g.fear = Math.min(FULL, g.fear + gain);
		sync(g, ring);
		RandomSource random = level.getRandom();
		Vec3 body = dead.getBoundingBox().getCenter();
		for (int i = 0; i < 6 + (int) gain; i++) {
			Vec3 at = body.add((random.nextDouble() - 0.5) * dead.getBbWidth(), (random.nextDouble() - 0.5) * dead.getBbHeight(),
					(random.nextDouble() - 0.5) * dead.getBbWidth());
			Vec3 vel = new Vec3(random.nextGaussian() * 0.2, 0.2 + random.nextDouble() * 0.3, random.nextGaussian() * 0.2);
			WISPS.add(new Wisp(level, at, vel, player.getUUID(), null));
		}
		level.playSound(null, dead.getX(), dead.getY(), dead.getZ(), SoundEvents.SOUL_ESCAPE.value(), SoundSource.HOSTILE, 1.2f, 0.7f);
	}

	/** The thin yellow smoke over a fear ground, wider and thicker the more fear there is. */
	private static void smoke(ServerLevel level, Ground g, RandomSource random) {
		if (g.centre == null || g.fear <= 0) return;
		double r = 4 + (GROUND - 4) * g.fear / FULL;
		int count = 3 + (int) (g.fear / 3);
		for (int i = 0; i < count; i++) {
			double a = random.nextDouble() * Math.PI * 2, d = Math.sqrt(random.nextDouble()) * r;
			double x = g.centre.x + Math.cos(a) * d, z = g.centre.z + Math.sin(a) * d;
			double y = floor(level, x, g.centre.y, z);
			if (Double.isNaN(y)) continue;
			level.sendParticles(SMOKE, x, y + 0.08, z, 1, 0.4, 0.02, 0.4, 0.002);
			if (random.nextInt(3) == 0) level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.YELLOW), x, y + 0.15, z, 1, 0.3, 0.05, 0.3, 0.004);
		}
	}

	/** The top of the floor under (x, z) near height {@code near}, or NaN if there isn't one close by. */
	private static double floor(ServerLevel level, double x, double near, double z) {
		BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos(Mth.floor(x), Mth.floor(near) + 4, Mth.floor(z));
		for (int i = 0; i < 14; i++) {
			BlockPos below = p.below();
			if (level.getBlockState(p).getCollisionShape(level, p).isEmpty()
					&& !level.getBlockState(below).getCollisionShape(level, below).isEmpty()) return p.getY();
			p.move(0, -1, 0);
		}
		return Double.NaN;
	}

	// ---- wisps of fear ------------------------------------------------------------------------------

	/** A wisp of fear flowing to a player (like an XP orb), or to a nuke's orb. */
	private static final class Wisp {
		final ServerLevel level;
		Vec3 pos, vel;
		final @Nullable UUID to;
		final @Nullable Nuke orb;
		/** Flows into the nuke {@link #to} is forming in the sky rather than to their body. */
		final boolean hand;
		int age;

		Wisp(ServerLevel level, Vec3 pos, Vec3 vel, @Nullable UUID to, @Nullable Nuke orb) {
			this(level, pos, vel, to, orb, false);
		}

		Wisp(ServerLevel level, Vec3 pos, Vec3 vel, @Nullable UUID to, @Nullable Nuke orb, boolean hand) {
			this.level = level;
			this.pos = pos;
			this.vel = vel;
			this.to = to;
			this.orb = orb;
			this.hand = hand;
		}
	}

	private static final List<Wisp> WISPS = new ArrayList<>();

	private static void wisps() {
		for (Iterator<Wisp> it = WISPS.iterator(); it.hasNext(); ) {
			Wisp w = it.next();
			Vec3 target;
			if (w.orb != null) {
				target = w.orb.pos;
			} else {
				Player p = w.to == null ? null : w.level.getPlayerByUUID(w.to);
				if (p == null) {
					it.remove();
					continue;
				}
				target = w.hand ? forming(p) : p.position().add(0, 0.9, 0);
			}
			Vec3 d = target.subtract(w.pos);
			double dist = d.length();
			double arrive = w.orb != null ? w.orb.radius() : w.hand ? 2.5 : 0.9;
			if (dist < arrive || ++w.age > 200) {
				it.remove();
				if (w.orb == null && !w.hand) {
					// It settles into the smoke round their feet.
					w.level.sendParticles(SMOKE, w.pos.x, w.pos.y - 0.6, w.pos.z, 3, 0.8, 0.05, 0.8, 0.002);
					if (w.level.getRandom().nextInt(4) == 0) {
						w.level.playSound(null, w.pos.x, w.pos.y, w.pos.z, SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.PLAYERS,
								0.15f, 0.5f + w.level.getRandom().nextFloat() * 0.4f);
					}
				}
				continue;
			}
			w.vel = w.vel.scale(0.86).add(d.scale(0.16 / dist));
			double speed = w.vel.length();
			if (speed > 1.3) w.vel = w.vel.scale(1.3 / speed);
			w.pos = w.pos.add(w.vel);
			w.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.YELLOW), w.pos.x, w.pos.y, w.pos.z, 1, 0, 0, 0, 0);
			w.level.sendParticles(SPARK, w.pos.x, w.pos.y, w.pos.z, 1, 0.05, 0.05, 0.05, 0);
		}
	}

	// ---- holding it over the ring ----------------------------------------------------------------------

	/** A nuke a bearer holds up over their raised ring, ready to throw. */
	private static final class Build {
		final ServerLevel level;
		final long start;
		/** The ground's fear when it started: it drains into the bomb as it drops in, and goes back if it's let go early. */
		final double fear;
		/** Where it is held now: over the raised ring, following the bearer. */
		Vec3 site;
		boolean readyNoted;

		Build(ServerLevel level, double fear, Vec3 site) {
			this.level = level;
			this.start = level.getGameTime();
			this.fear = fear;
			this.site = site;
		}
	}

	private static final Map<UUID, Build> BUILDS = new HashMap<>();

	/** How far ahead of the eyes and how high over them the held bomb's middle is: its nose stays clear of the bearer's view and of the ground. */
	static final double HOLD_OUT = 4, HOLD_UP = 9;

	/** Where the bomb is held: up over the bearer's head and a little ahead, the way they're facing. */
	public static Vec3 held(Player player) {
		Vec3 look = player.getLookAngle();
		Vec3 flat = new Vec3(look.x, 0, look.z);
		flat = flat.lengthSqr() < 1e-4 ? Vec3.directionFromRotation(0, player.getYRot()) : flat.normalize();
		return player.getEyePosition().add(flat.scale(HOLD_OUT)).add(0, HOLD_UP, 0);
	}

	/** Where this bearer's nuke is held, or where it would be if they aren't holding one. */
	public static Vec3 forming(Player player) {
		Build b = BUILDS.get(player.getUUID());
		return b != null ? b.site : held(player);
	}

	/** Ticks a nuke takes to drop into place. */
	public static int buildTicks() {
		return Math.max(1, RingTuning.FEAR_NUKE_BUILD.ticks());
	}

	/** How far it has dropped into place over this bearer, 0..1, or -1 if they aren't holding one. */
	public static float building(Player player) {
		Build b = BUILDS.get(player.getUUID());
		if (b == null) return -1f;
		return building(b);
	}

	private static float building(Build b) {
		return Mth.clamp((b.level.getGameTime() - b.start) / (float) buildTicks(), 0f, 1f);
	}

	/**
	 * Each tick the bearer holds right-click in Aerial mode (J, 2026-10-15: "the nuke should drop where i begin
	 * to hold right click instead of forming there"): the bomb drops out of the sky into place over the raised
	 * ring in {@link #buildTicks} and is carried there, following the bearer, until they let go and throw it.
	 * The fear on their ground streams up into it.
	 */
	public static void buildTick(ServerPlayer player, ItemStack ring) {
		ServerLevel level = player.level();
		Ground g = ground(player, ring);
		Build b = BUILDS.get(player.getUUID());
		if (b == null || b.level != level) {
			if (busy(player)) return;
			b = new Build(level, g.fear, held(player));
			BUILDS.put(player.getUUID(), b);
			g.consuming = true;
			level.playSound(null, b.site.x, b.site.y, b.site.z, SoundEvents.FIREWORK_ROCKET_LAUNCH, SoundSource.PLAYERS, 2f, 0.4f);
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.5f, 0.6f);
		}
		b.site = held(player);
		long t = level.getGameTime() - b.start;
		float k = building(b);
		g.fear = b.fear * (1 - k);
		sync(g, ring);
		Vec3 hand = b.site;
		// Each client draws the bomb dropping in and the line of light from the bearer's ring up to it.
		Corps before = Corps.enter(Corps.YELLOW);
		try {
			RingFx.send(level, Kind.FEAR_NUKE_FORM, hand, hand, k, buildTicks(), player);
		} finally {
			Corps.restore(before);
		}
		if (t % 4 == 0) hud(player, k);
		if (k < 1f) {
			if (t % 2 == 0) level.sendParticles(SPARK, true, false, hand.x, hand.y, hand.z, 6, 1.6, 1.6, 1.6, 0.04);
			// The fear on the ground streams up into it.
			if (g.centre != null && b.fear > 0 && g.centre.distanceToSqr(player.position()) < GROUND * GROUND) {
				RandomSource random = level.getRandom();
				double spread = 4 + (GROUND - 4) * b.fear / FULL;
				for (int i = 0; i < 2 + (int) (6 * b.fear / FULL); i++) {
					double a = random.nextDouble() * Math.PI * 2, d = Math.sqrt(random.nextDouble()) * spread;
					double fx = g.centre.x + Math.cos(a) * d, fz = g.centre.z + Math.sin(a) * d;
					double fy = floor(level, fx, g.centre.y, fz);
					if (Double.isNaN(fy)) continue;
					WISPS.add(new Wisp(level, new Vec3(fx, fy + 0.2, fz), new Vec3(0, 0.25, 0), player.getUUID(), null, true));
				}
			}
		} else {
			if (!b.readyNoted) {
				// It lands in place over the ring with a heavy clunk.
				b.readyNoted = true;
				level.playSound(null, hand.x, hand.y, hand.z, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 1.5f, 0.5f);
				level.playSound(null, hand.x, hand.y, hand.z, SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 2f, 0.6f);
			}
			if (t % 3 == 0) level.sendParticles(SPARK, true, false, hand.x, hand.y, hand.z, 3, 1.5, 2, 1.5, 0.01);
			int beat = 10;
			if (t % beat == 0) level.playSound(null, hand.x, hand.y, hand.z, SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 1.5f, 0.9f);
		}
	}

	/** The action bar while it's held: dropping in, then ready to throw. */
	private static void hud(ServerPlayer player, float k) {
		Component text = k < 1f
				? Component.translatable("message.lanternring.fear_nuke_building", Math.round(k * 100))
				: Component.translatable("message.lanternring.fear_nuke_built");
		player.sendOverlayMessage(text.copy().withStyle(k < 1f ? ChatFormatting.YELLOW : ChatFormatting.GOLD));
	}

	/** Whether the bearer's nuke has dropped into place and can be thrown. */
	public static boolean built(Player player) {
		return building(player) >= 1f;
	}

	/** Let go before it was in place, or the power was dropped: it comes apart and the fear goes back to the ground. */
	public static void cancelBuild(Player player) {
		Build b = BUILDS.remove(player.getUUID());
		if (b == null) return;
		Ground g = GROUNDS.get(player.getUUID());
		if (g != null) {
			g.fear = b.fear;
			g.consuming = false;
			sync(g, yellowRing(player));
		}
		Vec3 at = b.site;
		Corps before = Corps.enter(Corps.YELLOW);
		try {
			RingFx.send(b.level, Kind.FEAR_NUKE_SCATTER, at, at, building(b), 1, player);
		} finally {
			Corps.restore(before);
		}
		b.level.sendParticles(SMOKE, true, false, at.x, at.y, at.z, 30, 2, 2, 2, 0.05);
		b.level.playSound(null, at.x, at.y, at.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 3f, 0.7f);
	}

	// ---- the throw -------------------------------------------------------------------------------------

	/**
	 * How it flies once thrown (J, 2026-10-15: "where i let go it throws it in that direction ... it should
	 * explode on contact or about 5 blocks above the ground"): launched at {@link #THROW} blocks a tick the way
	 * the bearer looks, then nothing but drag and heavy gravity. No hovering and no steering.
	 */
	public static final double THROW = 2.2, GRAVITY = 0.08, DRAG = 0.99;
	/** How high over the ground the bottom of the bomb is when it airbursts. */
	public static final double AIRBURST = 5;
	/** The bomb as drawn (FearNukeFx, fear_nuke.bbmodel at 3x): from its middle out to the nose, back to the tail, and out to the side. */
	public static final double NOSE = 4.3, TAIL = 6.2, SIDE = 2.25;

	/** One tick of flight: the velocity after drag and gravity. The client draws the same steps (FearNukeFx). */
	public static Vec3 nextVelocity(Vec3 vel) {
		return vel.scale(DRAG).add(0, -GRAVITY, 0);
	}

	/** The way the nose points, flying along {@code vel} (straight down when it's still). */
	public static Vec3 heading(Vec3 vel) {
		double len = vel.length();
		return len < 1e-6 ? new Vec3(0, -1, 0) : vel.scale(1 / len);
	}

	/** The lowest point of the bomb with its middle at {@code pos}, nose first along {@code vel}. */
	public static double bottom(Vec3 pos, Vec3 vel) {
		double dy = heading(vel).y;
		return pos.y + Math.min(NOSE * dy, -TAIL * dy) - SIDE * Math.sqrt(Math.max(0, 1 - dy * dy));
	}

	/** Ticks it may fly before it goes off anyway (thrown off a cliff into the void, say). */
	static int flightTicks() {
		return Math.max(20, RingTuning.FEAR_NUKE_FLIGHT.ticks());
	}

	private static final class Nuke {
		final ServerLevel level;
		final UUID owner;
		final Ground ground;
		final double fear;
		final double crater;
		final double reach;
		Vec3 pos, vel;
		int age;

		Nuke(ServerLevel level, UUID owner, Ground ground, double fear, Vec3 pos, Vec3 vel) {
			this.level = level;
			this.owner = owner;
			this.ground = ground;
			this.fear = fear;
			this.crater = crater(fear);
			this.reach = reach(fear);
			this.pos = pos;
			this.vel = vel;
		}

		double radius() {
			return ORB;
		}
	}

	private static final List<Nuke> NUKES = new ArrayList<>();

	/** Where the last nuke went off, how high its bottom was over the ground then, and after how many ticks of flight (tests). */
	public record Burst(Vec3 at, double height, int ticks) {
	}

	public static @Nullable Burst lastBurst;

	/** Where this bearer's thrown nuke is now, or null (tests). */
	public static @Nullable Vec3 flying(Player player) {
		for (Nuke n : NUKES) {
			if (n.owner.equals(player.getUUID())) return n.pos;
		}
		return null;
	}

	public static boolean busy(Player player) {
		for (Nuke n : NUKES) {
			if (n.owner.equals(player.getUUID())) return true;
		}
		return false;
	}

	/** How far out the marker looks for ground. */
	static final double AIM_RANGE = 90;

	/** The spot on the ground the bearer is looking at, up to {@link #AIM_RANGE} away, or null. */
	public static @Nullable BlockPos findMark(ServerLevel level, Player player) {
		Vec3 eye = player.getEyePosition();
		var hit = level.clip(new ClipContext(eye, eye.add(player.getLookAngle().scale(AIM_RANGE)), ClipContext.Block.COLLIDER,
				ClipContext.Fluid.NONE, player));
		if (hit.getType() == HitResult.Type.MISS) return null;
		BlockPos pos = hit.getBlockPos().relative(hit.getDirection());
		for (int i = 0; i < 24 && pos.getY() > level.getMinY(); i++) {
			BlockState below = level.getBlockState(pos.below());
			if (!below.canBeReplaced() && !below.is(ModRegistry.LIGHT_CONSTRUCT)) return pos;
			pos = pos.below();
		}
		return null;
	}

	/** The velocity it leaves the bearer's hand with: thrown the way they look, carrying their own speed. */
	static Vec3 throwVelocity(Player player) {
		return player.getLookAngle().scale(THROW).add(player.getDeltaMovement());
	}

	/**
	 * Where a bomb thrown now would go off, ignoring mobs in its way (the marker while aiming), or null if it
	 * wouldn't before {@link #flightTicks}.
	 */
	public static @Nullable Vec3 predict(ServerLevel level, Player player) {
		Vec3 pos = forming(player), vel = throwVelocity(player);
		for (int age = 1; age <= flightTicks(); age++) {
			Vec3 prev = pos;
			vel = nextVelocity(vel);
			pos = pos.add(vel);
			Vec3 at = strikes(level, prev, pos, vel, age, null);
			if (at != null) return at;
		}
		return null;
	}

	/** Where the nuke would land, as the marker's block: the ground under where it goes off. */
	public static @Nullable BlockPos predictMark(ServerLevel level, Player player) {
		Vec3 at = predict(level, player);
		return at == null ? null : BlockPos.containing(ground(level, at));
	}

	/**
	 * Whether the bomb, moving from {@code prev} to {@code pos} on its {@code age}th tick, goes off: it hits a
	 * block (or, when {@code owner} is given, anything living other than the thrower) nose first, or its
	 * bottom comes down within {@link #AIRBURST} blocks of the ground. Returns where its middle is when it
	 * goes off, or null to fly on.
	 */
	private static @Nullable Vec3 strikes(ServerLevel level, Vec3 prev, Vec3 pos, Vec3 vel, int age, @Nullable UUID owner) {
		Vec3 dir = heading(vel);
		Vec3 noseFrom = prev.add(dir.scale(NOSE)), noseTo = pos.add(dir.scale(NOSE));
		BlockHitResult wall = level.clip(new ClipContext(noseFrom, noseTo, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE,
				CollisionContext.empty()));
		Vec3 hitAt = wall.getType() == HitResult.Type.MISS ? null : wall.getLocation().subtract(dir.scale(NOSE));
		if (owner != null) {
			AABB sweep = new AABB(prev, pos).inflate(NOSE + SIDE);
			for (Entity e : level.getEntities((Entity) null, sweep, e -> e.isAlive() && !e.getUUID().equals(owner) && !e.isSpectator()
					&& (e instanceof LivingEntity || e.isPickable()))) {
				var touch = e.getBoundingBox().inflate(SIDE).clip(prev, noseTo);
				if (touch.isEmpty() && !e.getBoundingBox().inflate(SIDE).contains(pos)) continue;
				Vec3 at = touch.map(p -> p.subtract(dir.scale(NOSE))).orElse(pos);
				if (hitAt == null || at.distanceToSqr(prev) < hitAt.distanceToSqr(prev)) hitAt = at;
			}
		}
		if (hitAt != null) return hitAt;
		if (pos.y < level.getMinY() || age >= flightTicks()) return pos;
		// The airburst: only on the way down, and not right out of the hand.
		if (vel.y < 0 && age >= 3) {
			Vec3 low = new Vec3(pos.x, bottom(pos, vel), pos.z);
			BlockHitResult under = level.clip(new ClipContext(low, low.add(0, -AIRBURST, 0), ClipContext.Block.COLLIDER, ClipContext.Fluid.ANY,
					CollisionContext.empty()));
			if (under.getType() != HitResult.Type.MISS) return pos;
		}
		return null;
	}

	/** The top of the ground under {@code at} (water counts), or 24 blocks down if there's none that close. */
	static Vec3 ground(ServerLevel level, Vec3 at) {
		BlockHitResult under = level.clip(new ClipContext(at, at.add(0, -24, 0), ClipContext.Block.COLLIDER, ClipContext.Fluid.ANY,
				CollisionContext.empty()));
		return under.getType() == HitResult.Type.MISS ? at.add(0, -24, 0) : under.getLocation();
	}

	/** Let go with the nuke in place: it's thrown the way the bearer looks. The ring has been checked for charge. */
	public static boolean launch(ServerLevel level, ServerPlayer player, ItemStack ring) {
		Build b = BUILDS.remove(player.getUUID());
		if (b == null || b.level.getGameTime() - b.start < buildTicks()) {
			if (b != null) BUILDS.put(player.getUUID(), b);
			return false;
		}
		return drop(level, player, ring, b.fear, b.site, throwVelocity(player));
	}

	/** Throws a nuke from over the bearer's ring the way they look, with the ground's fear as it is now (tests). */
	public static boolean drop(ServerLevel level, ServerPlayer player, ItemStack ring) {
		Ground g = ground(player, ring);
		return drop(level, player, ring, g.fear, forming(player), throwVelocity(player));
	}

	private static boolean drop(ServerLevel level, ServerPlayer player, ItemStack ring, double fear, Vec3 from, Vec3 vel) {
		if (busy(player)) return false;
		BUILDS.remove(player.getUUID());
		Ground g = ground(player, ring);
		Nuke n = new Nuke(level, player.getUUID(), g, fear, from, vel);
		g.consuming = true;
		g.fear = 0;
		sync(g, ring);
		NUKES.add(n);
		// The bomb itself is a model each client draws (FearNukeFx), flying the same steps as here.
		Corps before = Corps.enter(Corps.YELLOW);
		try {
			RingFx.send(level, Kind.FEAR_NUKE, from, vel, flightTicks(), 0);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, player.blockPosition(), SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.PLAYERS, 3f, 0.6f);
		level.playSound(null, from.x, from.y, from.z, SoundEvents.PLAYER_ATTACK_SWEEP, SoundSource.PLAYERS, 3f, 0.4f);
		player.sendOverlayMessage(Component.translatable("message.lanternring.fear_nuke_thrown").withStyle(ChatFormatting.GOLD));
		Vec3 aim = predict(level, player);
		Vec3 near = aim != null ? aim : from;
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(near) < 160 * 160) {
				p.sendSystemMessage(Component.translatable("message.lanternring.fear_nuke_falls").withStyle(ChatFormatting.YELLOW, ChatFormatting.ITALIC));
			}
		}
		return true;
	}

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 20 == 0) {
			for (ServerPlayer p : server.getPlayerList().getPlayers()) groundTick(p);
		}
		if (server.getTickCount() % 4 == 0) {
			for (Map.Entry<UUID, Ground> e : GROUNDS.entrySet()) {
				ServerPlayer p = server.getPlayerList().getPlayer(e.getKey());
				Ground g = e.getValue();
				if (p == null || g.dim != p.level().dimension()) continue;
				smoke(p.level(), g, p.getRandom());
			}
		}
		// A held nuke whose bearer stopped holding it (switched away, died, logged off) comes apart.
		List<UUID> dropped = new ArrayList<>();
		for (UUID id : BUILDS.keySet()) {
			ServerPlayer p = server.getPlayerList().getPlayer(id);
			if (p == null || !p.isAlive() || !p.isUsingItem() || !(p.getUseItem().getItem() instanceof PowerRingItem)
					|| PowerRingItem.getMode(p.getUseItem()) != com.sparky.lanternring.RingMode.AERIAL) dropped.add(id);
		}
		for (UUID id : dropped) {
			ServerPlayer p = server.getPlayerList().getPlayer(id);
			if (p != null) cancelBuild(p);
			else BUILDS.remove(id);
		}
		wisps();
		BURNS.removeIf(Burn::step);
		for (Iterator<Nuke> it = NUKES.iterator(); it.hasNext(); ) {
			Nuke n = it.next();
			if (step(n)) {
				n.ground.consuming = false;
				it.remove();
			}
		}
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(FearNuke::tick);
		ServerLivingEntityEvents.AFTER_DEATH.register(FearNuke::died);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			NUKES.clear();
			BUILDS.clear();
			for (Burn b : BURNS) b.finish();
			BURNS.clear();
			WISPS.clear();
			GROUNDS.clear();
		});
		// The fear itself is kept on the ring, so a player who leaves can drop their ground.
		net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents.DISCONNECT.register(
				(handler, server) -> GROUNDS.remove(handler.getPlayer().getUUID()));
	}

	/** One tick of a thrown nuke: it falls, and goes off on contact or near the ground. Returns true once it has. */
	private static boolean step(Nuke n) {
		ServerLevel level = n.level;
		Vec3 prev = n.pos;
		n.age++;
		n.vel = nextVelocity(n.vel);
		n.pos = n.pos.add(n.vel);
		Vec3 at = strikes(level, prev, n.pos, n.vel, n.age, n.owner);
		if (at != null) {
			Vec3 land = ground(level, at);
			lastBurst = new Burst(at, bottom(at, n.vel) - land.y, n.age);
			blast(n, at, land);
			return true;
		}
		if (n.age % 2 == 0) level.sendParticles(SPARK, true, false, n.pos.x, n.pos.y, n.pos.z, 4, 0.6, 0.6, 0.6, 0.02);
		if (n.age % 5 == 0) level.playSound(null, n.pos.x, n.pos.y, n.pos.z, SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 4f, 1.2f);
		return false;
	}
	/**
	 * It airbursts (J, 2026-10-13: "it should realistically explode and incinerate around it ... doesn't
	 * damage but it causes fear in every mob"): the yellow aura burns a crater out under it, the clients
	 * draw the flash, fireball, mushroom and shock ring, and the yellow gas it leaves frenzies every
	 * mob in reach. Nothing is hurt by the blast itself; everything in reach floats down slowly as the
	 * ground goes from under it.
	 */
	private static void blast(Nuke n, Vec3 centre, Vec3 land) {
		ServerLevel level = n.level;
		int sweep = Math.max(RingTuning.FEAR_NUKE_BURN.ticks(), (int) Math.ceil(n.crater / 2.5));
		Burn burn = new Burn(level, centre, Mth.floor(land.y), n.crater, sweep);
		BURNS.add(burn);
		Corps before = Corps.enter(Corps.YELLOW);
		try {
			RingFx.send(level, Kind.NUKE_AURA, centre, centre.add(burn.outer, 0, 0), sweep, Burn.BURN);
			RingFx.send(level, Kind.FEAR_BURST, centre, land, (float) n.crater);
		} finally {
			Corps.restore(before);
		}
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, true, false, centre.x, centre.y, centre.z, 8, 4, 3, 4, 0);
		level.sendParticles(BLAST, true, false, centre.x, centre.y, centre.z, 200, 6, 4, 6, 0.2);
		level.playSound(null, centre.x, centre.y, centre.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 24f, 0.4f);
		level.playSound(null, centre.x, centre.y, centre.z, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 12f, 0.5f);
		level.playSound(null, centre.x, centre.y, centre.z, SoundEvents.LIGHTNING_BOLT_THUNDER, SoundSource.PLAYERS, 16f, 0.5f);
		n.ground.fear = 0;
		n.ground.centre = null;
		Entity source = level.getEntity(n.owner);
		if (source instanceof ServerPlayer p) sync(n.ground, yellowRing(p));

		// No damage: whatever stands where the ground goes floats down into the crater.
		int floatTicks = sweep + 200;
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(land, land).inflate(n.reach, n.reach * 0.6 + 20, n.reach),
				e -> e.isAlive() && horizontal(e.position(), land) < n.reach)) {
			e.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, floatTicks, 0, false, false));
			e.resetFallDistance();
		}
		FearFrenzy.gas(level, land.add(0, 1, 0), n.reach, n.owner);
	}

	private static double horizontal(Vec3 a, Vec3 b) {
		double dx = a.x - b.x, dz = a.z - b.z;
		return Math.sqrt(dx * dx + dz * dz);
	}

	/** In the air: flying (by ring, elytra or creative flight), a flying mob, or well clear of the ground. */
	static boolean flier(Entity e) {
		if (e instanceof Player p && (p.getAbilities().flying || p.isFallFlying())) return true;
		if (e instanceof Mob m && m.getNavigation() instanceof FlyingPathNavigation) return true;
		if (e.onGround() || e.isInWater()) return false;
		BlockPos.MutableBlockPos p = e.blockPosition().mutable();
		for (int i = 0; i < 3; i++) {
			p.move(0, -1, 0);
			if (!e.level().getBlockState(p).getCollisionShape(e.level(), p).isEmpty()) return false;
		}
		return true;
	}

	// ---- the yellow aura ----------------------------------------------------------------------------------

	/**
	 * What the nuke incinerates (J, 2026-10-12: "a green aura encasing and incinerating blocks within a
	 * near instant so you can see the destruction", then "it should be yellow not green"; 2026-10-13:
	 * airburst, "at least a 4x larger crater"). A sphere of yellow aura sweeps out from the burst point:
	 * everything above the ground within {@code crater} blocks of the point under it goes, and a bowl is
	 * scooped out of the ground below, {@link #DEPTH} of the crater's radius deep in the middle. Blocks
	 * at the surface (and anything built on it) are encased in yellow hard light first and burn away
	 * {@link #BURN} ticks later; the ground beneath them, which nobody can see, just goes. Bedrock and
	 * the like stay. The sweep works shell by shell, so a crater 80 blocks across costs only a slice of
	 * the world each tick. The client draws the aura's shell and the fire (NukeAuraFx).
	 */
	private static final class Burn {
		/** Ticks an encased block glows before it burns away. */
		static final int BURN = 5;
		/** The bowl's depth in the middle, as a share of the crater's radius. */
		static final double DEPTH = 0.3;
		private static final int QUIET = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;
		final ServerLevel level;
		final Vec3 centre;
		final int groundY;
		final double radius, depth;
		/** How far from the burst point the furthest block it takes is (the sweep's end). */
		final double outer;
		final int sweep;
		final int minX, minZ, size;
		/** Each column's ground height before the blast (lazily read), for what counts as the surface. */
		final int[] surface;
		final java.util.ArrayDeque<long[]> encased = new java.util.ArrayDeque<>();
		final long start;
		double done;

		Burn(ServerLevel level, Vec3 centre, int groundY, double radius, int sweep) {
			this.level = level;
			this.centre = centre;
			this.groundY = groundY;
			this.radius = radius;
			this.depth = radius * DEPTH;
			double h = centre.y - groundY;
			this.outer = Math.max(Math.sqrt(radius * radius + h * h), h + depth) + 1.5;
			this.sweep = Math.max(1, sweep);
			int r = (int) Math.ceil(radius) + 1;
			this.minX = Mth.floor(centre.x) - r;
			this.minZ = Mth.floor(centre.z) - r;
			this.size = 2 * r + 1;
			this.surface = new int[size * size];
			java.util.Arrays.fill(surface, Integer.MIN_VALUE);
			this.start = level.getGameTime();
		}

		private int surface(int x, int z) {
			int i = (x - minX) * size + (z - minZ);
			if (surface[i] == Integer.MIN_VALUE) {
				surface[i] = level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
			}
			return surface[i];
		}

		/** One tick. Returns true when it's all gone. */
		boolean step() {
			long t = level.getGameTime() - start;
			double front = outer * Math.min(1.0, (t + 1) / (double) sweep);
			if (front > done) {
				shell(done, front, t);
				done = front;
			}
			while (!encased.isEmpty() && encased.peekFirst()[1] <= t) {
				long[] e = encased.pollFirst();
				gone(BlockPos.of(e[0]), e[2] != 0);
			}
			return done >= outer && encased.isEmpty();
		}

		/** Everything between {@code r0} and {@code r1} from the burst point. */
		private void shell(double r0, double r1, long t) {
			BlockState aura = ModRegistry.LIGHT_CONSTRUCT.defaultBlockState().setValue(Corps.PROPERTY, Corps.YELLOW)
					.setValue(com.sparky.lanternring.block.LightConstructBlock.RIM, true);
			double r0s = r0 * r0, r1s = r1 * r1, rs = radius * radius;
			int lim = (int) Math.ceil(Math.min(r1, radius)) + 1;
			int cx = Mth.floor(centre.x), cz = Mth.floor(centre.z);
			BlockPos.MutableBlockPos p = new BlockPos.MutableBlockPos();
			for (int x = cx - lim; x <= cx + lim; x++) {
				double fx = x + 0.5 - centre.x;
				for (int z = cz - lim; z <= cz + lim; z++) {
					double fz = z + 0.5 - centre.z;
					double h2 = fx * fx + fz * fz;
					if (h2 > rs || h2 >= r1s) continue;
					double floorY = groundY - depth * (1 - h2 / rs);
					double hi = Math.sqrt(r1s - h2);
					double lo = r0s > h2 ? Math.sqrt(r0s - h2) : 0;
					int bottom = Math.max(level.getMinY(), (int) Math.ceil(floorY));
					int top = level.getMaxY();
					// Block middles at dy = y + 0.5 - centre.y, with lo <= |dy| < hi.
					int upFrom = lo > 0 ? (int) Math.ceil(centre.y + lo - 0.5) : (int) Math.ceil(centre.y - hi - 0.5);
					int upTo = (int) Math.ceil(centre.y + hi - 0.5) - 1;
					for (int y = Math.max(bottom, upFrom); y <= Math.min(top, upTo); y++) take(p.set(x, y, z), h2, floorY, t, aura);
					if (lo > 0) {
						int downFrom = (int) Math.floor(centre.y - hi - 0.5) + 1;
						int downTo = (int) Math.floor(centre.y - lo - 0.5);
						for (int y = Math.max(bottom, downFrom); y <= Math.min(top, downTo); y++) take(p.set(x, y, z), h2, floorY, t, aura);
					}
				}
			}
		}

		private void take(BlockPos.MutableBlockPos p, double h2, double floorY, long t, BlockState aura) {
			BlockState st = level.getBlockState(p);
			if (st.isAir() || st.getDestroySpeed(level, p) < 0 || st.is(ModRegistry.POWER_BATTERY) || st.is(ModRegistry.LIGHT_CONSTRUCT)) return;
			boolean edge = h2 > (radius - 2) * (radius - 2) || p.getY() < floorY + 2;
			if (p.getY() >= surface(p.getX(), p.getZ()) - 2) {
				// At the surface, or built on it: encased in yellow light, then gone.
				level.setBlock(p, aura, QUIET);
				encased.add(new long[] {p.asLong(), t + BURN, edge ? 1 : 0});
			} else {
				gone(p.immutable(), edge);
			}
		}

		private void gone(BlockPos p, boolean edge) {
			// The rim of the crater tells its neighbours, so water and sand fall in.
			level.setBlock(p, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), edge ? Block.UPDATE_ALL : QUIET);
		}

		/** The server is stopping: everything left goes at once. */
		void finish() {
			if (done < outer) shell(done, outer, Long.MIN_VALUE / 2);
			done = outer;
			while (!encased.isEmpty()) {
				long[] e = encased.pollFirst();
				gone(BlockPos.of(e[0]), e[2] != 0);
			}
		}
	}

	private static final List<Burn> BURNS = new ArrayList<>();
}
