package com.sparky.lanternring;

import com.mojang.serialization.Codec;
import com.sparky.lanternring.corps.CorpsMobs;
import com.sparky.lanternring.corps.CorpsVillager;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * The Orange Lantern's power (J, 2026-10-13): with the lantern summoned, hold the lantern key and
 * the Horde crawls up out of the ground around you: polar bears, wardens, endermen, zombified
 * piglins, and the Blue Lantern villagers you have killed, back in orange. A mob a second for
 * {@link RingTuning#HORDE_TIME}, then a {@link RingTuning#HORDE_COOLDOWN} rest, about 40 a minute,
 * over and over while the lantern stays out. Hold the key again (or dismiss the lantern) to stop
 * it. Each fights for you like an Avarice copy and crumbles after {@link RingTuning#HORDE_LIFETIME}.
 */
public final class OrangeHorde {
	/** Tag on every Horde mob (so Avarice's own copy limit leaves them alone). */
	public static final String TAG = "lanternring.horde";
	/** Ticks between mobs while a wave runs. */
	private static final int EVERY = 20;
	/** Ticks a mob takes to crawl up out of the ground. */
	private static final int CRAWL = 30;
	private static final double NEAR = 3, FAR = 8;
	/** Every so many mobs, one of the Blue villagers you killed (if any). */
	private static final int VILLAGER_EVERY = 5;
	private static final EntityType<?>[] KINDS = {EntityTypes.POLAR_BEAR, EntityTypes.WARDEN, EntityTypes.ENDERMAN, EntityTypes.ZOMBIFIED_PIGLIN};

	/** How many Blue Lantern villagers this player has killed (they join the Horde). */
	public static final AttachmentType<Integer> FALLEN_BLUE = AttachmentRegistry.create(LanternRing.id("fallen_blue"),
			b -> b.persistent(Codec.INT).copyOnDeath());

	/** A running Horde: when its wave started (or its rest ends) and how many it has raised. */
	private static final class Run {
		final ServerPlayer owner;
		long waveStart;
		int raised;

		Run(ServerPlayer owner, long now) {
			this.owner = owner;
			this.waveStart = now;
		}
	}

	/** A mob still crawling up: where it ends and when it started. */
	private record Crawl(ServerLevel level, Mob mob, Vec3 top, long start, BlockState ground) {
	}

	private static final Map<UUID, Run> RUNS = new HashMap<>();
	private static final List<Crawl> CRAWLS = new ArrayList<>();

	private OrangeHorde() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(OrangeHorde::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			RUNS.clear();
			CRAWLS.clear();
		});
		// Nothing hurts a mob still in the ground (it would choke in the blocks it crawls through).
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			for (Crawl c : CRAWLS) if (c.mob == entity) return false;
			return true;
		});
		// Blue Lantern villagers killed by an orange bearer come back in the Horde.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(source.getEntity() instanceof ServerPlayer player) || !isBlueVillager(entity)) return;
			if (Corps.of(player.getMainHandItem()) != Corps.ORANGE && Corps.of(player.getOffhandItem()) != Corps.ORANGE) return;
			player.setAttached(FALLEN_BLUE, fallen(player) + 1);
		});
	}

	private static boolean isBlueVillager(net.minecraft.world.entity.LivingEntity entity) {
		if (entity instanceof CorpsVillager cv) return cv.corps() == Corps.BLUE;
		if (!(entity instanceof Villager)) return false;
		Hope.Mark mark = entity.getAttached(Hope.MARK);
		return mark != null && !mark.golem();
	}

	public static int fallen(ServerPlayer player) {
		Integer n = player.getAttached(FALLEN_BLUE);
		return n == null ? 0 : n;
	}

	public static boolean running(ServerPlayer player) {
		return RUNS.containsKey(player.getUUID());
	}

	/** Holding the lantern key with the orange lantern out: start the Horde, or call it off. */
	static void toggle(ServerPlayer player) {
		if (RUNS.remove(player.getUUID()) != null) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.horde_stop").withStyle(ChatFormatting.GOLD));
			return;
		}
		RUNS.put(player.getUUID(), new Run(player, player.level().getGameTime()));
		player.sendOverlayMessage(Component.translatable("message.lanternring.horde").withStyle(ChatFormatting.GOLD));
		player.level().playSound(null, player.blockPosition(), SoundEvents.WARDEN_EMERGE, SoundSource.PLAYERS, 0.8f, 1.2f);
	}

	/** The lantern was dismissed or taken back: the Horde stops raising more. */
	static void stop(ServerPlayer player) {
		RUNS.remove(player.getUUID());
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Run> it = RUNS.values().iterator(); it.hasNext(); ) {
			Run run = it.next();
			ServerPlayer owner = run.owner;
			if (owner.isRemoved() || !LanternSlot.out(owner) || Corps.ofLantern(LanternSlot.lantern(owner)) != Corps.ORANGE) {
				it.remove();
				continue;
			}
			ServerLevel level = (ServerLevel) owner.level();
			long t = level.getGameTime() - run.waveStart;
			int wave = Math.max(EVERY, RingTuning.HORDE_TIME.ticks());
			int rest = Math.max(1, RingTuning.HORDE_COOLDOWN.ticks());
			if (t >= wave + rest) {
				// Rested: the next wave.
				run.waveStart = level.getGameTime();
				t = 0;
				owner.sendOverlayMessage(Component.translatable("message.lanternring.horde").withStyle(ChatFormatting.GOLD));
			}
			if (t < wave && t % EVERY == 0) {
				raise(level, owner, run.raised++);
			} else if (t == wave) {
				owner.sendOverlayMessage(Component.translatable("message.lanternring.horde_rest", rest / 20).withStyle(ChatFormatting.GOLD));
			}
		}
		for (Iterator<Crawl> it = CRAWLS.iterator(); it.hasNext(); ) {
			Crawl c = it.next();
			if (crawlTick(c)) it.remove();
		}
	}

	/** One mob starts crawling up out of the ground somewhere around the bearer. */
	private static void raise(ServerLevel level, ServerPlayer owner, int n) {
		RandomSource r = level.getRandom();
		int villagers = fallen(owner);
		boolean villager = villagers > 0 && n % VILLAGER_EVERY == VILLAGER_EVERY - 1;
		EntityType<?> type = villager ? CorpsMobs.CORPS_VILLAGER : KINDS[r.nextInt(KINDS.length)];
		if (!(type.create(level, EntitySpawnReason.MOB_SUMMONED) instanceof Mob mob)) return;
		double angle = r.nextDouble() * Math.PI * 2, dist = NEAR + r.nextDouble() * (FAR - NEAR);
		Vec3 at = owner.position().add(Math.cos(angle) * dist, 0, Math.sin(angle) * dist);
		BlockPos pos = BlockPos.containing(at.x, owner.getY() + 1, at.z);
		double y = Avarice.ground(level, pos);
		Vec3 top = new Vec3(at.x, y, at.z);
		BlockState ground = level.getBlockState(BlockPos.containing(top).below());
		mob.snapTo(top.x, y - mob.getBbHeight(), top.z, r.nextFloat() * 360f, 0f);
		mob.finalizeSpawn(level, level.getCurrentDifficultyAt(pos), EntitySpawnReason.MOB_SUMMONED, null);
		if (mob instanceof CorpsVillager cv) cv.setCorps(Corps.ORANGE);
		mob.addTag(TAG);
		// Still in the ground: no AI and no collisions until it has crawled out.
		mob.setNoAi(true);
		mob.noPhysics = true;
		Avarice.enlist(level, owner, mob, Math.max(CRAWL + 20, RingTuning.HORDE_LIFETIME.ticks()) + CRAWL);
		CRAWLS.add(new Crawl(level, mob, top, level.getGameTime(), ground));
		level.playSound(null, BlockPos.containing(top), SoundEvents.ROOTED_DIRT_BREAK, SoundSource.HOSTILE, 1.2f, 0.6f);
	}

	/** Moves a crawling mob up a step; true once it's out (or gone). */
	private static boolean crawlTick(Crawl c) {
		Mob mob = c.mob;
		if (!mob.isAlive() || mob.isRemoved()) return true;
		float k = Math.min(1f, (c.level.getGameTime() - c.start) / (float) CRAWL);
		// Lurches up: quick at first, slowing as its feet come clear.
		float ease = 1f - (1f - k) * (1f - k);
		double y = c.top.y - mob.getBbHeight() * (1f - ease);
		mob.setPos(c.top.x, y, c.top.z);
		mob.setDeltaMovement(Vec3.ZERO);
		if (!c.ground.isAir()) {
			c.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, c.ground), c.top.x, c.top.y + 0.1, c.top.z,
					4, mob.getBbWidth() * 0.5, 0.05, mob.getBbWidth() * 0.5, 0.15);
		}
		if (c.level.getGameTime() % 3 == 0) {
			c.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.ORANGE), c.top.x, c.top.y + 0.2, c.top.z, 2,
					mob.getBbWidth() * 0.5, 0.1, mob.getBbWidth() * 0.5, 0.02);
		}
		if (k < 1f) return false;
		mob.setNoAi(false);
		mob.noPhysics = false;
		if (mob instanceof CorpsVillager cv) cv.suitUp(c.level);
		c.level.playSound(null, mob.blockPosition(), SoundEvents.ROOTED_DIRT_PLACE, SoundSource.HOSTILE, 1f, 0.8f);
		return true;
	}
}
