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
	public enum HandPose { RING_FORWARD, KNUCKLES_IN, FIST_DOWN, KNUCKLES_FORWARD, FLAT_ITEM }
	public enum RingGlow { OFF, MOTES, DRIPS, AURA }
	/** What the ring looks like as it charges in the lantern (see BeamChargeGlow.renderSun). */
	public enum LanternSun { INFLOW, SUN }
	public enum UseFx { LINE, HELIX, HELIX_RECALL, SHARDS }
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
	/** Pass 403 double-jump take-off, standing: S1 snap (J's pick), or the S2a / S2b springs that rise faster and settle at 3.2. */
	public enum TakeoffStand { S1, S2A, S2B }
	/** Pass 403 free arm in the R3 dart and laid-out flight: A2 a little forward (default), A1 flush along the side, A3 forward and out. */
	public enum FreeArm { A2, A1, A3 }
	/** Pass 404 ring arm leading flight by 0.08 s: D1 pure lead (default), D2 overshoots into turns, D3 adds a bank. */
	public enum ArmLead { D1, D2, D3 }
	/**
	 * Pass 405 double-tap landing (replaced 403's L2: "land much closer ... should be faster too"): brake, drop straight
	 * in, absorb crouch, stand. L5 (default) 0.4 blocks of carry, down 0.25 s after the tap; L4 0.8 blocks, 0.30 s; L6 none, 0.20 s.
	 */
	public enum SoftLanding { L5, L4, L6 }
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
	public HandPose handPose = HandPose.RING_FORWARD;
	public RingGlow ringGlow = RingGlow.AURA;
	public UseFx useFx = UseFx.HELIX;
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
	public SoftLanding softLanding = SoftLanding.L5;
	public SoulSightMode soulSight = SoulSightMode.PLAYERS_AND_MOBS;
	public ConstructLook constructLook = ConstructLook.W1_NEON;   // J: every construct should read like W1 neon from afar
	public WallLook wallLook = WallLook.BR1_JADE;
	public BlueLook blueLook = BlueLook.B1;
	public YellowLook yellowLook = YellowLook.Y1;
	public RedLook redLook = RedLook.R1;
	public RedLantern redLantern = RedLantern.NEW;
	public NebulaLight nebulaLight = NebulaLight.L1;
	public DrillModel drillModel = DrillModel.CLASSIC;
	public BarrierSurface barrierSurface = BarrierSurface.PICKED;
	public VioletLook violetLook = VioletLook.V1;
	public ConstructOpacity constructOpacity = ConstructOpacity.P50;
	/** Bumped when a new default should replace what older saved files picked. */
	public int version;
	/** The Ring Lab tab last open (null: the first) and the row picked on it. */
	public Group labTab;
	public int labRow;
	/** Ring Lab: also list superseded takes (an option's old values). */
	public boolean showOld;
	/** "option.VALUE" -> rating, e.g. "ring_model.SIGNET" -> KEEP. */
	public Map<String, Rating> ratings = new TreeMap<>();

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
		}

		void fillFrom(LabSettings s, LabSettings defaults) {
			if (current(s) == null) set.accept(s, current(defaults));
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
			new Option<>(Group.MOVEMENT, "sprint_carry", SprintCarry.class, s -> s.sprintCarry, (s, v) -> s.sprintCarry = v),
			new Option<>(Group.MOVEMENT, "takeoff", Takeoff.class, s -> s.takeoff, (s, v) -> s.takeoff = v),
			new Option<>(Group.MOVEMENT, "takeoff_stand", TakeoffStand.class, s -> s.takeoffStand, (s, v) -> s.takeoffStand = v),
			new Option<>(Group.MOVEMENT, "free_arm", FreeArm.class, s -> s.freeArm, (s, v) -> s.freeArm = v),
			new Option<>(Group.MOVEMENT, "soft_landing", SoftLanding.class, s -> s.softLanding, (s, v) -> s.softLanding = v),
			new Option<>(Group.MOVEMENT, "ground_halt", GroundHalt.class, s -> s.groundHalt, (s, v) -> s.groundHalt = v),
			new Option<>(Group.MOVEMENT, "super_fall_arm", SuperFallArm.class, s -> s.superFallArm, (s, v) -> s.superFallArm = v),
			new Option<>(Group.MOVEMENT, "super_landing", SuperLanding.class, s -> s.superLanding, (s, v) -> s.superLanding = v),
			new Option<>(Group.MOVEMENT, "super_wall", SuperWall.class, s -> s.superWall, (s, v) -> s.superWall = v),
			new Option<>(Group.MOVEMENT, "super_crater", SuperCrater.class, s -> s.superCrater, (s, v) -> s.superCrater = v),
			new Option<>(Group.MOVEMENT, "landing_slide", LandingSlide.class, s -> s.landingSlide, (s, v) -> s.landingSlide = v),
			// Flight: trail, effects
			new Option<>(Group.FLIGHT, "arm_lead", ArmLead.class, s -> s.armLead, (s, v) -> s.armLead = v),
			new Option<>(Group.FLIGHT, "flight_fx", FlightFx.class, s -> s.flightFx, (s, v) -> s.flightFx = v),
			new Option<>(Group.FLIGHT, "flight_shake", FlightShake.class, s -> s.flightShake, (s, v) -> s.flightShake = v),
			// Combat: blast, drill, ram
			new Option<>(Group.COMBAT, "blast_fx", BlastFx.class, s -> s.blastFx, (s, v) -> s.blastFx = v).withPreview("blast"),
			new Option<>(Group.COMBAT, "drill_model", DrillModel.class, s -> s.drillModel, (s, v) -> s.drillModel = v).withPreview("blast"),
			new Option<>(Group.COMBAT, "ram_hole", RamHole.class, s -> s.ramHole, (s, v) -> s.ramHole = v),
			new Option<>(Group.COMBAT, "flight_slam", FlightSlam.class, s -> s.flightSlam, (s, v) -> s.flightSlam = v),
			new Option<>(Group.COMBAT, "absorb_hold", AbsorbHold.class, s -> s.absorbHold, (s, v) -> s.absorbHold = v),
			new Option<>(Group.COMBAT, "hammer_swing", HammerSwing.class, s -> s.hammerSwing, (s, v) -> s.hammerSwing = v),
			// Beams
			new Option<>(Group.BEAMS, "use_fx", UseFx.class, s -> s.useFx, (s, v) -> s.useFx = v).withPreview("use"),
			new Option<>(Group.BEAMS, "omega_start", OmegaStart.class, s -> s.omegaStart, (s, v) -> s.omegaStart = v),
			// Constructs
			new Option<>(Group.CONSTRUCTS, "construct_look", ConstructLook.class, s -> s.constructLook, (s, v) -> s.constructLook = v)
					.withOld(ConstructLook.X3_EMERALD),
			new Option<>(Group.CONSTRUCTS, "wall_look", WallLook.class, s -> s.wallLook, (s, v) -> s.wallLook = v),
			new Option<>(Group.CONSTRUCTS, "barrier_surface", BarrierSurface.class, s -> s.barrierSurface, (s, v) -> s.barrierSurface = v),
			new Option<>(Group.CONSTRUCTS, "construct_opacity", ConstructOpacity.class, s -> s.constructOpacity, (s, v) -> s.constructOpacity = v),
			new Option<>(Group.CONSTRUCTS, "block_glow", BlockGlow.class, s -> s.blockGlow, (s, v) -> s.blockGlow = v),
			// Ring: model, hand, glow
			new Option<>(Group.RING, "ring_model", RingModel.class, s -> s.ringModel, (s, v) -> s.ringModel = v)
					.withOld(RingModel.CREST, RingModel.CREST_GOLD, RingModel.BEACON, RingModel.EMBLEM, RingModel.SIGNET, RingModel.SLIM,
							RingModel.LANTERN, RingModel.CROWN, RingModel.SQUARE),
			new Option<>(Group.RING, "hand_pose", HandPose.class, s -> s.handPose, (s, v) -> s.handPose = v),
			new Option<>(Group.RING, "ring_glow", RingGlow.class, s -> s.ringGlow, (s, v) -> s.ringGlow = v),
			new Option<>(Group.RING, "charge_glow", ChargeGlow.class, s -> s.chargeGlow, (s, v) -> s.chargeGlow = v).withPreview("use"),
			new Option<>(Group.RING, "charge_meter", ChargeMeter.class, s -> s.chargeMeter, (s, v) -> s.chargeMeter = v),
			// Lantern and charge
			new Option<>(Group.LANTERN, "lantern_model", LanternModel.class, s -> s.lanternModel, (s, v) -> s.lanternModel = v),
			new Option<>(Group.LANTERN, "nebula_light", NebulaLight.class, s -> s.nebulaLight, (s, v) -> s.nebulaLight = v),
			new Option<>(Group.LANTERN, "charge_style", ChargeStyle.class, s -> s.chargeStyle, (s, v) -> s.chargeStyle = v).withPreview("charge"),
			new Option<>(Group.LANTERN, "lantern_sun", LanternSun.class, s -> s.lanternSun, (s, v) -> s.lanternSun = v).withPreview("charge"),
			// Corps
			new Option<>(Group.CORPS, "red_look", RedLook.class, s -> s.redLook, (s, v) -> s.redLook = v),
			new Option<>(Group.CORPS, "red_lantern", RedLantern.class, s -> s.redLantern, (s, v) -> s.redLantern = v),
			new Option<>(Group.CORPS, "yellow_look", YellowLook.class, s -> s.yellowLook, (s, v) -> s.yellowLook = v),
			new Option<>(Group.CORPS, "violet_look", VioletLook.class, s -> s.violetLook, (s, v) -> s.violetLook = v),
			new Option<>(Group.CORPS, "blue_look", BlueLook.class, s -> s.blueLook, (s, v) -> s.blueLook = v),
			// Effects and particles
			new Option<>(Group.EFFECTS, "strength", Strength.class, s -> s.strength, (s, v) -> s.strength = v).withPreview("push"),
			new Option<>(Group.EFFECTS, "screen_shake", ScreenShake.class, s -> s.screenShake, (s, v) -> s.screenShake = v).withPreview("blast"),
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
				out.append('\n');
			}
		}
		String durations = RingTuning.report();
		if (!durations.isEmpty()) out.append("Durations changed:\n").append(durations);
		return out.toString();
	}

	private static Path file() {
		return FabricLoader.getInstance().getConfigDir().resolve("lanternring-lab.json");
	}

	private static LabSettings load() {
		Path path = file();
		if (Files.exists(path)) {
			try (Reader reader = Files.newBufferedReader(path)) {
				LabSettings loaded = GSON.fromJson(reader, LabSettings.class);
				if (loaded != null) {
					loaded.fillMissing();
					return loaded;
				}
			} catch (IOException | RuntimeException e) {
				LanternRing.LOGGER.warn("Couldn't read {}, using defaults", path, e);
			}
		}
		LabSettings fresh = new LabSettings();
		fresh.version = 11;
		return fresh;
	}

	/** Old or hand-edited files may lack newer fields; fall back to defaults for those. */
	private void fillMissing() {
		LabSettings defaults = new LabSettings();
		if (version < 2) {
			// The Blockbench ring replaced the earlier drafts; show it once even if another was picked.
			ringModel = RingModel.EMBLEM;
			version = 2;
		}
		if (version < 3) {
			// J's signet rings and the knuckles-in hand: show them once over earlier picks.
			ringModel = RingModel.CREST;
			handPose = HandPose.KNUCKLES_IN;
			version = 3;
		}
		if (version < 4) {
			// J: the ring faces forward, on the front of the fist, rather than up.
			handPose = HandPose.RING_FORWARD;
			version = 4;
		}
		if (version < 5) {
			// J's forged carbon ring with the gold and emerald face: show it once over earlier picks.
			ringModel = RingModel.FORGED;
			version = 5;
		}
		if (version < 6) {
			// J only uses the forged ring; and show the new Dark Lantern once over the keychain one.
			ringModel = RingModel.FORGED;
			lanternModel = LanternModel.DARK;
			version = 6;
		}
		if (version < 7) {
			// J picked the Torus Core battery with the ring handle: show it once over earlier picks.
			lanternModel = LanternModel.TORUS;
			version = 7;
		}
		if (version < 8) {
			// J's stone lantern from the two face sheets: show it once over earlier picks.
			lanternModel = LanternModel.STONE;
			version = 8;
		}
		if (version < 9) {
			// J's round-4 hand-off: W1 neon (dark, rich, translucent) is how constructs should look; show it once.
			constructLook = ConstructLook.W1_NEON;
			version = 9;
		}
		if (version < 10) {
			// J's per-corps construct picks from the Blender kits: show the new Blue and Yellow ones once.
			blueLook = BlueLook.B1;
			yellowLook = YellowLook.Y1;
			version = 10;
		}
		if (version < 11) {
			// J's square emblem picks (Blender pass 596, "the glowing looks great"): show P03 once over earlier picks.
			ringModel = RingModel.P03;
			version = 11;
		}
		// A value an older jar doesn't know loads as null; every menu row falls back to its default.
		for (Option<?> option : OPTIONS) option.fillFrom(this, defaults);
		if (ratings == null) ratings = new TreeMap<>();
		ratings.values().removeIf(r -> r == null || r == Rating.NONE);
	}

	public void save() {
		try (Writer writer = Files.newBufferedWriter(file())) {
			GSON.toJson(this, writer);
		} catch (IOException e) {
			LanternRing.LOGGER.warn("Couldn't save {}", file(), e);
		}
	}
}
