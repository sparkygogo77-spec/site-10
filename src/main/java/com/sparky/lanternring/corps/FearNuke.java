package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingPowers;
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
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.navigation.FlyingPathNavigation;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Explosion;
import net.minecraft.world.level.ExplosionDamageCalculator;
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
 * {@link #cost}). A bomb of yellow hard light (the client's FearNukeFx, fear_nuke.bbmodel) forms out
 * of the ring, drops nose first onto the marker, then drinks in all the fear on the ground (the smoke
 * streams into it) and grows brighter, then goes off: a blast of power 8 with no fear up to 16 at
 * full fear (a TNT block is 4), and a green aura that incinerates everything near it ({@link Burn}).</li>
 * <li>Everything airborne in its reach is flung far out along the blast, and everything it reaches
 * gets Dread: yellow hearts of fear that slowly kill (see DreadEffect). Yellow ring bearers are
 * spared.</li>
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

	/** How far the blast flings and fills with Dread. */
	public static double reach(double fear) {
		return power(fear) * 2.5;
	}

	public static Component status(ItemStack ring) {
		return Component.translatable("message.lanternring.fear_nuke_status", fear(ring), String.valueOf(cost(ring) / 10),
				String.valueOf(Math.round(power(fear(ring)))));
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
		@Nullable Nuke consuming;
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
		if (g.consuming != null) return;
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
		if (g.consuming != null) return;
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
		int age;

		Wisp(ServerLevel level, Vec3 pos, Vec3 vel, @Nullable UUID to, @Nullable Nuke orb) {
			this.level = level;
			this.pos = pos;
			this.vel = vel;
			this.to = to;
			this.orb = orb;
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
				target = p.position().add(0, 0.9, 0);
			}
			Vec3 d = target.subtract(w.pos);
			double dist = d.length();
			double arrive = w.orb != null ? w.orb.radius() : 0.9;
			if (dist < arrive || ++w.age > 200) {
				it.remove();
				if (w.orb == null) {
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

	// ---- the nuke ------------------------------------------------------------------------------------

	enum Stage { FORM, DROP, CONSUME, BLAST }

	private static final class Nuke {
		final ServerLevel level;
		final UUID owner;
		final Ground ground;
		final double fear;
		final float power;
		final double reach;
		final Vec3 from, land;
		Stage stage = Stage.FORM;
		long stageStart;
		double x, y, z;
		/** How big it is now, in blocks round its middle (fear's wisps arrive at this). */
		double size = 1;

		Nuke(ServerLevel level, UUID owner, Ground ground, Vec3 from, Vec3 land) {
			this.level = level;
			this.owner = owner;
			this.ground = ground;
			this.fear = ground.fear;
			this.power = power(fear);
			this.reach = reach(fear);
			this.from = from;
			this.land = land;
			this.x = from.x;
			this.y = from.y;
			this.z = from.z;
			this.stageStart = level.getGameTime();
		}

		double radius() {
			return size;
		}
	}

	private static final List<Nuke> NUKES = new ArrayList<>();

	public static boolean busy(Player player) {
		for (Nuke n : NUKES) {
			if (n.owner.equals(player.getUUID())) return true;
		}
		return false;
	}

	/** Released over {@code mark}: the orb forms out of the ring. The ring has been checked for charge. */
	public static boolean drop(ServerLevel level, ServerPlayer player, ItemStack ring, BlockPos mark) {
		if (busy(player)) return false;
		Ground g = ground(player, ring);
		Vec3 look = player.getLookAngle().multiply(1, 0, 1);
		look = look.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : look.normalize();
		Vec3 from = player.getEyePosition().add(look.scale(ORB + 3)).add(0, ORB, 0);
		Vec3 land = new Vec3(mark.getX() + 0.5, mark.getY() + ORB * 0.6, mark.getZ() + 0.5);
		Nuke n = new Nuke(level, player.getUUID(), g, from, land);
		g.consuming = n;
		NUKES.add(n);
		// The bomb itself is a model each client draws (FearNukeFx), on the same clock as the stages here.
		Corps before = Corps.enter(Corps.YELLOW);
		try {
			RingFx.send(level, Kind.FEAR_NUKE, from, land, Math.max(2, RingTuning.FEAR_NUKE_ORB.ticks() / 2),
					Math.max(1, RingTuning.FEAR_NUKE_CONSUME.ticks()));
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, player.blockPosition(), SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 3f, 0.5f);
		level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 2f, 0.5f);
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(land) < 160 * 160) {
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
		wisps();
		BURNS.removeIf(Burn::step);
		for (Iterator<Nuke> it = NUKES.iterator(); it.hasNext(); ) {
			Nuke n = it.next();
			if (step(n)) {
				n.ground.consuming = null;
				it.remove();
			}
		}
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(FearNuke::tick);
		ServerLivingEntityEvents.AFTER_DEATH.register(FearNuke::died);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			NUKES.clear();
			for (Burn b : BURNS) b.finish();
			BURNS.clear();
			WISPS.clear();
			GROUNDS.clear();
		});
	}

	/** One tick of a nuke. Returns true once it's over. */
	private static boolean step(Nuke n) {
		ServerLevel level = n.level;
		long t = level.getGameTime() - n.stageStart;
		int half = Math.max(2, RingTuning.FEAR_NUKE_ORB.ticks() / 2);
		RandomSource random = level.getRandom();
		switch (n.stage) {
			case FORM -> {
				// Swelling out of the ring.
				int r = (int) Math.max(1, Math.round(ORB * Math.min(1.0, (t + 1) / (double) half)));
				n.size = r;
				if (t % 3 == 0) level.sendParticles(SPARK, n.x, n.y, n.z, 10, r * 0.6, r * 0.6, r * 0.6, 0.05);
				if (t >= half) next(n, Stage.DROP);
			}
			case DROP -> {
				double k = Math.min(1.0, t / (double) half);
				n.x = Mth.lerp(k, n.from.x, n.land.x);
				n.z = Mth.lerp(k, n.from.z, n.land.z);
				n.y = Mth.lerp(k * k, n.from.y, n.land.y);
				n.size = ORB;
				if (t >= half) {
					level.playSound(null, n.x, n.y, n.z, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 3f, 0.4f);
					level.playSound(null, n.x, n.y, n.z, SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.PLAYERS, 3f, 0.5f);
					level.sendParticles(SMOKE, n.x, n.y - ORB * 0.6, n.z, 80, ORB, 0.3, ORB, 0.05);
					next(n, Stage.CONSUME);
				}
			}
			case CONSUME -> {
				int total = Math.max(1, RingTuning.FEAR_NUKE_CONSUME.ticks());
				double k = Math.min(1.0, t / (double) total);
				// The ground's fear drains into the orb.
				n.ground.fear = n.fear * (1 - k);
				ServerPlayer owner = level.getServer().getPlayerList().getPlayer(n.owner);
				if (owner != null) sync(n.ground, yellowRing(owner));
				int r = ORB + (k > 0.5 ? (int) Math.round(2 * n.fear / FULL) : 0);
				n.size = r;
				// The smoke streams in: from the ground if it's near, else from all round the orb.
				Vec3 src = n.ground.centre != null && n.ground.centre.distanceToSqr(n.land) < 80 * 80 ? n.ground.centre : n.land;
				double spread = 4 + (GROUND - 4) * n.fear / FULL;
				for (int i = 0; i < 2 + (int) (6 * n.fear / FULL); i++) {
					double a = random.nextDouble() * Math.PI * 2, d = Math.sqrt(random.nextDouble()) * spread;
					double fx = src.x + Math.cos(a) * d, fz = src.z + Math.sin(a) * d;
					double fy = floor(level, fx, src.y, fz);
					if (Double.isNaN(fy)) continue;
					WISPS.add(new Wisp(level, new Vec3(fx, fy + 0.2, fz), new Vec3(0, 0.25, 0), null, n));
				}
				if (t % 10 == 0) {
					for (LivingEntity m : level.getEntitiesOfClass(LivingEntity.class, new AABB(n.land, n.land).inflate(n.reach),
							e -> Terror.isPreyOf(e, n.owner))) {
						WISPS.add(new Wisp(level, m.getBoundingBox().getCenter(), new Vec3(0, 0.3, 0), null, n));
					}
				}
				int beat = Math.max(2, (int) Math.round(12 - 10 * k));
				if (t % beat == 0) level.playSound(null, n.x, n.y, n.z, SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 4f, 0.6f + 0.8f * (float) k);
				if (t % 20 == 0) level.playSound(null, n.x, n.y, n.z, SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 4f, 0.5f + (float) k);
				if (t >= total) {
					blast(n);
					next(n, Stage.BLAST);
				}
			}
			case BLAST -> {
				// A ring of yellow fear rolls out to the edge of its reach, under a rising cloud.
				int span = 30;
				double ringR = n.reach * Math.min(1.0, (t + 1) / (double) span);
				double gy = n.land.y - ORB * 0.6;
				int pts = 24 + (int) ringR * 3;
				for (int i = 0; i < pts; i++) {
					double a = i / (double) pts * Math.PI * 2;
					level.sendParticles(BLAST, true, false, n.land.x + Math.cos(a) * ringR, gy + 0.5, n.land.z + Math.sin(a) * ringR, 1, 0.3, 0.2, 0.3, 0);
				}
				level.sendParticles(ParticleTypes.LARGE_SMOKE, true, false, n.land.x, gy + 2 + t * 0.7, n.land.z, 12, 2 + t * 0.1, 1, 2 + t * 0.1, 0.02);
				level.sendParticles(BLAST, true, false, n.land.x, gy + 4 + t * 0.7, n.land.z, 10, 3 + t * 0.15, 1.5, 3 + t * 0.15, 0);
				return t >= span;
			}
		}
		return false;
	}

	private static void next(Nuke n, Stage stage) {
		n.stage = stage;
		n.stageStart = n.level.getGameTime();
	}

	/** It goes off: the explosion, the fling and the Dread. */
	private static void blast(Nuke n) {
		ServerLevel level = n.level;
		double x = n.land.x, y = n.land.y - ORB * 0.6 + 1, z = n.land.z;
		Entity source = level.getEntity(n.owner);
		UUID owner = n.owner;
		ExplosionDamageCalculator spares = new ExplosionDamageCalculator() {
			@Override
			public boolean shouldDamageEntity(Explosion explosion, Entity entity) {
				return !spared(entity, owner) && super.shouldDamageEntity(explosion, entity);
			}

			@Override
			public float getKnockbackMultiplier(Entity entity) {
				return spared(entity, owner) ? 0f : super.getKnockbackMultiplier(entity);
			}
		};
		// The blast itself throws and hurts; the blocks go to the green aura instead (see Burn).
		level.explode(source, null, spares, x, y, z, n.power, false, Level.ExplosionInteraction.NONE);
		Vec3 centre = new Vec3(x, y, z);
		double eviscerate = n.power * 1.25;
		BURNS.add(new Burn(level, centre, eviscerate));
		Corps before = Corps.enter(Corps.GREEN);
		try {
			RingFx.send(level, Kind.NUKE_AURA, centre, centre.add(eviscerate, 0, 0), RingTuning.FEAR_NUKE_BURN.ticks(), Burn.BURN);
		} finally {
			Corps.restore(before);
		}
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, true, false, x, y, z, 8, n.power / 3, n.power / 4, n.power / 3, 0);
		level.sendParticles(BLAST, true, false, x, y, z, 200, n.power / 2, n.power / 3, n.power / 2, 0.2);
		level.playSound(null, x, y, z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 16f, 0.5f);
		level.playSound(null, x, y, z, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 8f, 0.6f);
		n.ground.fear = 0;
		n.ground.centre = null;
		if (source instanceof ServerPlayer p) sync(n.ground, yellowRing(p));

		int dread = RingTuning.FEAR_DREAD.ticks();
		for (Entity e : level.getEntitiesOfClass(Entity.class, new AABB(centre, centre).inflate(n.reach),
				e -> e.isAlive() && e.distanceToSqr(centre) < n.reach * n.reach && !spared(e, owner))) {
			double d = Math.sqrt(e.distanceToSqr(centre));
			if (d < eviscerate && e instanceof LivingEntity living) {
				// Inside the aura: incinerated.
				living.igniteForSeconds(8);
				living.hurtServer(level, level.damageSources().explosion(source, source), 10000f);
				continue;
			}
			if (flier(e)) {
				// Flung far out along the blast.
				Vec3 dir = e.position().subtract(centre).multiply(1, 0, 1);
				dir = dir.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : dir.normalize();
				double strength = 2.2 + 3.5 * (1 - d / n.reach);
				if (e instanceof ServerPlayer p && p.getAbilities().flying) {
					p.getAbilities().flying = false;
					p.onUpdateAbilities();
				}
				e.setDeltaMovement(dir.add(0, 0.35, 0).normalize().scale(strength));
				RingPowers.syncVelocity(e);
			}
			if (e instanceof LivingEntity living) {
				living.addEffect(new MobEffectInstance(ModEffects.DREAD, dread, 0, false, true), source);
				Terror.frighten(level, living, owner, dread);
			}
		}
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

	// ---- the green aura ----------------------------------------------------------------------------------

	/**
	 * What the nuke eviscerates (J, 2026-10-12: "a green aura encasing and incinerating blocks within a
	 * near instant so you can see the destruction"). A sphere of green aura sweeps out from the blast
	 * over RingTuning.FEAR_NUKE_BURN: every block it reaches that could be seen (one with open air beside
	 * it) is encased in green hard light, then burns away {@link #BURN} ticks later; the blocks inside,
	 * which nobody can see, just go. Bedrock and the like stay. The client draws the aura's shell and
	 * the fire (LabFx, NUKE_AURA).
	 */
	private static final class Burn {
		/** Ticks an encased block glows before it burns away. */
		static final int BURN = 5;
		private static final int QUIET = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;
		final ServerLevel level;
		final Vec3 centre;
		final double radius;
		final List<BlockPos> order = new ArrayList<>();
		final List<Double> dist = new ArrayList<>();
		final java.util.Set<BlockPos> seen = new java.util.HashSet<>();
		final java.util.ArrayDeque<long[]> encased = new java.util.ArrayDeque<>();
		final long start;
		int next;

		Burn(ServerLevel level, Vec3 centre, double radius) {
			this.level = level;
			this.centre = centre;
			this.radius = radius;
			this.start = level.getGameTime();
			int r = (int) Math.ceil(radius);
			BlockPos c = BlockPos.containing(centre);
			List<BlockPos> all = new ArrayList<>();
			for (BlockPos p : BlockPos.betweenClosed(c.offset(-r, -r, -r), c.offset(r, r, r))) {
				if (p.getY() < level.getMinY() || p.getY() > level.getMaxY()) continue;
				if (Vec3.atCenterOf(p).distanceToSqr(centre) > radius * radius) continue;
				BlockState st = level.getBlockState(p);
				if (st.isAir() || st.getDestroySpeed(level, p) < 0 || st.is(ModRegistry.POWER_BATTERY)) continue;
				all.add(p.immutable());
			}
			all.sort(java.util.Comparator.comparingDouble(p -> Vec3.atCenterOf(p).distanceToSqr(centre)));
			for (BlockPos p : all) {
				order.add(p);
				dist.add(Math.sqrt(Vec3.atCenterOf(p).distanceToSqr(centre)));
				// Whether anyone could see it, before anything goes.
				for (net.minecraft.core.Direction d : net.minecraft.core.Direction.values()) {
					BlockState side = level.getBlockState(p.relative(d));
					if (side.isAir() || !side.canOcclude()) {
						seen.add(p);
						break;
					}
				}
			}
		}

		/** One tick. Returns true when it's all gone. */
		boolean step() {
			long t = level.getGameTime() - start;
			int sweep = Math.max(1, RingTuning.FEAR_NUKE_BURN.ticks());
			double front = radius * Math.min(1.0, (t + 1) / (double) sweep);
			BlockState aura = ModRegistry.LIGHT_CONSTRUCT.defaultBlockState().setValue(Corps.PROPERTY, Corps.GREEN)
					.setValue(com.sparky.lanternring.block.LightConstructBlock.RIM, true);
			while (next < order.size() && dist.get(next) <= front) {
				BlockPos p = order.get(next++);
				if (seen.contains(p)) {
					level.setBlock(p, aura, QUIET);
					encased.add(new long[] {p.asLong(), t + BURN});
				} else {
					gone(p);
				}
			}
			while (!encased.isEmpty() && encased.peekFirst()[1] <= t) {
				gone(BlockPos.of(encased.pollFirst()[0]));
			}
			return next >= order.size() && encased.isEmpty();
		}

		private void gone(BlockPos p) {
			// The edge of the crater tells its neighbours, so water and sand fall in.
			boolean edge = Vec3.atCenterOf(p).distanceTo(centre) > radius - 2;
			level.setBlock(p, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), edge ? Block.UPDATE_ALL : QUIET);
		}

		/** The server is stopping: everything left goes at once. */
		void finish() {
			while (next < order.size()) gone(order.get(next++));
			while (!encased.isEmpty()) gone(BlockPos.of(encased.pollFirst()[0]));
		}
	}

	private static final List<Burn> BURNS = new ArrayList<>();
}
