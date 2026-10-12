package com.sparky.lanternring;

import com.mojang.serialization.Codec;
import com.sparky.lanternring.item.PowerRingItem;
import io.netty.buffer.ByteBuf;
import java.util.Collection;
import java.util.EnumSet;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.BlockItemStateProperties;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.EnumProperty;

/**
 * The Lantern Corps: which colour of the emotional spectrum a ring (and its lantern) belongs to.
 * Every corps shares the one ring item and the one lantern block; the {@code lanternring:corps}
 * component (ring) or blockstate (lantern, constructs) says which colour it is. Each corps cycles
 * through its own set of modes, its constructs and effects take its colour, and its ring charges
 * only from its own lantern. See plans/lantern-corps.md for the corps still to come.
 */
public enum Corps implements StringRepresentable {
	GREEN("green", "will", 0x3CFF5A, ChatFormatting.GREEN, EnumSet.complementOf(EnumSet.of(RingMode.INFERNO, RingMode.MIND_LINK, RingMode.CRYSTAL_PRISON, RingMode.FEAR,
			RingMode.HOARD, RingMode.STEAL, RingMode.AVARICE,
			RingMode.RENEW, RingMode.RESTORE, RingMode.SPARK, RingMode.HOPE_GOLEM))),
	RED("red", "rage", 0xFF2A1A, ChatFormatting.RED, EnumSet.of(RingMode.BLAST, RingMode.BEAM, RingMode.WALL, RingMode.DOME,
			RingMode.PUSH, RingMode.DELUGE, RingMode.SHIELD, RingMode.INFERNO)),
	// Star Sapphire: love. Mind Link first, then the constructs.
	VIOLET("violet", "love", 0xA83CFF, ChatFormatting.LIGHT_PURPLE, List.of(RingMode.MIND_LINK, RingMode.CRYSTAL_PRISON, RingMode.WALL, RingMode.DOME,
			RingMode.TETHER, RingMode.SHIELD)),
	// Larfleeze's ring: crafted, never handed out, and greedy (see Avarice).
	ORANGE("orange", "avarice", 0xFF8A00, ChatFormatting.GOLD, List.of(RingMode.HOARD, RingMode.STEAL, RingMode.AVARICE,
			RingMode.BLAST, RingMode.BEAM, RingMode.SHIELD, RingMode.TETHER, RingMode.ARMY)),
	// Hope: Renew, Restore, Villager Spark and the Hope Golem first, then the constructs (see Hope).
	BLUE("blue", "hope", 0x3AA8FF, ChatFormatting.AQUA, List.of(RingMode.RENEW, RingMode.RESTORE, RingMode.SPARK, RingMode.HOPE_GOLEM,
			RingMode.WALL, RingMode.DOME, RingMode.BRIDGE, RingMode.SHIELD, RingMode.TETHER, RingMode.BUILD)),
	// Sinestro's corps: fear. Fear first (and the Brood, see Terror), then the constructs.
	YELLOW("yellow", "fear", 0xFFD21A, ChatFormatting.YELLOW, List.of(RingMode.FEAR, RingMode.BLAST, RingMode.BEAM, RingMode.WALL,
			RingMode.TETHER, RingMode.SHIELD, RingMode.ARMY));

	public static final Codec<Corps> CODEC = StringRepresentable.fromEnum(Corps::values);
	public static final StreamCodec<ByteBuf, Corps> STREAM_CODEC = ByteBufCodecs.idMapper(i -> values()[i], Corps::ordinal);
	/** The blockstate on the lantern and the constructs. */
	public static final EnumProperty<Corps> PROPERTY = EnumProperty.create("corps", Corps.class);

	private final String name;
	private final String emotion;
	/** The corps' colour, 0xRRGGBB. */
	public final int rgb;
	public final ChatFormatting chat;
	private final List<RingMode> modes;

	Corps(String name, String emotion, int rgb, ChatFormatting chat, Collection<RingMode> modes) {
		this.name = name;
		this.emotion = emotion;
		this.rgb = rgb;
		this.chat = chat;
		this.modes = List.copyOf(modes);
	}

	@Override
	public String getSerializedName() {
		return name;
	}

	public float red() {
		return (rgb >> 16 & 0xFF) / 255f;
	}

	public float green() {
		return (rgb >> 8 & 0xFF) / 255f;
	}

	public float blue() {
		return (rgb & 0xFF) / 255f;
	}

	public Component emotion() {
		return Component.translatable("corps.lanternring." + name + ".emotion");
	}

	// ---- modes ------------------------------------------------------------------------------

	public boolean has(RingMode mode) {
		return modes.contains(mode);
	}

	/** This corps' modes in its ring's order (the order crouch + right-click cycles them). */
	public List<RingMode> modes() {
		return modes;
	}

	/** The mode after this one on this corps' ring. */
	public RingMode next(RingMode mode) {
		int i = modes.indexOf(mode);
		return modes.get((i + 1) % modes.size());
	}

	/** A mode this corps doesn't have (an old saved index) falls back to its first. */
	public RingMode allowed(RingMode mode) {
		return has(mode) ? mode : modes.getFirst();
	}

	/** The mode's name on this corps' ring: the red ring's Deluge is a Lava Deluge. */
	public Component modeName(RingMode mode) {
		if (this == RED && mode == RingMode.DELUGE) return Component.translatable("mode.lanternring.lava_deluge");
		return mode.displayName();
	}

	public Component modeDescription(RingMode mode) {
		if (this == RED && mode == RingMode.DELUGE) return Component.translatable("mode.lanternring.lava_deluge.desc");
		return mode.description();
	}

	// ---- which corps an item or block is ----------------------------------------------------

	/** A ring's corps (green unless it says otherwise). */
	public static Corps of(ItemStack stack) {
		return stack.getOrDefault(ModComponents.CORPS, GREEN);
	}

	/** A lantern item's corps, from the blockstate it places. */
	public static Corps ofLantern(ItemStack stack) {
		Corps corps = stack.getOrDefault(DataComponents.BLOCK_STATE, BlockItemStateProperties.EMPTY).get(PROPERTY);
		return corps == null ? GREEN : corps;
	}

	public static Corps of(BlockState state) {
		return state.hasProperty(PROPERTY) ? state.getValue(PROPERTY) : GREEN;
	}

	/** The corps of the ring this entity holds (main hand first), green if none. */
	public static Corps held(LivingEntity entity) {
		if (entity == null) return GREEN;
		if (entity.getMainHandItem().getItem() instanceof PowerRingItem) return of(entity.getMainHandItem());
		if (entity.getOffhandItem().getItem() instanceof PowerRingItem) return of(entity.getOffhandItem());
		return GREEN;
	}

	public ItemStack ring() {
		ItemStack stack = new ItemStack(ModRegistry.POWER_RING);
		if (this != GREEN) {
			stack.set(ModComponents.CORPS, this);
			stack.set(ModComponents.MODE, modes.getFirst().ordinal());
		}
		return stack;
	}

	public ItemStack lantern() {
		ItemStack stack = new ItemStack(ModRegistry.POWER_BATTERY_ITEM);
		if (this != GREEN) stack.set(DataComponents.BLOCK_STATE, BlockItemStateProperties.EMPTY.with(PROPERTY, this));
		return stack;
	}

	// ---- the corps a power is being used for, on the server thread --------------------------

	/**
	 * While a ring's power runs (PowerRingItem's use, hold and release, and the ticks of effects
	 * that outlive them), the corps whose colour its constructs and effects take. Green otherwise.
	 */
	private static final ThreadLocal<Corps> CURRENT = ThreadLocal.withInitial(() -> GREEN);

	public static Corps current() {
		return CURRENT.get();
	}

	/** Makes {@code corps} current and returns the one before, to hand back to {@link #restore}. */
	public static Corps enter(Corps corps) {
		Corps before = CURRENT.get();
		CURRENT.set(corps);
		return before;
	}

	public static void restore(Corps before) {
		CURRENT.set(before);
	}

	/** The block's default state in the current corps' colour (constructs have a corps blockstate). */
	public static BlockState state(Block block) {
		return tint(block.defaultBlockState());
	}

	public static BlockState tint(BlockState state) {
		return state.hasProperty(PROPERTY) ? state.setValue(PROPERTY, current()) : state;
	}
}
