package com.sparky.lanternring.corps;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.ally.ModEntities;
import com.sparky.lanternring.designs.BlockPlan;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Hope sanctuary (J's A6 "Battery + cone" from the lead Blender chat, 2026-10-14, replacing the
 * A3 Lotus tiers: the lotus base with a tall hourglass Power Battery on top and an open flyer cone
 * round it): once a Blue
 * Lantern squad has its rescued safe under the dome, a floating sanctuary forms in the sky above
 * them, about 34 blocks over the dome, from the bottom of its underside up. It stays for good.
 * <p>
 * Its block plan is J's Blender take (data/lanternring/plans/hope_sanctuary.plan). The turbine at the
 * top isn't placed as blocks: it is a {@link HopeTurbine} that the client draws turning once every
 * 20 s, with the Hope mark through its hub. While it stands (J's 19 b+c) it lifts everyone round it:
 * players, villagers and animals within {@link #REACH} blocks (the dome below included) heal, and
 * Blue rings there slowly charge.
 */
public final class HopeSanctuary {
	public static final String PLAN = "hope_sanctuary";
	/** The plan's parts: the battery and cone are placed, the turbine and mark are drawn turning. */
	public static final String LOTUS = "A6_battery_cone";
	public static final List<String> TURBINE_PARTS = List.of("A6_turbine", "A6_turbine_mark");
	/** The turbine's blocks start this high in the plan; its entity stands there on the axis. */
	public static final int TURBINE_Y = 22;
	/** How far above the dome's centre the sanctuary's floor floats (J: about 34 in the renders). */
	static final int ABOVE = 34;
	/** No second sanctuary this close to one. */
	private static final double APART = 160;
	/** Blocks set per tick while it forms (16,298 in all: about 14 s). */
	private static final int PER_TICK = 60;
	/** How far round it the healing and charging reach, across and down. */
	public static final double REACH = 32;
	private static final double BELOW = 56, OVER = 40;
	/** Every so often: Regeneration for this long, and this much ring charge (a full ring in about 7 minutes). */
	private static final int PULSE = 40, REGEN = 80, CHARGE = 10;
	private static final int FLAGS = Block.UPDATE_CLIENTS;

	private HopeSanctuary() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(HopeSanctuary::tick);
	}

	/**
	 * A dome has just formed over the rescued at {@code dome}: if there's no sanctuary near, one starts
	 * forming above it. Returns true if it did.
	 */
	public static boolean request(ServerLevel level, BlockPos dome) {
		Data data = Data.get(level);
		for (Site s : data.sites) {
			if (horizontal(s.anchor, dome) < APART) return false;
		}
		int top = level.getMaxY() - 40;
		BlockPos anchor = new BlockPos(dome.getX(), Math.min(dome.getY() + ABOVE, top), dome.getZ());
		data.sites.add(new Site(anchor, 0, false));
		data.setDirty();
		level.playSound(null, anchor, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 4f, 0.8f);
		return true;
	}

	/** Every sanctuary in this level. */
	public static List<Site> sites(ServerLevel level) {
		return Collections.unmodifiableList(Data.get(level).sites);
	}

	private static void tick(MinecraftServer server) {
		for (ServerLevel level : server.getAllLevels()) {
			Data data = Data.get(level);
			if (data.sites.isEmpty()) continue;
			long now = level.getGameTime();
			for (Site s : data.sites) {
				if (!level.isLoaded(s.anchor)) continue;
				if (!s.built()) {
					build(level, s);
					data.setDirty();
				} else if (!s.turbine) {
					spawnTurbine(level, s);
					data.setDirty();
				} else if (now % PULSE == 0) {
					bless(level, s);
				}
			}
		}
	}

	/** Sets the next blocks of the lotus, bottom layer first, each with a little blue light. */
	private static void build(ServerLevel level, Site s) {
		List<BlockPlan.Entry> blocks = BlockPlan.get(PLAN).part(LOTUS).blocks();
		int end = Math.min(blocks.size(), s.placed + PER_TICK);
		for (int i = s.placed; i < end; i++) {
			BlockPlan.Entry e = blocks.get(i);
			BlockPos p = s.anchor.offset(e.x(), e.y(), e.z());
			BlockState there = level.getBlockState(p);
			// It forms in open sky: never over terrain or anything built.
			if (!there.isAir() && !there.canBeReplaced()) continue;
			level.setBlock(p, e.state(), FLAGS);
			if (i % 24 == 0) {
				level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5,
						2, 0.4, 0.4, 0.4, 0.02);
			}
		}
		s.placed = end;
		if (s.built()) level.playSound(null, s.anchor, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 4f, 0.6f);
	}

	private static void spawnTurbine(ServerLevel level, Site s) {
		HopeTurbine turbine = ModEntities.HOPE_TURBINE.create(level, EntitySpawnReason.STRUCTURE);
		if (turbine == null) return;
		turbine.setPos(s.anchor.getX(), s.anchor.getY() + TURBINE_Y, s.anchor.getZ());
		level.addFreshEntity(turbine);
		s.turbine = true;
		level.playSound(null, s.anchor.above(TURBINE_Y), SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 4f, 0.7f);
	}

	/** The mark's light: everyone round it heals, and Blue rings charge. */
	private static void bless(ServerLevel level, Site s) {
		Vec3 c = Vec3.atBottomCenterOf(s.anchor);
		AABB area = new AABB(c.x - REACH, c.y - BELOW, c.z - REACH, c.x + REACH, c.y + OVER, c.z + REACH);
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, area, HopeSanctuary::blessed)) {
			if (e.getHealth() < e.getMaxHealth() && !e.hasEffect(MobEffects.REGENERATION)) {
				e.addEffect(new MobEffectInstance(MobEffects.REGENERATION, REGEN, 0, true, true));
			}
			if (e instanceof Player p) {
				for (ItemStack stack : p.getInventory()) {
					if (stack.is(ModRegistry.POWER_RING) && Corps.of(stack) == Corps.BLUE
							&& PowerRingItem.getCharge(stack) < PowerRingItem.MAX_CHARGE) {
						PowerRingItem.setCharge(stack, PowerRingItem.getCharge(stack) + CHARGE);
					}
				}
			}
		}
		// The mark breathes out a little light.
		Vec3 hub = c.add(0, TURBINE_Y + 6, 0);
		level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), hub.x, hub.y, hub.z, 6, 3, 3, 3, 0.02);
	}

	private static boolean blessed(LivingEntity e) {
		return e.isAlive() && (e instanceof Player || e instanceof AbstractVillager || e instanceof Animal);
	}

	private static double horizontal(BlockPos a, BlockPos b) {
		double dx = a.getX() - b.getX(), dz = a.getZ() - b.getZ();
		return Math.sqrt(dx * dx + dz * dz);
	}

	// ---- saved -------------------------------------------------------------------------------

	/** One sanctuary: its centre (the floor's middle), how many lotus blocks have set, and whether its turbine is up. */
	public static final class Site {
		final BlockPos anchor;
		int placed;
		boolean turbine;

		Site(BlockPos anchor, int placed, boolean turbine) {
			this.anchor = anchor;
			this.placed = placed;
			this.turbine = turbine;
		}

		public BlockPos anchor() {
			return anchor;
		}

		public boolean built() {
			return placed >= BlockPlan.get(PLAN).part(LOTUS).blocks().size();
		}

		public boolean standing() {
			return built() && turbine;
		}

		private static final Codec<Site> CODEC = RecordCodecBuilder.create(i -> i.group(
				BlockPos.CODEC.fieldOf("anchor").forGetter(s -> s.anchor),
				Codec.INT.optionalFieldOf("placed", 0).forGetter(s -> s.placed),
				Codec.BOOL.optionalFieldOf("turbine", false).forGetter(s -> s.turbine)
		).apply(i, Site::new));
	}

	static final class Data extends SavedData {
		final List<Site> sites = new ArrayList<>();

		private static final Codec<Data> CODEC = RecordCodecBuilder.create(i -> i.group(
				Site.CODEC.listOf().optionalFieldOf("sites", List.of()).forGetter(d -> d.sites)
		).apply(i, sites -> {
			Data d = new Data();
			d.sites.addAll(sites);
			return d;
		}));

		static final SavedDataType<Data> TYPE = new SavedDataType<>(LanternRing.id("hope_sanctuaries"), Data::new, CODEC,
				DataFixTypes.SAVED_DATA_COMMAND_STORAGE);

		static Data get(ServerLevel level) {
			return level.getDataStorage().computeIfAbsent(TYPE);
		}
	}
}
