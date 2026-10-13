package com.sparky.lanternring;

import com.sparky.lanternring.block.LightConstructBlock;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;

/**
 * The Green Lantern's power (J, 2026-10-13: "Lantern fortress"): with the green lantern summoned,
 * hold the lantern key and a big dome of hard light rises up out of the ground around you, ring by
 * ring over {@link RingTuning#FORTRESS_RISE}. It stands where it rose for as long as you keep holding
 * the key (at most {@link RingTuning#FORTRESS_TIME}), then comes apart into your ring. It only fills
 * open space: nothing is dug out.
 */
public final class GreenFortress {
	public static final int RADIUS = 8;

	private static final class Fortress {
		final ServerLevel level;
		final long started;
		/** Every block of the dome's shell, lowest first. */
		final List<BlockPos> shell;
		final Set<BlockPos> placed = new HashSet<>();

		Fortress(ServerLevel level, long started, List<BlockPos> shell) {
			this.level = level;
			this.started = started;
			this.shell = shell;
		}
	}

	private static final Map<UUID, Fortress> FORTS = new HashMap<>();

	private GreenFortress() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(GreenFortress::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Fortress f : FORTS.values()) {
				for (BlockPos pos : f.placed) {
					if (f.level.isLoaded(pos) && f.level.getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) ReplacedBlocks.restore(f.level, pos);
				}
			}
			FORTS.clear();
		});
	}

	public static boolean standing(ServerPlayer player) {
		return FORTS.containsKey(player.getUUID());
	}

	/** True for a block of a fortress that is still held up. */
	public static boolean isLive(ServerLevel level, BlockPos pos) {
		for (Fortress f : FORTS.values()) {
			if (f.level == level && f.placed.contains(pos)) return true;
		}
		return false;
	}

	/** Holding the key: the dome rises around where you stand. */
	static void start(ServerPlayer player) {
		if (standing(player)) return;
		ServerLevel level = player.level();
		FORTS.put(player.getUUID(), new Fortress(level, level.getGameTime(), shell(player.blockPosition())));
		player.sendOverlayMessage(Component.translatable("message.lanternring.fortress").withStyle(ChatFormatting.GREEN));
		level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.2f, 0.7f);
		level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.5f, 0.6f);
	}

	/** Letting go of the key (or dismissing the lantern): the dome comes apart into the ring. */
	public static void stop(ServerPlayer player) {
		Fortress f = FORTS.remove(player.getUUID());
		if (f != null) dismiss(f, player);
	}

	private static void dismiss(Fortress f, ServerPlayer player) {
		Dismissal.blocks(f.level, player, f.placed, s -> s.is(ModRegistry.LIGHT_CONSTRUCT));
		f.placed.clear();
	}

	/** A hemisphere of shell blocks around {@code feet}, sorted bottom to top so it rises in rings. */
	private static List<BlockPos> shell(BlockPos feet) {
		List<BlockPos> shell = new ArrayList<>();
		Vec3 c = Vec3.atBottomCenterOf(feet);
		for (int dx = -RADIUS - 1; dx <= RADIUS + 1; dx++) {
			for (int dy = 0; dy <= RADIUS + 1; dy++) {
				for (int dz = -RADIUS - 1; dz <= RADIUS + 1; dz++) {
					BlockPos pos = feet.offset(dx, dy, dz);
					double d = Vec3.atBottomCenterOf(pos).distanceTo(c);
					if (d >= RADIUS - 0.5 && d < RADIUS + 0.5) shell.add(pos);
				}
			}
		}
		shell.sort((a, b) -> Integer.compare(a.getY(), b.getY()));
		return shell;
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Fortress>> it = FORTS.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Fortress> e = it.next();
			Fortress f = e.getValue();
			ServerPlayer player = server.getPlayerList().getPlayer(e.getKey());
			long t = f.level.getGameTime() - f.started;
			if (player == null || !player.isAlive() || player.level() != f.level || !LanternSlot.out(player)
					|| t > Math.max(1, RingTuning.FORTRESS_TIME.ticks())) {
				it.remove();
				dismiss(f, player);
				continue;
			}
			rise(f, player, t);
		}
	}

	/** Fills the shell up to the height it has risen to, retrying spots something was standing in. */
	private static void rise(Fortress f, ServerPlayer player, long t) {
		int bottom = f.shell.getFirst().getY();
		float k = Math.min(1f, (t + 1) / (float) Math.max(1, RingTuning.FORTRESS_RISE.ticks()));
		int top = bottom + (int) Math.ceil((RADIUS + 1) * k);
		BlockState inner = Corps.GREEN.tint(ModRegistry.LIGHT_CONSTRUCT.defaultBlockState()).setValue(LightConstructBlock.HELD, true);
		BlockState rim = inner.setValue(LightConstructBlock.RIM, true);
		int newly = 0;
		for (BlockPos pos : f.shell) {
			if (pos.getY() > top) break;
			if (f.placed.contains(pos)) continue;
			// The bottom ring glows like a wall's outline.
			BlockState want = pos.getY() <= bottom ? rim : inner;
			BlockState was = f.level.getBlockState(pos);
			if (!was.canBeReplaced() || !f.level.mayInteract(player, pos) || !f.level.isUnobstructed(want, pos, CollisionContext.empty())) continue;
			ReplacedBlocks.remember(f.level, pos, was);
			// Register before placing, so the block's own check finds it.
			f.placed.add(pos.immutable());
			f.level.setBlock(pos, want, 3);
			newly++;
		}
		if (newly > 0 && t % 3 == 0) {
			f.level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 0.8f + k * 0.8f);
		}
	}
}
