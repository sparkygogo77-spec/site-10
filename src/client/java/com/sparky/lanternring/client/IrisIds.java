package com.sparky.lanternring.client;

import java.lang.reflect.Method;

/**
 * Iris tags each piece of geometry with the entity, block entity and item being drawn when it is
 * submitted, and shader packs pick a material from those IDs. Geometry the mod submits on its own
 * (outside any entity) picks up whatever was drawn last: under Complementary the falling Anvil took
 * a stale item's material and came out as pale glass (J, 2026-10-14). {@link #cleared} submits with
 * all three IDs at 0, so the pack draws it as a plain lit surface. Without Iris it just runs.
 */
public final class IrisIds {
	private static Object state;
	private static Method getEntity, setEntity, getBlockEntity, setBlockEntity, getItem, setItem;
	private static boolean tried;

	private IrisIds() {
	}

	/** Runs {@code submit} with Iris's current entity, block entity and item IDs cleared, then puts them back. */
	public static void cleared(Runnable submit) {
		if (!SoulSight.shaderPackOn() || !find()) {
			submit.run();
			return;
		}
		int entity, blockEntity, item;
		try {
			entity = (int) getEntity.invoke(state);
			blockEntity = (int) getBlockEntity.invoke(state);
			item = (int) getItem.invoke(state);
			set(0, 0, 0);
		} catch (ReflectiveOperationException | RuntimeException e) {
			state = null;
			submit.run();
			return;
		}
		try {
			submit.run();
		} finally {
			try {
				set(entity, blockEntity, item);
			} catch (ReflectiveOperationException | RuntimeException ignored) {
				state = null;
			}
		}
	}

	private static void set(int entity, int blockEntity, int item) throws ReflectiveOperationException {
		setEntity.invoke(state, entity);
		setBlockEntity.invoke(state, blockEntity);
		setItem.invoke(state, item);
	}

	private static boolean find() {
		if (tried) return state != null;
		tried = true;
		try {
			Class<?> c = Class.forName("net.irisshaders.iris.uniforms.CapturedRenderingState");
			Object s = c.getField("INSTANCE").get(null);
			getEntity = c.getMethod("getCurrentRenderedEntity");
			setEntity = c.getMethod("setCurrentEntity", int.class);
			getBlockEntity = c.getMethod("getCurrentRenderedBlockEntity");
			setBlockEntity = c.getMethod("setCurrentBlockEntity", int.class);
			getItem = c.getMethod("getCurrentRenderedItem");
			setItem = c.getMethod("setCurrentRenderedItem", int.class);
			state = s;
		} catch (ReflectiveOperationException | RuntimeException | LinkageError e) {
			state = null;
		}
		return state != null;
	}
}
