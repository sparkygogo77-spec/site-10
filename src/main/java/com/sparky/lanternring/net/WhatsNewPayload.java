package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server: the player did something only the client sees (a Ring Lab pick: lab.&lt;row&gt;.&lt;value&gt;), so the
 * What's New book can tick it; or {@link #GIVE_BOOK} from the Ring Lab's button.
 */
public record WhatsNewPayload(String trigger) implements CustomPacketPayload {
	public static final String GIVE_BOOK = "book.give";
	public static final CustomPacketPayload.Type<WhatsNewPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("whats_new"));
	public static final StreamCodec<RegistryFriendlyByteBuf, WhatsNewPayload> CODEC =
			ByteBufCodecs.stringUtf8(128).map(WhatsNewPayload::new, WhatsNewPayload::trigger).cast();

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
