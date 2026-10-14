package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.CombatFxPayload;
import com.sparky.lanternring.net.CombatPayload;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The combat moves J picked in Blender (Chat C, passes 503, 509, 510): the big flight slam (FlightSlams), the
 * flying flurry (FlyingFlurries) and the absorb and return blast (AbsorbBlasts). This holds what they share: the
 * payloads, the blocks their craters take on a schedule (top layer only, never unbreakable blocks, containers or
 * constructs; see PowerLandings.takes), and the effect broadcast.
 */
public final class CombatMoves {
	private record Clear(ServerLevel level, BlockPos pos, int at) {
	}

	private static final List<Clear> PENDING = new ArrayList<>();
	private static int now;

	private CombatMoves() {
	}

	static void register() {
		PayloadTypeRegistry.serverboundPlay().register(CombatPayload.TYPE, CombatPayload.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(CombatFxPayload.TYPE, CombatFxPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(CombatPayload.TYPE, (payload, context) -> {
			ServerPlayer player = context.player();
			switch (payload.action()) {
				case CombatPayload.SLAM -> FlightSlams.dive(player, payload.at(), payload.dir(), Math.round(payload.value()));
				case CombatPayload.SLAM_LAND -> FlightSlams.land(player, payload.at());
				case CombatPayload.ABSORB -> AbsorbBlasts.hold(player, payload.value() > 0);
				default -> {
				}
			}
		});
		ServerTickEvents.END_SERVER_TICK.register(CombatMoves::tick);
		FlightSlams.register();
		FlyingFlurries.register();
		AbsorbBlasts.register();
	}

	/** Server ticks since start, for the schedules. */
	static int now() {
		return now;
	}

	/** The block at pos goes (dissolves to construct pixels, nothing drops) in ticks, if the bearer may change it. */
	static void clear(ServerLevel level, ServerPlayer bearer, BlockPos pos, int ticks) {
		if (level.mayInteract(bearer, pos)) PENDING.add(new Clear(level, pos.immutable(), now + Math.max(0, ticks)));
	}

	/** The charged ring this player carries, or empty. */
	static ItemStack chargedRing(ServerPlayer player) {
		ItemStack ring = RingFlight.findRing(player);
		return !ring.isEmpty() && PowerRingItem.getCharge(ring) > 0 ? ring : ItemStack.EMPTY;
	}

	/** Whether a move leaves this alone: its bearer's pets and construct allies. */
	static boolean spared(Entity e, @Nullable Entity owner) {
		if (e instanceof com.sparky.lanternring.ally.ConstructAlly) return true;
		return e instanceof TamableAnimal pet && owner instanceof LivingEntity o && pet.isOwnedBy(o);
	}

	/** Tells every client near "from" to draw it, in the current corps' colour. */
	static void send(ServerLevel level, CombatFxPayload.Kind kind, Vec3 from, Vec3 to, float value, int variant, @Nullable Player bearer, int target) {
		CombatFxPayload payload = new CombatFxPayload(kind, from, to, value, variant, bearer == null ? -1 : bearer.getId(), target, Corps.current());
		for (ServerPlayer player : PlayerLookup.around(level, from, 128)) ServerPlayNetworking.send(player, payload);
	}

	private static void tick(MinecraftServer server) {
		now++;
		for (Iterator<Clear> it = PENDING.iterator(); it.hasNext(); ) {
			Clear c = it.next();
			if (now < c.at()) continue;
			it.remove();
			BlockState state = c.level().getBlockState(c.pos());
			if (!PowerLandings.takes(c.level(), c.pos(), state)) continue;
			BlockPos up = c.pos().above();
			BlockState above = c.level().getBlockState(up);
			if (!above.isAir() && above.canBeReplaced() && above.getFluidState().isEmpty()) c.level().setBlock(up, Blocks.AIR.defaultBlockState(), 3);
			c.level().setBlock(c.pos(), Blocks.AIR.defaultBlockState(), 3);
		}
		FlightSlams.tick(server);
		FlyingFlurries.tick(server);
		AbsorbBlasts.tick(server);
	}
}
