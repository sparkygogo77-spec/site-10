package com.sparky.lanternring.corps;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Brightness;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Red Lantern sanctuary (J, 2026-10-12, design S1 "Rage Spire" with F1 "drips off"): a level 4
 * red Deluge doesn't flood, it raises a floating outpost. A big blood orb forms high over the spot,
 * falls onto the spire's first block (the tip of its lantern tower), and the spire then forms from
 * the top down. Each block first appears as blood ({@link #BLOOD_COAT}) and sets into what it's meant
 * to be a few seconds later, so a band of blood rolls down the spire, dripping off it as it goes,
 * and is gone by the time the point at the bottom forms. Then the angriest mobs move in, each with
 * a red ring: sky raiders (pillagers), a warden, rage cats and a red golem. They attack anyone
 * who isn't holding a red ring. Breaking the red lantern on the plaza dissolves the whole spire
 * back into blood.
 * <p>
 * Sanctuaries are saved per dimension ({@link Data}); the plan is rebuilt from the anchor, so only
 * the anchor, the stage and how far the build has got are stored.
 */
public final class RedSanctuary {
	private static final int FLAGS = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;
	/** Every resident carries this tag, so they leave each other (and red ring bearers) alone. */
	public static final String TAG = "lanternring.sanctuary";

	// ---- blocks ---------------------------------------------------------------------------------

	/** The spire's permanent red hard light: its ribs, post tips, lantern glass and cage cores. */
	public static final Block RAGE_LIGHT = block("rage_light", TransparentBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.COLOR_RED)
			.strength(0.6f)
			.noLootTable()
			.lightLevel(state -> 12)
			.sound(SoundType.GLASS)
			.noOcclusion()
			.isValidSpawn(Blocks::never)
			.isRedstoneConductor(Blocks::never)
			.isSuffocating(Blocks::never)
			.isViewBlocking((state, level, pos, box) -> false));
	/** Blood a block forms as before it sets. Short-lived: one left behind dries up on its next random tick. */
	public static final Block BLOOD_COAT = block("blood_coat", BloodCoatBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.CRIMSON_NYLIUM)
			.strength(0.4f)
			.noLootTable()
			.randomTicks()
			.lightLevel(state -> 5)
			.sound(SoundType.HONEY_BLOCK)
			.isValidSpawn(Blocks::never)
			.pushReaction(PushReaction.IMMOVEABLE));

	private static Block block(String name, java.util.function.Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties props) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(props.setId(key)));
	}

	public static class BloodCoatBlock extends Block {
		public BloodCoatBlock(Properties properties) {
			super(properties);
		}

		@Override
		protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
			if (!pending(level, pos)) level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
		}
	}

	// ---- the Rage Spire -------------------------------------------------------------------------

	/** The plaza's radius, and the heights (above the bottom point) of the plaza and the crown. */
	public static final int R = 12, PLAZA = 22, CROWN = PLAZA + 16;
	/** How far above the aimed-at ground the bottom point floats. */
	public static final int FLOAT = 4;
	/** How many layers the blood runs down ahead of the blocks forming under it. */
	static final int BLOOD_LEAD = 10;
	/** The blood orb's radius, and how far above the crown it forms. */
	static final int ORB = 7, ORB_HEIGHT = 12;

	private static final BlockState RED = Blocks.CONCRETE.red().defaultBlockState();
	private static final BlockState BLACK = Blocks.CONCRETE.black().defaultBlockState();
	private static final BlockState STONE = Blocks.POLISHED_BLACKSTONE.defaultBlockState();
	private static final BlockState FLOOR = Blocks.POLISHED_BLACKSTONE_BRICKS.defaultBlockState();
	private static final BlockState WART = Blocks.NETHER_WART_BLOCK.defaultBlockState();
	private static final BlockState GLASS = Blocks.STAINED_GLASS.red().defaultBlockState();

	/** The core: the red lantern on the plaza, in front of the tower. */
	public static BlockPos core(BlockPos anchor) {
		return anchor.offset(0, PLAZA + 2, 8);
	}

	/** Where the residents stand: the middle of the plaza floor's top. */
	public static BlockPos plaza(BlockPos anchor) {
		return anchor.above(PLAZA + 2);
	}

	/** Every block of the spire, keyed by position. {@code anchor} is the bottom point. */
	public static Map<BlockPos, BlockState> plan(BlockPos anchor) {
		Map<BlockPos, BlockState> m = new LinkedHashMap<>();
		BlockState light = RAGE_LIGHT.defaultBlockState();
		// The cone under the plaza, narrowing to one point, with eight glowing ribs.
		for (int y = 0; y < PLAZA; y++) {
			double r = R * Math.pow((y + 1) / (double) PLAZA, 0.85);
			for (int x = -R; x <= R; x++) {
				for (int z = -R; z <= R; z++) {
					double d = Math.sqrt(x * x + z * z);
					if (d > r) continue;
					boolean edge = d > r - 1.3;
					boolean rib = edge && (Math.abs(x) < 0.6 || Math.abs(z) < 0.6 || Math.abs(Math.abs(x) - Math.abs(z)) < 0.8);
					m.put(anchor.offset(x, y, z), rib ? light : y % 7 == 3 ? BLACK : RED);
				}
			}
		}
		m.put(anchor.below(), light);
		m.put(anchor.below(3), light);
		// The plaza: a black floor with blood-red rings and a red rim.
		for (int x = -R - 1; x <= R + 1; x++) {
			for (int z = -R - 1; z <= R + 1; z++) {
				double d = Math.sqrt(x * x + z * z);
				if (d > R + 0.6) continue;
				boolean rim = d > R - 1;
				m.put(anchor.offset(x, PLAZA, z), rim ? RED : STONE);
				m.put(anchor.offset(x, PLAZA + 1, z), rim ? RED : Math.round(d) % 4 == 0 && d > 1 ? WART : FLOOR);
			}
		}
		// Twelve ember posts round the rim.
		for (int i = 0; i < 12; i++) {
			double a = i / 12.0 * Math.PI * 2;
			int x = (int) Math.round(Math.cos(a) * (R - 0.5)), z = (int) Math.round(Math.sin(a) * (R - 0.5));
			for (int y = PLAZA + 2; y < PLAZA + 5; y++) m.put(anchor.offset(x, y, z), STONE);
			m.put(anchor.offset(x, PLAZA + 5, z), light);
		}
		// The Red Lantern tower in the middle.
		cylinder(m, anchor, 5, PLAZA + 2, PLAZA + 2, (x, y, z, d) -> STONE);
		cylinder(m, anchor, 4, PLAZA + 3, PLAZA + 3, (x, y, z, d) -> RED);
		cylinder(m, anchor, 3, PLAZA + 4, PLAZA + 11, (x, y, z, d) -> {
			boolean bar = x == 0 || z == 0;
			return d > 2.2 && !bar && y > PLAZA + 4 && y < PLAZA + 11 ? light : STONE;
		});
		cylinder(m, anchor, 4, PLAZA + 12, PLAZA + 12, (x, y, z, d) -> RED);
		cylinder(m, anchor, 2, PLAZA + 13, PLAZA + 14, (x, y, z, d) -> STONE);
		m.put(anchor.above(PLAZA + 15), RED);
		m.put(anchor.above(CROWN), light);
		// Four cages hung on chains from under the rim.
		for (int i = 0; i < 4; i++) {
			double a = (i + 0.5) / 4 * Math.PI * 2;
			int cx = (int) Math.round(Math.cos(a) * R), cz = (int) Math.round(Math.sin(a) * R);
			for (int y = PLAZA - 6; y < PLAZA; y++) m.put(anchor.offset(cx, y, cz), Blocks.IRON_CHAIN.defaultBlockState());
			for (int x = -1; x <= 1; x++) {
				for (int y = PLAZA - 11; y <= PLAZA - 7; y++) {
					for (int z = -1; z <= 1; z++) {
						boolean middle = x == 0 && z == 0 && y > PLAZA - 11 && y < PLAZA - 7;
						boolean face = (x == 0 || z == 0) && y > PLAZA - 11 && y < PLAZA - 7;
						m.put(anchor.offset(cx + x, y, cz + z), middle ? light : face ? GLASS : STONE);
					}
				}
			}
		}
		// The core lantern on its pedestal.
		m.put(core(anchor).below(), STONE);
		m.put(core(anchor), ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, Corps.RED));
		return m;
	}

	private interface Slice {
		BlockState at(int x, int y, int z, double d);
	}

	private static void cylinder(Map<BlockPos, BlockState> m, BlockPos anchor, int r, int y0, int y1, Slice slice) {
		for (int y = y0; y <= y1; y++) {
			for (int x = -r - 1; x <= r + 1; x++) {
				for (int z = -r - 1; z <= r + 1; z++) {
					double d = Math.sqrt(x * x + z * z);
					if (d <= r + 0.35) m.put(anchor.offset(x, y, z), slice.at(x, y, z, d));
				}
			}
		}
	}

	// ---- saved state ----------------------------------------------------------------------------

	enum Stage { ORB, BUILD, STANDING, DISSOLVE }

	/** One sanctuary: where it is, what it's doing, and the last layer (from the top) that has formed. */
	public static final class Site {
		final BlockPos anchor;
		Stage stage;
		int layer;
		boolean peopled;

		Site(BlockPos anchor, Stage stage, int layer, boolean peopled) {
			this.anchor = anchor;
			this.stage = stage;
			this.layer = layer;
			this.peopled = peopled;
		}

		public BlockPos anchor() {
			return anchor;
		}

		public boolean standing() {
			return stage == Stage.STANDING;
		}

		private static final Codec<Site> CODEC = RecordCodecBuilder.create(i -> i.group(
				BlockPos.CODEC.fieldOf("anchor").forGetter(s -> s.anchor),
				Codec.INT.optionalFieldOf("stage", 1).forGetter(s -> s.stage.ordinal()),
				Codec.INT.optionalFieldOf("layer", 0).forGetter(s -> s.layer),
				Codec.BOOL.optionalFieldOf("peopled", false).forGetter(s -> s.peopled)
		).apply(i, (anchor, stage, layer, peopled) -> new Site(anchor,
				// An orb isn't saved: one that was forming picks up at the build.
				Stage.values()[Math.max(1, Math.min(stage, Stage.values().length - 1))], layer, peopled)));
	}

	public static final class Data extends SavedData {
		final List<Site> sites = new ArrayList<>();

		private static final Codec<Data> CODEC = RecordCodecBuilder.create(i -> i.group(
				Site.CODEC.listOf().optionalFieldOf("sites", List.of()).forGetter(d -> d.sites)
		).apply(i, sites -> {
			Data d = new Data();
			d.sites.addAll(sites);
			return d;
		}));

		static final SavedDataType<Data> TYPE = new SavedDataType<>(LanternRing.id("red_sanctuaries"), Data::new, CODEC,
				DataFixTypes.SAVED_DATA_COMMAND_STORAGE);

		public static Data get(ServerLevel level) {
			return level.getDataStorage().computeIfAbsent(TYPE);
		}

		public List<Site> all() {
			return java.util.Collections.unmodifiableList(sites);
		}
	}

	// ---- what's happening now (not saved) -------------------------------------------------------

	private record Pending(BlockPos pos, BlockState want, long due) {
	}

	/** A site's plan and the blocks waiting to set, while it builds or dissolves. */
	private static final class Work {
		final ServerLevel level;
		final Site site;
		final Map<BlockPos, BlockState> plan;
		/** The plan's positions in layers, top first. */
		final List<List<BlockPos>> layers = new ArrayList<>();
		final Deque<Pending> pending = new ArrayDeque<>();
		/** Blood already running down over blocks that haven't started forming yet, and the next layer it reaches. */
		final Set<BlockPos> wet = new HashSet<>();
		int wetTo;
		final List<Display.BlockDisplay> orb = new ArrayList<>();
		final List<int[]> orbOffsets = new ArrayList<>();
		int orbRadius = -1;
		/** The orb's centre. It forms out of the ring, in the air in front of whoever let the Deluge go. */
		double orbX, orbY, orbZ;
		Vec3 orbFrom;
		long started, nextLayer;
		boolean resumed;

		Work(ServerLevel level, Site site) {
			this.level = level;
			this.site = site;
			this.plan = plan(site.anchor);
			Map<Integer, List<BlockPos>> byY = new HashMap<>();
			for (BlockPos p : plan.keySet()) byY.computeIfAbsent(p.getY(), y -> new ArrayList<>()).add(p);
			byY.keySet().stream().sorted(java.util.Comparator.reverseOrder()).forEach(y -> layers.add(byY.get(y)));
			this.started = level.getGameTime();
			BlockPos c = site.anchor.above(CROWN);
			this.orbX = c.getX() + 0.5;
			this.orbY = c.getY() + ORB + ORB_HEIGHT;
			this.orbZ = c.getZ() + 0.5;
			this.orbFrom = new Vec3(orbX, orbY, orbZ);
		}

		BlockPos crown() {
			return site.anchor.above(CROWN);
		}
	}

	private static final List<Work> WORK = new ArrayList<>();

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(RedSanctuary::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			// Set whatever is still blood, so nothing is left half-formed.
			for (Work w : WORK) {
				for (Pending p : w.pending) {
					if (w.level.getBlockState(p.pos).is(BLOOD_COAT)) w.level.setBlock(p.pos, p.want, FLAGS);
				}
				for (BlockPos p : w.wet) {
					if (w.level.getBlockState(p).is(BLOOD_COAT)) w.level.setBlock(p, w.plan.get(p), FLAGS);
				}
				clearOrb(w);
			}
			WORK.clear();
		});
	}

	/** Whether a blood coat block at {@code pos} is still waiting to set. */
	static boolean pending(ServerLevel level, BlockPos pos) {
		for (Work w : WORK) {
			if (w.level != level) continue;
			if (w.wet.contains(pos)) return true;
			for (Pending p : w.pending) {
				if (p.pos.equals(pos)) return true;
			}
		}
		return false;
	}

	// ---- raising one ----------------------------------------------------------------------------

	/**
	 * A level 4 red Deluge let go over {@code mark}: starts the orb, or says why it can't (no room
	 * under the sky, or too much in the way). Returns whether it started.
	 */
	public static boolean raise(ServerLevel level, ServerPlayer player, BlockPos mark) {
		BlockPos anchor = mark.above(FLOAT);
		int roof = level.getMaxY() - ORB * 2 - ORB_HEIGHT - 2;
		if (anchor.getY() + CROWN > roof) anchor = anchor.atY(roof - CROWN);
		if (anchor.getY() < mark.getY() + 2) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.sanctuary_no_sky").withStyle(ChatFormatting.RED));
			return false;
		}
		Map<BlockPos, BlockState> plan = plan(anchor);
		int blocked = 0;
		for (BlockPos p : plan.keySet()) {
			if (!fillable(level.getBlockState(p))) blocked++;
		}
		if (blocked > plan.size() / 20) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.sanctuary_blocked").withStyle(ChatFormatting.RED));
			return false;
		}
		Data data = Data.get(level);
		for (Site s : data.sites) {
			if (s.anchor.distSqr(anchor) < 48 * 48) {
				player.sendOverlayMessage(Component.translatable("message.lanternring.sanctuary_too_close").withStyle(ChatFormatting.RED));
				return false;
			}
		}
		Site site = new Site(anchor, Stage.ORB, 0, false);
		data.sites.add(site);
		data.setDirty();
		Work w = new Work(level, site);
		// The orb forms out of the ring: in the air ahead of the player, high enough to be seen whole.
		Vec3 look = player.getLookAngle().multiply(1, 0, 1);
		look = look.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : look.normalize();
		w.orbFrom = player.getEyePosition().add(look.scale(ORB + 4)).add(0, ORB, 0);
		w.orbX = w.orbFrom.x;
		w.orbY = w.orbFrom.y;
		w.orbZ = w.orbFrom.z;
		WORK.add(w);
		level.playSound(null, w.crown(), SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 4f, 0.6f);
		level.playSound(null, w.crown(), SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.PLAYERS, 3f, 0.6f);
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(Vec3.atCenterOf(anchor)) < 160 * 160) {
				p.sendSystemMessage(Component.translatable("message.lanternring.sanctuary_rises").withStyle(ChatFormatting.DARK_RED, ChatFormatting.ITALIC));
			}
		}
		return true;
	}

	/** Air, plants, snow and liquids give way to the spire; anything solid stays. */
	private static boolean fillable(BlockState s) {
		return s.isAir() || s.canBeReplaced() || s.is(BLOOD_COAT) || s.getBlock() instanceof net.minecraft.world.level.block.LiquidBlock;
	}

	// ---- every tick -----------------------------------------------------------------------------

	private static void tick(MinecraftServer server) {
		for (ServerLevel level : server.getAllLevels()) {
			Data data = Data.get(level);
			for (Iterator<Site> it = data.sites.iterator(); it.hasNext(); ) {
				Site site = it.next();
				if (!level.isLoaded(site.anchor) || !level.isLoaded(site.anchor.above(PLAZA))) continue;
				Work w = work(level, site);
				if (site.stage == Stage.STANDING) {
					if (w != null) finish(w);
					if (!site.peopled) {
						people(level, site);
						site.peopled = true;
						data.setDirty();
					}
					if (level.getGameTime() % 40 == 0 && !level.getBlockState(core(site.anchor)).is(ModRegistry.POWER_BATTERY)) {
						site.stage = Stage.DISSOLVE;
						site.layer = 0;
						data.setDirty();
						level.playSound(null, core(site.anchor), SoundEvents.WARDEN_DEATH, SoundSource.HOSTILE, 4f, 0.5f);
						// Its residents go with it, back into blood.
						BlockPos plaza = plaza(site.anchor);
						for (Mob mob : level.getEntitiesOfClass(Mob.class, new net.minecraft.world.phys.AABB(plaza).inflate(48),
								m -> m.entityTags().contains(TAG))) {
							level.sendParticles(BLOOD, mob.getX(), mob.getY() + mob.getBbHeight() / 2, mob.getZ(), 40,
									mob.getBbWidth() / 2, mob.getBbHeight() / 2, mob.getBbWidth() / 2, 0.1);
							mob.discard();
						}
						for (ServerPlayer p : level.players()) {
							if (p.distanceToSqr(Vec3.atCenterOf(site.anchor)) < 160 * 160) {
								p.sendSystemMessage(Component.translatable("message.lanternring.sanctuary_falls").withStyle(ChatFormatting.DARK_RED, ChatFormatting.ITALIC));
							}
						}
					}
					continue;
				}
				if (w == null) {
					w = new Work(level, site);
					w.resumed = true;
					WORK.add(w);
				}
				if (step(w, data)) {
					finish(w);
					it.remove();
					data.setDirty();
				}
			}
		}
	}

	@Nullable
	private static Work work(ServerLevel level, Site site) {
		for (Work w : WORK) {
			if (w.level == level && w.site == site) return w;
		}
		return null;
	}

	private static void finish(Work w) {
		clearOrb(w);
		for (Pending p : w.pending) {
			if (w.level.getBlockState(p.pos).is(BLOOD_COAT)) w.level.setBlock(p.pos, p.want, FLAGS);
		}
		w.pending.clear();
		WORK.remove(w);
	}

	/** One tick of an orb, build or dissolve. Returns true once a dissolve is over (the site is gone). */
	private static boolean step(Work w, Data data) {
		ServerLevel level = w.level;
		Site site = w.site;
		long now = level.getGameTime();
		setDue(w, now);
		int orbTicks = RingTuning.SANCTUARY_ORB.ticks();
		switch (site.stage) {
			case ORB -> {
				long t = now - w.started;
				Vec3 land = Vec3.atBottomCenterOf(w.crown()).add(0, ORB, 0);
				int r = (int) Math.max(1, Math.min(ORB, Math.round(ORB * Math.min(1.0, t / (orbTicks * 0.6)))));
				if (t < orbTicks * 0.6) {
					// Swelling out of the ring.
					w.orbX = w.orbFrom.x;
					w.orbY = w.orbFrom.y;
					w.orbZ = w.orbFrom.z;
					if (t % 3 == 0) level.sendParticles(BLOOD, w.orbX, w.orbY, w.orbZ, 12, r * 0.6, r * 0.6, r * 0.6, 0.1);
				} else {
					// Then it drops onto the crown: across in a straight line, down faster and faster.
					double k = Math.min(1.0, (t - orbTicks * 0.6) / (orbTicks * 0.4));
					w.orbX = Mth.lerp(k, w.orbFrom.x, land.x);
					w.orbZ = Mth.lerp(k, w.orbFrom.z, land.z);
					w.orbY = Mth.lerp(k * k, w.orbFrom.y, land.y);
				}
				// The first block forms just before the orb lands on it.
				if (t == (long) (orbTicks * 0.6)) place(w, w.crown(), false, now);
				showOrb(w, r);
				if (t % 10 == 0) level.playSound(null, w.crown().above(ORB_HEIGHT), SoundEvents.WARDEN_HEARTBEAT, SoundSource.HOSTILE, 3f, 0.6f);
				if (t >= orbTicks) {
					level.playSound(null, w.crown(), SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 4f, 0.5f);
					level.playSound(null, w.crown(), SoundEvents.HONEY_BLOCK_BREAK, SoundSource.HOSTILE, 4f, 0.5f);
					level.sendParticles(BLOOD, w.crown().getX() + 0.5, w.crown().getY() + 1, w.crown().getZ() + 0.5, 120, 3, 1, 3, 0.4);
					site.stage = Stage.BUILD;
					site.layer = 0;
					w.nextLayer = now;
					data.setDirty();
				}
			}
			case BUILD -> {
				if (w.resumed) {
					// After a restart: everything above the saved layer is finished.
					for (int i = 0; i < Math.min(site.layer, w.layers.size()); i++) {
						for (BlockPos p : w.layers.get(i)) {
							if (fillable(level.getBlockState(p))) level.setBlock(p, w.plan.get(p), FLAGS);
						}
					}
					w.resumed = false;
					w.wetTo = site.layer;
				}
				int perLayer = Math.max(1, RingTuning.SANCTUARY_BUILD.ticks() / Math.max(1, w.layers.size()));
				// The blood runs down first, BLOOD_LEAD layers ahead, and the spire forms underneath it.
				while (w.wetTo < Math.min(w.layers.size(), site.layer + BLOOD_LEAD)) {
					for (BlockPos p : w.layers.get(w.wetTo)) {
						if (open(w, p) && fillable(level.getBlockState(p)) && !level.getBlockState(p).is(BLOOD_COAT)) {
							level.setBlock(p, BLOOD_COAT.defaultBlockState(), FLAGS);
							w.wet.add(p);
						}
					}
					w.wetTo++;
				}
				if (now >= w.nextLayer && site.layer < w.layers.size()) {
					for (BlockPos p : w.layers.get(site.layer)) place(w, p, false, now);
					site.layer++;
					w.nextLayer = now + perLayer;
					data.setDirty();
					if (site.layer % 3 == 0) level.playSound(null, w.layers.get(site.layer - 1).getFirst(), SoundEvents.HONEY_BLOCK_PLACE, SoundSource.BLOCKS, 2f, 0.6f);
				}
				// The orb drains into the spire as it builds.
				double done = site.layer / (double) w.layers.size();
				showOrb(w, (int) Math.round(ORB * Math.pow(1 - done, 0.7)));
				drips(w);
				if (site.layer >= w.layers.size() && w.pending.isEmpty()) {
					site.stage = Stage.STANDING;
					data.setDirty();
					level.playSound(null, core(site.anchor), SoundEvents.WARDEN_ROAR, SoundSource.HOSTILE, 4f, 0.7f);
				}
			}
			case DISSOLVE -> {
				clearOrb(w);
				int perLayer = Math.max(1, RingTuning.SANCTUARY_BUILD.ticks() / 2 / Math.max(1, w.layers.size()));
				if (now >= w.nextLayer && site.layer < w.layers.size()) {
					for (BlockPos p : w.layers.get(site.layer)) {
						BlockState planned = w.plan.get(p);
						if (level.getBlockState(p).is(planned.getBlock())) place(w, p, true, now);
					}
					site.layer++;
					w.nextLayer = now + perLayer;
					data.setDirty();
				}
				drips(w);
				return site.layer >= w.layers.size() && w.pending.isEmpty();
			}
			default -> {
			}
		}
		return false;
	}

	/**
	 * Forms one block as blood. Blocks with nothing open beside them skip the blood and form at once
	 * (nobody would see it). When {@code away}, it's the dissolve: the blood drains to air.
	 */
	private static void place(Work w, BlockPos p, boolean away, long now) {
		BlockState want = away ? Blocks.AIR.defaultBlockState() : w.plan.get(p);
		w.wet.remove(p);
		if (!away && !fillable(w.level.getBlockState(p))) return;
		if (!open(w, p)) {
			w.level.setBlock(p, want, FLAGS);
			return;
		}
		w.level.setBlock(p, BLOOD_COAT.defaultBlockState(), FLAGS);
		w.pending.add(new Pending(p, want, now + RingTuning.SANCTUARY_BLOOD.ticks()));
	}

	/** Whether any side of {@code p} faces out of the spire (so someone could see it). */
	private static boolean open(Work w, BlockPos p) {
		for (Direction d : Direction.values()) {
			if (!w.plan.containsKey(p.relative(d))) return true;
		}
		return false;
	}

	/** Blood that has waited long enough sets into its block (or drains away). */
	private static void setDue(Work w, long now) {
		while (!w.pending.isEmpty() && w.pending.peekFirst().due <= now) {
			Pending p = w.pending.pollFirst();
			if (!w.level.getBlockState(p.pos).is(BLOOD_COAT)) continue;
			w.level.setBlock(p.pos, p.want, FLAGS);
			if (w.level.getRandom().nextInt(6) == 0) {
				w.level.sendParticles(BLOOD, p.pos.getX() + 0.5, p.pos.getY() + 0.5, p.pos.getZ() + 0.5, 3, 0.4, 0.4, 0.4, 0.05);
			}
		}
	}

	static final DustParticleOptions BLOOD = new DustParticleOptions(0xA00A12, 1.2f);

	/** Blood runs off the lowest open blocks in the band and drips away like red rain. */
	private static void drips(Work w) {
		List<BlockPos> all = new ArrayList<>(w.wet);
		for (Pending p : w.pending) all.add(p.pos);
		if (all.isEmpty()) return;
		RandomSource random = w.level.getRandom();
		for (int i = 0; i < 8; i++) {
			BlockPos p = all.get(random.nextInt(all.size()));
			if (!w.level.getBlockState(p.below()).isAir()) continue;
			// Count 0: the offsets are the drop's velocity.
			for (int k = 0; k < 3; k++) {
				w.level.sendParticles(BLOOD, p.getX() + random.nextDouble(), p.getY() - 0.05, p.getZ() + random.nextDouble(),
						0, 0, -1, 0, 1.0);
			}
			w.level.sendParticles(ParticleTypes.DRIPPING_LAVA, p.getX() + random.nextDouble(), p.getY() - 0.05, p.getZ() + random.nextDouble(), 1, 0, 0, 0, 0);
			w.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.RED), p.getX() + 0.5, p.getY(), p.getZ() + 0.5,
					1, 0.3, 0.1, 0.3, 0.01);
		}
	}

	// ---- the orb ----------------------------------------------------------------------------------

	/** Shows the orb at radius {@code r} (0 removes it), centred at {@code w.orbX, orbY, orbZ}. */
	private static void showOrb(Work w, int r) {
		if (r <= 0) {
			clearOrb(w);
			return;
		}
		double cx = w.orbX - 0.5, cy = w.orbY, cz = w.orbZ - 0.5;
		if (r != w.orbRadius) {
			clearOrb(w);
			w.orbRadius = r;
			BlockState blood = BLOOD_COAT.defaultBlockState();
			for (int dx = -r; dx <= r; dx++) {
				for (int dy = -r; dy <= r; dy++) {
					for (int dz = -r; dz <= r; dz++) {
						double d = Math.sqrt(dx * dx + dy * dy + dz * dz);
						if (d > r + 0.5 || d < r - 1.2) continue;
						Display.BlockDisplay body = EntityTypes.BLOCK_DISPLAY.create(w.level, EntitySpawnReason.TRIGGERED);
						if (body == null) continue;
						body.setBlockState(blood);
						body.setBrightnessOverride(new Brightness(12, 15));
						body.setPosRotInterpolationDuration(2);
						body.setPos(cx + dx, cy + dy, cz + dz);
						body.addTag(TAG);
						w.level.addFreshEntity(body);
						w.orb.add(body);
						w.orbOffsets.add(new int[] {dx, dy, dz});
					}
				}
			}
		}
		for (int i = 0; i < w.orb.size(); i++) {
			Display.BlockDisplay body = w.orb.get(i);
			int[] o = w.orbOffsets.get(i);
			if (body.position().distanceToSqr(cx + o[0], cy + o[1], cz + o[2]) > 1e-4) body.setPos(cx + o[0], cy + o[1], cz + o[2]);
		}
	}

	private static void clearOrb(Work w) {
		for (Entity e : w.orb) e.discard();
		w.orb.clear();
		w.orbOffsets.clear();
		w.orbRadius = -1;
	}

	// ---- the residents ----------------------------------------------------------------------------

	private static void people(ServerLevel level, Site site) {
		BlockPos plaza = plaza(site.anchor);
		RandomSource random = level.getRandom();
		List<Mob> arrivals = new ArrayList<>();
		for (int i = 0; i < 4; i++) {
			SkyRaider r = CorpsMobs.SKY_RAIDER.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (r == null) continue;
			r.sanctuary(plaza.below(), i == 0);
			r.setItemSlot(EquipmentSlot.MAINHAND, Corps.RED.ring());
			arrivals.add(at(r, plaza, 9, i / 4.0, 3));
		}
		RageWarden warden = CorpsMobs.RAGE_WARDEN.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (warden != null) {
			warden.setItemSlot(EquipmentSlot.MAINHAND, Corps.RED.ring());
			arrivals.add(at(warden, plaza, 7, 0.6, 0));
		}
		for (int i = 0; i < 2; i++) {
			RageCat cat = CorpsMobs.RAGE_CAT.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (cat == null) continue;
			cat.blueCoat(level);
			arrivals.add(at(cat, plaza, 6, 0.1 + i * 0.45, 0));
		}
		CorpsGolem golem = CorpsMobs.CORPS_GOLEM.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (golem != null) {
			golem.setup(Corps.RED, plaza);
			arrivals.add(at(golem, plaza, 6, 0.85, 0));
		}
		for (Mob mob : arrivals) {
			mob.addTag(TAG);
			mob.setPersistenceRequired();
			mob.setHomeTo(plaza, R - 2);
			level.addFreshEntity(mob);
			CorpsShots.summon(level, mob.position(), mob.getBbHeight(), mob.getBbWidth(), Corps.RED);
		}
		level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.RED), plaza.getX() + 0.5, plaza.getY() + 1, plaza.getZ() + 0.5,
				80, R * 0.5, 1, R * 0.5, 0.02);
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(Vec3.atCenterOf(plaza)) < 160 * 160) {
				p.sendSystemMessage(Component.translatable("message.lanternring.sanctuary_stands").withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
			}
		}
		if (random.nextBoolean()) level.playSound(null, plaza.getX(), plaza.getY(), plaza.getZ(), SoundEvents.RAID_HORN, SoundSource.HOSTILE, 16f, 0.8f);
	}

	private static Mob at(Mob mob, BlockPos plaza, double radius, double turn, int up) {
		double a = turn * Math.PI * 2;
		mob.snapTo(plaza.getX() + 0.5 + Math.cos(a) * radius, plaza.getY() + up, plaza.getZ() + 0.5 + Math.sin(a) * radius,
				(float) (a * 180 / Math.PI) + 90f, 0f);
		return mob;
	}

	// ---- who is on whose side ----------------------------------------------------------------------

	/** A sanctuary resident or another Red Lantern mob. */
	public static boolean resident(Entity e) {
		return e.entityTags().contains(TAG) || e instanceof SkyRaider || e instanceof RageWarden || e instanceof RageCat;
	}

	/** Whom the residents leave alone: each other, and anyone holding a red ring. */
	public static boolean friend(@Nullable Entity e) {
		if (e == null) return false;
		if (resident(e)) return true;
		if (e instanceof LivingEntity living) {
			for (ItemStack s : new ItemStack[] {living.getMainHandItem(), living.getOffhandItem()}) {
				if (s.getItem() instanceof PowerRingItem && Corps.of(s) == Corps.RED) return true;
			}
		}
		return false;
	}

	/** For MobTargetMixin: a resident never takes a friend as its target. */
	public static boolean spares(Mob mob, @Nullable LivingEntity target) {
		return target != null && resident(mob) && friend(target);
	}

	private RedSanctuary() {
	}
}
