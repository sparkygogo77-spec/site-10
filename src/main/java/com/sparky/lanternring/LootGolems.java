package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.GolemPayload;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Loot Golem: a hard-light copper golem that floats along with its owner, picks up item
 * drops around them and, when its sack is full (or its time is up, or the owner sends it home),
 * opens a portal and carries the loot through it into the chest by the owner's Portal exit (see
 * PortalGun). Then it comes back out and carries on. Without a chest by the exit it keeps the
 * loot and hands it back at the owner's feet when it leaves.
 *
 * <p>Like the portals it isn't a real entity: the server moves it here and clients draw it
 * (GolemFx), so it can't be hurt, pushed or left behind in the world.
 */
public final class LootGolems {
	/** Stacks the sack holds before a trip to the chest. */
	public static final int CAPACITY = 27;
	/** How far around its owner it looks for drops. */
	private static final double REACH = 14;
	private static final double SPEED = 0.45;
	/** Ticks it spends inside the portal, filling the chest. */
	private static final int INSIDE = 30;
	/** Dropped items younger than this are left alone, so it doesn't snatch things mid-throw. */
	private static final int MIN_ITEM_AGE = 15;

	private enum State { COLLECT, TO_PORTAL, INSIDE, OUT }

	private static final class Golem {
		final int id;
		final UUID owner;
		ServerLevel level;
		Vec3 pos;
		Vec3 vel = Vec3.ZERO;
		float yaw;
		final List<ItemStack> sack = new ArrayList<>();
		State state = State.COLLECT;
		int stateTicks;
		long until;
		boolean leaving;
		boolean warned;
		Portals.Portal entrance;

		Golem(int id, UUID owner, ServerLevel level, Vec3 pos, float yaw, long until) {
			this.id = id;
			this.owner = owner;
			this.level = level;
			this.pos = pos;
			this.yaw = yaw;
			this.until = until;
		}

		boolean full() {
			return sack.size() >= CAPACITY && sack.stream().allMatch(s -> s.getCount() >= s.getMaxStackSize());
		}

		float fill() {
			return Math.min(1f, sack.size() / (float) CAPACITY);
		}
	}

	private static final Map<UUID, Golem> GOLEMS = new HashMap<>();
	private static int nextId = 1;

	private LootGolems() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(LootGolems::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			// Nothing is lost on the way out: whatever it carries drops where it is.
			for (Golem g : GOLEMS.values()) dropSack(g, g.pos);
			GOLEMS.clear();
		});
	}

	/**
	 * Golem mode: summons the owner's golem, or sends one that's already out home. Returns true
	 * when a new golem came out (and the summon's charge is due).
	 */
	public static boolean use(ServerLevel level, Player player) {
		Golem g = GOLEMS.get(player.getUUID());
		if (g != null) {
			if (!g.leaving) {
				g.leaving = true;
				player.sendOverlayMessage(Component.translatable("message.lanternring.golem_home").withStyle(ChatFormatting.GREEN));
				if (g.state == State.COLLECT && player instanceof ServerPlayer owner) startTrip(g, owner);
			}
			return false;
		}
		Vec3 at = player.getEyePosition().add(player.getLookAngle().multiply(1, 0, 1).normalize().scale(2)).subtract(0, 1, 0);
		g = new Golem(nextId++, player.getUUID(), level, at, player.getYRot(), level.getServer().getTickCount() + RingTuning.GOLEM_LIFETIME.ticks());
		GOLEMS.put(player.getUUID(), g);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(player), at.add(0, 0.6, 0));
		level.playSound(null, at.x, at.y, at.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 1.2f);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.COPPER_GOLEM_SPIN, SoundSource.PLAYERS, 1f, 1.3f);
		player.sendOverlayMessage(Component.translatable(storageFor(player) != null
				? "message.lanternring.golem_out" : "message.lanternring.golem_no_chest").withStyle(ChatFormatting.GREEN));
		return true;
	}

	/** Whether the player has a golem out right now. */
	public static boolean isOut(Player player) {
		return GOLEMS.containsKey(player.getUUID());
	}

	private record Storage(ServerLevel level, PortalExit exit, Container chest) {
	}

	/** The chest by the Portal exit of the first ring the player carries that has one. */
	private static Storage storageFor(Player player) {
		if (!(player.level() instanceof ServerLevel level)) return null;
		for (ItemStack stack : withWorn(player)) {
			if (!(stack.getItem() instanceof PowerRingItem)) continue;
			PortalExit exit = PortalGun.exit(stack);
			if (exit == null) continue;
			ServerLevel exitLevel = level.getServer().getLevel(exit.pos().dimension());
			if (exitLevel == null) continue;
			Container chest = PortalGun.storage(exitLevel, exit.pos().pos());
			if (chest != null) return new Storage(exitLevel, exit, chest);
		}
		return null;
	}

	private static void tick(MinecraftServer server) {
		if (GOLEMS.isEmpty()) return;
		long now = server.getTickCount();
		for (Iterator<Golem> it = GOLEMS.values().iterator(); it.hasNext(); ) {
			Golem g = it.next();
			ServerPlayer owner = server.getPlayerList().getPlayer(g.owner);
			if (owner == null || !owner.isAlive()) {
				// Owner left: whatever it carries drops where it is.
				dropSack(g, g.pos);
				send(g, false, true);
				it.remove();
				continue;
			}
			if (owner.level() != g.level && g.state != State.INSIDE) {
				// Owner went through a portal or changed dimension: it follows.
				send(g, false, true);
				g.level = (ServerLevel) owner.level();
				g.pos = owner.position().add(0, 1.5, 0);
				g.vel = Vec3.ZERO;
			}
			g.stateTicks++;
			if (!step(g, owner, now)) {
				send(g, false, true);
				it.remove();
				continue;
			}
			send(g, g.state != State.INSIDE, false);
		}
	}

	/** Moves one golem a tick; false when it's done for good. */
	private static boolean step(Golem g, ServerPlayer owner, long now) {
		switch (g.state) {
			case COLLECT -> {
				if (now >= g.until && !g.leaving) {
					g.leaving = true;
					startTrip(g, owner);
					return true;
				}
				if (g.leaving && g.sack.isEmpty()) {
					poof(g);
					return false;
				}
				ItemEntity target = g.full() ? null : nearestDrop(g, owner);
				if (target != null) {
					Vec3 aim = target.position().add(0, 0.2, 0);
					fly(g, aim, SPEED);
					if (g.pos.distanceTo(aim) < 1.2) grab(g, target);
				} else {
					// Float just ahead of the owner's right shoulder (in sight in first person), bobbing a little.
					float r = owner.getYRot() * Mth.DEG_TO_RAD;
					Vec3 ahead = new Vec3(-Mth.sin(r), 0, Mth.cos(r));
					Vec3 right = new Vec3(-Mth.cos(r), 0, -Mth.sin(r));
					Vec3 home = owner.position().add(ahead.scale(0.9)).add(right.scale(2.2)).add(0, 1.0 + 0.15 * Math.sin(now * 0.12), 0);
					double d = g.pos.distanceTo(home);
					if (d > 24) g.pos = home;
					fly(g, home, Math.min(SPEED * 2, 0.08 + d * 0.15));
					if (d < 2) g.yaw = Mth.approachDegrees(g.yaw, owner.getYRot(), 10f);
				}
				if (g.full() && !g.warned) startTrip(g, owner);
				else if (g.full() && g.stateTicks % 100 == 0) startTrip(g, owner);
			}
			case TO_PORTAL -> {
				if (g.entrance == null) {
					g.state = State.COLLECT;
					return true;
				}
				fly(g, g.entrance.center, SPEED);
				if (g.pos.distanceTo(g.entrance.center) < 0.5 || g.stateTicks > 80) {
					g.pos = g.entrance.center;
					setState(g, State.INSIDE);
					deposit(g, owner);
				}
			}
			case INSIDE -> {
				if (g.stateTicks >= INSIDE) {
					if (g.leaving) {
						if (g.entrance != null) Portals.close(g.entrance);
						return false;
					}
					// Back out the way it came, toward its owner.
					setState(g, State.OUT);
					g.vel = g.entrance != null ? g.entrance.normal().scale(SPEED) : Vec3.ZERO;
				}
			}
			case OUT -> {
				g.pos = g.pos.add(g.vel);
				if (g.stateTicks > 6) {
					if (g.entrance != null) Portals.close(g.entrance);
					g.entrance = null;
					setState(g, State.COLLECT);
				}
			}
		}
		return true;
	}

	private static void setState(Golem g, State state) {
		g.state = state;
		g.stateTicks = 0;
	}

	/** Opens a portal just ahead of the golem to the chest, and sets off into it. */
	private static void startTrip(Golem g, ServerPlayer owner) {
		Storage storage = storageFor(owner);
		if (storage == null) {
			if (g.leaving) {
				// Nowhere to put it: hand the loot back and go.
				dropSack(g, owner.position().add(0, 0.5, 0));
				poof(g);
				g.sack.clear();
			} else if (!g.warned) {
				g.warned = true;
				owner.sendOverlayMessage(Component.translatable("message.lanternring.golem_full").withStyle(ChatFormatting.YELLOW));
			}
			return;
		}
		if (g.sack.isEmpty()) {
			if (g.leaving) poof(g);
			return;
		}
		// The portal opens two blocks ahead of it (away from the owner), facing it.
		Vec3 away = g.pos.subtract(owner.position()).multiply(1, 0, 1);
		if (away.lengthSqr() < 0.01) away = Portals.normal(g.yaw);
		away = away.normalize();
		Vec3 center = g.pos.add(away.scale(2.2));
		// Its front faces back toward the golem (a yaw's facing is (-sin, cos)).
		float yaw = (float) (Mth.atan2(away.x, -away.z) * Mth.RAD_TO_DEG);
		PortalExit exit = storage.exit();
		Portals.Portal[] pair = Portals.openPair(g.level, center, yaw, storage.level(), exit.center(), exit.yaw(), g.owner, true,
				INSIDE + 100);
		g.entrance = pair[0];
		g.yaw = Mth.wrapDegrees(yaw + 180f);
		setState(g, State.TO_PORTAL);
	}

	/** Empties the sack into the chest by the exit; anything that doesn't fit drops out of the exit portal. */
	private static void deposit(Golem g, ServerPlayer owner) {
		Storage storage = storageFor(owner);
		if (storage == null) return;
		Vec3 out = storage.exit().center().add(Portals.normal(storage.exit().yaw()).scale(0.8));
		int stored = 0;
		boolean spilled = false;
		for (ItemStack stack : g.sack) {
			int before = stack.getCount();
			ItemStack left = HopperBlockEntity.addItem(null, storage.chest(), stack, Direction.UP);
			stored += before - left.getCount();
			if (!left.isEmpty()) {
				spilled = true;
				Containers.dropItemStack(storage.level(), out.x, out.y - 0.6, out.z, left);
			}
		}
		g.sack.clear();
		g.warned = false;
		storage.chest().setChanged();
		Vec3 at = storage.exit().center();
		storage.level().playSound(null, at.x, at.y, at.z, SoundEvents.CHEST_OPEN, SoundSource.BLOCKS, 0.6f, 1.2f);
		storage.level().playSound(null, at.x, at.y, at.z, SoundEvents.CHEST_CLOSE, SoundSource.BLOCKS, 0.6f, 1.2f);
		RingFx.send(storage.level(), Kind.MODE_CHANGE, at.subtract(0, 1, 0));
		owner.sendOverlayMessage(Component.translatable(spilled ? "message.lanternring.golem_stored_full" : "message.lanternring.golem_stored", stored)
				.withStyle(spilled ? ChatFormatting.YELLOW : ChatFormatting.GREEN));
	}

	private static ItemEntity nearestDrop(Golem g, ServerPlayer owner) {
		AABB box = owner.getBoundingBox().inflate(REACH);
		ItemEntity best = null;
		double bestDist = Double.MAX_VALUE;
		for (ItemEntity item : g.level.getEntitiesOfClass(ItemEntity.class, box,
				e -> e.isAlive() && !e.getItem().isEmpty() && e.getAge() >= MIN_ITEM_AGE)) {
			if (!fits(g, item.getItem())) continue;
			double d = item.distanceToSqr(g.pos);
			if (d < bestDist) {
				bestDist = d;
				best = item;
			}
		}
		return best;
	}

	private static boolean fits(Golem g, ItemStack stack) {
		if (g.sack.size() < CAPACITY) return true;
		for (ItemStack s : g.sack) {
			if (s.getCount() < s.getMaxStackSize() && ItemStack.isSameItemSameComponents(s, stack)) return true;
		}
		return false;
	}

	/** Takes as much of a drop as fits in the sack. */
	private static void grab(Golem g, ItemEntity item) {
		ItemStack stack = item.getItem().copy();
		for (ItemStack s : g.sack) {
			if (stack.isEmpty()) break;
			if (ItemStack.isSameItemSameComponents(s, stack) && s.getCount() < s.getMaxStackSize()) {
				int move = Math.min(stack.getCount(), s.getMaxStackSize() - s.getCount());
				s.grow(move);
				stack.shrink(move);
			}
		}
		while (!stack.isEmpty() && g.sack.size() < CAPACITY) {
			int move = Math.min(stack.getCount(), stack.getMaxStackSize());
			g.sack.add(stack.split(move));
		}
		if (stack.isEmpty()) item.discard();
		else item.setItem(stack);
		g.level.playSound(null, g.pos.x, g.pos.y, g.pos.z, SoundEvents.ITEM_PICKUP, SoundSource.PLAYERS, 0.4f, 1.6f);
	}

	private static void fly(Golem g, Vec3 to, double speed) {
		Vec3 d = to.subtract(g.pos);
		double len = d.length();
		Vec3 want = len < 1e-3 ? Vec3.ZERO : d.scale(Math.min(speed, len) / len);
		g.vel = g.vel.lerp(want, 0.3);
		g.pos = g.pos.add(g.vel);
		if (g.vel.horizontalDistanceSqr() > 0.002) {
			float face = (float) (Mth.atan2(g.vel.z, g.vel.x) * Mth.RAD_TO_DEG) - 90f;
			g.yaw = Mth.approachDegrees(g.yaw, face, 15f);
		}
	}

	private static void dropSack(Golem g, Vec3 at) {
		for (ItemStack stack : g.sack) Containers.dropItemStack(g.level, at.x, at.y, at.z, stack);
		g.sack.clear();
	}

	private static void poof(Golem g) {
		RingFx.send(g.level, Kind.MODE_CHANGE, g.pos.subtract(0, 0.5, 0));
		g.level.playSound(null, g.pos.x, g.pos.y, g.pos.z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.PLAYERS, 0.8f, 1.4f);
		g.leaving = true;
		g.state = State.INSIDE;
		g.stateTicks = INSIDE;
		g.entrance = null;
	}

	private static void send(Golem g, boolean visible, boolean gone) {
		GolemPayload payload = new GolemPayload(g.id, g.pos, g.yaw, gone ? -1f : g.fill(), visible && !gone);
		for (ServerPlayer player : PlayerLookup.around(g.level, g.pos, 128)) {
			ServerPlayNetworking.send(player, payload);
		}
	}

	private static java.util.List<ItemStack> withWorn(Player player) {
		java.util.List<ItemStack> all = new java.util.ArrayList<>();
		player.getInventory().forEach(all::add);
		all.add(RingSlot.worn(player));
		return all;
	}
}
