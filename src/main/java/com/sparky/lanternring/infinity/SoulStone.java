package com.sparky.lanternring.infinity;

import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.ally.ConstructAlly;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.ProblemReporter;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.ai.memory.MemoryStatus;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.TagValueInput;
import net.minecraft.world.level.storage.TagValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * The Soul Stone. Every mob that dies is remembered for RingTuning.SOUL_MEMORY; using the stone
 * brings back up to {@link #MAX_REVIVE} of the ones that died within {@link #RADIUS} blocks, as
 * they were (same kind, look and gear), as loyal souls: they never target or hurt you, fight
 * whatever you fight (or the nearest monster) and follow you. A soul that is killed passes on
 * instead of dying (no loot), and every soul passes on after RingTuning.SOUL_BOND.
 *
 * <p><b>Raise the Graves</b> (crouch): {@link #GRAVES} undead claw their way up out of the ground
 * around you over RingTuning.SOUL_GRAVES_RISE, leaving dug-up coarse dirt, and join you as souls.
 * The kind fits the ground: husks from sand, strays from snow and ice, wither skeletons in the
 * Nether, drowned from under water, zombies and skeletons anywhere else.
 */
public final class SoulStone {
	public static final double RADIUS = 24;
	private static final int MAX_REVIVE = 8;
	/** At most this many souls follow one player; the oldest pass on first. */
	private static final int MAX_SOULS = 16;
	private static final int MAX_DEATHS = 64;
	private static final String SOUL_TAG = "lanternring.soul";
	/** How many undead Raise the Graves brings up, and how far out from you (3 to GRAVE_REACH blocks). */
	private static final int GRAVES = 6, GRAVE_REACH = 9;

	private record Death(EntityType<?> type, CompoundTag data, Vec3 pos, float yaw, long time) {
	}

	private record Soul(ServerLevel level, Mob mob, ServerPlayer owner, long until) {
	}

	private static final Map<ResourceKey<Level>, Deque<Death>> DEATHS = new HashMap<>();
	private static final Map<UUID, Soul> SOULS = new HashMap<>();

	/** An undead still climbing out of its grave: from below the ground up to standing on it. */
	private record Rising(Mob mob, double fromY, double toY, long start, BlockState ground) {
	}

	private static final Map<UUID, Rising> RISING = new HashMap<>();

	private SoulStone() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(SoulStone::tick);
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> remember(entity));
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Soul s : SOULS.values()) s.mob.discard();
			SOULS.clear();
			RISING.clear();
			DEATHS.clear();
		});
		// A soul left in a saved world (or an unloaded chunk) has passed on by the time it loads again.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(SOUL_TAG) && !SOULS.containsKey(entity.getUUID())) entity.discard();
		});
		// Souls never hurt their owner, each other or the owner's pets.
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			// Nothing hurts the dead while they climb out of the ground.
			if (RISING.containsKey(entity.getUUID())) return false;
			Soul attacker = source.getEntity() == null ? null : SOULS.get(source.getEntity().getUUID());
			return attacker == null || !isFriend(attacker.owner, entity);
		});
		// A soul that is killed passes on: no loot, no XP, and it isn't remembered again.
		ServerLivingEntityEvents.ALLOW_DEATH.register((entity, source, amount) -> {
			Soul soul = SOULS.remove(entity.getUUID());
			if (soul == null) return true;
			passOn(soul);
			return false;
		});
	}

	/** Whether {@code mob} is a soul and {@code target} its owner or one of the owner's friends (MobTargetMixin). */
	public static boolean spares(Mob mob, LivingEntity target) {
		if (target == null || SOULS.isEmpty()) return false;
		Soul soul = SOULS.get(mob.getUUID());
		return soul != null && isFriend(soul.owner, target);
	}

	/** Whether the entity is one of this player's souls. */
	public static boolean isSoulOf(Entity entity, Player player) {
		Soul soul = SOULS.get(entity.getUUID());
		return soul != null && soul.owner == player;
	}

	private static boolean isFriend(ServerPlayer owner, Entity entity) {
		if (entity == owner) return true;
		Soul other = SOULS.get(entity.getUUID());
		if (other != null) return other.owner == owner;
		return entity instanceof OwnableEntity pet && owner.equals(pet.getOwner());
	}

	private static void remember(LivingEntity entity) {
		if (!(entity instanceof Mob) || !(entity.level() instanceof ServerLevel level)) return;
		if (entity.getType() == EntityTypes.WITHER || entity.getType() == EntityTypes.ENDER_DRAGON || entity instanceof ConstructAlly) return;
		if (entity.entityTags().stream().anyMatch(t -> t.startsWith("lanternring."))) return;
		TagValueOutput out = TagValueOutput.createWithContext(ProblemReporter.DISCARDING, level.registryAccess());
		entity.saveWithoutId(out);
		Deque<Death> deaths = DEATHS.computeIfAbsent(level.dimension(), k -> new ArrayDeque<>());
		deaths.addFirst(new Death(entity.getType(), out.buildResult(), entity.position(), entity.getYRot(), level.getGameTime()));
		while (deaths.size() > MAX_DEATHS) deaths.removeLast();
	}

	/** Brings back the mobs that died near the player lately, newest first. */
	public static boolean revive(ServerLevel level, ServerPlayer player) {
		Deque<Death> deaths = DEATHS.get(level.dimension());
		long now = level.getGameTime();
		List<Death> picks = new ArrayList<>();
		if (deaths != null) {
			deaths.removeIf(d -> now - d.time > RingTuning.SOUL_MEMORY.ticks());
			for (Death d : deaths) {
				if (d.pos.distanceTo(player.position()) <= RADIUS) picks.add(d);
				if (picks.size() >= MAX_REVIVE) break;
			}
		}
		if (picks.isEmpty()) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.soul_none").withStyle(ChatFormatting.GOLD));
			return false;
		}
		int revived = 0;
		for (Death d : picks) {
			deaths.remove(d);
			Optional<Entity> made = EntityType.create(d.type, TagValueInput.create(ProblemReporter.DISCARDING, level.registryAccess(), d.data),
					level, EntitySpawnReason.LOAD);
			if (made.isEmpty() || !(made.get() instanceof Mob mob)) continue;
			mob.setUUID(UUID.randomUUID());
			mob.snapTo(d.pos.x, d.pos.y, d.pos.z, d.yaw, 0);
			mob.removeAllEffects();
			mob.clearFire();
			mob.deathTime = 0;
			mob.setHealth(mob.getMaxHealth());
			mob.fallDistance = 0;
			mob.setTarget(null);
			bind(mob);
			mob.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 1, false, false));
			// Known before it joins the world, or ENTITY_LOAD takes it for a leftover and removes it.
			SOULS.put(mob.getUUID(), new Soul(level, mob, player, now + RingTuning.SOUL_BOND.ticks()));
			if (!level.addFreshEntity(mob)) {
				SOULS.remove(mob.getUUID());
				continue;
			}
			rise(level, mob);
			revived++;
		}
		if (revived == 0) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.soul_none").withStyle(ChatFormatting.GOLD));
			return false;
		}
		trim(player);
		level.playSound(null, player.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.6f, 0.7f);
		level.playSound(null, player.blockPosition(), SoundEvents.SOUL_ESCAPE.value(), SoundSource.PLAYERS, 1.5f, 0.8f);
		level.sendParticles(ModParticles.of(ModParticles.MOTE, InfinityStone.SOUL.colour), player.getX(), player.getY() + 1.2, player.getZ(),
				30, 0.4, 0.5, 0.4, 0.05);
		player.sendOverlayMessage(Component.translatable("message.lanternring.soul_revived", revived).withStyle(ChatFormatting.GOLD));
		return true;
	}

	/** Marks a mob as a soul: it stays, drops nothing and doesn't burn by day. */
	private static void bind(Mob mob) {
		mob.addTag(SOUL_TAG);
		mob.setPersistenceRequired();
		for (EquipmentSlot slot : EquipmentSlot.values()) mob.setDropChance(slot, 0f);
		mob.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, -1, 0, false, false));
	}

	/** An orange column of light and souls where a mob comes back. */
	private static void rise(ServerLevel level, Mob mob) {
		double w = mob.getBbWidth() / 2, h = mob.getBbHeight();
		for (int i = 0; i < 6; i++) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, InfinityStone.SOUL.colour), mob.getX(), mob.getY() + i * h / 5, mob.getZ(),
					6, w, 0.1, w, 0.02);
		}
		level.sendParticles(ParticleTypes.SOUL, mob.getX(), mob.getY() + h / 2, mob.getZ(), 12, w, h / 2, w, 0.04);
		level.sendParticles(ModParticles.of(ModParticles.SHARD, InfinityStone.SOUL.colour), mob.getX(), mob.getY() + h / 2, mob.getZ(),
				20, w, h / 2, w, 0.05);
	}

	private static void trim(ServerPlayer owner) {
		List<Soul> mine = new ArrayList<>();
		for (Soul s : SOULS.values()) if (s.owner == owner) mine.add(s);
		mine.sort((a, b) -> Long.compare(a.until, b.until));
		for (int i = 0; i < mine.size() - MAX_SOULS; i++) {
			SOULS.remove(mine.get(i).mob.getUUID());
			passOn(mine.get(i));
		}
	}

	private static void passOn(Soul soul) {
		Mob mob = soul.mob;
		double h = mob.getBbHeight();
		soul.level.sendParticles(ParticleTypes.SOUL, mob.getX(), mob.getY() + h / 2, mob.getZ(), 16, mob.getBbWidth() / 2, h / 2, mob.getBbWidth() / 2, 0.06);
		soul.level.sendParticles(ModParticles.of(ModParticles.SHARD, InfinityStone.SOUL.colour), mob.getX(), mob.getY() + h / 2, mob.getZ(),
				24, mob.getBbWidth() / 2, h / 2, mob.getBbWidth() / 2, 0.08);
		soul.level.playSound(null, mob.blockPosition(), SoundEvents.SOUL_ESCAPE.value(), SoundSource.NEUTRAL, 1.2f, 1.0f);
		mob.discard();
	}

	private static void tick(MinecraftServer server) {
		if (SOULS.isEmpty()) return;
		if (!RISING.isEmpty()) RISING.values().removeIf(SoulStone::riseTick);
		for (Iterator<Soul> it = SOULS.values().iterator(); it.hasNext(); ) {
			Soul s = it.next();
			long now = s.level.getGameTime();
			if (!s.mob.isAlive() || s.mob.isRemoved()) {
				it.remove();
			} else if (now >= s.until || s.owner.isRemoved()) {
				it.remove();
				passOn(s);
			} else if (!RISING.containsKey(s.mob.getUUID())) {
				soulTick(s, now);
			}
		}
	}

	private static void soulTick(Soul s, long now) {
		Mob mob = s.mob;
		ServerPlayer owner = s.owner;
		// Undead souls don't burn by day (Fire Resistance stops the damage, this the flames).
		mob.clearFire();
		LivingEntity target = mob.getTarget();
		if (target != null && (!target.isAlive() || isFriend(owner, target))) target = null;
		if (target == null || now % 10 == 0) target = pickTarget(s);
		mob.setTarget(target);
		if (mob.getBrain().checkMemory(MemoryModuleType.ATTACK_TARGET, MemoryStatus.REGISTERED)) {
			if (target != null) mob.getBrain().setMemory(MemoryModuleType.ATTACK_TARGET, target);
			else mob.getBrain().eraseMemory(MemoryModuleType.ATTACK_TARGET);
		}
		if (target != null) {
			if (!(mob instanceof Enemy) && mob instanceof PathfinderMob && now % 10 == 0) mob.getNavigation().moveTo(target, 1.4);
			// Every soul can hit, even ones that never fight (a cow headbutts for its owner).
			if (!(mob instanceof Enemy) && now % 20 == 0 && mob.distanceTo(target) < 2.0 + mob.getBbWidth()) {
				float damage = mob.getAttributes().hasAttribute(Attributes.ATTACK_DAMAGE) ? (float) mob.getAttributeValue(Attributes.ATTACK_DAMAGE) : 0f;
				target.hurtServer(s.level, s.level.damageSources().mobAttack(mob), Math.max(4f, damage));
			}
		} else if (owner.level() == s.level) {
			double d = mob.distanceTo(owner);
			if (d > 32) mob.teleportTo(owner.getX(), owner.getY(), owner.getZ());
			else if (d > 5 && now % 10 == 0) mob.getNavigation().moveTo(owner, 1.2);
		}
		if ((now + mob.getId()) % 6 == 0) {
			s.level.sendParticles(ModParticles.of(ModParticles.MOTE, InfinityStone.SOUL.colour), mob.getX(), mob.getY() + mob.getBbHeight() * 0.5, mob.getZ(),
					1, mob.getBbWidth() * 0.4, mob.getBbHeight() * 0.4, mob.getBbWidth() * 0.4, 0.01);
		}
		if ((now + mob.getId()) % 40 == 0) {
			s.level.sendParticles(ParticleTypes.SOUL, mob.getX(), mob.getY() + mob.getBbHeight(), mob.getZ(), 1, 0.2, 0.1, 0.2, 0.02);
		}
	}

	// ---- Raise the Graves --------------------------------------------------------------------

	public static boolean raiseGraves(ServerLevel level, ServerPlayer player) {
		RandomSource random = level.getRandom();
		long now = level.getGameTime();
		int raised = 0;
		for (int i = 0; i < GRAVES; i++) {
			BlockPos grave = null;
			for (int tries = 0; tries < 12 && grave == null; tries++) {
				double a = Math.PI * 2 * (i + random.nextDouble() * 0.6) / GRAVES;
				double r = 3 + random.nextDouble() * (GRAVE_REACH - 3);
				grave = groundAt(level, BlockPos.containing(player.getX() + Math.cos(a) * r, player.getY(), player.getZ() + Math.sin(a) * r));
			}
			if (grave == null) continue;
			BlockState ground = level.getBlockState(grave.below());
			EntityType<? extends Mob> type = undeadFor(level, grave, ground, random);
			if (!(type.create(level, EntitySpawnReason.MOB_SUMMONED) instanceof Mob mob)) continue;
			double toY = grave.getY();
			double fromY = toY - mob.getBbHeight() - 0.2;
			mob.snapTo(grave.getX() + 0.5, fromY, grave.getZ() + 0.5, random.nextFloat() * 360f, 0f);
			mob.finalizeSpawn(level, level.getCurrentDifficultyAt(grave), EntitySpawnReason.MOB_SUMMONED, null);
			bind(mob);
			// Held still and unhurt in the ground while it climbs out.
			mob.setNoAi(true);
			mob.setNoGravity(true);
			mob.noPhysics = true;
			SOULS.put(mob.getUUID(), new Soul(level, mob, player, now + RingTuning.SOUL_BOND.ticks()));
			if (!level.addFreshEntity(mob)) {
				SOULS.remove(mob.getUUID());
				continue;
			}
			RISING.put(mob.getUUID(), new Rising(mob, fromY, toY, now, ground));
			// The grave: dug-up earth where it comes out.
			if (ground.is(Blocks.GRASS_BLOCK) || ground.is(Blocks.DIRT) || ground.is(Blocks.PODZOL) || ground.is(Blocks.MYCELIUM)) {
				level.setBlockAndUpdate(grave.below(), Blocks.COARSE_DIRT.defaultBlockState());
			}
			raised++;
		}
		if (raised == 0) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.graves_none").withStyle(ChatFormatting.GOLD));
			return false;
		}
		trim(player);
		level.playSound(null, player.blockPosition(), SoundEvents.SOUL_ESCAPE.value(), SoundSource.PLAYERS, 2f, 0.5f);
		level.playSound(null, player.blockPosition(), SoundEvents.ZOMBIE_AMBIENT, SoundSource.HOSTILE, 1.2f, 0.6f);
		level.sendParticles(ModParticles.of(ModParticles.MOTE, InfinityStone.SOUL.colour), player.getX(), player.getY() + 1.2, player.getZ(),
				30, 0.4, 0.5, 0.4, 0.05);
		player.sendOverlayMessage(Component.translatable("message.lanternring.graves", raised).withStyle(ChatFormatting.GOLD));
		return true;
	}

	/** Where something can stand near pos: solid ground below, room for a body above (searched a few blocks up and down). */
	private static BlockPos groundAt(ServerLevel level, BlockPos pos) {
		for (int dy = 4; dy >= -6; dy--) {
			BlockPos at = pos.above(dy);
			BlockState below = level.getBlockState(at.below());
			if (below.isFaceSturdy(level, at.below(), Direction.UP) && !below.hasBlockEntity()
					&& level.getBlockState(at).getCollisionShape(level, at).isEmpty()
					&& level.getBlockState(at.above()).getCollisionShape(level, at.above()).isEmpty()) {
				return at;
			}
		}
		return null;
	}

	private static EntityType<? extends Mob> undeadFor(ServerLevel level, BlockPos pos, BlockState ground, RandomSource random) {
		if (level.dimension() == Level.NETHER) return random.nextInt(3) == 0 ? EntityTypes.SKELETON : EntityTypes.WITHER_SKELETON;
		if (!level.getFluidState(pos).isEmpty()) return EntityTypes.DROWNED;
		if (ground.is(BlockTags.SAND)) return EntityTypes.HUSK;
		if (ground.is(Blocks.SNOW_BLOCK) || ground.is(BlockTags.ICE) || level.getBlockState(pos).is(Blocks.SNOW)) return EntityTypes.STRAY;
		if (ground.is(Blocks.MUD) || ground.is(Blocks.MUDDY_MANGROVE_ROOTS)) return EntityTypes.BOGGED;
		return random.nextInt(3) == 0 ? EntityTypes.SKELETON : EntityTypes.ZOMBIE;
	}

	/** Moves a rising undead up a step; true once it stands on the ground and is let loose. */
	private static boolean riseTick(Rising r) {
		Mob mob = r.mob;
		if (!mob.isAlive() || mob.isRemoved() || !(mob.level() instanceof ServerLevel level)) return true;
		float t = Math.min(1f, (level.getGameTime() - r.start) / (float) Math.max(1, RingTuning.SOUL_GRAVES_RISE.ticks()));
		// Fast at first, slowing as it hauls itself out.
		double eased = 1 - (1 - t) * (1 - t);
		mob.setPos(mob.getX(), r.fromY + (r.toY - r.fromY) * eased, mob.getZ());
		mob.setDeltaMovement(Vec3.ZERO);
		if (level.getGameTime() % 2 == 0) {
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, r.ground), mob.getX(), r.toY + 0.1, mob.getZ(),
					6, 0.4, 0.05, 0.4, 0.1);
			level.sendParticles(ParticleTypes.SOUL, mob.getX(), r.toY + 0.3, mob.getZ(), 1, 0.3, 0.1, 0.3, 0.03);
			level.sendParticles(ModParticles.of(ModParticles.MOTE, InfinityStone.SOUL.colour), mob.getX(), r.toY + 0.2, mob.getZ(),
					2, 0.4, 0.1, 0.4, 0.02);
		}
		if (level.getGameTime() % 8 == 0) {
			level.playSound(null, mob.blockPosition(), SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 0.8f, 0.7f + level.getRandom().nextFloat() * 0.3f);
		}
		if (t < 1f) return false;
		mob.noPhysics = false;
		mob.setNoAi(false);
		mob.setNoGravity(false);
		rise(level, mob);
		level.playSound(null, mob.blockPosition(), SoundEvents.GRAVEL_BREAK, SoundSource.HOSTILE, 1f, 0.6f);
		return true;
	}

	/** What the owner last hit, or what last hit them, or the nearest monster. */
	private static LivingEntity pickTarget(Soul s) {
		ServerPlayer owner = s.owner;
		for (LivingEntity e : new LivingEntity[] {owner.getLastHurtMob(), owner.getLastHurtByMob()}) {
			if (e != null && e.isAlive() && e.level() == s.level && !isFriend(owner, e) && e.distanceTo(s.mob) < 32) return e;
		}
		LivingEntity best = null;
		double bestD = 16 * 16;
		for (LivingEntity e : s.level.getEntitiesOfClass(LivingEntity.class, s.mob.getBoundingBox().inflate(16),
				e -> e instanceof Enemy && e.isAlive() && !isFriend(owner, e))) {
			double d = e.distanceToSqr(s.mob);
			if (d < bestD) {
				bestD = d;
				best = e;
			}
		}
		return best;
	}
}
