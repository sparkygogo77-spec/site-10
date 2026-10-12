package com.sparky.lanternring.corps;

import com.mojang.math.Transformation;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Brightness;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * The Orange Lantern's aerial drop, Larfleeze's Hoard Rain (J, 2026-10-12: "a ton of individual Gold
 * and diamond blocks he drops and even some netherite swords that act like very deadly arrows mixed
 * in the bunch, Big gold bars would be better ... gold dripstone swords or Pure gold arrows"). Over
 * {@link RingTuning#HOARD_RAIN} a storm of his hoard falls round the marker: big gold bars, gold and
 * diamond blocks that crush what they land on, and golden and netherite swords that fall point first
 * like arrows, the netherite ones deadly. It is still his: whatever lands bursts back into orange light
 * after {@link RingTuning#HOARD_LINGER}, so nothing is left to pick up.
 */
public final class HoardRain {
	/** What it costs, in charge (a full ring is 1000). */
	public static final int COST = 400;
	/** How far round the marker the hoard falls, and from how high. */
	public static final double RADIUS = 9, HEIGHT = 34;
	/** Pieces per second while it rains. */
	private static final int PER_SECOND = 22;
	private static final double GRAVITY = 0.11, TERMINAL = 2.6;

	enum Kind {
		BAR(Blocks.GOLD_BLOCK, null, 9f), GOLD(Blocks.GOLD_BLOCK, null, 10f), DIAMOND(Blocks.DIAMOND_BLOCK, null, 12f),
		GOLD_SWORD(null, Items.GOLDEN_SWORD, 12f), NETHERITE_SWORD(null, Items.NETHERITE_SWORD, 40f);

		final BlockState block;
		final ItemStack item;
		final float damage;

		Kind(net.minecraft.world.level.block.Block block, net.minecraft.world.item.Item item, float damage) {
			this.block = block == null ? null : block.defaultBlockState();
			this.item = item == null ? null : new ItemStack(item);
			this.damage = damage;
		}

		boolean sword() {
			return item != null;
		}

		static Kind pick(RandomSource random) {
			int r = random.nextInt(100);
			return r < 38 ? BAR : r < 52 ? GOLD : r < 68 ? DIAMOND : r < 86 ? GOLD_SWORD : NETHERITE_SWORD;
		}
	}

	private static final class Piece {
		final Kind kind;
		final Display body;
		Vec3 pos;
		double vy;
		/** Game time it landed, or -1 while it falls. */
		long landed = -1;
		/** Swords stop in the first thing they hit; blocks crush through everything on the way down. */
		final List<UUID> hit = new ArrayList<>();

		Piece(Kind kind, Display body, Vec3 pos, double vy) {
			this.kind = kind;
			this.body = body;
			this.pos = pos;
			this.vy = vy;
		}
	}

	private static final class Storm {
		final ServerLevel level;
		final UUID owner;
		final Vec3 centre;
		final long start;
		int spawned;
		final List<Piece> pieces = new ArrayList<>();

		Storm(ServerLevel level, UUID owner, Vec3 centre) {
			this.level = level;
			this.owner = owner;
			this.centre = centre;
			this.start = level.getGameTime();
		}
	}

	private static final List<Storm> STORMS = new ArrayList<>();

	private HoardRain() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(HoardRain::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Storm s : STORMS) {
				for (Piece p : s.pieces) p.body.discard();
			}
			STORMS.clear();
		});
	}

	/** Released over {@code mark}: the hoard starts to fall. The ring has been checked for charge. */
	public static boolean drop(ServerLevel level, Entity by, BlockPos mark) {
		Vec3 centre = Vec3.atBottomCenterOf(mark);
		STORMS.add(new Storm(level, by.getUUID(), centre));
		level.playSound(null, mark.above(12), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 3f, 0.7f);
		level.playSound(null, mark.above(12), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 3f, 0.5f);
		level.sendParticles(ModParticles.of(ModParticles.SHARD, Corps.ORANGE), centre.x, centre.y + HEIGHT, centre.z, 120, RADIUS * 0.6, 1.5, RADIUS * 0.6, 0.1);
		return true;
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Storm> it = STORMS.iterator(); it.hasNext(); ) {
			if (step(it.next())) it.remove();
		}
	}

	/** One tick of a storm. Returns true once it has all fallen and faded. */
	private static boolean step(Storm s) {
		ServerLevel level = s.level;
		long t = level.getGameTime() - s.start;
		int rain = Math.max(1, RingTuning.HOARD_RAIN.ticks());
		int due = (int) Math.min((long) rain * PER_SECOND / 20, (t + 1) * PER_SECOND / 20);
		while (s.spawned < due) {
			spawn(s);
			s.spawned++;
		}
		Entity owner = level.getEntity(s.owner);
		int linger = Math.max(1, RingTuning.HOARD_LINGER.ticks());
		for (Iterator<Piece> it = s.pieces.iterator(); it.hasNext(); ) {
			Piece p = it.next();
			if (p.landed < 0) {
				fall(s, p, owner);
			} else if (level.getGameTime() - p.landed >= linger) {
				level.sendParticles(ModParticles.of(ModParticles.SHARD, Corps.ORANGE), p.pos.x, p.pos.y + 0.4, p.pos.z, 8, 0.3, 0.3, 0.3, 0.06);
				p.body.discard();
				it.remove();
			}
		}
		if (t % 6 == 0 && s.spawned < due + 1 && t < rain) {
			level.playSound(null, s.centre.x, s.centre.y + 8, s.centre.z, SoundEvents.CHAIN_PLACE, SoundSource.PLAYERS, 1.5f, 0.6f + level.getRandom().nextFloat() * 0.4f);
		}
		return t >= rain && s.pieces.isEmpty();
	}

	private static void spawn(Storm s) {
		ServerLevel level = s.level;
		RandomSource random = level.getRandom();
		Kind kind = Kind.pick(random);
		double a = random.nextDouble() * Math.PI * 2, d = Math.sqrt(random.nextDouble()) * RADIUS;
		Vec3 pos = s.centre.add(Math.cos(a) * d, HEIGHT + random.nextDouble() * 10, Math.sin(a) * d);
		Display body;
		Transformation shape;
		float spin = random.nextFloat() * 360f;
		if (kind.sword()) {
			Display.ItemDisplay item = EntityTypes.ITEM_DISPLAY.create(level, EntitySpawnReason.TRIGGERED);
			if (item == null) return;
			item.setItemStack(kind.item.copy());
			item.setItemTransform(ItemDisplayContext.FIXED);
			// Turned so the point is down (the display shows the icon mirrored), and made big.
			shape = new Transformation(new Vector3f(), new Quaternionf().rotationY(spin * Mth.DEG_TO_RAD).rotateZ(45f * Mth.DEG_TO_RAD),
					new Vector3f(2.2f), new Quaternionf());
			body = item;
		} else {
			Display.BlockDisplay block = EntityTypes.BLOCK_DISPLAY.create(level, EntitySpawnReason.TRIGGERED);
			if (block == null) return;
			block.setBlockState(kind.block);
			// A big gold bar is a gold block stretched long and pressed flat; the blocks tumble a little.
			Vector3f size = kind == Kind.BAR ? new Vector3f(1.7f, 0.55f, 0.8f) : new Vector3f(1f);
			Quaternionf turn = new Quaternionf().rotationY(spin * Mth.DEG_TO_RAD);
			if (kind != Kind.BAR) turn.rotateX((random.nextFloat() - 0.5f) * 0.6f);
			// Display blocks hang from their corner: centre them on the piece.
			Vector3f centre = new Vector3f(size).mul(-0.5f, 0f, -0.5f);
			turn.transform(centre);
			shape = new Transformation(centre, turn, size, new Quaternionf());
			body = block;
		}
		body.setTransformation(shape);
		body.setPosRotInterpolationDuration(1);
		body.setViewRange(4f);
		body.setBrightnessOverride(new Brightness(15, 15));
		body.setPos(pos.x, pos.y, pos.z);
		level.addFreshEntity(body);
		s.pieces.add(new Piece(kind, body, pos, -0.6 - random.nextDouble() * 0.6));
	}

	/** Moves a falling piece, hurting what it passes through, and stops it on the ground. */
	private static void fall(Storm s, Piece p, Entity owner) {
		ServerLevel level = s.level;
		p.vy = Math.max(-TERMINAL, p.vy - GRAVITY);
		Vec3 next = p.pos.add(0, p.vy, 0);
		// The ground: the first solid block between here and the next step.
		double floor = Double.NaN;
		for (int y = Mth.floor(p.pos.y); y >= Mth.floor(next.y); y--) {
			BlockPos at = BlockPos.containing(next.x, y, next.z);
			if (!level.getBlockState(at).getCollisionShape(level, at).isEmpty()) {
				floor = at.getY() + level.getBlockState(at).getCollisionShape(level, at).max(net.minecraft.core.Direction.Axis.Y);
				break;
			}
		}
		if (!Double.isNaN(floor) && next.y <= floor) next = new Vec3(next.x, floor, next.z);
		double half = p.kind.sword() ? 0.4 : p.kind == Kind.BAR ? 0.8 : 0.5;
		AABB swept = new AABB(next.x - half, next.y, next.z - half, p.pos.x + half, p.pos.y + 1, p.pos.z + half);
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, swept, e -> e.isAlive() && !spared(e, owner))) {
			if (p.hit.contains(e.getUUID())) continue;
			p.hit.add(e.getUUID());
			DamageSource source = p.kind.sword()
					? (owner != null ? level.damageSources().thrown(owner, owner) : level.damageSources().fallingStalactite(null))
					: level.damageSources().fallingBlock(owner);
			e.hurtServer(level, source, p.kind.damage);
			level.playSound(null, e.getX(), e.getY(), e.getZ(), p.kind.sword() ? SoundEvents.TRIDENT_HIT : SoundEvents.ANVIL_LAND,
					SoundSource.PLAYERS, 1f, p.kind.sword() ? 0.8f : 1.4f);
			if (p.kind.sword()) {
				// Stuck in its target: it rides it down until it fades.
				next = new Vec3(next.x, Math.max(next.y, e.getY() + e.getBbHeight() * 0.5), next.z);
				land(s, p, next, false);
				return;
			}
		}
		p.pos = next;
		p.body.setPos(next.x, next.y + (p.kind.sword() ? 0.6 : 0), next.z);
		if (!Double.isNaN(floor) && next.y <= floor + 1e-3) land(s, p, next, true);
	}

	private static void land(Storm s, Piece p, Vec3 at, boolean ground) {
		ServerLevel level = s.level;
		p.landed = level.getGameTime();
		p.pos = at;
		// Swords bury their point in the ground.
		p.body.setPos(at.x, at.y + (p.kind.sword() ? 0.25 : 0), at.z);
		if (!ground) return;
		RandomSource random = level.getRandom();
		if (random.nextInt(3) == 0) {
			level.playSound(null, at.x, at.y, at.z, p.kind.sword() ? SoundEvents.TRIDENT_HIT_GROUND
					: p.kind == Kind.DIAMOND ? SoundEvents.AMETHYST_BLOCK_HIT : SoundEvents.CHAIN_BREAK,
					SoundSource.PLAYERS, 1.2f, 0.7f + random.nextFloat() * 0.4f);
		}
		level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.ORANGE), at.x, at.y + 0.2, at.z, 3, 0.4, 0.1, 0.4, 0.02);
	}

	/** The bearer and what is theirs (tamed pets) are spared. */
	private static boolean spared(LivingEntity e, Entity owner) {
		if (owner == null) return false;
		if (e == owner) return true;
		return e instanceof OwnableEntity pet && pet.getOwner() == owner;
	}
}
