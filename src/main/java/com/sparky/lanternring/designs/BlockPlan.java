package com.sparky.lanternring.designs;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/**
 * A structure designed in J's Blender and exported as a block plan (tools/blender_plan.py writes
 * data/lanternring/plans/*.plan from the lead Blender chat's JSON). Positions are in blocks round the
 * structure's centre, with y = 0 its floor; each part keeps its blocks bottom layer first. Read once
 * and shared by the server (which places them) and the client (which draws the moving parts).
 */
public final class BlockPlan {
	/** One block of a part: its offset from the centre and what goes there. */
	public record Entry(int x, int y, int z, BlockState state) {
	}

	/** A named part, and whether it moves (drawn as a spinning model instead of placed). */
	public record Part(String name, boolean moving, List<Entry> blocks) {
	}

	private static final Map<String, BlockPlan> CACHE = new LinkedHashMap<>();

	private final Map<String, Part> parts = new LinkedHashMap<>();

	private BlockPlan() {
	}

	/** The plan data/lanternring/plans/{name}.plan, loaded once. */
	public static synchronized BlockPlan get(String name) {
		return CACHE.computeIfAbsent(name, BlockPlan::load);
	}

	public Part part(String name) {
		Part p = parts.get(name);
		if (p == null) throw new IllegalArgumentException("no part " + name);
		return p;
	}

	public Iterable<Part> parts() {
		return parts.values();
	}

	private static BlockPlan load(String name) {
		BlockPlan plan = new BlockPlan();
		String path = "/data/" + LanternRing.MOD_ID + "/plans/" + name + ".plan";
		try (InputStream in = BlockPlan.class.getResourceAsStream(path)) {
			if (in == null) throw new IllegalStateException("missing " + path);
			BufferedReader r = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8));
			List<BlockState> palette = new ArrayList<>();
			List<Entry> current = null;
			String line;
			while ((line = r.readLine()) != null) {
				if (line.isEmpty() || line.startsWith("#")) continue;
				String[] f = line.split(" ");
				if (f[0].equals("block")) {
					palette.add(Integer.parseInt(f[1]), state(f[2]));
				} else if (f[0].equals("part")) {
					current = new ArrayList<>();
					plan.parts.put(f[1], new Part(f[1], f[2].equals("1"), current));
				} else if (current != null) {
					current.add(new Entry(Integer.parseInt(f[0]), Integer.parseInt(f[1]), Integer.parseInt(f[2]), palette.get(Integer.parseInt(f[3]))));
				}
			}
		} catch (IOException e) {
			throw new IllegalStateException("can't read " + path, e);
		}
		return plan;
	}

	/** A block id, with an optional [corps=...] for the corps-coloured construct blocks. */
	private static BlockState state(String id) {
		String corps = null;
		int b = id.indexOf('[');
		if (b >= 0) {
			corps = id.substring(id.indexOf('=', b) + 1, id.length() - 1);
			id = id.substring(0, b);
		}
		Block block = BuiltInRegistries.BLOCK.getValue(Identifier.parse(id));
		BlockState state = block.defaultBlockState();
		if (corps != null && state.hasProperty(Corps.PROPERTY)) {
			for (Corps c : Corps.values()) {
				if (c.getSerializedName().equals(corps)) state = state.setValue(Corps.PROPERTY, c);
			}
		}
		return state;
	}
}
