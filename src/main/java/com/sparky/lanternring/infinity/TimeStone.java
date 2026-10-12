package com.sparky.lanternring.infinity;

import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.RingTuning;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.ProblemReporter;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.item.PrimedTnt;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.TagValueInput;
import net.minecraft.world.phys.Vec3;

/**
 * The Time Stone.
 * <ul>
 * <li><b>Rewind</b> (right-click): every block changed within {@link #RADIUS} blocks in the last
 * RingTuning.TIME_REWIND goes back to how it was, newest change first, over
 * RingTuning.TIME_REWIND_PLAY. Chests and other containers come back with what was in them, and
 * items dropped in the area since then vanish (they're un-dropped, so nothing is duplicated).
 * <li><b>Freeze</b> (crouch + right-click): mobs, arrows and other projectiles, falling blocks,
 * lit TNT and dropped items within {@link #RADIUS} blocks stop dead for RingTuning.TIME_FREEZE.
 * Frozen mobs can still be hit; they move again when time starts.
 * </ul>
 * Block changes are only logged while someone online carries a Time Stone (loose or in a Gauntlet),
 * so without one this costs nothing. The log is filled by LevelSetBlockMixin.
 */
public final class TimeStone {
	public static final int RADIUS = 16;
	private static final int MAX_LOG = 250_000;
	private static final String FROZEN_TAG = "lanternring.time_frozen";

	/** Whether block changes are being logged (someone online carries the stone). Read by LevelSetBlockMixin. */
	public static volatile boolean recording;
	/** True while the stone itself is putting blocks back, so those changes aren't logged. */
	private static boolean rewinding;

	private record Change(BlockPos pos, BlockState old, CompoundTag blockEntity, long time) {
	}

	private static final Map<ResourceKey<Level>, ArrayDeque<Change>> LOG = new HashMap<>();
	private static final List<Rewind> REWINDS = new ArrayList<>();

	private record Frozen(Entity entity, Vec3 pos, Vec3 motion, boolean noGravity, boolean noAi, long until) {
	}

	private static final Map<UUID, Frozen> FROZEN = new HashMap<>();

	private TimeStone() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(TimeStone::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Frozen f : FROZEN.values()) thaw(f);
			FROZEN.clear();
			REWINDS.clear();
			LOG.clear();
			recording = false;
		});
		// Something frozen when the world was saved moves again when it loads.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(FROZEN_TAG) && !FROZEN.containsKey(entity.getUUID())) {
				entity.removeTag(FROZEN_TAG);
				entity.setNoGravity(false);
				if (entity instanceof Mob mob) mob.setNoAi(false);
			}
		});
	}

	// ---- the block log ----------------------------------------------------------------------

	/** Called by LevelSetBlockMixin just before a block changes. */
	public static void beforeSet(Level level, BlockPos pos, BlockState next) {
		if (rewinding || !(level instanceof ServerLevel server) || !server.getServer().isSameThread() || level.isOutsideBuildHeight(pos)) return;
		BlockState old = level.getBlockState(pos);
		if (old == next) return;
		CompoundTag data = null;
		if (old.hasBlockEntity()) {
			BlockEntity be = level.getBlockEntity(pos);
			if (be != null) data = be.saveWithFullMetadata(level.registryAccess());
		}
		ArrayDeque<Change> log = LOG.computeIfAbsent(server.dimension(), k -> new ArrayDeque<>());
		log.addLast(new Change(pos.immutable(), old, data, server.getGameTime()));
		if (log.size() > MAX_LOG) log.removeFirst();
	}

	private static boolean carries(Player player) {
		Inventory inv = player.getInventory();
		for (int i = 0; i < inv.getContainerSize(); i++) {
			ItemStack stack = inv.getItem(i);
			if (stack.is(Infinity.TIME_STONE)) return true;
			if (stack.getItem() instanceof InfinityGauntletItem && InfinityGauntletItem.has(stack, InfinityStone.TIME)) return true;
		}
		return false;
	}

	// ---- Rewind -----------------------------------------------------------------------------

	/** Blocks being put back, a few each tick. */
	private static final class Rewind {
		final ServerLevel level;
		final List<Change> changes;
		final int ticks;
		int age;
		int done;

		Rewind(ServerLevel level, List<Change> changes) {
			this.level = level;
			this.changes = changes;
			this.ticks = Math.max(1, RingTuning.TIME_REWIND_PLAY.ticks());
		}

		/** Puts back this tick's share; true when every block is back. */
		boolean step() {
			age++;
			int upTo = Math.min(changes.size(), (int) Math.ceil(changes.size() * age / (double) ticks));
			rewinding = true;
			try {
				for (; done < upTo; done++) restore(level, changes.get(done), done % 3 == 0);
			} finally {
				rewinding = false;
			}
			return done >= changes.size();
		}
	}

	private static void restore(ServerLevel level, Change c, boolean sparkle) {
		if (!level.isLoaded(c.pos)) return;
		level.setBlock(c.pos, c.old, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE | Block.UPDATE_SUPPRESS_DROPS);
		if (c.blockEntity != null) {
			BlockEntity be = level.getBlockEntity(c.pos);
			if (be != null) {
				be.loadWithComponents(TagValueInput.create(ProblemReporter.DISCARDING, level.registryAccess(), c.blockEntity));
				be.setChanged();
				level.sendBlockUpdated(c.pos, c.old, c.old, Block.UPDATE_CLIENTS);
			}
		}
		if (sparkle) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, InfinityStone.TIME.colour), c.pos.getX() + 0.5, c.pos.getY() + 0.5, c.pos.getZ() + 0.5,
					2, 0.35, 0.35, 0.35, 0.01);
		}
	}

	public static boolean rewind(ServerLevel level, ServerPlayer player) {
		ArrayDeque<Change> log = LOG.get(level.dimension());
		long now = level.getGameTime();
		long window = RingTuning.TIME_REWIND.ticks();
		BlockPos center = player.blockPosition();
		double r2 = (double) RADIUS * RADIUS;
		// Newest first; each block goes back to its oldest state in the window, and blocks are put
		// back in the order they last changed (most recent first), like a film run backwards.
		LinkedHashMap<BlockPos, Change> back = new LinkedHashMap<>();
		if (log != null) {
			for (Iterator<Change> it = log.descendingIterator(); it.hasNext(); ) {
				Change c = it.next();
				if (now - c.time > window) break;
				if (c.pos.distSqr(center) > r2) continue;
				back.put(c.pos, c);
				it.remove();
			}
		}
		// Items dropped here since then are un-dropped.
		int unDropped = 0;
		for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, player.getBoundingBox().inflate(RADIUS),
				e -> e.getAge() < window && e.distanceToSqr(player) <= r2 && !e.getItem().is(Infinity.TIME_STONE))) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, InfinityStone.TIME.colour), item.getX(), item.getY() + 0.2, item.getZ(),
					3, 0.1, 0.1, 0.1, 0.02);
			item.discard();
			unDropped++;
		}
		if (back.isEmpty() && unDropped == 0) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.time_rewind_none").withStyle(ChatFormatting.GREEN));
			return false;
		}
		if (!back.isEmpty()) REWINDS.add(new Rewind(level, new ArrayList<>(back.values())));
		clock(level, player, 3);
		level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.2f, 0.5f);
		level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.2f, 0.6f);
		player.sendOverlayMessage(Component.translatable("message.lanternring.time_rewind", back.size(),
				RingTuning.TIME_REWIND.ticks() / 20).withStyle(ChatFormatting.GREEN));
		return true;
	}

	// ---- Freeze -----------------------------------------------------------------------------

	public static boolean freeze(ServerLevel level, ServerPlayer player) {
		long until = level.getGameTime() + RingTuning.TIME_FREEZE.ticks();
		double r2 = (double) RADIUS * RADIUS;
		int frozen = 0;
		for (Entity e : level.getEntities(player, player.getBoundingBox().inflate(RADIUS), e -> e.isAlive() && e.distanceToSqr(player) <= r2)) {
			if (!(e instanceof Mob || e instanceof Projectile || e instanceof ItemEntity || e instanceof FallingBlockEntity || e instanceof PrimedTnt)) continue;
			if (e instanceof Mob mob && mob.isNoAi() && !FROZEN.containsKey(e.getUUID())) continue;
			if (SoulStone.isSoulOf(e, player) || e instanceof OwnableEntity pet && player.equals(pet.getOwner())) continue;
			Frozen old = FROZEN.get(e.getUUID());
			if (old != null) {
				// Already frozen: the clock just starts over.
				FROZEN.put(e.getUUID(), new Frozen(e, old.pos, old.motion, old.noGravity, old.noAi, until));
				frozen++;
				continue;
			}
			FROZEN.put(e.getUUID(), new Frozen(e, e.position(), e.getDeltaMovement(), e.isNoGravity(),
					e instanceof Mob mob && mob.isNoAi(), until));
			e.addTag(FROZEN_TAG);
			e.setNoGravity(true);
			if (e instanceof Mob mob) mob.setNoAi(true);
			e.setDeltaMovement(Vec3.ZERO);
			RingPowers.syncVelocity(e);
			level.sendParticles(ModParticles.of(ModParticles.SHARD, InfinityStone.TIME.colour), e.getX(), e.getY() + e.getBbHeight() / 2, e.getZ(),
					8, e.getBbWidth() / 2, e.getBbHeight() / 2, e.getBbWidth() / 2, 0.02);
			frozen++;
		}
		if (frozen == 0) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.time_freeze_none").withStyle(ChatFormatting.GREEN));
			return false;
		}
		clock(level, player, 4);
		level.playSound(null, player.blockPosition(), SoundEvents.BELL_BLOCK, SoundSource.PLAYERS, 1.5f, 0.5f);
		level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.0f, 0.6f);
		player.sendOverlayMessage(Component.translatable("message.lanternring.time_freeze", frozen).withStyle(ChatFormatting.GREEN));
		return true;
	}

	private static void thaw(Frozen f) {
		Entity e = f.entity;
		e.removeTag(FROZEN_TAG);
		if (e.isRemoved()) return;
		e.setNoGravity(f.noGravity);
		if (e instanceof Mob mob) mob.setNoAi(f.noAi);
		// Projectiles fly on as if nothing happened.
		if (!(e instanceof Mob)) {
			e.setDeltaMovement(f.motion);
			RingPowers.syncVelocity(e);
		}
	}

	/** Green rings of light around the player, like the Time Stone's mandala. */
	private static void clock(ServerLevel level, Player player, int rings) {
		Vec3 at = player.position().add(0, 0.1, 0);
		for (int ring = 1; ring <= rings; ring++) {
			double r = RADIUS * ring / (double) rings;
			int points = (int) (r * 6);
			for (int i = 0; i < points; i++) {
				double a = Math.PI * 2 * i / points;
				level.sendParticles(ModParticles.of(ModParticles.MOTE, InfinityStone.TIME.colour), at.x + Math.cos(a) * r, at.y, at.z + Math.sin(a) * r,
						1, 0, 0.05, 0, 0);
			}
		}
		// The ring of runes at the hand.
		Vec3 hand = RingPowers.handPos(player);
		for (int i = 0; i < 16; i++) {
			double a = Math.PI * 2 * i / 16;
			level.sendParticles(ModParticles.of(ModParticles.SPARK, InfinityStone.TIME.colour), hand.x + Math.cos(a) * 0.6, hand.y + Math.sin(a) * 0.6, hand.z,
					1, 0, 0, 0, 0);
		}
	}

	// ---- every tick -------------------------------------------------------------------------

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 20 == 0) {
			boolean any = false;
			for (ServerPlayer p : server.getPlayerList().getPlayers()) {
				if (carries(p)) {
					any = true;
					break;
				}
			}
			recording = any;
			if (!any) {
				LOG.clear();
			} else {
				long window = RingTuning.TIME_REWIND.ticks();
				for (ServerLevel level : server.getAllLevels()) {
					ArrayDeque<Change> log = LOG.get(level.dimension());
					long now = level.getGameTime();
					while (log != null && !log.isEmpty() && now - log.peekFirst().time > window) log.removeFirst();
				}
			}
		}
		REWINDS.removeIf(Rewind::step);
		if (FROZEN.isEmpty()) return;
		for (Iterator<Frozen> it = FROZEN.values().iterator(); it.hasNext(); ) {
			Frozen f = it.next();
			Entity e = f.entity;
			long now = e.level().getGameTime();
			if (e.isRemoved() || now >= f.until) {
				it.remove();
				thaw(f);
				continue;
			}
			e.setDeltaMovement(Vec3.ZERO);
			if (e.position().distanceToSqr(f.pos) > 1.0e-4) e.setPos(f.pos.x, f.pos.y, f.pos.z);
			if (e instanceof PrimedTnt tnt) tnt.setFuse(tnt.getFuse() + 1);
			if (e instanceof ItemEntity item) item.setPickUpDelay(2);
			if ((now + e.getId()) % 10 == 0 && e.level() instanceof ServerLevel level) {
				level.sendParticles(ModParticles.of(ModParticles.MOTE, InfinityStone.TIME.colour), e.getX(), e.getY() + e.getBbHeight() / 2, e.getZ(),
						1, e.getBbWidth() / 2, e.getBbHeight() / 2, e.getBbWidth() / 2, 0);
			}
		}
	}
}
