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
 * {@link #cost}). It isn't thrown (J, 2026-10-13): holding right-click raises the ring arm and a
 * bomb of yellow hard light forms plate by plate up in the sky toward the marker ("the nuke should
 * also be held and formed in the sky"), over RingTuning.FEAR_NUKE_BUILD, tethered to the ring by a
 * line of light while the fear on the ground streams up into it; everyone sees the arm come up (the
 * client's NukeHold). Stray more than RingTuning.FEAR_NUKE_RANGE blocks from it ("you have to stay
 * within 30 blocks otherwise it cancels") and it breaks apart: the fear and the charge put into it
 * so far are lost. Let go once it's built and it flies on over the marker, hangs there drinking the
 * last of the fear, and airbursts without ever touching the ground ({@link #blast}).</li>
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
		for (ItemStack s : new ItemStack[] {player.getMainHandItem(), player.getOffhandItem()}) {
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
			for (ItemStack s : new ItemStack[] {living.getMainHandItem(), living.getOffhandItem()}) {
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
				target = new Vec3(w.orb.x, w.orb.y, w.orb.z);
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

	// ---- forming it in the sky -----------------------------------------------------------------------

	/** A nuke a bearer is forming in the sky, tethered to their raised ring. */
	private static final class Build {
		final ServerLevel level;
		final long start;
		/** The ground's fear when it started: it drains into the bomb as it builds, and goes back if it's let go early. */
		final double fear;
		/** Where in the sky it forms; it stays there however the bearer moves. */
		final Vec3 site;
		boolean readyNoted;

		Build(ServerLevel level, double fear, Vec3 site) {
			this.level = level;
			this.start = level.getGameTime();
			this.fear = fear;
			this.site = site;
		}
	}

	private static final Map<UUID, Build> BUILDS = new HashMap<>();
	/** Bearers whose nuke broke apart (they strayed too far) and who are still holding right-click: no new one forms until they let go. */
	private static final java.util.Set<UUID> BROKEN = new java.util.HashSet<>();

	/** How far the bearer may stray from the forming nuke before it breaks apart, in blocks. */
	public static double range() {
		return Math.max(4, RingTuning.FEAR_NUKE_RANGE.seconds());
	}

	/** Where the bomb forms: up in the sky toward the marker, well inside the range. */
	static Vec3 site(ServerLevel level, Player player) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		Vec3 flat = new Vec3(look.x, 0, look.z);
		flat = flat.lengthSqr() < 1e-4 ? Vec3.directionFromRotation(0, player.getYRot()) : flat.normalize();
		double reach = range() * 0.7;
		double out = reach * 0.75, up = reach * 0.65;
		BlockPos mark = findMark(level, player);
		if (mark != null) out = Math.min(out, Math.max(4, horizontal(eye, Vec3.atBottomCenterOf(mark))));
		return eye.add(flat.scale(out)).add(0, up, 0);
	}

	/** Where this bearer's nuke is forming, or just over their head if it isn't. */
	public static Vec3 forming(Player player) {
		Build b = BUILDS.get(player.getUUID());
		return b != null ? b.site : held(player);
	}

	/** How far this bearer is from their forming nuke (from the chest), or -1. */
	public static double strayed(Player player) {
		Build b = BUILDS.get(player.getUUID());
		return b == null ? -1 : player.position().add(0, player.getBbHeight() * 0.6, 0).distanceTo(b.site);
	}

	/** Ticks a nuke takes to form. */
	public static int buildTicks() {
		return Math.max(1, RingTuning.FEAR_NUKE_BUILD.ticks());
	}

	/** Just over the raised ring fist, above the bearer's head. */
	public static Vec3 held(Player player) {
		boolean mainHandRing = player.getMainHandItem().getItem() instanceof PowerRingItem;
		boolean right = (player.getMainArm() == net.minecraft.world.entity.HumanoidArm.RIGHT) == mainHandRing;
		float yaw = player.yBodyRot * Mth.DEG_TO_RAD;
		// The body's right, in world space.
		Vec3 side = new Vec3(-Mth.cos(yaw), 0, -Mth.sin(yaw)).scale(right ? 1 : -1);
		return player.position().add(side.scale(0.4)).add(0, player.getBbHeight() + 0.75, 0);
	}

	/** How far through the build this bearer's nuke is, 0..1, or -1 if they aren't building one. */
	public static float building(Player player) {
		Build b = BUILDS.get(player.getUUID());
		if (b == null) return -1f;
		return Mth.clamp((b.level.getGameTime() - b.start) / (float) buildTicks(), 0f, 1f);
	}

	/**
	 * Each tick the bearer holds right-click in Aerial mode: the bomb forms plate by plate in the sky,
	 * tethered to the raised ring, and the fear on their ground streams up into it. Straying past
	 * {@link #range} breaks it apart.
	 */
	public static void buildTick(ServerPlayer player, ItemStack ring) {
		ServerLevel level = player.level();
		if (BROKEN.contains(player.getUUID())) return;
		Ground g = ground(player, ring);
		Build b = BUILDS.get(player.getUUID());
		if (b == null || b.level != level) {
			if (busy(player)) return;
			b = new Build(level, g.fear, site(level, player));
			BUILDS.put(player.getUUID(), b);
			g.consuming = true;
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.5f, 0.6f);
			level.playSound(null, b.site.x, b.site.y, b.site.z, SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 3f, 0.5f);
		}
		long t = level.getGameTime() - b.start;
		float k = building(player);
		double away = strayed(player);
		if (away > range()) {
			breakApart(player, ring, b, k);
			return;
		}
		g.fear = b.fear * (1 - k);
		sync(g, ring);
		Vec3 hand = b.site;
		RandomSource random = level.getRandom();
		if (t % 2 == 0) {
			// Each client draws the bomb forming and the line of light from the bearer's ring up to it.
			Corps before = Corps.enter(Corps.YELLOW);
			try {
				RingFx.send(level, Kind.FEAR_NUKE_FORM, b.site, b.site, k, buildTicks(), player);
			} finally {
				Corps.restore(before);
			}
		}
		if (t % 4 == 0) hud(player, k, away);
		if (k < 1f) {
			// Yellow light gathers in the sky as the plates lock on.
			if (t % 2 == 0) level.sendParticles(SPARK, true, false, hand.x, hand.y, hand.z, 6, 1.6, 1.6, 1.6, 0.04);
			if (t % 4 == 0) {
				level.playSound(null, hand.x, hand.y, hand.z, SoundEvents.AMETHYST_BLOCK_PLACE, SoundSource.PLAYERS, 0.8f,
						0.6f + 0.8f * k);
			}
			// The fear on the ground streams up into it.
			if (g.centre != null && b.fear > 0 && g.centre.distanceToSqr(player.position()) < GROUND * GROUND) {
				double spread = 4 + (GROUND - 4) * b.fear / FULL;
				for (int i = 0; i < 1 + (int) (3 * b.fear / FULL); i++) {
					double a = random.nextDouble() * Math.PI * 2, d = Math.sqrt(random.nextDouble()) * spread;
					double fx = g.centre.x + Math.cos(a) * d, fz = g.centre.z + Math.sin(a) * d;
					double fy = floor(level, fx, g.centre.y, fz);
					if (Double.isNaN(fy)) continue;
					WISPS.add(new Wisp(level, new Vec3(fx, fy + 0.2, fz), new Vec3(0, 0.25, 0), player.getUUID(), null, true));
				}
			}
			int beat = Math.max(3, (int) Math.round(14 - 10 * k));
			if (t % beat == 0) level.playSound(null, hand.x, hand.y, hand.z, SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 2f, 0.6f + 0.6f * k);
		} else {
			if (!b.readyNoted) {
				b.readyNoted = true;
				level.playSound(null, hand.x, hand.y, hand.z, SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 2f, 0.6f);
			}
			if (t % 3 == 0) level.sendParticles(SPARK, true, false, hand.x, hand.y, hand.z, 4, 2, 2, 2, 0.01);
		}
	}

	/** The action bar while it forms: how far through it is and how far from it the bearer is, red near the limit. */
	private static void hud(ServerPlayer player, float k, double away) {
		double range = range();
		boolean near = away > range * 0.8;
		Component text = k < 1f
				? Component.translatable("message.lanternring.fear_nuke_building", Math.round(k * 100), Math.round(away), Math.round(range))
				: Component.translatable("message.lanternring.fear_nuke_built", Math.round(away), Math.round(range));
		player.sendOverlayMessage(text.copy().withStyle(near ? ChatFormatting.RED : k < 1f ? ChatFormatting.YELLOW : ChatFormatting.GOLD));
	}

	/**
	 * The bearer strayed past the range: the bomb breaks apart in the sky, its plates scattering and
	 * fading. The fear drawn into it and the charge it took so far are lost. Nothing more forms until
	 * they let go.
	 */
	private static void breakApart(ServerPlayer player, ItemStack ring, Build b, float k) {
		BUILDS.remove(player.getUUID());
		BROKEN.add(player.getUUID());
		Ground g = GROUNDS.get(player.getUUID());
		if (g != null) {
			g.fear = b.fear * (1 - k);
			g.consuming = false;
			if (g.fear <= 0) g.centre = null;
			sync(g, ring);
		}
		if (!player.isCreative()) {
			int spent = Math.round(cost(ring) * k);
			PowerRingItem.setCharge(ring, Math.max(0, PowerRingItem.getCharge(ring) - spent));
		}
		ServerLevel level = b.level;
		Corps before = Corps.enter(Corps.YELLOW);
		try {
			RingFx.send(level, Kind.FEAR_NUKE_SCATTER, b.site, b.site, k, 0, player);
		} finally {
			Corps.restore(before);
		}
		level.sendParticles(SMOKE, true, false, b.site.x, b.site.y, b.site.z, 60, 2.5, 2.5, 2.5, 0.08);
		level.playSound(null, b.site.x, b.site.y, b.site.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 4f, 0.5f);
		level.playSound(null, b.site.x, b.site.y, b.site.z, SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 4f, 0.6f);
		level.playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 1.5f, 0.6f);
		player.sendOverlayMessage(Component.translatable("message.lanternring.fear_nuke_strayed", Math.round(range())).withStyle(ChatFormatting.RED));
	}

	private static float building(Build b) {
		return Mth.clamp((b.level.getGameTime() - b.start) / (float) buildTicks(), 0f, 1f);
	}

	/** Whether this bearer's nuke broke apart and they haven't let go yet. */
	public static boolean broken(Player player) {
		return BROKEN.contains(player.getUUID());
	}

	/** Whether the bearer's nuke is fully built. */
	public static boolean built(Player player) {
		return building(player) >= 1f;
	}

	/** Let go before it was built, or the power was dropped: it comes apart and the fear goes back to the ground. */
	public static void cancelBuild(Player player) {
		BROKEN.remove(player.getUUID());
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

	// ---- the nuke ------------------------------------------------------------------------------------

	enum Stage { FLY, HANG }

	private static final class Nuke {
		final ServerLevel level;
		final UUID owner;
		final Ground ground;
		final double fear;
		final double crater;
		final double reach;
		/** The raised hand it leaves from, the point in the air it bursts at, and the ground under that. */
		final Vec3 from, burst, land;
		Stage stage = Stage.FLY;
		long stageStart;
		double x, y, z;

		Nuke(ServerLevel level, UUID owner, Ground ground, double fear, Vec3 from, Vec3 burst, Vec3 land) {
			this.level = level;
			this.owner = owner;
			this.ground = ground;
			this.fear = fear;
			this.crater = crater(fear);
			this.reach = reach(fear);
			this.from = from;
			this.burst = burst;
			this.land = land;
			this.x = from.x;
			this.y = from.y;
			this.z = from.z;
			this.stageStart = level.getGameTime();
		}

		double radius() {
			return ORB;
		}
	}

	private static final List<Nuke> NUKES = new ArrayList<>();

	public static boolean busy(Player player) {
		for (Nuke n : NUKES) {
			if (n.owner.equals(player.getUUID())) return true;
		}
		return false;
	}

	/** How far out the nuke can be aimed: further than the other drops, so the bearer can stand clear of the crater. */
	static final double AIM_RANGE = 90;

	/** The spot on the ground the bearer is looking at, up to {@link #AIM_RANGE} away, or null. */
	public static @Nullable BlockPos findMark(ServerLevel level, Player player) {
		Vec3 eye = player.getEyePosition();
		var hit = level.clip(new net.minecraft.world.level.ClipContext(eye, eye.add(player.getLookAngle().scale(AIM_RANGE)),
				net.minecraft.world.level.ClipContext.Block.COLLIDER, net.minecraft.world.level.ClipContext.Fluid.NONE, player));
		if (hit.getType() == net.minecraft.world.phys.HitResult.Type.MISS) return null;
		BlockPos pos = hit.getBlockPos().relative(hit.getDirection());
		for (int i = 0; i < 24 && pos.getY() > level.getMinY(); i++) {
			BlockState below = level.getBlockState(pos.below());
			if (!below.canBeReplaced() && !below.is(ModRegistry.LIGHT_CONSTRUCT)) return pos;
			pos = pos.below();
		}
		return null;
	}

	/** How high over the ground it bursts: high enough that it never touches down. */
	static double burstHeight(double crater) {
		return Math.max(10, crater * 0.3);
	}

	/**
	 * Let go with the nuke built: it leaves the sky where it formed for the air over {@code mark} and bursts
	 * there. The ring has been checked for charge.
	 */
	public static boolean launch(ServerLevel level, ServerPlayer player, ItemStack ring, BlockPos mark) {
		Build b = BUILDS.remove(player.getUUID());
		if (b == null || b.level.getGameTime() - b.start < buildTicks()) {
			if (b != null) BUILDS.put(player.getUUID(), b);
			return false;
		}
		return drop(level, player, ring, mark, b.fear, b.site);
	}

	/** Sends a nuke from where it formed (over the raised hand if none is forming) to burst over {@code mark} with the ground's fear as it is now (tests). */
	public static boolean drop(ServerLevel level, ServerPlayer player, ItemStack ring, BlockPos mark) {
		Ground g = ground(player, ring);
		return drop(level, player, ring, mark, g.fear, forming(player));
	}

	private static boolean drop(ServerLevel level, ServerPlayer player, ItemStack ring, BlockPos mark, double fear, Vec3 from) {
		if (busy(player)) return false;
		BUILDS.remove(player.getUUID());
		Ground g = ground(player, ring);
		Vec3 land = new Vec3(mark.getX() + 0.5, mark.getY(), mark.getZ() + 0.5);
		Vec3 burst = land.add(0, burstHeight(crater(fear)), 0);
		Nuke n = new Nuke(level, player.getUUID(), g, fear, from, burst, land);
		g.consuming = true;
		g.fear = 0;
		sync(g, ring);
		NUKES.add(n);
		// The bomb itself is a model each client draws (FearNukeFx), on the same clock as the stages here.
		Corps before = Corps.enter(Corps.YELLOW);
		try {
			RingFx.send(level, Kind.FEAR_NUKE, from, burst, flyTicks(), hangTicks());
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, player.blockPosition(), SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.PLAYERS, 3f, 0.6f);
		level.playSound(null, player.blockPosition(), SoundEvents.FIREWORK_ROCKET_LAUNCH, SoundSource.PLAYERS, 3f, 0.5f);
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(land) < 160 * 160) {
				p.sendSystemMessage(Component.translatable("message.lanternring.fear_nuke_falls").withStyle(ChatFormatting.YELLOW, ChatFormatting.ITALIC));
			}
		}
		return true;
	}

	static int flyTicks() {
		return Math.max(10, RingTuning.FEAR_NUKE_ORB.ticks());
	}

	static int hangTicks() {
		return Math.max(1, RingTuning.FEAR_NUKE_CONSUME.ticks());
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
		// A build whose bearer stopped holding it (switched away, died, logged off) comes apart.
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
		BROKEN.removeIf(id -> {
			ServerPlayer p = server.getPlayerList().getPlayer(id);
			return p == null || !p.isUsingItem() || !(p.getUseItem().getItem() instanceof PowerRingItem);
		});
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
			BROKEN.clear();
			for (Burn b : BURNS) b.finish();
			BURNS.clear();
			WISPS.clear();
			GROUNDS.clear();
		});
		// The fear itself is kept on the ring, so a player who leaves can drop their ground.
		net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents.DISCONNECT.register(
				(handler, server) -> GROUNDS.remove(handler.getPlayer().getUUID()));
	}

	/** One tick of a nuke. Returns true once it's over. */
	private static boolean step(Nuke n) {
		ServerLevel level = n.level;
		long t = level.getGameTime() - n.stageStart;
		RandomSource random = level.getRandom();
		switch (n.stage) {
			case FLY -> {
				// From where it formed, over in an arc to the burst point.
				double k = Math.min(1.0, t / (double) flyTicks());
				n.x = Mth.lerp(k, n.from.x, n.burst.x);
				n.z = Mth.lerp(k, n.from.z, n.burst.z);
				n.y = Mth.lerp(k, n.from.y, n.burst.y) + Math.sin(k * Math.PI) * Math.max(4, n.from.distanceTo(n.burst) * 0.25);
				if (t % 2 == 0) level.sendParticles(SPARK, true, false, n.x, n.y, n.z, 4, 0.4, 0.4, 0.4, 0.02);
				if (t >= flyTicks()) next(n, Stage.HANG);
			}
			case HANG -> {
				// It hangs in the air over the target, drinking the last of the fear round it.
				int total = hangTicks();
				double k = Math.min(1.0, t / (double) total);
				n.x = n.burst.x;
				n.y = n.burst.y;
				n.z = n.burst.z;
				if (t % 6 == 0) {
					for (LivingEntity m : level.getEntitiesOfClass(LivingEntity.class, new AABB(n.land, n.land).inflate(n.reach),
							e -> Terror.isPreyOf(e, n.owner) || e instanceof Mob && !spared(e, n.owner))) {
						if (random.nextInt(3) == 0) WISPS.add(new Wisp(level, m.getBoundingBox().getCenter(), new Vec3(0, 0.3, 0), null, n));
					}
				}
				int beat = Math.max(2, (int) Math.round(12 - 10 * k));
				if (t % beat == 0) level.playSound(null, n.x, n.y, n.z, SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 4f, 0.6f + 0.8f * (float) k);
				if (t >= total) {
					blast(n);
					return true;
				}
			}
		}
		return false;
	}

	private static void next(Nuke n, Stage stage) {
		n.stage = stage;
		n.stageStart = n.level.getGameTime();
	}

	/**
	 * It airbursts (J, 2026-10-13: "it should realistically explode and incinerate around it ... doesn't
	 * damage but it causes fear in every mob"): the yellow aura burns a crater out under it, the clients
	 * draw the flash, fireball, mushroom and shock ring, and the yellow gas it leaves frenzies every
	 * mob in reach. Nothing is hurt by the blast itself; everything in reach floats down slowly as the
	 * ground goes from under it.
	 */
	private static void blast(Nuke n) {
		ServerLevel level = n.level;
		Vec3 centre = n.burst;
		int sweep = Math.max(RingTuning.FEAR_NUKE_BURN.ticks(), (int) Math.ceil(n.crater / 2.5));
		Burn burn = new Burn(level, centre, Mth.floor(n.land.y), n.crater, sweep);
		BURNS.add(burn);
		Corps before = Corps.enter(Corps.YELLOW);
		try {
			RingFx.send(level, Kind.NUKE_AURA, centre, centre.add(burn.outer, 0, 0), sweep, Burn.BURN);
			RingFx.send(level, Kind.FEAR_BURST, centre, n.land, (float) n.crater);
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
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(n.land, n.land).inflate(n.reach, n.reach * 0.6 + 20, n.reach),
				e -> e.isAlive() && horizontal(e.position(), n.land) < n.reach)) {
			e.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, floatTicks, 0, false, false));
			e.resetFallDistance();
		}
		FearFrenzy.gas(level, n.land.add(0, 1, 0), n.reach, n.owner);
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
