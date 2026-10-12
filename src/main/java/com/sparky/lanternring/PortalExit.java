package com.sparky.lanternring;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import io.netty.buffer.ByteBuf;
import net.minecraft.core.GlobalPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.phys.Vec3;

/** A ring's Portal exit: the block its foot stands in, and the way its front faces (a yaw). */
public record PortalExit(GlobalPos pos, float yaw) {
	public static final Codec<PortalExit> CODEC = RecordCodecBuilder.create(i -> i.group(
			GlobalPos.CODEC.fieldOf("pos").forGetter(PortalExit::pos),
			Codec.FLOAT.fieldOf("yaw").forGetter(PortalExit::yaw)).apply(i, PortalExit::new));
	public static final StreamCodec<ByteBuf, PortalExit> STREAM_CODEC = StreamCodec.composite(
			GlobalPos.STREAM_CODEC, PortalExit::pos,
			ByteBufCodecs.FLOAT, PortalExit::yaw,
			PortalExit::new);

	/** The middle of the portal's oval. */
	public Vec3 center() {
		return Vec3.atBottomCenterOf(pos.pos()).add(0, Portals.HALF_HEIGHT, 0);
	}
}
