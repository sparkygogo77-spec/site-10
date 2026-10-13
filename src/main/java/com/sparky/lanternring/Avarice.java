package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.ComponentUtils;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.scores.PlayerTeam;
import net.minecraft.world.scores.Scoreboard;

/**
 * The Orange Lantern's powers of avarice. Hoard pulls every item and XP orb within 20 blocks to the
 * bearer, and each stack it hauls in feeds the ring. Steal snatches what the mob you look at holds
 * or wears, or robs it of its loot if it has nothing. Avarice calls up orange copies of the last
 * kinds of mob the bearer killed while wearing the ring; they fight for the bearer, never drop
 * anything, and fade after RingTuning.AVARICE_LIFETIME.
 */
public final class Avarice {
	/** How far Hoard reaches, in blocks. */
	public static final double HOARD_RADIUS = 20;
	/** Charge each stack Hoard hauls in feeds back to the ring (0.5% of a full ring). */
	private static final int FEED_PER_STACK = 5;
	private static final double STEAL_RANGE = 24;
	/** The kinds of slain mob a ring remembers, newest first. */
	private static final int HOARD_KINDS = 6;
	/** Avarice calls up this many copies (the newest kinds), and a bearer has at most MAX_COPIES at once. */
	private static final int SUMMON = 3, MAX_COPIES = 6;
	private static final String COPY_TAG = "lanternring.avarice_copy", ROBBED_TAG = "lanternring.robbed";
	private static final String TEAM = "lanternring_avarice";

	/** The kinds of mob this ring's bearer has slain with it on, newest first (entity type ids). */
	public static final DataComponentType<List<Identifier>> SLAIN = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("slain"),
			DataComponentType.<List<Identifier>>builder().persistent(Identifier.CODEC.listOf())
					.networkSynchronized(Identifier.STREAM_CODEC.apply(ByteBufCodecs.list())).build());

	/** Items and orbs being hauled in, and how far along. */
	private static final class Haul {
		final ServerLevel level;
		final ServerPlayer owner;
		final List<Entity> loot;
		final List<Vec3> from = new ArrayList<>();
		final long start;
		final int ticks;

		Haul(ServerLevel level, ServerPlayer owner, List<Entity> loot) {
			this.level = level;
			this.owner = owner;
			this.loot = loot;
			for (Entity e : loot) from.add(e.position());
			this.start = level.getGameTime();
			this.ticks = Math.max(1, RingTuning.HOARD_TIME.ticks());
		}
	}

	private record Copy(ServerLevel level, Mob mob, ServerPlayer owner, long until) {
	}

	private static final List<Haul> HAULS = new ArrayList<>();
	private static final Map<UUID, Copy> COPIES = new HashMap<>();

	private Avarice() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Avarice::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Copy c : COPIES.values()) c.mob.discard();
			COPIES.clear();
			HAULS.clear();
		});
		// A copy left over from a saved world (or an unloaded chunk) is gone when it loads again.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(COPY_TAG) && !COPIES.containsKey(entity.getUUID())) entity.discard();
		});
		// Copies never hurt their bearer, each other or the bearer's pets.
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			Copy attacker = source.getEntity() == null ? null : COPIES.get(source.getEntity().getUUID());
			return attacker == null || !isFriend(attacker.owner, entity);
		});
		// A copy that dies fades out instead: no loot, no XP.
		ServerLivingEntityEvents.ALLOW_DEATH.register((entity, source, amount) -> {
			Copy copy = COPIES.remove(entity.getUUID());
			if (copy == null) return true;
			fade(copy);
			return false;
		});
		// Every mob slain with the orange ring on joins its hoard.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(source.getEntity() instanceof ServerPlayer player) || entity instanceof Player) return;
			if (entity.getType() == EntityTypes.ENDER_DRAGON || entity.getType() == EntityTypes.WITHER) return;
			ItemStack ring = orangeRing(player);
			if (ring.isEmpty()) return;
			List<Identifier> slain = new ArrayList<>(ring.getOrDefault(SLAIN, List.of()));
			Identifier kind = BuiltInRegistries.ENTITY_TYPE.getKey(entity.getType());
			slain.remove(kind);
			slain.addFirst(kind);
			while (slain.size() > HOARD_KINDS) slain.removeLast();
			ring.set(SLAIN, List.copyOf(slain));
		});
	}

	private static ItemStack orangeRing(Player player) {
		for (ItemStack stack : new ItemStack[] {player.getMainHandItem(), player.getOffhandItem()}) {
			if (stack.getItem() instanceof PowerRingItem && Corps.of(stack) == Corps.ORANGE) return stack;
		}
		return ItemStack.EMPTY;
	}

	private static boolean isFriend(ServerPlayer owner, Entity entity) {
		if (entity == owner || COPIES.containsKey(entity.getUUID())) return true;
		return entity instanceof OwnableEntity pet && owner.equals(pet.getOwner());
	}

	// ---- Hoard ------------------------------------------------------------------------------

	public static boolean hoard(ServerLevel level, Player player) {
		if (!(player instanceof ServerPlayer owner)) return false;
		Vec3 at = owner.position();
		AABB box = owner.getBoundingBox().inflate(HOARD_RADIUS);
		List<Entity> loot = new ArrayList<>();
		for (Entity e : level.getEntities(owner, box, e -> e instanceof ItemEntity || e instanceof ExperienceOrb)) {
			if (e.isAlive() && e.position().distanceTo(at) <= HOARD_RADIUS) loot.add(e);
		}
		if (loot.isEmpty()) {
			owner.sendOverlayMessage(Component.translatable("message.lanternring.hoard_nothing").withStyle(ChatFormatting.GOLD));
			return false;
		}
		int stacks = 0;
		for (Entity e : loot) {
			e.noPhysics = true;
			if (e instanceof ItemEntity item) {
				item.setNoPickUpDelay();
				stacks++;
			}
		}
		HAULS.add(new Haul(level, owner, loot));
		// Avarice feeds the ring: every stack hauled in pays some charge back.
		ItemStack ring = orangeRing(owner);
		if (!ring.isEmpty()) PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) + stacks * FEED_PER_STACK);
		owner.sendOverlayMessage(Component.translatable("message.lanternring.hoard", stacks, loot.size() - stacks).withStyle(ChatFormatting.GOLD));
		RingFx.send(level, Kind.PUSH, RingPowers.handPos(owner), at);
		level.playSound(null, owner.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.0f, 0.6f);
		return true;
	}

	private static void haulTick(Haul haul) {
		float t = Math.min(1f, (haul.level.getGameTime() - haul.start) / (float) haul.ticks);
		// Eases in: a slow tug that speeds up as the loot nears.
		float ease = t * t;
		Vec3 to = haul.owner.position().add(0, 0.6, 0);
		for (int i = 0; i < haul.loot.size(); i++) {
			Entity e = haul.loot.get(i);
			if (!e.isAlive()) continue;
			Vec3 p = haul.from.get(i).lerp(to, ease).add(0, Math.sin(t * Math.PI) * 2.5, 0);
			e.setPos(p.x, p.y, p.z);
			e.setDeltaMovement(Vec3.ZERO);
			e.needsSync = true;
			if ((haul.level.getGameTime() + i) % 2 == 0) {
				haul.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.ORANGE), p.x, p.y + 0.2, p.z, 1, 0.05, 0.05, 0.05, 0.01);
			}
			if (t >= 1) e.noPhysics = false;
		}
	}

	// ---- Steal ------------------------------------------------------------------------------

	private static final EquipmentSlot[] STEAL_ORDER = {EquipmentSlot.MAINHAND, EquipmentSlot.OFFHAND, EquipmentSlot.HEAD,
			EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET, EquipmentSlot.BODY};

	public static boolean steal(ServerLevel level, Player player) {
		RingPowers.Target target = RingPowers.trace(level, player, STEAL_RANGE);
		if (!(target.entity() instanceof LivingEntity victim) || COPIES.containsKey(victim.getUUID())
				|| victim instanceof Player other && other.isCreative()) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.steal_no_target").withStyle(ChatFormatting.GOLD));
			return false;
		}
		List<ItemStack> taken = new ArrayList<>();
		for (EquipmentSlot slot : STEAL_ORDER) {
			ItemStack held = victim.getItemBySlot(slot);
			if (held.isEmpty()) continue;
			taken.add(held.copy());
			victim.setItemSlot(slot, ItemStack.EMPTY);
			break;
		}
		if (taken.isEmpty() && victim instanceof Mob mob && !mob.entityTags().contains(ROBBED_TAG)) {
			// Nothing in its hands or on its back: rob it of the loot it would have dropped, once.
			mob.getLootTable().ifPresent(key -> mob.dropFromLootTable(level, level.damageSources().playerAttack(player), true, key, taken::add));
			mob.addTag(ROBBED_TAG);
		}
		if (taken.isEmpty()) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.steal_nothing", victim.getDisplayName()).withStyle(ChatFormatting.GOLD));
			return false;
		}
		Vec3 from = victim.position().add(0, victim.getBbHeight() * 0.6, 0);
		for (ItemStack stack : taken) {
			if (!player.getInventory().add(stack)) player.spawnAtLocation(level, stack);
		}
		player.sendOverlayMessage(Component.translatable("message.lanternring.stole", taken.getFirst().getHoverName(), victim.getDisplayName())
				.withStyle(ChatFormatting.GOLD));
		RingFx.send(level, Kind.TETHER, RingPowers.handPos(player), from);
		level.sendParticles(ModParticles.of(ModParticles.SHARD, Corps.ORANGE), from.x, from.y, from.z, 25, 0.3, 0.3, 0.3, 0.1);
		level.playSound(null, victim.blockPosition(), SoundEvents.ITEM_PICKUP, SoundSource.PLAYERS, 1.0f, 0.7f);
		level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0f, 0.6f);
		return true;
	}

	// ---- Avarice: copies of slain mobs ------------------------------------------------------

	public static boolean summon(ServerLevel level, Player player) {
		if (!(player instanceof ServerPlayer owner)) return false;
		ItemStack ring = orangeRing(owner);
		List<Identifier> slain = ring.isEmpty() ? List.of() : ring.getOrDefault(SLAIN, List.of());
		if (slain.isEmpty()) {
			owner.sendOverlayMessage(Component.translatable("message.lanternring.avarice_empty").withStyle(ChatFormatting.GOLD));
			return false;
		}
		Team.of(level.getServer());
		Vec3 look = owner.getLookAngle().multiply(1, 0, 1).normalize();
		Vec3 side = new Vec3(-look.z, 0, look.x);
		List<Component> names = new ArrayList<>();
		int n = Math.min(SUMMON, slain.size());
		for (int i = 0; i < n; i++) {
			EntityType<?> type = BuiltInRegistries.ENTITY_TYPE.getValue(slain.get(i));
			if (!(type.create(level, EntitySpawnReason.MOB_SUMMONED) instanceof Mob mob)) continue;
			Vec3 at = owner.position().add(look.scale(2.5)).add(side.scale((i - (n - 1) / 2.0) * 2.2));
			BlockPos pos = BlockPos.containing(at);
			mob.snapTo(at.x, ground(level, pos), at.z, owner.getYRot(), 0f);
			mob.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), EntitySpawnReason.MOB_SUMMONED, null);
			enlist(level, owner, mob, RingTuning.AVARICE_LIFETIME.ticks());
			names.add(mob.getType().getDescription());
			Vec3 mid = mob.position().add(0, mob.getBbHeight() / 2, 0);
			RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(owner), mid);
			level.sendParticles(ModParticles.of(ModParticles.SHARD, Corps.ORANGE), mid.x, mid.y, mid.z, 40, mob.getBbWidth() / 2, mob.getBbHeight() / 2, mob.getBbWidth() / 2, 0.05);
		}
		if (names.isEmpty()) return false;
		trimCopies(owner);
		owner.sendOverlayMessage(Component.translatable("message.lanternring.avarice", ComponentUtils.formatList(names, Component.literal(", ")))
				.withStyle(ChatFormatting.GOLD));
		level.playSound(null, owner.blockPosition(), SoundEvents.EVOKER_PREPARE_SUMMON, SoundSource.PLAYERS, 1.0f, 0.8f);
		return true;
	}

	/**
	 * Adds a mob to the world fighting for {@code owner} for {@code lifetime} ticks: outlined in
	 * orange, a little tougher than the real thing, dropping nothing, and fading when its time is up
	 * or it dies. Also used by the Orange Lantern's Horde (see OrangeHorde).
	 */
	public static void enlist(ServerLevel level, ServerPlayer owner, Mob mob, int lifetime) {
		Team.of(level.getServer());
		mob.addTag(COPY_TAG);
		mob.setPersistenceRequired();
		mob.setGlowingTag(true);
		mob.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, -1, 0, false, false));
		// Copies are a little tougher and hit harder than the real thing.
		mob.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, -1, 0, false, false));
		mob.addEffect(new MobEffectInstance(MobEffects.STRENGTH, -1, 1, false, false));
		for (EquipmentSlot slot : EquipmentSlot.values()) mob.setDropChance(slot, 0f);
		// Known before it joins the world, or ENTITY_LOAD takes it for a leftover and removes it.
		COPIES.put(mob.getUUID(), new Copy(level, mob, owner, level.getGameTime() + lifetime));
		level.addFreshEntity(mob);
		level.getScoreboard().addPlayerToTeam(mob.getScoreboardName(), Team.of(level.getServer()));
	}

	/** True for a mob fighting for a bearer (an Avarice copy or one of the Horde). */
	public static boolean isCopy(Entity entity) {
		return COPIES.containsKey(entity.getUUID());
	}

	/** The top of the ground at or below pos (a few blocks down at most). */
	static double ground(ServerLevel level, BlockPos pos) {
		for (int i = 0; i < 8 && level.getBlockState(pos.below()).getCollisionShape(level, pos.below()).isEmpty(); i++) pos = pos.below();
		for (int i = 0; i < 8 && !level.getBlockState(pos).getCollisionShape(level, pos).isEmpty(); i++) pos = pos.above();
		return pos.getY();
	}

	/** Oldest copies fade once a bearer has more than MAX_COPIES. */
	private static void trimCopies(ServerPlayer owner) {
		List<Copy> mine = new ArrayList<>();
		for (Copy c : COPIES.values()) if (c.owner == owner && !c.mob.entityTags().contains(OrangeHorde.TAG)) mine.add(c);
		mine.sort((a, b) -> Long.compare(a.until, b.until));
		for (int i = 0; i < mine.size() - MAX_COPIES; i++) {
			COPIES.remove(mine.get(i).mob.getUUID());
			fade(mine.get(i));
		}
	}

	private static void fade(Copy copy) {
		Mob mob = copy.mob;
		Vec3 mid = mob.position().add(0, mob.getBbHeight() / 2, 0);
		copy.level.sendParticles(ModParticles.of(ModParticles.SHARD, Corps.ORANGE), mid.x, mid.y, mid.z, 30, mob.getBbWidth() / 2, mob.getBbHeight() / 2, mob.getBbWidth() / 2, 0.08);
		copy.level.playSound(null, mob.blockPosition(), SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.NEUTRAL, 1.0f, 0.8f);
		Scoreboard board = copy.level.getScoreboard();
		PlayerTeam team = board.getPlayersTeam(mob.getScoreboardName());
		if (team != null) board.removePlayerFromTeam(mob.getScoreboardName(), team);
		mob.discard();
	}

	private static void copyTick(Copy c, long now) {
		Mob mob = c.mob;
		ServerPlayer owner = c.owner;
		// Copies of undead don't burn by day (Fire Resistance stops the damage, this the flames).
		mob.clearFire();
		LivingEntity target = mob.getTarget();
		if (target != null && (!target.isAlive() || isFriend(owner, target))) target = null;
		if (target == null || now % 10 == 0) target = pickTarget(c);
		mob.setTarget(target);
		if (target != null) {
			if (!(mob instanceof Enemy) && mob instanceof PathfinderMob && now % 10 == 0) mob.getNavigation().moveTo(target, 1.4);
			// Every copy can hit, even ones that never fight (a cow headbutts for the bearer).
			if (now % 20 == 0 && mob.distanceTo(target) < 2.0 + mob.getBbWidth()) {
				float damage = mob.getAttributes().hasAttribute(Attributes.ATTACK_DAMAGE) ? (float) mob.getAttributeValue(Attributes.ATTACK_DAMAGE) : 0f;
				target.hurtServer(c.level, c.level.damageSources().mobAttack(mob), Math.max(5f, damage));
			}
		} else if (owner.level() == c.level) {
			double d = mob.distanceTo(owner);
			if (d > 24) mob.teleportTo(owner.getX(), owner.getY(), owner.getZ());
			else if (d > 5 && now % 10 == 0) mob.getNavigation().moveTo(owner, 1.2);
		}
		if (now % 4 == 0) {
			c.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.ORANGE), mob.getX(), mob.getY() + mob.getBbHeight() * 0.5, mob.getZ(),
					1, mob.getBbWidth() * 0.4, mob.getBbHeight() * 0.4, mob.getBbWidth() * 0.4, 0.01);
		}
	}

	/** What the bearer last hit, or what last hit them, or the nearest monster. */
	private static LivingEntity pickTarget(Copy c) {
		ServerPlayer owner = c.owner;
		for (LivingEntity e : new LivingEntity[] {owner.getLastHurtMob(), owner.getLastHurtByMob()}) {
			if (e != null && e.isAlive() && e.level() == c.level && !isFriend(owner, e) && e.distanceTo(c.mob) < 32) return e;
		}
		LivingEntity best = null;
		double bestD = 16 * 16;
		for (LivingEntity e : c.level.getEntitiesOfClass(LivingEntity.class, c.mob.getBoundingBox().inflate(16),
				e -> e instanceof Enemy && e.isAlive() && !isFriend(owner, e))) {
			double d = e.distanceToSqr(c.mob);
			if (d < bestD) {
				bestD = d;
				best = e;
			}
		}
		return best;
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Haul> it = HAULS.iterator(); it.hasNext(); ) {
			Haul h = it.next();
			if (h.owner.isRemoved() || h.owner.level() != h.level) {
				for (Entity e : h.loot) e.noPhysics = false;
				it.remove();
				continue;
			}
			haulTick(h);
			if (h.level.getGameTime() - h.start >= h.ticks) it.remove();
		}
		for (Iterator<Copy> it = COPIES.values().iterator(); it.hasNext(); ) {
			Copy c = it.next();
			long now = c.level.getGameTime();
			if (!c.mob.isAlive() || c.mob.isRemoved()) {
				it.remove();
			} else if (now >= c.until || c.owner.isRemoved()) {
				it.remove();
				fade(c);
			} else {
				copyTick(c, now);
			}
		}
	}

	/** The scoreboard team that outlines copies in orange. */
	private static final class Team {
		static PlayerTeam of(MinecraftServer server) {
			Scoreboard board = server.getScoreboard();
			PlayerTeam team = board.getPlayerTeam(TEAM);
			if (team == null) {
				team = board.addPlayerTeam(TEAM);
				team.setColor(java.util.Optional.of(net.minecraft.world.scores.TeamColor.GOLD));
				team.setAllowFriendlyFire(true);
			}
			return team;
		}
	}
}
