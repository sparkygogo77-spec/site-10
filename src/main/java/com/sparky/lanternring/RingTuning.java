package com.sparky.lanternring;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import com.sparky.lanternring.item.PowerRingItem;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.util.Mth;

/**
 * Every editable duration in the mod, in seconds, saved to config/lanternring-tuning.json and
 * edited in game from the Ring Lab's Durations page. Code reads a value with {@code ticks()} when
 * it needs it, so edits apply straight away. To add one, declare an {@link Entry} below and add a
 * {@code tuning.lanternring.<key>} line to the lang file; it shows up in the menu by itself.
 *
 * <p>In singleplayer the menu edits the values the integrated server uses. A dedicated server uses
 * its own copy of the file.
 */
public final class RingTuning {
	/** One editable duration. */
	public static final class Entry {
		public final String key;
		public final double defaultSeconds;
		public final double min;
		public final double max;
		/** How much one click of - or + changes it. */
		public final double step;
		private volatile double seconds;

		private Entry(String key, double defaultSeconds, double min, double max, double step) {
			this.key = key;
			this.defaultSeconds = defaultSeconds;
			this.min = min;
			this.max = max;
			this.step = step;
			this.seconds = defaultSeconds;
		}

		public double seconds() {
			return seconds;
		}

		public int ticks() {
			return (int) Math.round(seconds * 20);
		}

		public void set(double value) {
			// Whole ticks only, so repeated clicks don't pile up rounding errors.
			seconds = Mth.clamp(Math.round(value * 20) / 20.0, min, max);
		}

		public void nudge(int clicks) {
			set(seconds + clicks * step);
		}

		public boolean isDefault() {
			return Math.abs(seconds - defaultSeconds) < 1.0e-6;
		}
	}

	private static final List<Entry> ENTRIES = new ArrayList<>();
	private static final Map<RingMode, Entry> COOLDOWNS = new EnumMap<>(RingMode.class);
	/** Values that used to be the default; a saved file holding one of them gets today's default instead. */
	private static final Map<String, Double> OLD_DEFAULTS = new HashMap<>();

	/** How long Bridge (and any other unheld) hard-light blocks last before fading. */
	public static final Entry CONSTRUCT_LIFETIME = entry("construct_lifetime", 10, 1, 120, 1);
	/** How long a Blast tunnel keeps glowing and lighting its walls. 0 turns the light off. */
	public static final Entry BLAST_AFTERGLOW = entry("blast_afterglow", 12, 0, 60, 1);
	/** How long the Blast's drill takes to bore its whole 50-block tunnel. */
	public static final Entry BLAST_DRILL_TIME = entry("blast_drill_time", 1, 0.05, 5, 0.05);
	/** How long to hold right-click in Blast mode for the drill's full 50-block reach. */
	public static final Entry BLAST_CHARGE = entry("blast_charge", 3, 0.25, 10, 0.25);
	/** How long the Red Lantern's Rage Bull (Blast level 4) takes to trot its longest, 80-block run. */
	public static final Entry RAGE_BULL_RUN = entry("rage_bull_run", 20, 2, 60, 1);
	/** The Yellow Lantern's Dread Runner (Blast level 4): its longest, 64-block sprint, how long its fear stays on the ground, and how long its blind takes to fade once you're out of it. */
	public static final Entry DREAD_RUN = entry("dread_run", 9, 1, 30, 0.5);
	public static final Entry DREAD_TRAIL = entry("dread_trail", 10, 1, 120, 1);
	public static final Entry DREAD_BLIND = entry("dread_blind", 3, 0.5, 20, 0.5);
	/** How long a Wall stands. */
	public static final Entry WALL_LIFETIME = entry("wall_lifetime", 30, 1, 120, 1);
	/** How long a construct takes to come apart and pour its light back into the ring when it is let go (see Dismissal). */
	public static final Entry DISMISS_TIME = entry("dismiss_time", 0.4, 0.05, 3, 0.05);
	/** How long the Lasso takes to reel a catch in from its full 32-block reach. */
	public static final Entry LASSO_REEL_TIME = entry("lasso_reel_time", 1, 0.1, 10, 0.1);
	/** How long the Anvil takes to build itself in the air (the anvil; bigger levels take up to 3.5x this). */
	public static final Entry ANVIL_BUILD = entry("anvil_build", 0.25, 0.05, 5, 0.05);
	/** How long the built Anvil hangs in the air before it drops. */
	public static final Entry ANVIL_HANG = entry("anvil_hang", 0.1, 0, 3, 0.05);
	/** How long a fresh Anvil glows bright before it has cooled to clear jade. */
	public static final Entry ANVIL_GLOW = entry("anvil_glow", 1.5, 0, 10, 0.25);
	/** How long the Anvil takes to dig its crater after it lands. */
	public static final Entry ANVIL_CRATER_TIME = entry("anvil_crater_time", 0.5, 0.05, 5, 0.05);
	/** How long the Anvil rests in its crater before it fades. */
	public static final Entry ANVIL_LIFETIME = entry("anvil_lifetime", 8, 1, 120, 1);
	/** How long the Deluge's liquid takes to spread out to its edge after the globe bursts. */
	public static final Entry DELUGE_SPREAD = entry("deluge_spread", 0.75, 0.05, 5, 0.05);
	/** How long the red Lava Deluge's heavy pool takes to roll out to its edge (slower than the green flood). */
	public static final Entry RED_DELUGE_SPREAD = entry("red_deluge_spread", 1.75, 0.05, 5, 0.05);
	/** How long a level 1 Deluge's liquid lasts from the burst, drain included (levels 2 and 3 last 5 and 10 s longer). */
	public static final Entry DELUGE_LIFETIME = entry("deluge_lifetime", 15, 3, 120, 1);
	/** How long the Deluge's liquid takes to drain, outer edge first. */
	public static final Entry DELUGE_DRAIN = entry("deluge_drain", 2, 0.05, 10, 0.25);
	/** How long the Deluge ball's top half takes to dissolve, top surface down, once its bottom tears away. */
	/** How long holding left-click in Deluge mode takes to suck a Deluge back into the ring. */
	public static final Entry DELUGE_RECALL = entry("deluge_recall", 0.35, 0.05, 5, 0.05);
	public static final Entry DELUGE_VANISH = entry("deluge_vanish", 0.2, 0.05, 5, 0.05);
	/** How long the Red Lantern's Flame Ring takes to run out to its edge. */
	public static final Entry FLAME_RING_SPREAD = entry("flame_ring_spread", 1.25, 0.25, 5, 0.25);
	/** How long a mob caught by the Flame Ring takes to melt down into its pool. */
	public static final Entry FLAME_RING_MELT = entry("flame_ring_melt", 1.5, 0.25, 5, 0.25);
	/** How often the Red Lantern's Lava Deluge melts another layer of ground under it (it melts two). */
	public static final Entry LAVA_MELT = entry("lava_melt", 2.25, 0.25, 10, 0.25);
	/** How long the Violet Lantern's Mind Link holds the mobs it links. */
	public static final Entry MIND_LINK_TIME = entry("mind_link_time", 300, 10, 1800, 10);
	/** How long the Violet Lantern's Crystal Prison holds a creature before the crystal shatters. */
	public static final Entry CRYSTAL_PRISON_TIME = entry("crystal_prison_time", 20, 2, 300, 1);
	/** How long the Orange Lantern's Hoard takes to haul every item and orb in to the bearer. */
	public static final Entry HOARD_TIME = entry("hoard_time", 1.5, 0.25, 5, 0.25);
	/** How long the Orange Lantern's Avarice copies of slain mobs fight before they fade. */
	public static final Entry AVARICE_LIFETIME = entry("avarice_lifetime", 60, 10, 600, 10);
	/** How long the Yellow Lantern's Fear lasts on a mob (darkness, Weakness, Slowness, running from you). */
	public static final Entry FEAR_TIME = entry("fear_time", 12, 2, 60, 1);
	/** How long the Yellow Lantern's Brood spiders hunt before they fade back into the dark. */
	public static final Entry BROOD_LIFETIME = entry("brood_lifetime", 25, 3, 120, 1);
	/** How long a Black Hole stays open, pulling, before it collapses. */
	public static final Entry BLACK_HOLE_TIME = entry("black_hole_time", 6, 1, 30, 0.5);
	/** How long holding right-click in Build mode takes to grow the area from smallest to biggest. */
	public static final Entry BUILD_GROW = entry("build_grow", 4, 0.5, 20, 0.5);
	/** How long the Build mode takes to clear and flatten its area (bigger areas take up to 3x this). */
	public static final Entry BUILD_CLEAR = entry("build_clear", 2, 0.05, 10, 0.25);
	/** How long each build takes to rise in green hard light when it's shown (bigger builds take up to 3x this). */
	public static final Entry BUILD_PREVIEW = entry("build_preview", 1, 0.05, 10, 0.25);
	/** How long a chosen build takes to turn from green into its real blocks (bigger builds take up to 4x this). */
	public static final Entry BUILD_FORM = entry("build_form", 5, 0.05, 30, 0.5);
	/** How long to hold left-click and right-click together with the lantern in the off hand before charging starts. */
	public static final Entry CHARGE_HOLD = entry("charge_hold", 0.5, 0.25, 10, 0.25);
	/** How long the ring stays in the lantern before it is full. */
	public static final Entry CHARGE_TIME = entry("charge_time", 12.0, 0.5, 30, 0.25);
	/** Holding on past a full charge: how long the overcharge takes to fill (it burns out battery charges). */
	public static final Entry CHARGE_OVER = entry("charge_over", 1.5, 0.5, 6, 0.25);
	/** How long the ring hand takes to bend, show the ring and press it into the lantern's port (part of the charge time). */
	public static final Entry CHARGE_REACH = entry("charge_reach", 2.5, 0.25, 5, 0.05);
	/** How long the sunlight round a charging ring takes to dim once the lantern is up. */
	public static final Entry CHARGE_DIM_IN = entry("charge_dim_in", 2, 0.25, 10, 0.25);
	/** How long the sunlight takes to come back once the charge ends. */
	public static final Entry CHARGE_DIM_OUT = entry("charge_dim_out", 2.5, 0.25, 10, 0.25);
	/** How long the lantern flashbang takes to clear from someone's eyes once they look away from the charger. */
	public static final Entry LANTERN_FLASH_FADE = entry("lantern_flash_fade", 1.5, 0.25, 10, 0.25);
	/** How quickly the lantern's light winds back down from the blinding flash to its calm resting glow once the ring is full. */
	public static final Entry LANTERN_SETTLE = entry("lantern_settle", 0.6, 0.1, 2.5, 0.05);
	/** Longest gap between the two right-clicks of the double-click that sets the lantern down. */
	public static final Entry LANTERN_DOUBLE_CLICK = entry("lantern_double_click", 0.35, 0.1, 1, 0.05);
	/** How long the second click of that double-click is held before the lantern is set down. */
	public static final Entry LANTERN_PLACE_HOLD = entry("lantern_place_hold", 0.5, 0.1, 3, 0.05);
	/** How long the lantern takes to float in from its slot when summoned (key R), and to break up into light when dismissed. */
	public static final Entry LANTERN_SUMMON = entry("lantern_summon", 0.6, 0.1, 3, 0.05);
	/** How long to hold the lantern key with the lantern summoned to set off its corps' power. */
	public static final Entry LANTERN_POWER_HOLD = entry("lantern_power_hold", 0.4, 0.1, 2, 0.05);
	/** How long the Orange Lantern's Horde keeps crawling up out of the ground (a mob a second: with the rest, 40 a minute)... */
	public static final Entry HORDE_TIME = entry("horde_time", 40, 5, 300, 5);
	/** ...and how long it rests before the next wave, while the lantern stays out. */
	public static final Entry HORDE_COOLDOWN = entry("horde_cooldown", 20, 1, 120, 1);
	/** How long the Red Lantern's rage builds before it self-destructs. */
	public static final Entry RED_SELF_DESTRUCT = entry("red_self_destruct", 2, 0.25, 10, 0.25);
	/** How long the Green Lantern's fortress dome takes to rise around you... */
	public static final Entry FORTRESS_RISE = entry("fortress_rise", 1.5, 0.1, 10, 0.1);
	/** ...and the longest it stands while you hold the key. */
	public static final Entry FORTRESS_TIME = entry("fortress_time", 60, 5, 600, 5);
	/** How long the Blue Lantern's beacon of hope heals and grows things around it. */
	public static final Entry HOPE_BEACON = entry("hope_beacon", 120, 10, 600, 10);
	/** How long monsters charmed by the Violet Lantern stay peaceful. */
	public static final Entry LOVE_CHARM = entry("love_charm", 30, 5, 300, 5);
	/** How often each standing Red sanctuary sends a red ring out to the nearest monster. */
	public static final Entry RED_RING_SEEK = entry("red_ring_seek", 90, 10, 1200, 10);
	/** How long each Horde mob fights before it crumbles back into the ground. */
	public static final Entry HORDE_LIFETIME = entry("horde_lifetime", 60, 10, 600, 10);
	/** How long to hold right-click in Beam mode to fire the big charged beam. */
	public static final Entry BEAM_CHARGE = entry("beam_charge", 1, 0.25, 5, 0.25);
	/** How long the Shockwave takes to charge from its tap size up to double size (hold right-click). */
	public static final Entry SHOCKWAVE_CHARGE = entry("shockwave_charge", 1.5, 0.25, 5, 0.25);
	/** Shortest gap between the small Shockwaves a Beam sets off where it lands. */
	public static final Entry BEAM_SHOCKWAVE_INTERVAL = entry("beam_shockwave_interval", 0.5, 0, 5, 0.25);
	/** How long the Saw takes to roll forward one block while it spins. */
	public static final Entry SAW_BLOCK = entry("saw_block", 0.15, 0.05, 1, 0.05);
	/** How long to hold right-click in Portal mode to set the exit where you look. */
	public static final Entry PORTAL_SET = entry("portal_set", 0.75, 0.25, 5, 0.25);
	/** How long a pair of portals stays open. */
	public static final Entry PORTAL_LIFETIME = entry("portal_lifetime", 15, 2, 120, 1);
	/** How long the Loot Golem collects before it takes the loot to the chest and goes. */
	public static final Entry GOLEM_LIFETIME = entry("golem_lifetime", 120, 10, 900, 10);
	/** How long the Blue Lantern's Renew takes to spread out to its edge. */
	public static final Entry RENEW_SPREAD = entry("renew_spread", 1.5, 0.25, 10, 0.25);
	/** How long the Blue Lantern's builder villagers take to build a house. */
	public static final Entry HOPE_BUILD = entry("hope_build", 20, 1, 300, 1);
	/** How long a blue village waits between houses while its builders are still blue. */
	public static final Entry HOPE_GROW = entry("hope_grow", 120, 10, 1800, 10);
	/** How long the blue villagers take to fade to their normal colours (they stop building then). */
	public static final Entry HOPE_FADE = entry("hope_fade", 900, 30, 7200, 30);
	/** How long a Hope Golem stays before it fades. */
	public static final Entry HOPE_GOLEM_LIFETIME = entry("hope_golem_lifetime", 300, 10, 3600, 10);
	/** How long the Soul Stone remembers a mob that died, so it can bring it back. */
	public static final Entry SOUL_MEMORY = entry("soul_memory", 60, 5, 600, 5);
	/** How long the souls the Soul Stone brings back fight for you before they pass on. */
	public static final Entry SOUL_BOND = entry("soul_bond", 300, 10, 3600, 10);
	/** How long the undead from Raise the Graves take to climb out of the ground. */
	public static final Entry SOUL_GRAVES_RISE = entry("soul_graves_rise", 1.5, 0.25, 10, 0.25);
	/** How long before the Soul Stone can be used again. */
	public static final Entry SOUL_COOLDOWN = entry("soul_cooldown", 5, 0, 120, 1);
	/** How far back the Time Stone's Rewind turns the blocks around you. */
	public static final Entry TIME_REWIND = entry("time_rewind", 30, 5, 300, 5);
	/** How long the Rewind takes to put every block back. */
	public static final Entry TIME_REWIND_PLAY = entry("time_rewind_play", 1.5, 0.05, 10, 0.25);
	/** How long the Time Stone's Freeze holds things still. */
	public static final Entry TIME_FREEZE = entry("time_freeze", 8, 1, 60, 1);
	/** How long before the Time Stone can be used again. */
	public static final Entry TIME_COOLDOWN = entry("time_cooldown", 5, 0, 120, 1);
	/** How long an Army construct lasts on a full share of charge (less on the last of the ring's charge, more crouched). */
	public static final Entry ALLY_LIFETIME = entry("ally_lifetime", 120, 10, 900, 10);
	/** How long a full ring keeps you in the air. */
	public static final Entry FLIGHT_TIME = entry("flight_time",
			PowerRingItem.MAX_CHARGE * 10 / 20.0, 50, 1800, 50);
	/** How long the streak of light behind fast flight takes to fade (client side, see FlightTrail). */
	public static final Entry FLIGHT_TRAIL = entry("flight_trail", 0.25, 0.05, 2, 0.05);
	/** How long the ground flight barrier's imprint stays on a wall before it is gone (client side, see GroundFlight). */
	public static final Entry GROUND_IMPRINT = entry("ground_imprint", 5, 0.5, 30, 0.5);
	/** How long you must fly fast before the ram barrier forms ahead of you (see RamBarrier). */
	public static final Entry RAM_BARRIER_FORM = entry("ram_barrier_form", 1.75, 0.25, 10, 0.25);
	/** How long after the ram barrier shatters on a wall before it can form again. */
	public static final Entry RAM_BARRIER_COOLDOWN = entry("ram_barrier_cooldown", 2, 0, 60, 0.5);
	/** Corps villages and Red sky outposts (see corps/CorpsVillager and corps/SkyRaider). */
	public static final Entry LANTERN_OATH = entry("lantern_oath", 5, 1, 60, 1);
	public static final Entry CORPS_BUILD = entry("corps_build", 30, 5, 600, 5);
	public static final Entry CORPS_BUILD_TIME = entry("corps_build_time", 20, 2, 120, 2);
	public static final Entry CORPS_GOLEM = entry("corps_golem", 60, 10, 900, 10);
	public static final Entry CORPS_RIVAL = entry("corps_rival", 300, 10, 3600, 10);
	public static final Entry CORPS_RAID = entry("corps_raid", 180, 20, 3600, 10);
	public static final Entry CORPS_RAIDER_CALL = entry("corps_raider_call", 45, 5, 600, 5);
	/** Blue Lantern villagers in a fight (see corps/BlueCombat): time between ring attacks, and how long they swing a lassoed mob before flinging it. */
	public static final Entry BLUE_ATTACK = entry("blue_attack", 1.5, 0.25, 10, 0.25);
	public static final Entry BLUE_LASSO_SWING = entry("blue_lasso_swing", 1.5, 0.5, 10, 0.5);
	/** The Blue Lantern rescue squad (see corps/BlueSquad): how long a lantern rests before a village under attack can call another squad out of it. */
	public static final Entry BLUE_SQUAD_REST = entry("blue_squad_rest", 60, 5, 900, 5);
	/** The Blue Lantern sky city (see city/BlueCity): how long one piece takes to form, and how long its hard light glows before it sets into Skystone. */
	public static final Entry CITY_PIECE = entry("city_piece", 30, 5, 300, 5);
	public static final Entry CITY_SET = entry("city_set", 3, 0.5, 30, 0.5);
	/** The Red Lantern sanctuary (see corps/RedSanctuary): the blood orb forming and falling, the spire forming top to bottom, and how long each block stays blood before it sets. */
	public static final Entry SANCTUARY_ORB = entry("sanctuary_orb", 4, 1, 30, 0.5);
	public static final Entry SANCTUARY_BUILD = entry("sanctuary_build", 25, 5, 300, 5);
	public static final Entry SANCTUARY_BLOOD = entry("sanctuary_blood", 3, 0.5, 20, 0.5);
	/** The Yellow Fear Nuke (see corps/FearNuke): the orb forming and falling, how long it sits drinking in the fear before it goes off, and how long its Dread takes to kill. */
	public static final Entry FEAR_NUKE_ORB = entry("fear_nuke_orb", 2, 1, 20, 0.5);
	public static final Entry FEAR_NUKE_CONSUME = entry("fear_nuke_consume", 1.5, 0.5, 30, 0.5);
	public static final Entry FEAR_DREAD = entry("fear_dread", 30, 5, 300, 5);
	/** How long the Fear Nuke's yellow aura takes to sweep out and incinerate everything near the blast. */
	public static final Entry FEAR_NUKE_BURN = entry("fear_nuke_burn", 0.6, 0.1, 5, 0.1);
	/** The Fear Nuke built in the ring hand: how long it takes to build, how long its Fear Frenzy lasts, how long a construct weapon from the gas lasts, and how long the yellow gas lingers. */
	public static final Entry FEAR_NUKE_BUILD = entry("fear_nuke_build", 3, 0.5, 20, 0.5);
	/** Not a time: how many blocks the bearer may stray from the Fear Nuke forming in the sky before it breaks apart. */
	public static final Entry FEAR_NUKE_RANGE = entry("fear_nuke_range", 30, 10, 100, 5);
	public static final Entry FEAR_FRENZY = entry("fear_frenzy", 30, 5, 300, 5);
	public static final Entry FEAR_WEAPON = entry("fear_weapon", 30, 5, 300, 5);
	public static final Entry FEAR_GAS = entry("fear_gas", 20, 5, 300, 5);
	/** How long the 1911 takes to reload its magazine. */
	public static final Entry PISTOL_RELOAD = entry("pistol_reload", 1.5, 0.25, 10, 0.25);
	/** The Blue Hope Drop (see corps/HopeDrop): the fall, how long it shows as hard light, how long it takes to set into Hope Bricks, and how often a Blue villager may drop one in a raid. */
	public static final Entry HOPE_DROP_FALL = entry("hope_drop_fall", 1.5, 0.5, 10, 0.25);
	public static final Entry HOPE_DROP_LIGHT = entry("hope_drop_light", 2, 0.5, 20, 0.5);
	public static final Entry HOPE_DROP_SET = entry("hope_drop_set", 3, 0.5, 30, 0.5);
	public static final Entry HOPE_DROP_VILLAGER = entry("hope_drop_villager", 45, 5, 600, 5);
	/** The Orange Hoard Rain (see corps/HoardRain): how long the hoard keeps falling, and how long each piece lies before it fades. */
	public static final Entry HOARD_RAIN = entry("hoard_rain", 3, 0.5, 20, 0.5);
	public static final Entry HOARD_LINGER = entry("hoard_linger", 5, 1, 60, 1);
	/** The Hammer leap (see HammerSlams): how far you can aim the landing, in blocks (J: 24, up to 40). */
	public static final Entry HAMMER_RANGE = entry("hammer_range", 24, 8, 40, 4);
	/** Super sprint (see SuperJumps): how long a sprint takes to build up to top speed. */
	public static final Entry SUPER_SPRINT_BUILD = entry("super_sprint_build", 2.5, 0.25, 10, 0.25);
	/** The super jump: how long you must sprint before a jump goes super, and until it's fully charged (85 blocks). */
	public static final Entry SUPER_JUMP_ARM = entry("super_jump_arm", 0.75, 0.05, 5, 0.05);
	public static final Entry SUPER_JUMP_CHARGE = entry("super_jump_charge", 4, 0.5, 20, 0.25);
	/** How long left-click is held in the air to prime the ring for a bigger landing. */
	public static final Entry SUPER_JUMP_PRIME = entry("super_jump_prime", 0.5, 0.05, 3, 0.05);
	/** How long the superhero landing pose holds before you stand up. */
	public static final Entry SUPER_LANDING = entry("super_landing", 0.8, 0.1, 3, 0.05);
	/** Omega beams (see OmegaBeams): E2 smoulder's build-up, E4 crackle's arcs, how long a burnt creature glows before it crumbles, and the longest a beam chases. */
	public static final Entry OMEGA_SMOULDER = entry("omega_smoulder", 1, 0.1, 3, 0.05);
	public static final Entry OMEGA_CRACKLE = entry("omega_crackle", 0.5, 0.1, 2, 0.05);
	public static final Entry OMEGA_EMBERS = entry("omega_embers", 1, 0.25, 4, 0.05);
	public static final Entry OMEGA_CHASE = entry("omega_chase", 8, 1, 30, 0.5);
	/** The pass 403 double-jump take-off: the standing puff up to the hover (S1, 3 ticks) and the running dart's arc (R3, 6 ticks). */
	public static final Entry TAKEOFF_PUFF = entry("takeoff_puff", 0.15, 0.05, 1, 0.05);
	public static final Entry TAKEOFF_ARC = entry("takeoff_arc", 0.3, 0.1, 1.5, 0.05);
	/** The L2 soft landing (pass 403): the eased descent (8 ticks) and the run-out after touchdown (12 ticks). */
	public static final Entry SOFT_LANDING_DESCENT = entry("soft_landing_descent", 0.4, 0.1, 2, 0.05);
	public static final Entry SOFT_LANDING_RUNOUT = entry("soft_landing_runout", 0.6, 0, 3, 0.05);
	/** How far the ring arm leads the body in flight (pass 404: 1.6 ticks, 0.08 s). */
	public static final Entry ARM_LEAD = entry("arm_lead", 0.08, 0, 0.15, 0.05);

	static {
		for (RingMode mode : RingMode.values()) {
			// No cooldowns by default: each mode fires as fast as you click until one is set in the menu.
			Entry cooldown = entry("cooldown." + mode.name().toLowerCase(), 0, 0, 10, 0.25);
			COOLDOWNS.put(mode, cooldown);
			OLD_DEFAULTS.put(cooldown.key, mode.cooldown / 20.0);
		}
		// Crouch + hold used to take 0.75 s; holding both clicks takes 0.5 s.
		OLD_DEFAULTS.put(CHARGE_HOLD.key, 0.75);
		// The super jump was charged by crouching (0.35 s to arm, 1.25 s to full); J wanted it charged by sprinting.
		OLD_DEFAULTS.put(SUPER_JUMP_ARM.key, 0.35);
		OLD_DEFAULTS.put(SUPER_JUMP_CHARGE.key, 1.25);
		// The ram barrier formed after 2 s of fast flight; J asked for 1.75 s.
		OLD_DEFAULTS.put(RAM_BARRIER_FORM.key, 2.0);
		// And waited 5 s after shattering; J picked 2 s.
		OLD_DEFAULTS.put(RAM_BARRIER_COOLDOWN.key, 5.0);
		// Charging in the lantern took 4.5 s, then 6 s; J picked G3 R4's full 12 s from Blender.
		OLD_DEFAULTS.put(CHARGE_TIME.key, 6.0);
		// The ring hand reached the port in 0.9 s; G3 R4's ring takes 2.5 s to fly in and seat.
		OLD_DEFAULTS.put(CHARGE_REACH.key, 0.9);
		// The Dread Runner sprinted its 64 blocks in 5 s; J: not TOO fast. 9 s is about 7 blocks a second.
		OLD_DEFAULTS.put(DREAD_RUN.key, 5.0);
		// The Deluge's liquid used to stay 10 s after it spread; now 15 s in all at level 1.
		OLD_DEFAULTS.put(DELUGE_LIFETIME.key, 10.0);
		// J: the Fear Nuke took too long to go off (3 s orb + 4 s consume); now 2 s + 1.5 s.
		OLD_DEFAULTS.put(FEAR_NUKE_ORB.key, 3.0);
		OLD_DEFAULTS.put(FEAR_NUKE_CONSUME.key, 4.0);
		// J: the Anvil hung too long before falling; it built in 0.4 s, now 0.25 s.
		OLD_DEFAULTS.put(ANVIL_BUILD.key, 0.4);
		// Mind Link used to hold mobs for 60 s; now 5 minutes.
		OLD_DEFAULTS.put(MIND_LINK_TIME.key, 60.0);
	}

	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

	private RingTuning() {
	}

	private static Entry entry(String key, double seconds, double min, double max, double step) {
		Entry entry = new Entry(key, seconds, min, max, step);
		ENTRIES.add(entry);
		return entry;
	}

	public static List<Entry> entries() {
		return Collections.unmodifiableList(ENTRIES);
	}

	/** Ticks before the ring can be used again after this mode. */
	public static int cooldownTicks(RingMode mode) {
		return COOLDOWNS.get(mode).ticks();
	}

	/** Ticks of flight per point of charge. */
	public static int flightDrainInterval() {
		return Math.max(1, Math.round(FLIGHT_TIME.ticks() / (float) PowerRingItem.MAX_CHARGE));
	}

	public static void resetAll() {
		for (Entry entry : ENTRIES) entry.set(entry.defaultSeconds);
	}

	/** Changed values, one per line, for the Ring Lab report. Empty if nothing was changed. */
	public static String report() {
		StringBuilder out = new StringBuilder();
		for (Entry entry : ENTRIES) {
			if (!entry.isDefault()) {
				out.append("- ").append(entry.key).append(": ").append(format(entry.seconds()))
						.append("s (default ").append(format(entry.defaultSeconds)).append("s)\n");
			}
		}
		return out.toString();
	}

	public static String format(double seconds) {
		String text = String.format(Locale.ROOT, "%.2f", seconds);
		return text.replaceAll("\\.?0+$", "");
	}

	private static Path file() {
		return FabricLoader.getInstance().getConfigDir().resolve("lanternring-tuning.json");
	}

	static void load() {
		Path path = file();
		if (!Files.exists(path)) return;
		try (Reader reader = Files.newBufferedReader(path)) {
			Map<String, Double> values = GSON.fromJson(reader, new TypeToken<Map<String, Double>>() { }.getType());
			if (values == null) return;
			for (Entry entry : ENTRIES) {
				Double value = values.get(entry.key);
				Double old = OLD_DEFAULTS.get(entry.key);
				if (old != null && value != null && Math.abs(value - old) < 1.0e-6) continue;
				if (value != null && Double.isFinite(value)) entry.set(value);
			}
		} catch (IOException | RuntimeException e) {
			LanternRing.LOGGER.warn("Couldn't read {}, using default durations", path, e);
		}
	}

	public static void save() {
		Map<String, Double> values = new LinkedHashMap<>();
		for (Entry entry : ENTRIES) values.put(entry.key, entry.seconds());
		try (Writer writer = Files.newBufferedWriter(file())) {
			GSON.toJson(values, writer);
		} catch (IOException e) {
			LanternRing.LOGGER.warn("Couldn't save {}", file(), e);
		}
	}
}
