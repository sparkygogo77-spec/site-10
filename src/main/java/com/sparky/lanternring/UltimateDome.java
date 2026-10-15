package com.sparky.lanternring;

import com.sparky.lanternring.net.RingFxPayload;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Green Lantern's ultimate (J's pick D1, Blender pass 835): with the green lantern out, look up and hold
 * the lantern key. A beam goes straight up to the top of a construct dome of radius {@link #RADIUS}, which then
 * forms top-down and, a little later, bottom-up from the ground; the two fronts meet 70% of the way down
 * after {@link RingTuning#ULTIMATE_FORM}. It stands for {@link RingTuning#ULTIMATE_TIME}, then comes apart top
 * first.
 *
 * <p>Every spot of the shell appears on the exact tick its front reaches it (no fade-in, no random delay). A
 * 150-block hemisphere is about 141,000 blocks of surface, so no blocks are placed: each client draws the shell
 * as one textured mesh revealed by the same front ({@code UltimateDomeFx}), and the server's barrier is a sphere
 * check on entities. Nothing but the caster crosses a formed part of the shell, either way.
 */
public final class UltimateDome {
	public static final int RADIUS = 150;
	/** How far below the centre the shell reaches, in blocks, so it meets ground that dips away. */
	public static final int SKIRT = 12;
	/** The polar angle (0 straight up) of the shell's lowest edge. */
	public static final double MAX_POLAR = Math.PI / 2 + SKIRT / (double) RADIUS;
	/** Timeline in ticks (pass 835): the beam goes up at BEAM_START, hits the apex at APEX, where the top front starts. */
	public static final int BEAM_START = 18, APEX = 28;
	/** Where the two fronts meet, as a fraction of the way down. */
	public static final double MEET = 0.7;
	/** How long the dome takes to come apart at the end. */
	public static final int BREAK = 30;
	/** Looking at least this far up (degrees) turns the lantern power into the ultimate. */
	public static final float LOOK_UP = 45f;
	private static final double SYNC_RANGE = RADIUS + 96;

	private static final class Dome {
		final ServerLevel level;
		final Vec3 center;
		final long started;
		final int form;
		final int stand;
		/** Which side of the shell each entity near it was on last tick (true: inside). */
		Map<Integer, Boolean> sides = new HashMap<>();

		Dome(ServerLevel level, Vec3 center, long started, int form, int stand) {
			this.level = level;
			this.center = center;
			this.started = started;
			this.form = form;
			this.stand = stand;
		}

		long end() {
			return APEX + form + stand;
		}
	}

	private static final Map<UUID, Dome> DOMES = new HashMap<>();

	private UltimateDome() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(UltimateDome::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> DOMES.clear());
	}

	public static boolean standing(ServerPlayer player) {
		return DOMES.containsKey(player.getUUID());
	}

	/** Whether the player is looking up far enough for the lantern power to be the ultimate. */
	static boolean lookingUp(ServerPlayer player) {
		return player.getXRot() <= -LOOK_UP;
	}

	/** Starts the ultimate over the ground under the player. */
	public static void start(ServerPlayer player) {
		if (standing(player)) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.ultimate_dome.up").withStyle(ChatFormatting.GREEN));
			return;
		}
		ServerLevel level = player.level();
		BlockPos feet = player.blockPosition();
		int ground = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, feet.getX(), feet.getZ());
		double y = Math.min(player.getY(), ground);
		Vec3 center = new Vec3(player.getX(), y, player.getZ());
		int form = Math.max(20, RingTuning.ULTIMATE_FORM.ticks());
		int stand = Math.max(20, RingTuning.ULTIMATE_TIME.ticks());
		DOMES.put(player.getUUID(), new Dome(level, center, level.getGameTime(), form, stand));
		WhatsNew.done(player, "lantern.ultimate_dome");
		player.sendOverlayMessage(Component.translatable("message.lanternring.ultimate_dome").withStyle(ChatFormatting.GREEN));
		level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 2f, 0.5f);
		sync(player, DOMES.get(player.getUUID()), 0);
	}

	// ---- the fronts, shared with the client so what you see is what stops things ----

	/** How far down the top front is at tick t (0 the top, MEET the meeting line). */
	public static double topFrac(float t, int form) {
		double u = Mth.clamp((t - APEX) / form, 0, 1);
		return MEET * Math.pow(u, 1 / 1.6);
	}

	/** The tick the bottom front starts climbing (60 when forming takes 200 ticks). */
	public static int bottomStart(int form) {
		return APEX + Math.round(form * 0.16f);
	}

	/** How far down the bottom front is at tick t (1 the ground, MEET the meeting line). */
	public static double bottomFrac(float t, int form) {
		int start = bottomStart(form);
		double u = Mth.clamp((t - start) / (APEX + form - start), 0, 1);
		return 1 - (1 - MEET) * u;
	}

	/** The top front's polar angle at whole tick t, snapped to whole blocks of arc. */
	public static double topPolar(long t, int form) {
		if (t >= APEX + form) return MAX_POLAR;
		return Math.floor(topFrac(t, form) * MAX_POLAR * RADIUS) / RADIUS;
	}

	/** The bottom front's polar angle at whole tick t, snapped to whole blocks of arc. */
	public static double bottomPolar(long t, int form) {
		if (t >= APEX + form) return 0;
		if (t < bottomStart(form)) return MAX_POLAR + 1;
		return Math.ceil(bottomFrac(t, form) * MAX_POLAR * RADIUS) / RADIUS;
	}

	/** Whether the shell at polar angle polar has formed at tick t. */
	public static boolean formed(double polar, long t, int form) {
		if (t < APEX || polar > MAX_POLAR) return false;
		return polar <= topPolar(t, form) || polar >= bottomPolar(t, form);
	}

	// ---- server tick ----

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Dome>> it = DOMES.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Dome> e = it.next();
			Dome d = e.getValue();
			ServerPlayer player = server.getPlayerList().getPlayer(e.getKey());
			long t = d.level.getGameTime() - d.started;
			if (t >= d.end()) {
				it.remove();
				sendAll(d, player, -1);
				d.level.playSound(null, BlockPos.containing(d.center.add(0, RADIUS, 0)), SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.PLAYERS, 6f, 0.5f);
				continue;
			}
			// The beam straight up from the ring to the dome's top.
			int beam = Math.max(10, RingTuning.ULTIMATE_BEAM.ticks());
			if (player != null && player.level() == d.level && t >= BEAM_START && t < BEAM_START + beam && (t - BEAM_START) % 5 == 0) {
				Corps before = Corps.enter(Corps.GREEN);
				try {
					RingFx.send(d.level, RingFxPayload.Kind.EMIT, RingPowers.handPos(player), d.center.add(0, RADIUS, 0));
				} finally {
					Corps.restore(before);
				}
			}
			if (t == APEX) {
				d.level.playSound(null, BlockPos.containing(d.center.add(0, Math.min(RADIUS, 40), 0)), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 8f, 0.5f);
			}
			if (t > APEX && t <= APEX + d.form && t % 10 == 0) {
				d.level.playSound(null, BlockPos.containing(d.center), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 3f, 0.6f + 0.8f * (t - APEX) / d.form);
			}
			// Keep every client nearby in step (and catch up anyone who walks or logs in).
			if (t % 20 == 0) sendAll(d, player, t);
			if (t >= APEX) barrier(d, player, t);
		}
	}

	/** Pushes back anything (but the caster and what they shot) crossing a formed part of the shell. */
	private static void barrier(Dome d, ServerPlayer owner, long t) {
		Vec3 c = d.center;
		AABB box = new AABB(c.x - RADIUS - 4, c.y - SKIRT - 4, c.z - RADIUS - 4, c.x + RADIUS + 4, c.y + RADIUS + 4, c.z + RADIUS + 4);
		Map<Integer, Boolean> sides = new HashMap<>();
		for (Entity e : d.level.getEntities((Entity) null, box, e -> e.isAlive() && !e.isSpectator())) {
			if (owner != null && (e == owner || e.getVehicle() == owner || owner.getVehicle() == e)) continue;
			if (e instanceof ItemEntity || e instanceof ExperienceOrb) continue;
			if (e instanceof Projectile p && owner != null && p.getOwner() == owner) continue;
			double half = e.getBbHeight() / 2;
			Vec3 now = e.position().add(0, half, 0);
			double dn = now.distanceTo(c);
			if (Math.abs(dn - RADIUS) > 48) continue;
			double pad = Math.max(e.getBbWidth(), e.getBbHeight()) / 2;
			Boolean wasIn = d.sides.get(e.getId());
			// New near the shell: which side it came from (its position at the start of the tick).
			boolean in = wasIn != null ? wasIn : new Vec3(e.xo, e.yo + half, e.zo).distanceTo(c) < RADIUS;
			sides.put(e.getId(), in);
			// Crossing, or pressed into the shell from its side.
			boolean hits = in ? dn > RADIUS - pad : dn < RADIUS + pad;
			if (!hits) continue;
			Vec3 dir = now.subtract(c);
			if (dir.lengthSqr() < 1e-6) continue;
			dir = dir.normalize();
			double polar = Math.acos(Mth.clamp(dir.y, -1, 1));
			if (!formed(polar, t, d.form)) {
				// Not there yet: it may cross.
				sides.put(e.getId(), dn < RADIUS);
				continue;
			}
			if (e instanceof Projectile) {
				d.level.sendParticles(ModParticles.of(ModParticles.SPARK, Corps.GREEN), now.x, now.y, now.z, 3, 0.1, 0.1, 0.1, 0);
				e.discard();
				continue;
			}
			double r = in ? RADIUS - pad - 0.6 : RADIUS + pad + 0.6;
			Vec3 to = c.add(dir.scale(r)).subtract(0, half, 0);
			Vec3 v = e.getDeltaMovement();
			double radial = v.dot(dir);
			// Take away the motion into the shell and bounce it back a little.
			Vec3 bounced = v.subtract(dir.scale(radial * 1.4));
			if (e instanceof ServerPlayer sp) {
				sp.teleportTo(to.x, to.y, to.z);
			} else {
				e.setPos(to.x, to.y, to.z);
			}
			e.setDeltaMovement(bounced);
			RingPowers.syncVelocity(e);
		}
		d.sides = sides;
	}

	private static void sync(ServerPlayer owner, Dome d, long t) {
		sendAll(d, owner, t);
	}

	/** value is the dome's age in ticks, or -1 when it comes apart. */
	private static void sendAll(Dome d, ServerPlayer owner, long t) {
		RingFxPayload payload = new RingFxPayload(RingFxPayload.Kind.ULTIMATE_DOME, d.center, d.center.add(0, RADIUS, 0), t,
				d.form, Corps.GREEN, owner == null ? -1 : owner.getId());
		for (ServerPlayer p : PlayerLookup.around(d.level, d.center, SYNC_RANGE)) {
			ServerPlayNetworking.send(p, payload);
		}
	}
}
