package com.sparky.lanternring.infinity;

import com.mojang.serialization.Codec;
import com.sparky.lanternring.Corps;
import io.netty.buffer.ByteBuf;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.util.StringRepresentable;
import net.minecraft.world.item.Item;

/** The Infinity Stones made so far. Each one is a held item and can be socketed into the Infinity Gauntlet. */
public enum InfinityStone implements StringRepresentable {
	SOUL("soul", Corps.ORANGE, ChatFormatting.GOLD),
	TIME("time", Corps.GREEN, ChatFormatting.GREEN);

	public static final Codec<InfinityStone> CODEC = StringRepresentable.fromEnum(InfinityStone::values);
	public static final StreamCodec<ByteBuf, InfinityStone> STREAM_CODEC = ByteBufCodecs.idMapper(i -> values()[i], InfinityStone::ordinal);

	private final String name;
	/** The colour its particles take. */
	public final Corps colour;
	public final ChatFormatting chat;

	InfinityStone(String name, Corps colour, ChatFormatting chat) {
		this.name = name;
		this.colour = colour;
		this.chat = chat;
	}

	@Override
	public String getSerializedName() {
		return name;
	}

	public Component displayName() {
		return Component.translatable("stone.lanternring." + name).withStyle(chat);
	}

	public Item item() {
		return switch (this) {
			case SOUL -> Infinity.SOUL_STONE;
			case TIME -> Infinity.TIME_STONE;
		};
	}

	/** The powers this stone gives, in the order the Gauntlet cycles them. */
	public List<InfinityPower> powers() {
		return switch (this) {
			case SOUL -> List.of(InfinityPower.SOUL_REVIVE, InfinityPower.SOUL_GRAVES);
			case TIME -> List.of(InfinityPower.TIME_REWIND, InfinityPower.TIME_FREEZE);
		};
	}
}
