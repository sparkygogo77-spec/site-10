package com.sparky.lanternring.corps;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.sparky.lanternring.LanternRing;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.UUIDUtil;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;
import org.jspecify.annotations.Nullable;

/**
 * Which hawk each player is bonded to (the last one they tamed), saved with the world, so a Hawk
 * Whistle can find it anywhere. When the whistle can't reach the hawk (its chunk isn't loaded, or
 * it's in another dimension) a new one comes to the player in its place, and the old one is
 * listed as replaced: it vanishes the next time it loads, so there's never two.
 */
public final class HawkBonds extends SavedData {
	private final Map<UUID, UUID> bonds = new HashMap<>();
	private final Set<UUID> replaced = new HashSet<>();

	private record Bond(UUID player, UUID hawk) {
		static final Codec<Bond> CODEC = RecordCodecBuilder.create(i -> i.group(
				UUIDUtil.CODEC.fieldOf("player").forGetter(Bond::player),
				UUIDUtil.CODEC.fieldOf("hawk").forGetter(Bond::hawk)).apply(i, Bond::new));
	}

	private static final Codec<HawkBonds> CODEC = RecordCodecBuilder.create(i -> i.group(
			Bond.CODEC.listOf().optionalFieldOf("bonds", List.of()).forGetter(d -> {
				List<Bond> out = new ArrayList<>();
				d.bonds.forEach((p, h) -> out.add(new Bond(p, h)));
				return out;
			}),
			UUIDUtil.CODEC.listOf().optionalFieldOf("replaced", List.of()).forGetter(d -> new ArrayList<>(d.replaced))
	).apply(i, (bonds, replaced) -> {
		HawkBonds d = new HawkBonds();
		for (Bond b : bonds) d.bonds.put(b.player(), b.hawk());
		d.replaced.addAll(replaced);
		return d;
	}));

	static final SavedDataType<HawkBonds> TYPE = new SavedDataType<>(LanternRing.id("hawk_bonds"), HawkBonds::new, CODEC,
			DataFixTypes.SAVED_DATA_COMMAND_STORAGE);

	/**
	 * The whistle: the player's hawk comes to them, flying in if it's loaded in this dimension, or a
	 * new one hatches beside them in its place. Returns what to tell the player.
	 */
	public static net.minecraft.network.chat.Component whistle(ServerLevel level, net.minecraft.server.level.ServerPlayer player) {
		HawkBonds bonds = get(level);
		UUID id = bonds.hawkOf(player.getUUID());
		if (id == null) return net.minecraft.network.chat.Component.translatable("message.lanternring.whistle_none");
		if (level.getEntity(id) instanceof DivingHawk hawk && hawk.isAlive() && hawk.isOwner(player)) {
			hawk.call(player);
			return net.minecraft.network.chat.Component.translatable("message.lanternring.whistle_coming");
		}
		// Somewhere it can't hear (unloaded, or another dimension): it comes as light, and the old one goes.
		for (ServerLevel other : level.getServer().getAllLevels()) {
			if (other != level && other.getEntity(id) instanceof DivingHawk old) old.discard();
		}
		DivingHawk hawk = FlierHighway.DIVING_HAWK.create(level, net.minecraft.world.entity.EntitySpawnReason.MOB_SUMMONED);
		if (hawk == null) return net.minecraft.network.chat.Component.translatable("message.lanternring.whistle_none");
		hawk.snapTo(player.getX(), player.getY() + 5, player.getZ(), player.getYRot(), 0f);
		level.addFreshEntity(hawk);
		bonds.replace(id);
		hawk.tameTo(level, player, false);
		hawk.call(player);
		return net.minecraft.network.chat.Component.translatable("message.lanternring.whistle_coming");
	}

	/** One record for the whole world (kept with the overworld). */
	public static HawkBonds get(ServerLevel level) {
		return level.getServer().overworld().getDataStorage().computeIfAbsent(TYPE);
	}

	void bond(UUID player, UUID hawk) {
		bonds.put(player, hawk);
		setDirty();
	}

	@Nullable
	UUID hawkOf(UUID player) {
		return bonds.get(player);
	}

	/** The old hawk was replaced by a new one: it goes the next time it loads. */
	void replace(UUID oldHawk) {
		replaced.add(oldHawk);
		setDirty();
	}

	/** Whether this hawk was replaced (and forgets it, since the hawk is about to go). */
	boolean replaced(UUID hawk) {
		if (replaced.isEmpty() || !replaced.remove(hawk)) return false;
		setDirty();
		return true;
	}
}
