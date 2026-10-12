package com.sparky.lanternring.client.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Hope;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.client.HopeTint;
import com.sparky.lanternring.corps.CorpsGolem;
import net.fabricmc.fabric.api.client.rendering.v1.FabricRenderState;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.IronGolemRenderer;
import net.minecraft.client.renderer.entity.state.IronGolemRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.animal.golem.IronGolem;
import org.jspecify.annotations.Nullable;

/**
 * The Blue Lantern's golems (the Hope Golem and Blue corps golems) as hard light constructs from
 * J's concept sheets: faceted blue crystal plates with bright rims, the emblem on the chest and
 * glowing eyes (tools/hard_light_skins.py). Other iron golems keep the vanilla renderer
 * (EntityRenderDispatcherMixin picks this one only for blue ones).
 */
public class HopeGolemRenderer extends IronGolemRenderer {
	private static final Identifier SKIN = LanternRing.id("textures/entity/hope_golem.png");

	@Nullable
	private static HopeGolemRenderer instance;

	public static class State extends IronGolemRenderState {
	}

	public HopeGolemRenderer(EntityRendererProvider.Context context) {
		super(context);
		instance = this;
	}

	public static @Nullable HopeGolemRenderer forEntity(Entity entity) {
		return instance != null && isBlue(entity) ? instance : null;
	}

	public static @Nullable HopeGolemRenderer forState(Object state) {
		return state instanceof State ? instance : null;
	}

	public static boolean isBlue(Entity entity) {
		if (entity instanceof CorpsGolem cg) return cg.corps() == Corps.BLUE;
		if (!(entity instanceof IronGolem)) return false;
		Hope.Mark mark = entity.getAttached(Hope.MARK);
		return mark != null && mark.golem();
	}

	@Override
	public IronGolemRenderState createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(IronGolem entity, IronGolemRenderState state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		// The skin is blue already; the old all-over blue tint would only darken it.
		((FabricRenderState) state).setData(HopeTint.KEY, 0f);
	}

	@Override
	public Identifier getTextureLocation(IronGolemRenderState state) {
		return SKIN;
	}

	@Override
	protected @Nullable RenderType getRenderType(IronGolemRenderState state, boolean visible, boolean transparent, boolean glowing) {
		// Emissive translucent: lit up under shader packs without the black box "eyes" gives there.
		return visible || transparent ? RenderTypes.entityTranslucentEmissive(SKIN) : null;
	}

	@Override
	protected int getBlockLightLevel(IronGolem entity, BlockPos pos) {
		return 15;
	}
}
