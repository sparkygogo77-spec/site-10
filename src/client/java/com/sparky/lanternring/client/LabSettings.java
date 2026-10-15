package com.sparky.lanternring.client;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.RingTuning;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.function.BiConsumer;
import java.util.function.Function;
import net.fabricmc.loader.api.FabricLoader;

/**
 * Ring Lab: which version of each look is active, and how the player rated each version.
 * Saved to config/lanternring-lab.json. Later these become the mod's real settings.
 */
public final class LabSettings {
	public enum RingModel { FORGED, CREST, CREST_GOLD, BEACON, EMBLEM, SIGNET, SLIM, LANTERN, CROWN, SQUARE,
		/** J's square emblem picks from Blender pass 596 (P03 is the default): see tools/square_ring_r2.py. */
		P03, N01, N04, R19D, R12B, R12C, R16A }
	/** The Power Battery's look: the Torus Core, Nebula and Compact Unit concepts, the Dark Lantern or J's keychain lantern. */
	public enum LanternModel { STONE, CLASSIC, TORUS, NEBULA, COMPACT, DARK, KEYCHAIN }
	/** How the lantern is carried and used to charge the ring (see LanternFirstPerson and LanternShrine). */
	public enum ChargeStyle {
		HAND, SHRINE, FLOAT, HIP, SUMMON, LEAN, PUSH, KNEEL;

		/** True when the off hand holds the lantern by its handle. */
		public boolean inHand() {
			return this == HAND || this == HIP || this == SHRINE || this == LEAN || this == PUSH || this == KNEEL;
		}

		/** True when the lantern is set down in the world to charge (see LanternShrine). */
		public boolean grounded() {
			return this == SHRINE || this == LEAN || this == PUSH || this == KNEEL;
		}
	}
	/** How big the lantern stands once set down to charge (J's charge takes and the shrine). */
	public enum SetDownSize { BLOCK, HAND }
	public enum HandPose { RING_FORWARD, KNUCKLES_IN, FIST_DOWN, KNUCKLES_FORWARD, FLAT_ITEM }
	public enum RingGlow { OFF, MOTES, DRIPS, AURA }
	/** What the ring looks like as it charges in the lantern (see BeamChargeGlow.renderSun). */
	public enum LanternSun { INFLOW, SUN }
	public enum UseFx { LINE, HELIX, HELIX_RECALL, SHARDS }
	/**
	 * The Beam's look: HELIX keeps today's (the Beam / tether row), the rest are J's eight lasers from Blender pass 836
	 * (docs/handoff/2026-10-15-laser-test-picks, drawn by LaserBeams). Only the look changes.
	 */
	public enum BeamLook {
		HELIX, H3_BRAID, N1_NEEDLE, N2_LAYERED, N3_CRACKLE, P1_PULSES, C1_WEAVE, C2_BRICK, C3_HEX_TUBE,
		// J's KEEPs from pass 834 (a new laser) and pass 830 (ring beam round 3), 2026-10-15
		L1_LANCE, L2_CONSTRUCT_LANCE, T2_BRICK_FLOW, T3_WEAVE_FLOW, T4_RIPPLE_FLOW, T5_HEX_FLOW, T6_DOUBLE_HELIX
	}
	public enum BlastFx { RINGS, BEAM, SCORCH }
	public enum FlightFx { OFF, TRAIL, JETS, HALO }
	public enum BlockGlow { OFF, CONSTRUCTS, NEARBY }
	public enum Strength { SUBTLE, NORMAL, INTENSE }
	public enum Rating { NONE, KEEP, IMPROVE, DROP }
	/**
	 * J's construct texture picks (Blender rounds, 2026-10-13): which animated strip each kind of construct
	 * shows (see ConstructLooks). {@code strip} names textures/block/construct_ripples_&lt;strip&gt;; null keeps
	 * the construct's own model (R2 K1 from the jade pack, or the classic glass and bricks).
	 */
	public enum ConstructLook {
		W1_NEON("w1_neon"), R2K1(null), H1_NEON("h1_neon"), H2_NEON("h2_neon"), HW_EMERALD("hw_emerald"),
		D1_NEON("d1_neon"), W1_EMERALD("w1_emerald"),
		// Round 6 picks to test (2026-10-13): X5 quantum ripple, X3 power aura, X1 cosmic dust
		X5_EMERALD("green_x5_emerald"), X5_NEON("green_x5_neon"), X3_EMERALD("green_x3_emerald"), X1_EMERALD("green_x1_emerald"),
		// J's pick (2026-10-14): X3 with finer wisps, drawn like glass (each pixel solid or clear, no blending)
		X3D1_EMERALD("green_x3d1_emerald", true);

		public final String strip;
		/** Drawn cutout like glass: every texel solid or clear, so no blending, sorting or stacked haze. */
		public final boolean glass;

		ConstructLook(String strip) {
			this(strip, false);
		}

		ConstructLook(String strip, boolean glass) {
			this.strip = strip;
			this.glass = glass;
		}
	}
	public enum WallLook {
		BR1_JADE("br1_jade"), BR1_EMERALD("br1_emerald"), BR1_LIME("br1_lime"), BR1_NEON("br1_neon"),
		BR1_FOREST("br1_forest"), BRD_NEON("brd_neon"), CLASSIC(null);

		public final String strip;

		WallLook(String strip) {
			this.strip = strip;
		}
	}
	/**
	 * The Blue Lantern's constructs. B1-B3 are J's Blender picks to test (2026-10-13) and cover Walls too;
	 * with H1 the Walls take BR1 blue; CLASSIC is the hue-shifted glass and bricks.
	 */
	public enum BlueLook {
		B1("blue_b1"), B2("blue_b2"), B3("blue_b3"), H1("h1_blue"), BR1("br1_blue");

		public final String strip;

		BlueLook(String strip) {
			this.strip = strip;
		}
	}
	/** How see-through constructs are (J: about half; the Blue hex Dome is the reference). */
	public enum ConstructOpacity {
		P20(0.2f), P30(0.3f), P40(0.4f), P50(0.5f), P60(0.6f), P70(0.7f), P80(0.8f), P90(0.9f), P100(1f);

		public final float alpha;

		ConstructOpacity(float alpha) {
			this.alpha = alpha;
		}
	}
	/** Yellow constructs and Walls; Y1-Y3 are J's Blender picks (2026-10-13): "all 3 yellow walls as options for now". */
	public enum YellowLook {
		Y1("yellow_y1"), Y2("yellow_y2"), Y3("yellow_y3"),
		// J (2026-10-14): yellow reskins of the confirmed green looks in place of G2N and N3
		W1("w1_yellow"), H1("h1_yellow"), HW("hw_yellow");

		public final String strip;

		YellowLook(String strip) {
			this.strip = strip;
		}
	}
	/** Red constructs and Walls (J's Blender picks, 2026-10-13): R1 magma, R2 bloodfire. */
	public enum RedLook {
		R1("red_r1"), R2("red_r2");

		public final String strip;

		RedLook(String strip) {
			this.strip = strip;
		}
	}
	/** The Red corps' lantern: the final rage battery from Blender (2026-10-13) or the classic gold-framed one. */
	public enum RedLantern { NEW, CLASSIC }
	/** The Nebula battery's light (Blender pass 430, J's picks 2026-10-14): L1 column or L4 core in a turning cage, wrapped in the green construct look. */
	public enum NebulaLight { L1, L4 }
	/** The Blast's drill: the classic flutes, or J's Blender drills (2026-10-14) D1 auger, D2 tiered, D3 crystal. */
	public enum DrillModel {
		CLASSIC("blast_drill"), D1_AUGER("blast_drill_d1"), D2_TIERED("blast_drill_d2"), D3_CRYSTAL("blast_drill_d3");

		public final String model;

		DrillModel(String model) {
			this.model = model;
		}
	}
	/**
	 * The surface green constructs (Walls, Domes, barriers) show: the picked construct and Wall looks, or one of
	 * J's particle-barrier strips from Blender (2026-10-13), a faint shell with construct pixels drifting on it.
	 */
	public enum BarrierSurface {
		PICKED(null), T1("barrier_t1"), T2("barrier_t2"), T3("barrier_t3"), T5("barrier_t5"), T6("barrier_t6"), T7("barrier_t7"), T9("barrier_t9");

		public final String strip;

		BarrierSurface(String strip) {
			this.strip = strip;
		}
	}
	/**
	 * The Army's Pig construct (Blender pass 828, J kept both, 2026-10-15): the construct texture it wears, stretched
	 * over each face of the vanilla pig at 88% (see ConstructSkins.stretched). {@code strip} names
	 * textures/block/construct_ripples_&lt;strip&gt;.
	 */
	public enum ConstructPig {
		P2("h1_neon"), P3("w1_neon");

		public final String strip;

		ConstructPig(String strip) {
			this.strip = strip;
		}
	}
	/**
	 * Light round block constructs (Blender pass 305, J kept D2, 2026-10-15; see ConstructRays): D2 is pass 304's L2
	 * shafts with the detail, every side glowing out to 4 blocks, rows of narrow beams from every side fading out
	 * by 6 blocks, and dust motes drifting in the light. OFF is how constructs looked before.
	 */
	public enum ConstructRays { D2, OFF }
	/** Violet constructs and Walls (J's Blender picks, 2026-10-13): V1 crystal, V3 silk. */
	public enum VioletLook {
		V1("violet_v1"), V3("violet_v3");

		public final String strip;

		VioletLook(String strip) {
			this.strip = strip;
		}
	}
	public enum SoulSightMode { PLAYERS_AND_MOBS, PLAYERS, OFF }
	/** The light building on the ring hand while the Beam charges (see BeamChargeGlow). */
	public enum ChargeGlow {
		SWIRL_AND_MOTES, SWIRL, MOTES, OFF;

		public boolean swirl() {
			return this == SWIRL_AND_MOTES || this == SWIRL;
		}

		public boolean motes() {
			return this == SWIRL_AND_MOTES || this == MOTES;
		}
	}
	/** The HUD meter of what each use costs (see ChargeMeter). */
	public enum ChargeMeter { LEVELS, BAR, OFF }
	/** How hard the camera kicks when a shot fires (see RingShake). */
	public enum ScreenShake {
		NORMAL(1f), STRONG(1.6f), SUBTLE(0.5f), OFF(0f);

		private final float amount;

		ScreenShake(float amount) {
			this.amount = amount;
		}

		public float amount() {
			return amount;
		}
	}

	/** How big a hole the ram barrier leaves in a wall it hits (sent to the server, see RamBarrier.Hole; same order). */
	public enum RamHole { DENT, CRATER, TOUCHING }
	/** How much faster a ring-bearer sprints on foot (sent to the server, see SuperJumps): the extra speed on top of walking. */
	public enum SuperSprint {
		FAST(0.6f), BLUR(1.2f), OFF(0f);

		private final float boost;

		SuperSprint(float boost) {
			this.boost = boost;
		}

		public float boost() {
			return boost;
		}
	}
	/** J's Blender picks for the super jump (2026-10-13): the ring arm on the way down (D1A at the ground, D1B ahead, D1C down and out). */
	public enum SuperFallArm { D1A, D1B, D1C }
	/** The landing: E1 three-point landing, E2 the wide slam. */
	public enum SuperLanding { E1, E2 }
	/** The low construct wall round the landing pad: W2 3 x 8 px, W1 8 x 8 px, W3 1.5 x 6 px, or none. */
	public enum SuperWall {
		W2(3, 8), W1(8, 8), W3(1.5f, 6), OFF(0, 0);

		/** Thickness and height in pixels. */
		public final float thick, high;

		SuperWall(float thick, float high) {
			this.thick = thick;
			this.high = high;
		}
	}
	/** Server side: a crater on every landing, shaped by the ground, or only on a primed one. */
	public enum SuperCrater { SURFACE, PRIMED_ONLY }
	/** Omega beams' start (J's Blender pass 225; server side OmegaBeams.Start, same order): E1 snap, E2 smoulder, E3 air brake, E4 crackle. */
	public enum OmegaStart { E1, E2, E3, E4 }
	/** Omega beams' chain (server side OmegaBeams.Chain, same order): pass 837 R4 (speed by distance, E3 pulse look), or today's chain. */
	public enum OmegaChain { R4, TODAY }
	/** J's sprint with a lantern in the off hand (Blender pass 227): S5a carry arm 43 degrees forward, S5b 57. */
	public enum SprintCarry { S5A, S5B }
	/** Low ground flight's halt against a wall (pass 228): H1 hard stop, H2 cushion, H3 into the block. */
	public enum GroundHalt { H1, H2, H3 }
	/** The sonic boom's screen shake, 0 to 100% (pass 218). */
	public enum FlightShake {
		P100(1f), P75(0.75f), P50(0.5f), P25(0.25f), P0(0f);

		private final float amount;

		FlightShake(float amount) {
			this.amount = amount;
		}

		public float amount() {
			return amount;
		}
	}
	/** Flying off the ground (not sprinting): J's F2 rocket takeoff (pass 216), or plain vanilla. */
	public enum Takeoff { F2, OFF }
	/** A fast super jump landing's slide (J's Blender pass 400): A3 dissolve above 25 blocks a second, or B2 plough above 15 (sent to the server). */
	public enum LandingSlide { DISSOLVE, PLOUGH }
	/** Pass 403 double-jump take-off, standing: S1 snap, the S2b spring (J's pick) to 3.2, or pass 407's S2a fast spring that settles at 2.2. */
	public enum TakeoffStand { S1, S2A, S2B }
	/** Pass 403 free arm in the R3 dart and laid-out flight: A2 a little forward (default), A1 flush along the side (J dropped A3, 2026-10-15). */
	public enum FreeArm { A2, A1 }
	/** Pass 404 ring arm leading flight by 0.08 s: D1 pure lead (default), D3 adds a bank (J dropped D2, 2026-10-15). */
	public enum ArmLead { D1, D3 }
	/**
	 * Pass 515 super speed on left click while flying (SuperSpeedFlight): S2 a tap goes straight to 60 b/s with a sonic
	 * boom, holds it 2 s and eases back (J's pick); S3 holding left click ramps 20 to 60 b/s over 1.5 s, and a hard dive
	 * at that speed still fires the flight slam (J dropped S1, the ramp alone).
	 */
	public enum SuperSpeed { S2, S3 }
	/**
	 * Pass 405 double-tap landing: brake, drop straight in, absorb crouch, stand. J kept L4 with 0.3 blocks of carry,
	 * down 0.30 s after the tap (2026-10-15); L5, L6 and 403's L2 are dropped, so a saved L5 or L6 loads as L4 and the
	 * Copy report says so ("reset: ...").
	 */
	public enum SoftLanding { L4 }
	/** The big flight slam's trigger height (Blender pass 510, client side): H5 5 blocks (J's pick), H6 6, H3 3. */
	public enum FlightSlam {
		H5(5), H6(6), H3(3);

		public final double height;

		FlightSlam(double height) {
			this.height = height;
		}
	}
	/** How an absorbed shot is held (pass 503 R4): R4b at the ring (J's pick), R4a in a construct cage, R4c swallowed by the ring. */
	public enum AbsorbHold { R4B, R4A, R4C }
	/** The construct hammer's swing (pass 503 R2): J's pick overhead with the side swing on walls, or always one. */
	public enum HammerSwing { AUTO, R2A, R2B }

	/**
	 * The Ring Lab's tabs, in order: each row belongs to one (J, 2026-10-14: "the system should have been worked on to make
	 * the options easier to navigate"). Updates holds the updater rather than rows.
	 */
	public enum Group { MOVEMENT, FLIGHT, COMBAT, BEAMS, CONSTRUCTS, RING, LANTERN, CORPS, EFFECTS, UPDATES }

	public RingModel ringModel = RingModel.P03;        // J's square emblem pick, pass 596 (see the v11 migration)
	public LanternModel lanternModel = LanternModel.STONE;
	public ChargeStyle chargeStyle = ChargeStyle.HAND;
	/** Blender pass 519: the Dark Lantern stands one block (16 px) tall set down; or as big as it is in your hand. */
	public SetDownSize setDownSize = SetDownSize.BLOCK;
	public HandPose handPose = HandPose.RING_FORWARD;
	public RingGlow ringGlow = RingGlow.AURA;
	public UseFx useFx = UseFx.HELIX;
	public BeamLook beamLook = BeamLook.HELIX;
	public BlastFx blastFx = BlastFx.SCORCH;
	public FlightFx flightFx = FlightFx.TRAIL;
	public BlockGlow blockGlow = BlockGlow.CONSTRUCTS;
	public Strength strength = Strength.NORMAL;
	public ChargeGlow chargeGlow = ChargeGlow.SWIRL_AND_MOTES;
	public LanternSun lanternSun = LanternSun.INFLOW;
	public ChargeMeter chargeMeter = ChargeMeter.LEVELS;
	public ScreenShake screenShake = ScreenShake.NORMAL;
	public RamHole ramHole = RamHole.DENT;
	public SuperSprint superSprint = SuperSprint.FAST;
	public SuperFallArm superFallArm = SuperFallArm.D1A;
	public SuperLanding superLanding = SuperLanding.E1;
	public SuperWall superWall = SuperWall.W2;
	public SuperCrater superCrater = SuperCrater.SURFACE;
	public OmegaStart omegaStart = OmegaStart.E1;
	public OmegaChain omegaChain = OmegaChain.R4;
	public SprintCarry sprintCarry = SprintCarry.S5A;
	public GroundHalt groundHalt = GroundHalt.H2;
	public FlightShake flightShake = FlightShake.P100;
	public Takeoff takeoff = Takeoff.F2;
	public LandingSlide landingSlide = LandingSlide.DISSOLVE;
	public FlightSlam flightSlam = FlightSlam.H5;
	public AbsorbHold absorbHold = AbsorbHold.R4B;
	public HammerSwing hammerSwing = HammerSwing.AUTO;
	public TakeoffStand takeoffStand = TakeoffStand.S1;
	public FreeArm freeArm = FreeArm.A2;
	public ArmLead armLead = ArmLead.D1;
	public SuperSpeed superSpeed = SuperSpeed.S2;
	public SoftLanding softLanding = SoftLanding.L4;
	public SoulSightMode soulSight = SoulSightMode.PLAYERS_AND_MOBS;
	public ConstructLook constructLook = ConstructLook.W1_NEON;   // J: every construct should read like W1 neon from afar
	public WallLook wallLook = WallLook.BR1_JADE;
	public BlueLook blueLook = BlueLook.BR1;     // J dropped B1 (2.1.647 report)
	public YellowLook yellowLook = YellowLook.W1; // J dropped Y1-Y3 (2.1.647 report)
	public RedLook redLook = RedLook.R1;
	public RedLantern redLantern = RedLantern.NEW;
	public NebulaLight nebulaLight = NebulaLight.L1;
	public DrillModel drillModel = DrillModel.CLASSIC;
	public BarrierSurface barrierSurface = BarrierSurface.PICKED;
	public VioletLook violetLook = VioletLook.V1;
	public ConstructOpacity constructOpacity = ConstructOpacity.P50;
	public ConstructPig constructPig = ConstructPig.P2;
	public ConstructRays constructRays = ConstructRays.D2;
	/** Bumped when a new default should replace what older saved files picked. */
	public int version;
	/** The Ring Lab tab last open (null: the first) and the row picked on it. */
	public Group labTab;
	public int labRow;
	/** Ring Lab: also list superseded takes (an option's old values). */
	public boolean showOld;
	/** "option.VALUE" -> rating, e.g. "ring_model.SIGNET" -> KEEP. */
	public Map<String, Rating> ratings = new TreeMap<>();
	/** "option.VALUE" -> the player's note on that take (the ✎ button), saved with the rating and sent in the report. */
	public Map<String, String> notes = new TreeMap<>();
	/**
	 * Option keys of the rows the player has set. A touched row is never changed by a new jar: when its ★ pick moves on,
	 * the row shows a "new pick" badge instead (J, 2026-10-14: "I need the next jar to consider this and for this to save for me").
	 */
	public Set<String> touched = new java.util.TreeSet<>();
	/** Option key -> the ★ pick the player last saw on that row; a different pick today is a "new pick available". */
	public Map<String, String> seenPicks = new TreeMap<>();
	/** Send to Claude's unsent text, kept until it is sent so closing the panel never loses it. */
	public String inboxDraft = "";
	/** Rows whose saved take no longer exists in this jar, for the Copy report ("reset: row (OLD no longer exists)"). */
	public transient List<String> resets = new java.util.ArrayList<>();

	/**
	 * One row of the Ring Lab menu: one feature, stepped through its takes with the arrows. {@code pick} is J's pick (starred,
	 * and what the reset buttons restore; null means the fresh default), {@code old} the superseded takes the menu hides unless
	 * "Show old takes" is on, and {@code preview} what Enter plays for it (LanternRingClientState.queuePreview), if anything.
	 */
	public record Option<E extends Enum<E>>(Group group, String key, Class<E> type, Function<LabSettings, E> get, BiConsumer<LabSettings, E> set,
			E pick, Set<E> old, String preview) {
		public Option(Group group, String key, Class<E> type, Function<LabSettings, E> get, BiConsumer<LabSettings, E> set) {
			this(group, key, type, get, set, null, Set.of(), null);
		}

		public Option<E> withPick(E value) {
			return new Option<>(group, key, type, get, set, value, old, preview);
		}

		@SafeVarargs
		public final Option<E> withOld(E... values) {
			return new Option<>(group, key, type, get, set, pick, Set.of(values), preview);
		}

		public Option<E> withPreview(String what) {
			return new Option<>(group, key, type, get, set, pick, old, what);
		}

		public E current(LabSettings s) {
			return get.apply(s);
		}

		/** J's pick: the starred value the reset buttons go back to. */
		public E jPick() {
			return pick != null ? pick : get.apply(DEFAULTS);
		}

		public boolean isPick(Enum<?> value) {
			return value == jPick();
		}

		public void resetToPick(LabSettings s) {
			set.accept(s, jPick());
			s.touch(this);
		}

		/** Step to the next or previous take, skipping superseded ones unless the menu shows them. */
		public void cycle(LabSettings s, int step) {
			E[] values = type.getEnumConstants();
			int i = current(s).ordinal();
			for (int n = 0; n < values.length; n++) {
				i = Math.floorMod(i + step, values.length);
				if (s.showOld || !old.contains(values[i])) break;
			}
			set.accept(s, values[i]);
			s.touch(this);
		}

		/** Set the row to a take as the player's own choice. */
		public void choose(LabSettings s, E value) {
			set.accept(s, value);
			s.touch(this);
		}

		/** True when the player set this row and a newer jar has since starred a different take. */
		public boolean newPickAvailable(LabSettings s) {
			if (!s.touched.contains(key)) return false;
			E pick = jPick();
			String seen = s.seenPicks.get(key);
			return pick != current(s) && seen != null && !seen.equals(pick.name());
		}

		/** Put the row on its ★ pick without marking it as the player's choice. */
		void resetToPickQuietly(LabSettings s) {
			set.accept(s, jPick());
		}

		@SuppressWarnings("unchecked")
		void setRaw(LabSettings s, Enum<?> value) {
			set.accept(s, (E) value);
		}

		public String ratingKey(LabSettings s) {
			return key + "." + current(s).name();
		}

		/** The row's name, e.g. "Take-off: standing". */
		public String label() {
			return net.minecraft.network.chat.Component.translatable("lab.lanternring." + key).getString();
		}

		/** A take's label with its code and pass, e.g. "S1 snap · pass 403". */
		public String valueLabel(Enum<?> value) {
			return net.minecraft.network.chat.Component.translatable("lab.lanternring." + key + "." + value.name().toLowerCase(java.util.Locale.ROOT)).getString();
		}

		/** True when the search text appears in the row's name, tab, key or any of its current takes' labels. */
		public boolean matches(String query, boolean showOld) {
			String q = query.toLowerCase(java.util.Locale.ROOT).trim();
			if (q.isEmpty()) return true;
			if (label().toLowerCase(java.util.Locale.ROOT).contains(q) || key.replace('_', ' ').contains(q)
					|| group.name().toLowerCase(java.util.Locale.ROOT).contains(q)) return true;
			for (E value : type.getEnumConstants()) {
				if (!showOld && old.contains(value)) continue;
				if (valueLabel(value).toLowerCase(java.util.Locale.ROOT).contains(q)) return true;
			}
			return false;
		}
	}

	private static final LabSettings DEFAULTS = new LabSettings();

	public static final List<Option<?>> OPTIONS = List.of(
			// Movement: sprint, super jump, take-off, landing, ground flight
			new Option<>(Group.MOVEMENT, "super_sprint", SuperSprint.class, s -> s.superSprint, (s, v) -> s.superSprint = v),
			new Option<>(Group.MOVEMENT, "sprint_carry", SprintCarry.class, s -> s.sprintCarry, (s, v) -> s.sprintCarry = v).withPick(SprintCarry.S5B),
			new Option<>(Group.MOVEMENT, "takeoff", Takeoff.class, s -> s.takeoff, (s, v) -> s.takeoff = v),
			new Option<>(Group.MOVEMENT, "takeoff_stand", TakeoffStand.class, s -> s.takeoffStand, (s, v) -> s.takeoffStand = v).withPick(TakeoffStand.S2B),
			new Option<>(Group.MOVEMENT, "free_arm", FreeArm.class, s -> s.freeArm, (s, v) -> s.freeArm = v),
			new Option<>(Group.MOVEMENT, "soft_landing", SoftLanding.class, s -> s.softLanding, (s, v) -> s.softLanding = v),
			new Option<>(Group.MOVEMENT, "ground_halt", GroundHalt.class, s -> s.groundHalt, (s, v) -> s.groundHalt = v),
			new Option<>(Group.MOVEMENT, "super_fall_arm", SuperFallArm.class, s -> s.superFallArm, (s, v) -> s.superFallArm = v).withPick(SuperFallArm.D1B),
			new Option<>(Group.MOVEMENT, "super_landing", SuperLanding.class, s -> s.superLanding, (s, v) -> s.superLanding = v),
			new Option<>(Group.MOVEMENT, "super_wall", SuperWall.class, s -> s.superWall, (s, v) -> s.superWall = v),
			new Option<>(Group.MOVEMENT, "super_crater", SuperCrater.class, s -> s.superCrater, (s, v) -> s.superCrater = v),
			new Option<>(Group.MOVEMENT, "landing_slide", LandingSlide.class, s -> s.landingSlide, (s, v) -> s.landingSlide = v),
			// Flight: trail, effects
			new Option<>(Group.FLIGHT, "arm_lead", ArmLead.class, s -> s.armLead, (s, v) -> s.armLead = v),
			new Option<>(Group.FLIGHT, "super_speed", SuperSpeed.class, s -> s.superSpeed, (s, v) -> s.superSpeed = v).withPick(SuperSpeed.S2),
			new Option<>(Group.FLIGHT, "flight_fx", FlightFx.class, s -> s.flightFx, (s, v) -> s.flightFx = v),
			new Option<>(Group.FLIGHT, "flight_shake", FlightShake.class, s -> s.flightShake, (s, v) -> s.flightShake = v),
			// Combat: blast, drill, ram
			new Option<>(Group.COMBAT, "blast_fx", BlastFx.class, s -> s.blastFx, (s, v) -> s.blastFx = v).withPreview("blast"),
			new Option<>(Group.COMBAT, "drill_model", DrillModel.class, s -> s.drillModel, (s, v) -> s.drillModel = v).withPick(DrillModel.D2_TIERED).withPreview("blast"),
			new Option<>(Group.COMBAT, "ram_hole", RamHole.class, s -> s.ramHole, (s, v) -> s.ramHole = v).withPick(RamHole.CRATER),
			new Option<>(Group.COMBAT, "flight_slam", FlightSlam.class, s -> s.flightSlam, (s, v) -> s.flightSlam = v),
			new Option<>(Group.COMBAT, "absorb_hold", AbsorbHold.class, s -> s.absorbHold, (s, v) -> s.absorbHold = v),
			new Option<>(Group.COMBAT, "hammer_swing", HammerSwing.class, s -> s.hammerSwing, (s, v) -> s.hammerSwing = v),
			// Beams
			new Option<>(Group.BEAMS, "use_fx", UseFx.class, s -> s.useFx, (s, v) -> s.useFx = v).withPreview("use"),
			new Option<>(Group.BEAMS, "beam_look", BeamLook.class, s -> s.beamLook, (s, v) -> s.beamLook = v).withPreview("beam"),
			new Option<>(Group.BEAMS, "omega_start", OmegaStart.class, s -> s.omegaStart, (s, v) -> s.omegaStart = v),
			new Option<>(Group.BEAMS, "omega_chain", OmegaChain.class, s -> s.omegaChain, (s, v) -> s.omegaChain = v).withPick(OmegaChain.R4),
			// Constructs
			new Option<>(Group.CONSTRUCTS, "construct_look", ConstructLook.class, s -> s.constructLook, (s, v) -> s.constructLook = v).withPick(ConstructLook.H1_NEON)
					.withOld(ConstructLook.X3_EMERALD, ConstructLook.H2_NEON),
			new Option<>(Group.CONSTRUCTS, "wall_look", WallLook.class, s -> s.wallLook, (s, v) -> s.wallLook = v).withPick(WallLook.BR1_EMERALD),
			new Option<>(Group.CONSTRUCTS, "barrier_surface", BarrierSurface.class, s -> s.barrierSurface, (s, v) -> s.barrierSurface = v),
			new Option<>(Group.CONSTRUCTS, "construct_opacity", ConstructOpacity.class, s -> s.constructOpacity, (s, v) -> s.constructOpacity = v).withPick(ConstructOpacity.P30),
			new Option<>(Group.CONSTRUCTS, "block_glow", BlockGlow.class, s -> s.blockGlow, (s, v) -> s.blockGlow = v),
			new Option<>(Group.CONSTRUCTS, "construct_rays", ConstructRays.class, s -> s.constructRays, (s, v) -> s.constructRays = v).withPick(ConstructRays.D2),
			new Option<>(Group.CONSTRUCTS, "construct_pig", ConstructPig.class, s -> s.constructPig, (s, v) -> s.constructPig = v).withPick(ConstructPig.P2),
			// Ring: model, hand, glow
			new Option<>(Group.RING, "ring_model", RingModel.class, s -> s.ringModel, (s, v) -> s.ringModel = v).withPick(RingModel.N04)
					.withOld(RingModel.CREST, RingModel.CREST_GOLD, RingModel.BEACON, RingModel.EMBLEM, RingModel.SIGNET, RingModel.SLIM,
							RingModel.LANTERN, RingModel.CROWN, RingModel.SQUARE),
			new Option<>(Group.RING, "hand_pose", HandPose.class, s -> s.handPose, (s, v) -> s.handPose = v).withPick(HandPose.KNUCKLES_IN),
			new Option<>(Group.RING, "ring_glow", RingGlow.class, s -> s.ringGlow, (s, v) -> s.ringGlow = v),
			new Option<>(Group.RING, "charge_glow", ChargeGlow.class, s -> s.chargeGlow, (s, v) -> s.chargeGlow = v).withPreview("use"),
			new Option<>(Group.RING, "charge_meter", ChargeMeter.class, s -> s.chargeMeter, (s, v) -> s.chargeMeter = v),
			// Lantern and charge
			new Option<>(Group.LANTERN, "lantern_model", LanternModel.class, s -> s.lanternModel, (s, v) -> s.lanternModel = v).withPick(LanternModel.DARK),
			new Option<>(Group.LANTERN, "nebula_light", NebulaLight.class, s -> s.nebulaLight, (s, v) -> s.nebulaLight = v),
			new Option<>(Group.LANTERN, "charge_style", ChargeStyle.class, s -> s.chargeStyle, (s, v) -> s.chargeStyle = v).withPick(ChargeStyle.HIP).withPreview("charge"),
			new Option<>(Group.LANTERN, "set_down_size", SetDownSize.class, s -> s.setDownSize, (s, v) -> s.setDownSize = v).withPreview("charge"),
			new Option<>(Group.LANTERN, "lantern_sun", LanternSun.class, s -> s.lanternSun, (s, v) -> s.lanternSun = v).withPreview("charge"),
			// Corps
			new Option<>(Group.CORPS, "red_look", RedLook.class, s -> s.redLook, (s, v) -> s.redLook = v),
			new Option<>(Group.CORPS, "red_lantern", RedLantern.class, s -> s.redLantern, (s, v) -> s.redLantern = v),
			new Option<>(Group.CORPS, "yellow_look", YellowLook.class, s -> s.yellowLook, (s, v) -> s.yellowLook = v).withOld(YellowLook.Y1, YellowLook.Y2, YellowLook.Y3),
			new Option<>(Group.CORPS, "violet_look", VioletLook.class, s -> s.violetLook, (s, v) -> s.violetLook = v),
			new Option<>(Group.CORPS, "blue_look", BlueLook.class, s -> s.blueLook, (s, v) -> s.blueLook = v).withOld(BlueLook.B1),
			// Effects and particles
			new Option<>(Group.EFFECTS, "strength", Strength.class, s -> s.strength, (s, v) -> s.strength = v).withPick(Strength.INTENSE).withPreview("push"),
			new Option<>(Group.EFFECTS, "screen_shake", ScreenShake.class, s -> s.screenShake, (s, v) -> s.screenShake = v).withPick(ScreenShake.SUBTLE).withPreview("blast"),
			new Option<>(Group.EFFECTS, "soul_sight", SoulSightMode.class, s -> s.soulSight, (s, v) -> s.soulSight = v));

	/** The rows on one tab, in menu order. */
	public static List<Option<?>> tab(Group group) {
		return OPTIONS.stream().filter(o -> o.group() == group).toList();
	}

	/** Every row the search text matches, tab by tab. */
	public List<Option<?>> search(String query) {
		List<Option<?>> out = new java.util.ArrayList<>();
		for (Group g : Group.values()) for (Option<?> o : tab(g)) if (o.matches(query, showOld)) out.add(o);
		return out;
	}

	/** Put every row in the list back to J's pick. */
	public void resetToPicks(List<Option<?>> options) {
		for (Option<?> o : options) o.resetToPick(this);
	}

	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static LabSettings instance;

	public static LabSettings get() {
		if (instance == null) instance = load();
		return instance;
	}

	/** Read lanternring-lab.json again (tests, and after the file is replaced by hand). */
	public static LabSettings reload() {
		instance = load();
		return instance;
	}

	public float amount() {
		return switch (strength) {
			case SUBTLE -> 0.5f;
			case NORMAL -> 1f;
			case INTENSE -> 2f;
		};
	}

	public Rating rating(String key) {
		return ratings.getOrDefault(key, Rating.NONE);
	}

	public void rate(String key, Rating rating) {
		if (rating == Rating.NONE) ratings.remove(key);
		else ratings.put(key, rating);
	}

	/**
	 * A plain-text summary the player can paste back to whoever is building the mod: grouped by tab, one line per feature
	 * ("feature (key): take, ★ when it is J's pick"), then any ratings, so KEEP / IMPROVE / DROP map straight back.
	 */
	public String report() {
		StringBuilder out = new StringBuilder("Lantern Ring - Ring Lab report (v").append(LanternRing.version()).append(")\n");
		for (Group group : Group.values()) {
			List<Option<?>> rows = tab(group);
			if (rows.isEmpty()) continue;
			out.append("[").append(net.minecraft.network.chat.Component.translatable("lab.lanternring.tab." + group.name().toLowerCase(java.util.Locale.ROOT)).getString())
					.append("]\n");
			for (Option<?> option : rows) {
				Enum<?> current = option.current(this);
				out.append("- ").append(option.label()).append(" (").append(option.key()).append("): ")
						.append(option.valueLabel(current)).append(" [").append(current.name()).append("]");
				if (option.isPick(current)) out.append(" \u2605");
				StringBuilder rated = new StringBuilder();
				for (Enum<?> value : option.type().getEnumConstants()) {
					Rating r = rating(option.key() + "." + value.name());
					if (r != Rating.NONE) rated.append(rated.isEmpty() ? "" : ", ").append(value.name()).append('=').append(r.name());
				}
				if (!rated.isEmpty()) out.append(" | rated ").append(rated);
				String note = note(option.key() + "." + current.name());
				if (!note.isEmpty()) out.append(" | note: ").append(oneLine(note));
				for (Enum<?> value : option.type().getEnumConstants()) {
					String other = value == current ? "" : note(option.key() + "." + value.name());
					if (!other.isEmpty()) out.append(" | note ").append(value.name()).append(": ").append(oneLine(other));
				}
				if (option.newPickAvailable(this)) out.append(" | new \u2605 pick available: ").append(option.jPick().name());
				out.append('\n');
			}
		}
		for (String reset : resets) out.append("reset: ").append(reset).append('\n');
		String durations = RingTuning.report();
		if (!durations.isEmpty()) out.append("Durations changed:\n").append(durations);
		return out.toString();
	}

	private static String oneLine(String text) {
		return text.replaceAll("\\s*\\R\\s*", " / ");
	}

	private static Path file() {
		return FabricLoader.getInstance().getConfigDir().resolve("lanternring-lab.json");
	}

	/** The settings version this jar writes; 12 replaced the forced "show it once" migrations with touched rows. */
	private static final int VERSION = 12;

	private static LabSettings load() {
		Path path = file();
		if (Files.exists(path)) {
			LabSettings loaded = null;
			try (Reader reader = Files.newBufferedReader(path)) {
				com.google.gson.JsonObject raw = com.google.gson.JsonParser.parseReader(reader).getAsJsonObject();
				loaded = GSON.fromJson(raw, LabSettings.class);
				if (loaded != null) loaded.fillMissing(raw);
			} catch (IOException | RuntimeException e) {
				LanternRing.LOGGER.warn("Couldn't read {}, using defaults", path, e);
				loaded = null;
			}
			if (loaded != null) {
				// Written straight back (reader closed) so the touched rows are on disk before anything else changes.
				loaded.save();
				return loaded;
			}
		}
		LabSettings fresh = new LabSettings();
		fresh.version = VERSION;
		fresh.followPicks();
		return fresh;
	}

	/** Mark a row as the player's own choice: no new jar changes it, and its current ★ pick counts as seen. */
	void touch(Option<?> option) {
		touched.add(option.key());
		seenPicks.put(option.key(), option.jPick().name());
	}

	/** Rows the player never set take today's ★ pick; set rows keep their value and only show a badge when the pick moves on. */
	private void followPicks() {
		for (Option<?> option : OPTIONS) {
			if (touched.contains(option.key())) continue;
			option.resetToPickQuietly(this);
			seenPicks.put(option.key(), option.jPick().name());
		}
	}

	/**
	 * Old or hand-edited files may lack newer fields. Before version 12 each jar forced its newest look over the saved pick
	 * ten times (ring model, hand, lantern, constructs, Blue and Yellow); now a row the player set is never reset.
	 */
	private void fillMissing(com.google.gson.JsonObject raw) {
		if (ratings == null) ratings = new TreeMap<>();
		if (notes == null) notes = new TreeMap<>();
		if (touched == null) touched = new java.util.TreeSet<>();
		if (seenPicks == null) seenPicks = new TreeMap<>();
		if (inboxDraft == null) inboxDraft = "";
		resets = new java.util.ArrayList<>();
		ratings.values().removeIf(r -> r == null || r == Rating.NONE);
		notes.values().removeIf(n -> n == null || n.isBlank());

		// A take an older jar saved that this jar no longer has loads as null: fall back to the pick and say so in the report.
		List<java.lang.reflect.Field> nulls = new java.util.ArrayList<>();
		for (java.lang.reflect.Field f : LabSettings.class.getDeclaredFields()) {
			if (f.getType().isEnum() && !java.lang.reflect.Modifier.isStatic(f.getModifiers())) {
				try {
					if (f.get(this) == null) nulls.add(f);
				} catch (IllegalAccessException ignored) {
				}
			}
		}
		for (Option<?> option : OPTIONS) {
			if (option.current(this) != null) continue;
			option.resetToPickQuietly(this);
			for (java.lang.reflect.Field f : nulls) {
				try {
					if (f.get(this) == null || !raw.has(f.getName()) || !raw.get(f.getName()).isJsonPrimitive()) continue;
				} catch (IllegalAccessException e) {
					continue;
				}
				resets.add(option.label() + " (" + raw.get(f.getName()).getAsString() + " no longer exists)");
				break;
			}
		}

		if (version < 12) {
			// J's 2.1.647 report (issue #323): what is set now is what he keeps. Every row counts as his, with today's picks seen.
			for (Option<?> option : OPTIONS) touch(option);
			version = 12;
		}
		followPicks();
	}

	/** The rows whose ★ pick changed since the player set them. */
	public List<Option<?>> newPicks() {
		return OPTIONS.stream().filter(o -> o.newPickAvailable(this)).toList();
	}

	public String note(String key) {
		return notes.getOrDefault(key, "");
	}

	public void setNote(String key, String text) {
		if (text == null || text.isBlank()) notes.remove(key);
		else notes.put(key, text.strip());
	}

	private static Path profileFile() {
		return FabricLoader.getInstance().getConfigDir().resolve("lanternring-profile-J.json");
	}

	/** Ring Lab > "Save as my profile": every row, rating, note and duration, so a reset or new install gets it all back. */
	public boolean saveProfile() {
		com.google.gson.JsonObject out = new com.google.gson.JsonObject();
		out.addProperty("saved_from", LanternRing.version());
		out.add("lab", GSON.toJsonTree(this));
		com.google.gson.JsonObject durations = new com.google.gson.JsonObject();
		for (RingTuning.Entry entry : RingTuning.entries()) durations.addProperty(entry.key, entry.seconds());
		out.add("durations", durations);
		try (Writer writer = Files.newBufferedWriter(profileFile())) {
			GSON.toJson(out, writer);
			return true;
		} catch (IOException e) {
			LanternRing.LOGGER.warn("Couldn't save {}", profileFile(), e);
			return false;
		}
	}

	/**
	 * Ring Lab > "Load my profile": the saved profile, or with none saved yet, J's 2.1.647 report bundled in the jar.
	 * Every row it names becomes touched with its value. Returns what was loaded, or null.
	 */
	public String loadProfile() {
		Path path = profileFile();
		if (Files.exists(path)) {
			try (Reader reader = Files.newBufferedReader(path)) {
				com.google.gson.JsonObject in = com.google.gson.JsonParser.parseReader(reader).getAsJsonObject();
				LabSettings saved = GSON.fromJson(in.getAsJsonObject("lab"), LabSettings.class);
				for (Option<?> option : OPTIONS) {
					Enum<?> value = option.current(saved);
					if (value != null) applyValue(option, value);
				}
				if (saved.ratings != null) saved.ratings.forEach((k, r) -> {
					if (r != null) rate(k, r);
				});
				if (saved.notes != null) saved.notes.forEach(this::setNote);
				if (in.has("durations")) {
					com.google.gson.JsonObject d = in.getAsJsonObject("durations");
					for (RingTuning.Entry entry : RingTuning.entries()) if (d.has(entry.key)) entry.set(d.get(entry.key).getAsDouble());
					RingTuning.save();
				}
				save();
				return profileFile().getFileName().toString();
			} catch (IOException | RuntimeException e) {
				LanternRing.LOGGER.warn("Couldn't read {}", path, e);
				return null;
			}
		}
		try (java.io.InputStream in = LabSettings.class.getResourceAsStream("/assets/lanternring/lab/j-report-2.1.647.txt")) {
			if (in == null) return null;
			applyReport(new String(in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8));
			save();
			return "2.1.647 report";
		} catch (IOException e) {
			return null;
		}
	}

	private void applyValue(Option<?> option, Enum<?> value) {
		option.setRaw(this, value);
		touch(option);
	}

	/**
	 * Read a Copy report back in: each "- name (key): label [VALUE]" line sets that row, "| rated A=KEEP, ..." its ratings,
	 * and "- duration: 1.5s (default ...)" lines under "Durations changed:" the durations.
	 */
	public void applyReport(String report) {
		java.util.regex.Pattern row = java.util.regex.Pattern.compile("^- .*?\\(([a-z_]+)\\): .*?\\[([A-Z0-9_]+)\\]");
		java.util.regex.Pattern duration = java.util.regex.Pattern.compile("^- ([a-z_.]+): ([0-9.]+)s");
		boolean inDurations = false;
		for (String line : report.split("\\R")) {
			if (line.startsWith("Durations changed")) {
				inDurations = true;
				continue;
			}
			if (inDurations) {
				java.util.regex.Matcher m = duration.matcher(line);
				if (!m.find()) continue;
				for (RingTuning.Entry entry : RingTuning.entries()) if (entry.key.equals(m.group(1))) entry.set(Double.parseDouble(m.group(2)));
				continue;
			}
			java.util.regex.Matcher m = row.matcher(line);
			if (!m.find()) continue;
			for (Option<?> option : OPTIONS) {
				if (!option.key().equals(m.group(1))) continue;
				for (Enum<?> value : option.type().getEnumConstants()) if (value.name().equals(m.group(2))) applyValue(option, value);
				int bar = line.indexOf("| rated ");
				if (bar >= 0) {
					for (String pair : line.substring(bar + 8).split(",")) {
						String[] kv = pair.trim().split("=");
						if (kv.length != 2) continue;
						try {
							rate(option.key() + "." + kv[0].trim(), Rating.valueOf(kv[1].trim()));
						} catch (IllegalArgumentException ignored) {
						}
					}
				}
			}
		}
		if (inDurations) RingTuning.save();
	}

	public void save() {
		try (Writer writer = Files.newBufferedWriter(file())) {
			GSON.toJson(this, writer);
		} catch (IOException e) {
			LanternRing.LOGGER.warn("Couldn't save {}", file(), e);
		}
	}
}
