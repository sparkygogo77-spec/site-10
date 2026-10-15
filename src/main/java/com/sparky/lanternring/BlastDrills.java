package com.sparky.lanternring;

import com.sparky.lanternring.ally.DreadRunner;
import com.sparky.lanternring.ally.RageBull;
import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.Fluids;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * BLAST: a spinning hard-light drill, steered like a saw construct. Holding right-click forms it
 * in front of the ring, pointing the way you face, and it hangs there (this is the only time it
 * shows before it drills). The longer it is held the further it will reach: MIN_LENGTH to LENGTH
 * over RingTuning.BLAST_CHARGE. Left-click launches it straight on from where it formed, boring a
 * tunnel and breaking each block as its tip reaches it, at LENGTH blocks per
 * RingTuning.BLAST_DRILL_TIME. While right-click stays held, a double left-click steers it toward
 * where you are looking relative to the drill, in a gradual curve (a quarter turn takes
 * RingTuning.BLAST_TURN), and holding the second click keeps it turning after your aim and boring
 * on past its reach until it is let go (up to RingTuning.BLAST_STEER_MAX). Crouch + left-click
 * before launching picks the level (3x3, 5x5 or 7x7). Letting go of right-click before launching
 * dissolves it for free; after launching the drill runs out its reach on its own.
 * Clients draw it from the BLAST_DRILL effect the server sends every tick (client BlastDrillFx).
 */
public final class BlastDrills {
	public static final double LENGTH = 50;
	/** The reach of a tap; holding builds it up to LENGTH. */
	public static final double MIN_LENGTH = 10;
	/** Tunnel width per level (index 1 to 3). */
	private static final int[] WIDTH = {3, 3, 5, 7};
	private static final float DAMAGE = 10.0f;
	/** The drill model from tip to back, in blocks (blast_drill.bbmodel is 100 pixels long). */
	public static final double DRILL_LENGTH = 100 / 16.0;
	/** How far ahead of the tunnel's start the drill's back appears, so it doesn't fill the screen. */
	public static final double START = 1.5;
	/** How far ahead of the tunnel's start the formed drill's back hangs, far enough out to see it whole. */
	public static final double FORM_GAP = 4.0;
	/** Steering aims at a point this far beyond the drill along your look, so it turns the way you look. */
	private static final double LEAD = 24;
	/** The drill moves in steps this long, cutting and turning a little at each. */
	private static final double STEP = 0.4;
	/** A double-click held counts as held until it's let go, or this many ticks after its last message (sent every tick), whichever comes first. */
	private static final int HOLD_GRACE = 10;

	private static final class Drill {
		final int id = ++lastId;
		final ServerLevel level;
		final Player owner;
		final int lvl;
		final int half;
		/** How far from the middle a mob can be and still be hit: the tunnel's half width plus a bit. */
		final double reach;
		/** Where the tunnel starts, on its centre line. */
		final Vec3 origin;
		/** The tip, on the tunnel's centre line, and the way it is heading. */
		Vec3 tip;
		Vec3 heading;
		Vec3 right;
		Vec3 up;
		/** How far the tip has come along its (maybe curved) path from origin. */
		double travelled;
		double length;
		boolean launched;
		/** The bearer still holds right-click, so double-clicks steer it. */
		boolean controlled = true;
		/** Where a double-click pointed it; it turns toward this until it gets there. */
		Vec3 steerTo;
		/** The game time the second click of a double-click was last held, and when launched. */
		long held = -100;
		boolean holding;
		long launchedAt;
		/** Blocks bored past the charged reach while held, and how many of them are paid for. */
		double extra;
		int paid;
		final Set<BlockPos> wet = new HashSet<>();
		final Set<UUID> hit = new HashSet<>();
		double nextLight = 2.0;
		double nextBubbles = 1.0;
		boolean gurgled;
		/** Whose drill it is: its tunnel lights take that corps' colour. */
		final Corps corps = Corps.current();

		Drill(ServerLevel level, Player owner, Vec3 origin, Vec3 look, int lvl) {
			this.level = level;
			this.owner = owner;
			this.lvl = lvl;
			this.half = width(lvl) / 2;
			this.reach = width(lvl) / 2.0 + 0.5;
			this.origin = origin;
			this.heading = look;
			frame();
			this.tip = origin.add(look.scale(FORM_GAP + DRILL_LENGTH));
			this.travelled = FORM_GAP + DRILL_LENGTH;
			this.length = LENGTH;
		}

		/** right and up across the heading; looking straight up or down keeps the last right. */
		void frame() {
			Vec3 r = heading.cross(new Vec3(0, 1, 0));
			if (r.lengthSqr() < 1.0e-4) {
				if (right == null) {
					Direction side = owner.getDirection().getClockWise();
					r = new Vec3(side.getStepX(), 0, side.getStepZ());
				} else {
					r = right.subtract(heading.scale(right.dot(heading)));
				}
			}
			right = r.normalize();
			up = right.cross(heading).normalize();
		}
	}

	private static int lastId;
	private static final List<Drill> DRILLS = new ArrayList<>();
	/** Each player's drill that is formed and waiting, or launched and still theirs to steer. */
	private static final Map<UUID, Drill> HELD = new HashMap<>();
	/** When each charging player's charge started (game time); a level change restarts it. */
	private static final Map<UUID, Long> CHARGING = new HashMap<>();

	private BlastDrills() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(BlastDrills::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			DRILLS.clear();
			HELD.clear();
			CHARGING.clear();
		});
	}

	/** Blocks per tick, from the Durations menu's time for the whole tunnel. */
	public static double speed() {
		return LENGTH / Math.max(1, RingTuning.BLAST_DRILL_TIME.ticks());
	}

	/** Where the tip is when the drill appears. */
	public static double startTip() {
		return START + DRILL_LENGTH;
	}

	/** The most the heading turns in a tick, in radians: a quarter turn over RingTuning.BLAST_TURN. */
	public static double turnPerTick() {
		return Math.PI / 2 / Math.max(1, RingTuning.BLAST_TURN.ticks());
	}

	// ---- levels and charging -------------------------------------------------------------

	/** Blast level 4 is the Red ring's Rage Bull (see RageBull) or the Yellow ring's Dread Runner (see DreadRunner) instead of a drill. */
	public static final int BULL = 4;

	public static int level(ItemStack ring) {
		int level = ring.getOrDefault(ModComponents.BLAST_LEVEL, 1);
		return level >= 1 && level <= maxLevel(ring) ? level : 1;
	}

	/** Three drill levels; the Red ring has the Rage Bull as a fourth and the Yellow ring the Dread Runner. */
	public static int maxLevel(ItemStack ring) {
		Corps corps = Corps.of(ring);
		return corps == Corps.RED || corps == Corps.YELLOW ? BULL : 3;
	}

	/** Whether this ring's Blast level 4 is the Dread Runner rather than the Rage Bull. */
	public static boolean runner(ItemStack ring) {
		return Corps.of(ring) == Corps.YELLOW;
	}

	public static int width(int level) {
		return WIDTH[Mth.clamp(level, 1, 3)];
	}

	/**
	 * Charge for a shot charged this far (0 to 1): 0.5% to 1% of a full ring at level 1, 1.5x that
	 * at level 2 and 2x at level 3 (PowerRingItem.MAX_CHARGE = 1000, so 5 = 0.5%).
	 */
	public static int cost(int level, float fraction) {
		// The Rage Bull, the biggest blast of all the rings: 3% to 6%.
		if (level >= BULL) return Math.round(30 + 30 * Mth.clamp(fraction, 0f, 1f));
		float base = 5 + 5 * Mth.clamp(fraction, 0f, 1f);
		float times = level >= 3 ? 2f : level == 2 ? 1.5f : 1f;
		return Math.round(base * times);
	}

	/** How far a charge held for this many ticks reaches, 0 to 1. */
	public static float fraction(long heldTicks) {
		return Mth.clamp(heldTicks / (float) Math.max(1, RingTuning.BLAST_CHARGE.ticks()), 0f, 1f);
	}

	public static double length(float fraction) {
		return MIN_LENGTH + (LENGTH - MIN_LENGTH) * fraction;
	}

	/** Right-click pressed in Blast mode: the charge starts building and the drill forms in front of the ring. */
	public static void beginCharge(ServerPlayer player) {
		CHARGING.put(player.getUUID(), player.level().getGameTime());
		ItemStack ring = player.getUseItem().getItem() instanceof PowerRingItem ? player.getUseItem() : player.getMainHandItem();
		if (ring.getItem() instanceof PowerRingItem && level(ring) < BULL) form(player, level(ring));
	}

	/** Charging stopped without letting go on purpose (switched to a lantern charge): no drill. */
	public static void cancel(ServerPlayer player) {
		CHARGING.remove(player.getUUID());
		Drill drill = HELD.get(player.getUUID());
		if (drill != null && !drill.launched) dissolve(drill);
		else if (drill != null) letGo(drill);
	}

	/** How far the player's current charge reaches, 0 to 1, or -1 when not charging. */
	public static float charged(ServerPlayer player) {
		Long since = CHARGING.get(player.getUUID());
		return since == null ? -1f : fraction(player.level().getGameTime() - since);
	}

	/** Crouch + left-click before launching: the next level, and the charge (and the drill) start over. */
	public static void cycleLevel(ServerPlayer player) {
		ItemStack ring = player.getUseItem();
		if (!(ring.getItem() instanceof PowerRingItem) || PowerRingItem.getMode(ring) != RingMode.BLAST || !CHARGING.containsKey(player.getUUID())) {
			return;
		}
		int next = level(ring) % maxLevel(ring) + 1;
		ring.set(ModComponents.BLAST_LEVEL, next);
		Drill drill = HELD.get(player.getUUID());
		if (drill != null && !drill.launched) dissolve(drill);
		beginCharge(player);
		player.sendOverlayMessage(levelText(next, ring).copy().withStyle(ChatFormatting.GREEN));
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.6f - 0.2f * next);
	}

	public static Component levelText(int level, ItemStack ring) {
		if (level >= BULL && runner(ring)) {
			return Component.translatable("message.lanternring.blast_runner", DreadRunner.WIDTH, DreadRunner.HEIGHT, percent(cost(level, 0f)), percent(cost(level, 1f)));
		}
		return levelText(level);
	}

	public static Component levelText(int level) {
		if (level >= BULL) {
			return Component.translatable("message.lanternring.blast_bull", (int) RageBull.DIAMETER, percent(cost(level, 0f)), percent(cost(level, 1f)));
		}
		int w = width(level);
		return Component.translatable("message.lanternring.blast_level", level, w, w,
				percent(cost(level, 0f)), percent(cost(level, 1f)));
	}

	/** Charge points as a percent of a full ring: 5 -> "0.5", 10 -> "1", 15 -> "1.5". */
	public static String percent(int points) {
		return points % 10 == 0 ? String.valueOf(points / 10) : String.valueOf(points / 10.0);
	}

	/**
	 * Left-click while holding right-click. Before launching it launches (as far as it was charged,
	 * if the ring has the charge); the Rage Bull and Dread Runner go too. After launching only a
	 * double-click does anything (see steer).
	 */
	public static boolean launch(ServerPlayer player) {
		ItemStack ring = player.getUseItem();
		if (!(ring.getItem() instanceof PowerRingItem) || PowerRingItem.getMode(ring) != RingMode.BLAST) return false;
		Long since = CHARGING.get(player.getUUID());
		if (since == null) return false;
		ServerLevel level = player.level();
		int lvl = level(ring);
		Drill drill = HELD.get(player.getUUID());
		if (lvl < BULL && (drill == null || drill.launched)) return false;
		float fraction = fraction(level.getGameTime() - since);
		int cost = cost(lvl, fraction);
		if (!player.isCreative() && PowerRingItem.getCharge(ring) < cost) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
			return false;
		}
		CHARGING.remove(player.getUUID());
		if (lvl >= BULL && runner(ring)) {
			if (!DreadRunner.start(level, player, fraction)) return false;
			WhatsNew.done(player, "yellow.dread_runner");
		} else if (lvl >= BULL) {
			if (!RageBull.start(level, player, fraction)) return false;
		} else {
			go(drill, length(fraction));
			WhatsNew.done(player, "mode.blast.drill");
		}
		if (!player.isCreative()) PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - cost);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.BLAST));
		return true;
	}

	/** A double left-click while right-click is held: turn toward where the bearer is looking. Launches it first if it hadn't gone. */
	public static void steer(ServerPlayer player) {
		Drill drill = HELD.get(player.getUUID());
		if (drill != null && !drill.launched) {
			launch(player);
			return;
		}
		if (drill == null || !drill.controlled) return;
		drill.steerTo = aim(drill);
		WhatsNew.done(player, "mode.blast.steer");
	}

	/** The second click of a double-click is held (sent every tick): it keeps turning after the aim and boring on. */
	public static void steerHeld(ServerPlayer player) {
		Drill drill = HELD.get(player.getUUID());
		if (drill == null || !drill.launched || !drill.controlled) return;
		if (!drill.holding) WhatsNew.done(player, "mode.blast.steer_hold");
		drill.holding = true;
		drill.held = drill.level.getGameTime();
	}

	/** The held second click was let go: it carries on along its current heading and runs out its reach. */
	public static void steerStop(ServerPlayer player) {
		Drill drill = HELD.get(player.getUUID());
		if (drill != null) drill.holding = false;
	}

	/**
	 * Right-click let go. Before launching the drill dissolves (nothing is spent); after, it runs
	 * out its reach on its own. Level 4 (the Rage Bull or the Dread Runner) still goes on release.
	 */
	public static boolean release(ServerLevel level, ServerPlayer player, ItemStack ring) {
		Drill drill = HELD.get(player.getUUID());
		if (drill != null) {
			CHARGING.remove(player.getUUID());
			if (!drill.launched) dissolve(drill);
			else letGo(drill);
			return false;
		}
		if (!CHARGING.containsKey(player.getUUID()) || level(ring) < BULL) {
			CHARGING.remove(player.getUUID());
			return false;
		}
		return launch(player);
	}

	/** While charging: a click each time the reach grows by a fifth, and a chime when it's full. */
	public static void chargeTick(ServerPlayer player) {
		Long since = CHARGING.get(player.getUUID());
		if (since == null) return;
		long held = player.level().getGameTime() - since;
		int full = Math.max(1, RingTuning.BLAST_CHARGE.ticks());
		if (held > 0 && held <= full && held % Math.max(1, full / 5) == 0) {
			float f = fraction(held);
			player.level().playSound(null, player.blockPosition(), held == full ? SoundEvents.BEACON_POWER_SELECT : SoundEvents.NOTE_BLOCK_HAT.value(),
					SoundSource.PLAYERS, 0.5f, 0.8f + 0.8f * f);
			ItemStack ring = player.getUseItem();
			boolean bull = level(ring) >= BULL;
			double reach = !bull ? length(f) : runner(ring) ? DreadRunner.run(f) : RageBull.run(f);
			player.sendOverlayMessage(Component.translatable("message.lanternring.blast_reach", Math.round(reach))
					.withStyle(held >= full ? ChatFormatting.WHITE : ChatFormatting.GREEN));
		}
	}

	// ---- the drill ------------------------------------------------------------------------

	/** The drill forms in front of the bearer's ring, pointing the way they face, and waits there. */
	private static void form(ServerPlayer player, int lvl) {
		Drill old = HELD.remove(player.getUUID());
		if (old != null && !old.launched) dissolve(old);
		else if (old != null) old.controlled = false;
		ServerLevel level = player.level();
		Drill drill = new Drill(level, player, tunnelStart(player, lvl), player.getLookAngle(), lvl);
		HELD.put(player.getUUID(), drill);
		DRILLS.add(drill);
		Vec3 middle = drill.tip.subtract(drill.heading.scale(DRILL_LENGTH / 2));
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), middle);
		level.playSound(null, middle.x, middle.y, middle.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0f, 1.3f);
		show(drill, 0f);
	}

	/** Centre the tunnel slightly below the eyes so the player's whole body fits through it. Wider tunnels grow upward and sideways from the same floor. */
	private static Vec3 tunnelStart(Player player, int lvl) {
		Vec3 look = player.getLookAngle();
		Vec3 right = look.cross(new Vec3(0, 1, 0));
		if (right.lengthSqr() < 1.0e-4) {
			Direction side = player.getDirection().getClockWise();
			right = new Vec3(side.getStepX(), 0, side.getStepZ());
		}
		Vec3 up = right.normalize().cross(look).normalize();
		return player.getEyePosition().subtract(0, 0.6, 0).add(up.scale(width(lvl) / 2 - 1));
	}

	/** Fires a drill straight away, reaching length blocks at the given level (1 to 3), that nobody steers (villagers). */
	public static boolean start(ServerLevel level, Player player, double length, int lvl) {
		Drill drill = new Drill(level, player, tunnelStart(player, lvl), player.getLookAngle(), lvl);
		drill.controlled = false;
		DRILLS.add(drill);
		go(drill, length);
		return true;
	}

	private static void go(Drill drill, double length) {
		drill.launched = true;
		drill.launchedAt = drill.level.getGameTime();
		drill.length = Math.max(drill.travelled, Math.min(LENGTH, length));
		Vec3 back = drill.tip.subtract(drill.heading.scale(DRILL_LENGTH));
		show(drill, 2f);
		drill.level.playSound(null, back.x, back.y, back.z, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 1.0f, 1.6f);
		// The stretch it formed over goes straight away, so it never bores on from inside a block.
		for (double t = 1.0; t <= drill.travelled; t += STEP) cut(drill, drill.origin.add(drill.heading.scale(t)));
	}

	/** Not launched and let go: it fades where it hung, nothing spent. */
	private static void dissolve(Drill drill) {
		DRILLS.remove(drill);
		HELD.remove(drill.owner.getUUID(), drill);
		show(drill, -2f);
		drill.level.playSound(null, drill.tip.x, drill.tip.y, drill.tip.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 0.8f, 1.2f);
	}

	/** The bearer let go of right-click after launching: no more steering, it finishes its reach. */
	private static void letGo(Drill drill) {
		drill.controlled = false;
		HELD.remove(drill.owner.getUUID(), drill);
		drill.holding = false;
		drill.length = Math.max(drill.length, drill.travelled);
	}

	/** Tells clients where the drill is: value 0 hanging (formed), 1 boring, 2 just launched, -1 burst at its end, -2 dissolved. */
	private static void show(Drill drill, float value) {
		Corps before = Corps.enter(drill.corps);
		try {
			RingFx.send(drill.level, Kind.BLAST_DRILL, drill.tip, drill.tip.add(drill.heading), value, drill.id * 4 + drill.lvl,
					value == 2f && drill.owner instanceof ServerPlayer ? drill.owner : null);
		} finally {
			Corps.restore(before);
		}
	}

	/** The way to where the bearer is looking, LEAD blocks past the drill along their look. */
	private static Vec3 aim(Drill drill) {
		Vec3 eye = drill.owner.getEyePosition();
		Vec3 at = eye.add(drill.owner.getLookAngle().scale(eye.distanceTo(drill.tip) + LEAD));
		Vec3 to = at.subtract(drill.tip);
		return to.lengthSqr() < 1.0e-4 ? drill.heading : to.normalize();
	}

	/** Turns from toward to by at most angle radians. */
	static Vec3 turn(Vec3 from, Vec3 to, double angle, Vec3 fallbackAxis) {
		double cos = Mth.clamp(from.dot(to), -1, 1);
		double between = Math.acos(cos);
		if (between <= angle) return to;
		Vec3 axis = from.cross(to);
		axis = axis.lengthSqr() < 1.0e-8 ? fallbackAxis : axis.normalize();
		// Rodrigues: from rotated about axis (perpendicular to it) by angle.
		return from.scale(Math.cos(angle)).add(axis.cross(from).scale(Math.sin(angle))).normalize();
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Drill> it = DRILLS.iterator(); it.hasNext(); ) {
			Drill drill = it.next();
			if (drill.controlled && !holding(drill)) {
						if (!drill.launched) {
					it.remove();
					HELD.remove(drill.owner.getUUID(), drill);
					show(drill, -2f);
					continue;
				}
				letGo(drill);
			}
			if (!drill.launched) {
				if (drill.level.getGameTime() % 4 == 0) show(drill, 0f);
				continue;
			}
			Corps before = Corps.enter(drill.corps);
			try {
				move(drill);
			} finally {
				Corps.restore(before);
			}
			if (drill.travelled >= drill.length) {
				// The tip bursts at the tunnel's end (clients draw the flash, LabFx.blastEnd).
				Vec3 end = drill.tip;
				show(drill, -1f);
				drill.level.playSound(null, end.x, end.y, end.z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.PLAYERS, 1.6f, 0.6f);
				drill.level.playSound(null, end.x, end.y, end.z, SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.PLAYERS, 0.8f, 1.4f);
				HELD.remove(drill.owner.getUUID(), drill);
				it.remove();
			} else {
				show(drill, 1f);
			}
		}
	}

	/** The owner still holds right-click with the ring in Blast mode, in the same world. */
	private static boolean holding(Drill drill) {
		Player owner = drill.owner;
		return owner.isAlive() && owner.level() == drill.level && owner.isUsingItem() && owner.getUseItem().getItem() instanceof PowerRingItem
				&& PowerRingItem.getMode(owner.getUseItem()) == RingMode.BLAST && HELD.get(owner.getUUID()) == drill;
	}

	/** One tick of boring: a few short steps, turning a little toward the aim at each. */
	private static void move(Drill drill) {
		long now = drill.level.getGameTime();
		boolean holdingTurn = drill.controlled && drill.holding && now - drill.held <= HOLD_GRACE
				&& now - drill.launchedAt < RingTuning.BLAST_STEER_MAX.ticks();
		Vec3 target = holdingTurn ? aim(drill) : drill.steerTo;
		double speed = speed();
		if (holdingTurn && drill.travelled + 2 * speed > drill.length) {
			// Held: it bores on past its reach, paying for each block as it goes (a tick ahead, so it never ends while held).
			if (pay(drill, drill.travelled + 2 * speed - drill.length)) drill.length = drill.travelled + 2 * speed;
		}
		double from = drill.travelled;
		Vec3 start = drill.tip;
		double left = Math.min(speed, drill.length - drill.travelled);
		double perStep = turnPerTick() * STEP / Math.max(1.0e-3, speed);
		BlockState loudest = null;
		while (left > 1.0e-6) {
			double s = Math.min(STEP, left);
			left -= s;
			if (target != null) {
				drill.heading = turn(drill.heading, target, perStep * s / STEP, drill.up);
				drill.frame();
			}
			drill.tip = drill.tip.add(drill.heading.scale(s));
			drill.travelled += s;
			BlockState broke = cut(drill, drill.tip);
			if (loudest == null) loudest = broke;
			lightTunnel(drill);
			bubbleTrail(drill);
		}
		// Rounding never leaves it hanging a hair short of its end.
		if (drill.length - drill.travelled < 1.0e-6) drill.travelled = drill.length;
		if (drill.steerTo != null && drill.heading.dot(drill.steerTo) > 0.9999) drill.steerTo = null;
		if (loudest != null) {
			// One grinding crunch per tick, in the sound of a block the drill just broke.
			drill.level.playSound(null, drill.tip.x, drill.tip.y, drill.tip.z, loudest.getSoundType().getBreakSound(), SoundSource.PLAYERS, 1.0f, 0.7f);
		}
		hurt(drill, start, from);
	}

	/** Charge for blocks bored past the charged reach: a full charge's price spread over LENGTH blocks. */
	private static boolean pay(Drill drill, double blocks) {
		drill.extra += blocks;
		if (!(drill.owner instanceof ServerPlayer player) || player.isCreative()) return true;
		ItemStack ring = player.getUseItem();
		int owed = (int) Math.ceil(drill.extra * cost(drill.lvl, 1f) / LENGTH) - drill.paid;
		if (owed <= 0) return true;
		if (PowerRingItem.getCharge(ring) < owed) {
			drill.extra -= blocks;
			player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
			return false;
		}
		PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - owed);
		drill.paid += owed;
		return true;
	}

	/** Breaks the tunnel's cross-section around this point on its centre line; returns the hardest block broken, or null. */
	private static BlockState cut(Drill drill, Vec3 center) {
		ServerLevel level = drill.level;
		BlockState loudest = null;
		float hardest = -1;
		for (int a = -drill.half; a <= drill.half; a++) {
			for (int b = -drill.half; b <= drill.half; b++) {
				BlockPos pos = BlockPos.containing(center.add(drill.right.scale(a)).add(drill.up.scale(b)));
				// Water and plants are cleared too; the surrounding water then flows back in by itself.
				// Only a real water source is put back: not flowing water or the Deluge's liquid,
				// which would otherwise leave new sources behind when the glow fades.
				if (level.getFluidState(pos).getType() == Fluids.WATER) drill.wet.add(pos);
				BlockState state = level.getBlockState(pos);
				if (state.isAir() || state.getBlock() instanceof BlastGlowBlock || state.getDestroySpeed(level, pos) < 0 || state.hasBlockEntity()
						|| !level.mayInteract(drill.owner, pos)) {
					continue;
				}
				level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
				// Plain water has no debris worth showing; it only clouded the shot underwater.
				if (!state.is(Blocks.WATER)) HeldConstructs.debris(level, pos, state);
				float hard = state.getDestroySpeed(level, pos);
				if (state.getFluidState().isEmpty() && hard > hardest) {
					hardest = hard;
					loudest = state;
				}
			}
		}
		return loudest;
	}

	/** Mobs the tip and body passed this tick, within the tunnel. */
	private static void hurt(Drill drill, Vec3 start, double from) {
		ServerLevel level = drill.level;
		Vec3 back = start.subtract(drill.heading.scale(Math.min(DRILL_LENGTH, from)));
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(back, drill.tip).inflate(drill.reach),
				e -> e != drill.owner && e.isAlive() && !e.isSpectator() && !drill.hit.contains(e.getUUID())
						&& near(e.getBoundingBox().getCenter(), back, drill.tip) < drill.reach)) {
			drill.hit.add(target.getUUID());
			target.hurtServer(level, level.damageSources().indirectMagic(drill.owner, drill.owner), DAMAGE);
		}
	}

	/** Distance from point to the segment a-b. */
	private static double near(Vec3 point, Vec3 a, Vec3 b) {
		Vec3 ab = b.subtract(a);
		double len = ab.lengthSqr();
		double t = len < 1.0e-6 ? 0 : Mth.clamp(point.subtract(a).dot(ab) / len, 0, 1);
		return point.distanceTo(a.add(ab.scale(t)));
	}

	// ---- for tests ----------------------------------------------------------------------------

	/** The way this player's drill is heading, or null if they have none in hand. */
	public static Vec3 heading(Player player) {
		Drill drill = HELD.get(player.getUUID());
		return drill == null ? null : drill.heading;
	}

	/** Where this player's drill's tip is, or null. */
	public static Vec3 tip(Player player) {
		Drill drill = HELD.get(player.getUUID());
		return drill == null ? null : drill.tip;
	}

	/** Whether this player's drill has been launched (false while it hangs where it formed). */
	public static boolean launched(Player player) {
		Drill drill = HELD.get(player.getUUID());
		return drill != null && drill.launched;
	}

	/**
	 * Underwater, the sea folds back over the tunnel almost at once, so the drill also leaves a
	 * trail of bubbles bursting out of the tunnel walls behind it to show where it went.
	 */
	private static void bubbleTrail(Drill drill) {
		ServerLevel level = drill.level;
		Vec3 look = drill.heading;
		for (; drill.nextBubbles <= drill.travelled; drill.nextBubbles += 1.5) {
			double t = drill.nextBubbles;
			Vec3 center = drill.tip;
			if (!drill.wet.contains(BlockPos.containing(center))) continue;
			for (int i = 0; i < 8; i++) {
				double a = i * Math.PI / 4 + t;
				Vec3 out = drill.right.scale(Math.cos(a)).add(drill.up.scale(Math.sin(a)));
				Vec3 at = center.add(out.scale(drill.reach - 0.5));
				// Count 0 makes the offsets a velocity: bubbles spray outwards and a little forwards.
				level.sendParticles(ParticleTypes.BUBBLE, at.x, at.y, at.z, 0, out.x + look.x * 0.5, out.y + look.y * 0.5, out.z + look.z * 0.5, 0.35);
			}
			level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, center.x, center.y, center.z, 3, 1.2, 1.2, 1.2, 0.05);
			if (!drill.gurgled) {
				drill.gurgled = true;
				level.playSound(null, drill.tip.x, drill.tip.y, drill.tip.z, SoundEvents.BUBBLE_COLUMN_WHIRLPOOL_INSIDE, SoundSource.PLAYERS, 1.0f, 1.2f);
			}
		}
	}

	/**
	 * Leaves a few invisible lights down the middle of the tunnel behind the drill, so the glowing
	 * scar lights its walls. Plain block light, so it works with any shader pack.
	 */
	private static void lightTunnel(Drill drill) {
		if (RingTuning.BLAST_AFTERGLOW.ticks() <= 0) return;
		BlockState glow = Corps.state(ModRegistry.BLAST_GLOW);
		for (; drill.nextLight <= drill.travelled; drill.nextLight += 4.0) {
			BlockPos pos = BlockPos.containing(drill.tip);
			if (drill.level.getBlockState(pos).isAir() && drill.level.mayInteract(drill.owner, pos)) {
				drill.level.setBlock(pos, glow.setValue(BlastGlowBlock.WATERLOGGED, drill.wet.contains(pos)), 3);
			}
		}
	}
}
