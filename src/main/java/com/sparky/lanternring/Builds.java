package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.block.GhostBlocks;
import com.sparky.lanternring.block.GhostMimicBlockEntity;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.designs.BuildDesigns;
import com.sparky.lanternring.designs.BuildDesigns.Area;
import com.sparky.lanternring.designs.BuildDesigns.Design;
import com.sparky.lanternring.designs.BuildDesigns.Group;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.BuildAreaPayload;
import com.sparky.lanternring.net.BuildStatePayload;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
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
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LeavesBlock;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;

/**
 * BUILD: hold right-click and a glowing ring traces an area on the ground under your cursor,
 * growing while you hold (crouch to shrink it). Left-click while holding switches between a
 * circle, a square and painting your own shape with the cursor. Let go and the land inside is
 * cleared and flattened. Then left-click shows the builds that fit, one after another, each rising
 * as green hard light (crouch + left-click goes back); right-click builds the one showing, and the
 * green blocks turn into the real materials from the ground up. Crouch + right-click calls it off.
 *
 * <p>The builds come from BuildDesigns: the game's own village houses, camps, ruins and ships,
 * generated towers, castles and houses in many materials, and the player's own structure files.
 */
public final class Builds {
	public static final int CIRCLE = 0, SQUARE = 1, PAINT = 2, SHAPES = 3;
	public static final int NONE = 0, SELECT = 1, CLEAR = 2, CHOOSE = 3;
	public static final int MIN_RADIUS = 2, MAX_RADIUS = 32;
	/** How wide the paint brush is (a radius in blocks). */
	private static final int BRUSH = 2;
	private static final int MAX_PAINTED = 4500;
	/** How far above the flattened ground trees and hills are cleared. */
	private static final int CLEAR_HEIGHT = 64;
	/** Ticks the green front runs ahead of the clearing. */
	private static final int CLEAR_LEAD = 6;
	/** How far down holes and water are filled. */
	private static final int FILL_DEPTH = 24;
	/** A chosen area waits this long for a build before it's let go. */
	private static final int CHOOSE_TIMEOUT = 20 * 60 * 5;
	private static final int MARKER_LIGHT = 8;
	/** Only this many blocks change per tick, so huge builds don't stall the server. */
	private static final int BLOCKS_PER_TICK = 2500;
	private static final int FLAGS = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;

	private static final class Plan {
		ServerLevel level;
		/** The ring's colour when the plan began: the preview and the clearing front are drawn in it. */
		Corps corps = Corps.GREEN;
		int phase = SELECT;
		int shape;
		float radius = 4;
		BlockPos mark;
		BlockPos lastPaint;
		final Set<Long> painted = new HashSet<>();
		BlockPos light;
		long lastTick;
		// Once the area is chosen:
		Area area;
		BlockPos center;
		BlockState surface;
		BlockState filler;
		List<Long> clearOrder;
		int clearIndex;
		/** How far the green front runs ahead of the clearing: columns before it are already green. */
		int greenIndex;
		/** The land the green front has overwritten, still waiting to be cleared. */
		final Map<BlockPos, BlockState> greenLand = new HashMap<>();
		int clearPerTick;
		List<Group> designs;
		int index;
		/** Which of the design's materials is showing. */
		int variant;
		/** The material picked last, kept while scrolling to other designs that come in it. */
		String material = "";
		Preview preview;
		long choosingSince;
		int awayTicks;
	}

	/** The design showing in green, block by block from the bottom. */
	private static final class Preview {
		Design design;
		/** Every block of the design, air included, bottom layer first. */
		Map<BlockPos, BlockState> blocks;
		List<BlockPos> order;
		int index;
		int perTick;
		/** Charge to build it, from cost(). */
		int cost;
		final Set<BlockPos> placed = new HashSet<>();
		/** Ground blocks the bottom layer replaced, put back if this design isn't built. */
		final Map<BlockPos, BlockState> replaced = new HashMap<>();
	}

	/** A confirmed build turning from green into its real blocks. */
	private static final class Job {
		ServerLevel level;
		Player owner;
		List<BlockPos> order;
		Map<BlockPos, BlockState> blocks;
		final Set<BlockPos> green = new HashSet<>();
		int index;
		int perTick;
	}

	private static final Map<UUID, Plan> PLANS = new HashMap<>();
	private static final List<Job> JOBS = new ArrayList<>();

	private Builds() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Builds::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Plan plan : PLANS.values()) {
				clearPreview(plan);
				restoreLand(plan);
				clearLight(plan);
			}
			PLANS.clear();
			// Finish what's being built rather than leave green blocks in the world.
			for (Job job : JOBS) {
				while (job.index < job.order.size()) form(job, job.order.get(job.index++));
				finish(job);
			}
			JOBS.clear();
			BuildDesigns.forget();
		});
		ServerLifecycleEvents.END_DATA_PACK_RELOAD.register((server, resources, success) -> BuildDesigns.forget());
	}

	public static boolean isLive(ServerLevel level, BlockPos pos) {
		for (Plan plan : PLANS.values()) {
			if (plan.level == level && plan.preview != null && plan.preview.placed.contains(pos)) return true;
			if (plan.level == level && plan.greenLand.containsKey(pos)) return true;
		}
		for (Job job : JOBS) {
			if (job.level == level && job.green.contains(pos)) return true;
		}
		return false;
	}

	public static int shape(ItemStack ring) {
		return Math.floorMod(ring.getOrDefault(ModComponents.BUILD_SHAPE, CIRCLE), SHAPES);
	}

	public static Component shapeText(int shape) {
		return Component.translatable("build_shape.lanternring." + switch (shape) {
			case SQUARE -> "square";
			case PAINT -> "paint";
			default -> "circle";
		});
	}

	/** The smallest build's charge (1% of a full ring); clearing the land needs at least this much. */
	public static final int MIN_COST = 10;
	/** The biggest build's charge (75% of a full ring). */
	public static final int MAX_COST = 750;
	/** Blocks in a design that cost the most; bigger ones cost no more. */
	private static final int MAX_COST_BLOCKS = 20000;

	/** Charge for a design of this many blocks: 1% up to 75% of a full ring, in step with its size. */
	public static int cost(int blocks) {
		return MIN_COST + Math.round((MAX_COST - MIN_COST) * Math.min(1f, blocks / (float) MAX_COST_BLOCKS));
	}

	// ---- right-click ------------------------------------------------------------------------------

	/**
	 * Right-click went down in Build mode (server side). While a build is waiting to be chosen it
	 * builds it; crouching calls it off.
	 *
	 * @return true if the click was used up and the ring shouldn't start a new area
	 */
	public static boolean press(ServerPlayer player, ItemStack ring, boolean crouching) {
		Plan plan = PLANS.get(player.getUUID());
		if (plan != null && plan.phase == CHOOSE) {
			if (crouching) cancel(player, true);
			else confirm(player, plan, ring);
			return true;
		}
		if (plan != null && plan.phase == CLEAR) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.build_clearing").withStyle(ChatFormatting.GREEN));
			return true;
		}
		if (crouching) return false;
		if (player.getCooldowns().isOnCooldown(ring)) return true;
		if (!player.isCreative() && PowerRingItem.getCharge(ring) < MIN_COST) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
			player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
			return true;
		}
		if (plan != null) clearLight(plan);
		plan = new Plan();
		plan.level = player.level();
		plan.corps = Corps.current();
		plan.shape = shape(ring);
		plan.lastTick = plan.level.getGameTime();
		PLANS.put(player.getUUID(), plan);
		state(player, SELECT);
		return false;
	}

	/** Every tick right-click is held in Build mode: the area follows the cursor and grows or gets painted. */
	public static void selectTick(ServerPlayer player, ItemStack ring) {
		Plan plan = PLANS.get(player.getUUID());
		if (plan == null || plan.phase != SELECT) return;
		ServerLevel level = player.level();
		if (plan.level != level) {
			cancel(player, false);
			return;
		}
		plan.lastTick = level.getGameTime();
		BlockPos mark = Anvils.findMark(level, player);
		boolean crouching = player.isShiftKeyDown();
		if (plan.shape == PAINT) {
			if (mark != null) paint(plan, mark, crouching);
		} else {
			float step = (MAX_RADIUS - MIN_RADIUS) / (float) Math.max(1, RingTuning.BUILD_GROW.ticks());
			plan.radius = Mth.clamp(plan.radius + (crouching ? -step : step), MIN_RADIUS, MAX_RADIUS);
		}
		if (mark != null) plan.mark = mark;
		marker(plan);
		if (plan.mark != null && level.getGameTime() % 2 == 0) outline(plan, false);
		if (level.getGameTime() % 4 == 0) {
			int columns = plan.shape == PAINT ? plan.painted.size() : columns(plan).size();
			player.sendOverlayMessage(Component.translatable("message.lanternring.build_size", shapeText(plan.shape), sizeText(plan, columns),
					ChargeText.percent(MIN_COST)).withStyle(ChatFormatting.GREEN));
		}
	}

	private static String sizeText(Plan plan, int columns) {
		if (plan.shape == PAINT) return columns + "";
		int across = Math.round(plan.radius) * 2 + 1;
		return across + "x" + across;
	}

	/** Paints (or with crouch, rubs out) a round brush along the cursor's path since last tick. */
	private static void paint(Plan plan, BlockPos mark, boolean erase) {
		BlockPos from = plan.lastPaint == null ? mark : plan.lastPaint;
		int steps = Math.max(1, (int) Math.ceil(Math.sqrt(from.distSqr(mark))));
		if (steps > 24) {
			from = mark;
			steps = 1;
		}
		for (int i = 0; i <= steps; i++) {
			int x = Mth.floor(Mth.lerp(i / (float) steps, from.getX(), mark.getX()));
			int z = Mth.floor(Mth.lerp(i / (float) steps, from.getZ(), mark.getZ()));
			for (int dx = -BRUSH; dx <= BRUSH; dx++) {
				for (int dz = -BRUSH; dz <= BRUSH; dz++) {
					if (dx * dx + dz * dz > BRUSH * BRUSH + 1) continue;
					long c = BuildDesigns.col(x + dx, z + dz);
					if (erase) plan.painted.remove(c);
					else if (plan.painted.size() < MAX_PAINTED) plan.painted.add(c);
				}
			}
		}
		plan.lastPaint = mark;
	}

	/** The columns of the area as it stands. */
	private static Set<Long> columns(Plan plan) {
		if (plan.shape == PAINT) return new HashSet<>(plan.painted);
		Set<Long> out = new HashSet<>();
		if (plan.mark == null) return out;
		int r = Math.round(plan.radius);
		for (int dx = -r; dx <= r; dx++) {
			for (int dz = -r; dz <= r; dz++) {
				if (plan.shape == CIRCLE && dx * dx + dz * dz > (plan.radius + 0.5f) * (plan.radius + 0.5f)) continue;
				out.add(BuildDesigns.col(plan.mark.getX() + dx, plan.mark.getZ() + dz));
			}
		}
		return out;
	}

	/** Left-click while holding: the next shape (it starts over). */
	public static void cycleShape(ServerPlayer player, ItemStack ring) {
		int next = (shape(ring) + 1) % SHAPES;
		ring.set(ModComponents.BUILD_SHAPE, next);
		Plan plan = PLANS.get(player.getUUID());
		if (plan != null && plan.phase == SELECT) {
			plan.shape = next;
			plan.painted.clear();
			plan.lastPaint = null;
			plan.radius = 4;
		}
		player.sendOverlayMessage(Component.translatable("message.lanternring.build_shape", shapeText(next)).withStyle(ChatFormatting.GREEN));
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.2f + 0.2f * next);
	}

	/** Right-click let go: the area is chosen, paid for, and cleared. */
	public static void release(ServerPlayer player, ItemStack ring) {
		Plan plan = PLANS.get(player.getUUID());
		if (plan == null || plan.phase != SELECT) return;
		clearLight(plan);
		Set<Long> cols = columns(plan);
		if (cols.size() < 4 || plan.mark == null || plan.level != player.level()) {
			cancel(player, false);
			return;
		}
		// Clearing is free; the build itself is paid for when it's confirmed.
		if (!player.isCreative() && PowerRingItem.getCharge(ring) < MIN_COST) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
			player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
			cancel(player, false);
			return;
		}
		ServerLevel level = plan.level;
		// Flatten to the middle height of the ground, so as little as possible is dug or filled.
		List<Integer> heights = new ArrayList<>();
		Map<BlockState, Integer> tops = new HashMap<>();
		for (long c : cols) {
			BlockPos top = ground(level, BuildDesigns.colX(c), BuildDesigns.colZ(c), plan.mark.getY());
			heights.add(top.getY());
			tops.merge(level.getBlockState(top), 1, Integer::sum);
		}
		Collections.sort(heights);
		int groundY = heights.get(heights.size() / 2);
		Direction toward = player.getDirection().getOpposite();
		plan.area = new Area(cols, groundY, toward);
		plan.center = new BlockPos((int) Math.round(plan.area.cx), groundY + 1, (int) Math.round(plan.area.cz));
		BlockState surface = tops.entrySet().stream().max(Map.Entry.comparingByValue()).map(Map.Entry::getKey).orElse(Blocks.GRASS_BLOCK.defaultBlockState());
		plan.surface = groundBlock(surface, level);
		plan.filler = fillerFor(plan.surface);
		plan.clearOrder = new ArrayList<>(cols);
		BlockPos center = plan.center;
		plan.clearOrder.sort(Comparator.comparingDouble(c -> Math.pow(BuildDesigns.colX(c) - center.getX(), 2) + Math.pow(BuildDesigns.colZ(c) - center.getZ(), 2)));
		int ticks = Math.max(1, Math.round(RingTuning.BUILD_CLEAR.ticks() * Mth.clamp((float) Math.sqrt(cols.size() / 300.0), 1f, 3f)));
		plan.clearPerTick = Math.max(1, (int) Math.ceil(cols.size() / (double) ticks));
		plan.phase = CLEAR;
		state(player, CLEAR);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.BUILD));
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), Vec3.atCenterOf(center));
		level.playSound(null, center, SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.5f, 0.7f);
	}

	/** The top of the ground at a column: trees, plants and water don't count. */
	private static BlockPos ground(ServerLevel level, int x, int z, int nearY) {
		int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z) - 1;
		// Under a roof or in a cave the heightmap is the roof: look near the cursor instead.
		if (top > nearY + 24) top = nearY + 8;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos(x, top, z);
		for (int i = 0; i < 48 && pos.getY() > level.getMinY(); i++, pos.move(Direction.DOWN)) {
			BlockState s = level.getBlockState(pos);
			if (s.isAir() || s.canBeReplaced() || s.is(BlockTags.LOGS) || s.is(BlockTags.LEAVES) || isOurs(s)) continue;
			return pos.immutable();
		}
		return new BlockPos(x, nearY - 1, z);
	}

	private static BlockState groundBlock(BlockState top, ServerLevel level) {
		Block[] natural = {Blocks.GRASS_BLOCK, Blocks.SAND, Blocks.RED_SAND, Blocks.SNOW_BLOCK, Blocks.PODZOL, Blocks.MYCELIUM, Blocks.DIRT,
				Blocks.COARSE_DIRT, Blocks.MUD, Blocks.MOSS_BLOCK, Blocks.STONE, Blocks.DEEPSLATE, Blocks.NETHERRACK, Blocks.END_STONE,
				Blocks.SANDSTONE, Blocks.TERRACOTTA, Blocks.GRAVEL, Blocks.SOUL_SOIL, Blocks.CRIMSON_NYLIUM, Blocks.WARPED_NYLIUM, Blocks.PALE_MOSS_BLOCK};
		for (Block b : natural) if (top.is(b)) return b.defaultBlockState();
		if (level.dimension() == net.minecraft.world.level.Level.NETHER) return Blocks.NETHERRACK.defaultBlockState();
		if (level.dimension() == net.minecraft.world.level.Level.END) return Blocks.END_STONE.defaultBlockState();
		return Blocks.GRASS_BLOCK.defaultBlockState();
	}

	private static BlockState fillerFor(BlockState surface) {
		if (surface.is(Blocks.SAND)) return Blocks.SANDSTONE.defaultBlockState();
		if (surface.is(Blocks.RED_SAND)) return Blocks.RED_SANDSTONE.defaultBlockState();
		if (surface.is(Blocks.GRAVEL)) return Blocks.STONE.defaultBlockState();
		if (surface.is(Blocks.GRASS_BLOCK) || surface.is(Blocks.PODZOL) || surface.is(Blocks.MYCELIUM) || surface.is(Blocks.SNOW_BLOCK)
				|| surface.is(Blocks.MOSS_BLOCK) || surface.is(Blocks.PALE_MOSS_BLOCK) || surface.is(Blocks.COARSE_DIRT)) {
			return Blocks.DIRT.defaultBlockState();
		}
		if (surface.is(Blocks.CRIMSON_NYLIUM) || surface.is(Blocks.WARPED_NYLIUM)) return Blocks.NETHERRACK.defaultBlockState();
		return surface;
	}

	// ---- clearing ---------------------------------------------------------------------------------

	/** Clears and flattens the next ring of columns, from the middle out. */
	private static void clearTick(ServerPlayer player, Plan plan) {
		ServerLevel level = plan.level;
		int groundY = plan.area.groundY;
		// A few ticks ahead of the clearing, the land turns into green construct copies of itself.
		int greenEnd = Math.min(plan.clearOrder.size(), plan.clearIndex + plan.clearPerTick * (CLEAR_LEAD + 1));
		for (; plan.greenIndex < greenEnd; plan.greenIndex++) {
			long c = plan.clearOrder.get(plan.greenIndex);
			int x = BuildDesigns.colX(c), z = BuildDesigns.colZ(c);
			int top = Math.min(groundY + CLEAR_HEIGHT, level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z));
			BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos(x, top, z);
			for (; pos.getY() > groundY; pos.move(Direction.DOWN)) {
				BlockState s = level.getBlockState(pos);
				if (s.isAir() || !s.getFluidState().isEmpty() || !removable(level, player, pos, s)) continue;
				BlockPos at = pos.immutable();
				plan.greenLand.put(at, s);
				setGreen(level, at, ghost(level, s, false), s);
			}
		}
		int end = Math.min(plan.clearOrder.size(), plan.clearIndex + plan.clearPerTick);
		for (; plan.clearIndex < end; plan.clearIndex++) {
			long c = plan.clearOrder.get(plan.clearIndex);
			int x = BuildDesigns.colX(c), z = BuildDesigns.colZ(c);
			int top = Math.min(groundY + CLEAR_HEIGHT, level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z));
			BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos(x, top, z);
			for (; pos.getY() > groundY; pos.move(Direction.DOWN)) {
				BlockState s = level.getBlockState(pos);
				BlockState was = plan.greenLand.remove(pos);
				if (was != null && isGreen(s)) s = was;
				else if (s.isAir() || !removable(level, player, pos, s)) continue;
				level.setBlock(pos, Blocks.AIR.defaultBlockState(), FLAGS);
				HeldConstructs.debris(level, pos, s);
			}
			// Fill holes and water under the new ground, bottom up so sand has something to sit on.
			List<BlockPos> holes = new ArrayList<>();
			pos.set(x, groundY - 1, z);
			for (int i = 0; i < FILL_DEPTH && pos.getY() > level.getMinY(); i++, pos.move(Direction.DOWN)) {
				BlockState s = level.getBlockState(pos);
				if (!s.canBeReplaced() && s.getFluidState().isEmpty()) break;
				holes.add(pos.immutable());
			}
			for (int i = holes.size() - 1; i >= 0; i--) level.setBlock(holes.get(i), plan.filler, FLAGS);
			pos.set(x, groundY, z);
			BlockState there = level.getBlockState(pos);
			if (!there.is(plan.surface.getBlock()) && removable(level, player, pos, there) || there.canBeReplaced()) {
				level.setBlock(pos, plan.surface, FLAGS);
			}
		}
		if (level.getGameTime() % 4 == 0) {
			level.playSound(null, plan.center, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.6f + 0.6f * plan.clearIndex / plan.clearOrder.size());
		}
		if (plan.clearIndex >= plan.clearOrder.size()) startChoosing(player, plan);
	}

	private static boolean removable(ServerLevel level, Player player, BlockPos pos, BlockState s) {
		return !s.hasBlockEntity() && s.getDestroySpeed(level, pos) >= 0 && !isOurs(s) && level.mayInteract(player, pos);
	}

	private static boolean isOurs(BlockState s) {
		return isGreen(s) || s.is(ModRegistry.BLAST_GLOW);
	}

	private static void startChoosing(ServerPlayer player, Plan plan) {
		plan.designs = BuildDesigns.forArea(player.level().getServer(), plan.area, plan.level.getRandom().nextLong());
		plan.phase = CHOOSE;
		plan.choosingSince = plan.level.getGameTime();
		state(player, CHOOSE);
		plan.level.playSound(null, plan.center, SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1.5f, 1.2f);
		if (plan.designs.isEmpty()) {
			player.sendSystemMessage(Component.translatable("message.lanternring.build_none").withStyle(ChatFormatting.YELLOW));
			cancel(player, false);
			return;
		}
		player.sendSystemMessage(Component.translatable("message.lanternring.build_help", plan.designs.size()).withStyle(ChatFormatting.GREEN));
		show(player, plan, 0, 0);
	}

	// ---- choosing ---------------------------------------------------------------------------------

	/** Left-click or scroll while choosing: the next design (or the one before). Keeps the material if it can. */
	public static void step(ServerPlayer player, int by) {
		Plan plan = PLANS.get(player.getUUID());
		if (plan == null || plan.phase != CHOOSE || plan.designs.isEmpty()) return;
		int index = Math.floorMod(plan.index + by, plan.designs.size());
		List<Design> variants = plan.designs.get(index).variants;
		int variant = 0;
		for (int i = 0; i < variants.size(); i++) {
			if (!plan.material.isEmpty() && variants.get(i).material.equals(plan.material)) variant = i;
		}
		show(player, plan, index, variant);
	}

	/** Crouch + scroll while choosing: the same design in its next (or previous) materials. */
	public static void stepMaterial(ServerPlayer player, int by) {
		Plan plan = PLANS.get(player.getUUID());
		if (plan == null || plan.phase != CHOOSE || plan.designs.isEmpty()) return;
		List<Design> variants = plan.designs.get(plan.index).variants;
		if (variants.size() < 2) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.build_one_material").withStyle(ChatFormatting.YELLOW));
			return;
		}
		int variant = Math.floorMod(plan.variant + by, variants.size());
		plan.material = variants.get(variant).material;
		show(player, plan, plan.index, variant);
	}

	private static void show(ServerPlayer player, Plan plan, int index, int variant) {
		clearPreview(plan);
		plan.index = index;
		plan.variant = variant;
		plan.choosingSince = plan.level.getGameTime();
		List<Design> variants = plan.designs.get(index).variants;
		Design design = variants.get(variant);
		Preview preview = new Preview();
		preview.design = design;
		try {
			preview.blocks = design.place(plan.area.groundY);
		} catch (RuntimeException e) {
			LanternRing.LOGGER.warn("Couldn't make build {}", design.name, e);
			preview.blocks = new LinkedHashMap<>();
		}
		List<BlockPos> order = new ArrayList<>();
		Map<BlockPos, Double> layer = new HashMap<>();
		for (Map.Entry<BlockPos, BlockState> e : preview.blocks.entrySet()) {
			if (e.getValue().isAir()) continue;
			order.add(e.getKey());
			layer.put(e.getKey(), e.getKey().getY() + plan.level.getRandom().nextFloat() * 0.95);
		}
		order.sort(Comparator.comparingDouble(layer::get));
		preview.order = order;
		preview.cost = cost(order.size());
		int ticks = Math.max(1, Math.round(RingTuning.BUILD_PREVIEW.ticks() * Mth.clamp((float) Math.sqrt(order.size() / 400.0), 1f, 3f)));
		preview.perTick = Mth.clamp((int) Math.ceil(order.size() / (double) ticks), 1, BLOCKS_PER_TICK);
		plan.preview = preview;
		// Keep only this one's blocks in memory; others are made again if shown again.
		for (Group g : plan.designs) for (Design d : g.variants) if (d != design) d.release();
		Component line = variants.size() > 1
				? Component.translatable("message.lanternring.build_design_materials", index + 1, plan.designs.size(), design.name, design.category,
						design.size(), ChargeText.percent(preview.cost), variant + 1, variants.size())
				: Component.translatable("message.lanternring.build_design", index + 1, plan.designs.size(), design.name, design.category,
						design.size(), ChargeText.percent(preview.cost));
		player.sendOverlayMessage(line.copy().withStyle(ChatFormatting.GREEN));
		state(player, CHOOSE, preview.cost);
		plan.level.playSound(null, plan.center, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.5f, 1.4f);
	}

	private static BlockState green(ServerLevel level) {
		return Corps.state(ModRegistry.LIGHT_CONSTRUCT).setValue(LightConstructBlock.HELD, true)
				.setValue(LightConstructBlock.RIM, level.getRandom().nextFloat() < 0.12f);
	}

	/** Designs up to this many blocks show every block as a green copy of itself; bigger ones keep plain cubes as construct cubes. */
	private static final int COPY_ALL_LIMIT = 4000;

	/**
	 * The green stand-in for one block: a hard-light copy of the real block (GhostMimicBlock,
	 * drawn from its own model, so plants, crops, flowers, leaves, stairs and so on look exactly
	 * right), or for plain cubes in big builds the usual construct block. Liquids become cubes.
	 */
	private static BlockState ghost(ServerLevel level, BlockState real, boolean copyCubes) {
		if (!real.getFluidState().isEmpty() && real.getCollisionShape(EmptyBlockGetter.INSTANCE, BlockPos.ZERO).isEmpty()) return green(level);
		boolean cube = real.isCollisionShapeFullBlock(EmptyBlockGetter.INSTANCE, BlockPos.ZERO) && real.getRenderShape() == RenderShape.MODEL
				&& !(real.getBlock() instanceof LeavesBlock);
		if (cube && !copyCubes) return green(level);
		return Corps.state(ModRegistry.GHOST_MIMIC);
	}

	/** Puts a green stand-in down and, if it's a copy, tells it which block it copies. */
	private static void setGreen(ServerLevel level, BlockPos pos, BlockState green, BlockState real) {
		level.setBlock(pos, green, FLAGS);
		if (level.getBlockEntity(pos) instanceof GhostMimicBlockEntity mimic) {
			mimic.setReal(real.hasProperty(BlockStateProperties.WATERLOGGED) ? real.setValue(BlockStateProperties.WATERLOGGED, false) : real);
		}
	}

	/** True for the construct cube and every green shape a preview or build uses. */
	public static boolean isGreen(BlockState s) {
		return s.is(ModRegistry.LIGHT_CONSTRUCT) || s.getBlock() instanceof GhostBlocks.Ghost;
	}

	/** Raises the next few green blocks of the design showing. */
	private static void previewTick(Plan plan) {
		Preview p = plan.preview;
		if (p == null) return;
		int end = Math.min(p.order.size(), p.index + p.perTick);
		for (; p.index < end; p.index++) placeGreen(plan, p, p.order.get(p.index));
	}

	private static void placeGreen(Plan plan, Preview p, BlockPos pos) {
		ServerLevel level = plan.level;
		BlockState current = level.getBlockState(pos);
		BlockState real = p.blocks.get(pos);
		BlockState green = real == null || real.isAir() ? green(level) : ghost(level, real, p.order.size() <= COPY_ALL_LIMIT);
		if (pos.getY() <= plan.area.groundY) {
			// The bottom layer sits in the ground: remember what it replaced.
			if (current.hasBlockEntity() || current.getDestroySpeed(level, pos) < 0) return;
			if (!isOurs(current)) p.replaced.put(pos, current);
		} else if (!current.canBeReplaced() || !level.isUnobstructed(green, pos, CollisionContext.empty())) {
			return;
		}
		setGreen(level, pos, green, real == null ? Blocks.AIR.defaultBlockState() : real);
		p.placed.add(pos);
	}

	private static void clearPreview(Plan plan) {
		Preview p = plan.preview;
		if (p == null) return;
		plan.preview = null;
		for (BlockPos pos : p.placed) {
			if (!isGreen(plan.level.getBlockState(pos))) continue;
			plan.level.setBlock(pos, p.replaced.getOrDefault(pos, Blocks.AIR.defaultBlockState()), FLAGS);
		}
	}

	/** Right-click while choosing: build it for real. */
	private static void confirm(ServerPlayer player, Plan plan, ItemStack ring) {
		Preview p = plan.preview;
		if (p == null) return;
		if (!player.isCreative()) {
			if (PowerRingItem.getCharge(ring) < p.cost) {
				player.sendOverlayMessage(Component.translatable("message.lanternring.build_no_charge", ChargeText.percent(p.cost)).withStyle(ChatFormatting.RED));
				player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
				return;
			}
			PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - p.cost);
		}
		// Finish the green version first: it all turns real from the ground up.
		while (p.index < p.order.size()) placeGreen(plan, p, p.order.get(p.index++));
		Job job = new Job();
		job.level = plan.level;
		job.owner = player;
		job.blocks = p.blocks;
		job.green.addAll(p.placed);
		List<BlockPos> order = new ArrayList<>(p.blocks.keySet());
		Map<BlockPos, Double> layer = new HashMap<>();
		for (BlockPos pos : order) layer.put(pos, pos.getY() + plan.level.getRandom().nextFloat() * 0.95);
		order.sort(Comparator.comparingDouble(layer::get));
		job.order = order;
		int ticks = Math.max(1, Math.round(RingTuning.BUILD_FORM.ticks() * Mth.clamp((float) Math.sqrt(order.size() / 500.0), 1f, 4f)));
		job.perTick = Mth.clamp((int) Math.ceil(order.size() / (double) ticks), 1, BLOCKS_PER_TICK);
		JOBS.add(job);
		// The green blocks now belong to the job; the plan is done.
		plan.preview = null;
		PLANS.remove(player.getUUID());
		state(player, NONE);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.BUILD));
		player.sendOverlayMessage(Component.translatable("message.lanternring.build_go", p.design.name).withStyle(ChatFormatting.GREEN));
		RingFx.send(plan.level, Kind.CONSTRUCT, RingPowers.handPos(player), Vec3.atCenterOf(plan.center));
		plan.level.playSound(null, plan.center, SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 2f, 1.0f);
	}

	/** Land that turned green but wasn't cleared yet comes back. */
	private static void restoreLand(Plan plan) {
		plan.greenLand.forEach((pos, was) -> {
			if (plan.level.isLoaded(pos) && isGreen(plan.level.getBlockState(pos))) plan.level.setBlock(pos, was, FLAGS);
		});
		plan.greenLand.clear();
	}

	/** Calls off whatever the bearer was choosing; the cleared land stays flat. */
	public static boolean cancel(Player player, boolean say) {
		Plan plan = PLANS.remove(player.getUUID());
		if (plan == null) return false;
		clearPreview(plan);
		restoreLand(plan);
		clearLight(plan);
		if (player instanceof ServerPlayer sp) {
			state(sp, NONE);
			if (say) {
				sp.sendOverlayMessage(Component.translatable("message.lanternring.build_cancel").withStyle(ChatFormatting.YELLOW));
				sp.level().playSound(null, sp.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.8f, 1.2f);
			}
		}
		return true;
	}

	// ---- forming ----------------------------------------------------------------------------------

	private static void form(Job job, BlockPos pos) {
		ServerLevel level = job.level;
		BlockState want = job.blocks.get(pos);
		BlockState current = level.getBlockState(pos);
		job.green.remove(pos);
		if (want.isAir()) {
			if (current.isAir() || current.hasBlockEntity() || current.getDestroySpeed(level, pos) < 0) return;
		} else if (!isGreen(current) && !current.canBeReplaced() && pos.getY() > level.getMinY()
				&& (current.hasBlockEntity() || current.getDestroySpeed(level, pos) < 0)) {
			return;
		}
		level.setBlock(pos, want, FLAGS);
		if (!want.isAir() && level.getRandom().nextInt(12) == 0) {
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, want), pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 4, 0.3, 0.3, 0.3, 0.05);
		}
		if (level.getRandom().nextInt(40) == 0) {
			level.playSound(null, pos, want.getSoundType().getPlaceSound(), SoundSource.BLOCKS, 1f, 0.9f);
		}
	}

	/** Once it's all real: let fences, panes and stairs join up with their neighbours. */
	private static void finish(Job job) {
		for (BlockPos pos : job.order) {
			BlockState s = job.level.getBlockState(pos);
			if (s.isAir()) continue;
			BlockState joined = Block.updateFromNeighbourShapes(s, job.level, pos);
			if (joined != s && !joined.isAir()) job.level.setBlock(pos, joined, FLAGS);
		}
		job.green.clear();
	}

	// ---- every tick -------------------------------------------------------------------------------

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Plan>> it = PLANS.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Plan> e = it.next();
			Plan plan = e.getValue();
			ServerPlayer player = server.getPlayerList().getPlayer(e.getKey());
			long now = plan.level.getGameTime();
			if (player == null || !player.isAlive()) {
				// Left or died mid-clear: the land already turned green comes back too.
				clearPreview(plan);
				restoreLand(plan);
				clearLight(plan);
				it.remove();
				continue;
			}
			Corps before = Corps.enter(plan.corps);
			try {
				switch (plan.phase) {
					case SELECT -> {
						// Stopped holding without a release (switched items...): no area.
						if (now - plan.lastTick > 5) {
							clearLight(plan);
							it.remove();
							state(player, NONE);
						}
					}
					case CLEAR -> clearTick(player, plan);
					case CHOOSE -> {
						previewTick(plan);
						if (now % 10 == 0) outline(plan, true);
						ItemStack held = player.getMainHandItem();
						boolean ring = held.getItem() instanceof PowerRingItem && PowerRingItem.getMode(held) == RingMode.BUILD;
						plan.awayTicks = ring ? 0 : plan.awayTicks + 1;
						boolean far = player.level() != plan.level || player.distanceToSqr(Vec3.atCenterOf(plan.center)) > 160 * 160;
						if (far || plan.awayTicks > 60 || now - plan.choosingSince > CHOOSE_TIMEOUT) {
							clearPreview(plan);
							it.remove();
							state(player, NONE);
						}
					}
					default -> {
					}
				}
			} finally {
				Corps.restore(before);
			}
		}
		for (Iterator<Job> it = JOBS.iterator(); it.hasNext(); ) {
			Job job = it.next();
			int end = Math.min(job.order.size(), job.index + job.perTick);
			for (; job.index < end; job.index++) form(job, job.order.get(job.index));
			if (job.index >= job.order.size()) {
				finish(job);
				job.level.playSound(null, job.order.get(job.order.size() - 1), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 1f, 1.2f);
				it.remove();
			}
		}
	}

	// ---- what the bearer sees ---------------------------------------------------------------------

	private static void state(ServerPlayer player, int phase) {
		state(player, phase, 0);
	}

	/** Tells the bearer's client the phase, and while choosing what the design showing costs. */
	private static void state(ServerPlayer player, int phase, int cost) {
		if (ServerPlayNetworking.canSend(player, BuildStatePayload.TYPE)) ServerPlayNetworking.send(player, new BuildStatePayload(phase, cost));
	}

	/** Sends the area's outline to everyone nearby to trace on the ground. */
	private static void outline(Plan plan, boolean locked) {
		Vec3 center;
		List<Integer> rim = new ArrayList<>();
		int shape = plan.shape;
		float radius = plan.radius;
		if (locked) {
			center = new Vec3(plan.center.getX() + 0.5, plan.area.groundY + 1, plan.center.getZ() + 0.5);
			if (shape == PAINT) rim = rim(plan.area.cols, plan.center.getX(), plan.center.getZ());
		} else {
			if (plan.mark == null) return;
			center = new Vec3(plan.mark.getX() + 0.5, plan.mark.getY(), plan.mark.getZ() + 0.5);
			if (shape == PAINT) rim = rim(plan.painted, plan.mark.getX(), plan.mark.getZ());
		}
		if (shape == PAINT && rim.isEmpty()) {
			if (locked) return;
			// Nothing painted yet: show the brush.
			shape = CIRCLE;
			radius = BRUSH;
		}
		BuildAreaPayload payload = new BuildAreaPayload(shape, center, radius, locked, rim);
		for (ServerPlayer p : PlayerLookup.around(plan.level, center, 96)) {
			if (ServerPlayNetworking.canSend(p, BuildAreaPayload.TYPE)) ServerPlayNetworking.send(p, payload);
		}
	}

	private static List<Integer> rim(Set<Long> cols, int cx, int cz) {
		List<Integer> out = new ArrayList<>();
		for (long c : cols) {
			int x = BuildDesigns.colX(c), z = BuildDesigns.colZ(c);
			if (cols.contains(BuildDesigns.col(x + 1, z)) && cols.contains(BuildDesigns.col(x - 1, z))
					&& cols.contains(BuildDesigns.col(x, z + 1)) && cols.contains(BuildDesigns.col(x, z - 1))) {
				continue;
			}
			out.add((x - cx) << 16 | (z - cz) & 0xFFFF);
		}
		return out;
	}

	/** A glowing light under the cursor while choosing the area, like the Anvil's marker. */
	private static void marker(Plan plan) {
		BlockPos light = plan.mark;
		if (light == null) {
			clearLight(plan);
			return;
		}
		if (!light.equals(plan.light)) clearLight(plan);
		BlockState there = plan.level.getBlockState(light);
		BlockState glow = Corps.state(ModRegistry.BLAST_GLOW).setValue(BlastGlowBlock.LEVEL, MARKER_LIGHT);
		if (there.isAir() || there.is(ModRegistry.BLAST_GLOW) && there.getValue(BlastGlowBlock.LEVEL) != MARKER_LIGHT) {
			plan.level.setBlock(light, glow, 3);
			plan.light = light;
		}
	}

	private static void clearLight(Plan plan) {
		if (plan.light != null && plan.level != null && plan.level.getBlockState(plan.light).is(ModRegistry.BLAST_GLOW)) {
			plan.level.setBlock(plan.light, Blocks.AIR.defaultBlockState(), 3);
		}
		plan.light = null;
	}

	/** Charge text helper shared with the HUD. */
	public static final class ChargeText {
		/** Charge points as a percent of a full ring: 5 -> "0.5", 10 -> "1". */
		public static String percent(int points) {
			return points % 10 == 0 ? String.valueOf(points / 10) : String.valueOf(points / 10.0);
		}

		private ChargeText() {
		}
	}
}
