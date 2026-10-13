# Brief for a game thread: the Yellow (Sinestro Corps) Blast level 4, "Dread Runner"

From J, in his words: "for Sinestro's blast, give him an animation of sprinting in a scary pace blasting
through whatever I aim him at, he destroys things and leaves fear on the ground that blinds in a yellow light
shadow type darkness on the user".

## The split
- **Blender session (me, branch claude/lantern-redesign-pass2):** the runner's model and animation.
  - The model is an original gaunt yellow hard-light fear construct, built pixel by pixel like the lanterns.
  - It has a sprint cycle at a menacing pace.
  - It is exported as a Blockbench model (`dread_runner.bbmodel`) with its run frames, the same pipeline
    as the Rage Bull and the lanterns.
  - I'll post renders to J and the files to this chat.
- **Game thread (you):** the power itself, using a stand-in until the model lands.

## Game behaviour wanted
1. **Level 4.** Make it the Yellow ring's Blast level 4, like Red's Rage Bull (BlastDrills.BULL, `maxLevel`
   is 4 only for RED today). Charge it the same way as the Bull. Release and the runner bursts out of the ring.
2. **The run.** It sprints along the aim direction at a fast, scary pace (faster than the Bull), ground-hugging,
   through anything:
   - it breaks blocks in a body-sized tunnel (about 3 wide, 4 high);
   - it knocks mobs aside and damages them;
   - it keeps going until its distance or charge runs out.
   - It is steered by where the user aims while the use key is held ("whatever I aim him at").
3. **Fear left on the ground.** Its path leaves a fear trail on the ground: yellow-black smoke and
   shadowy light. Reuse FearNuke's ground fear/smoke look.
4. **The blind.** Anyone standing in the trail, the user included, is blinded by a yellow light / shadow
   darkness:
   - a screen overlay of darkness with sickly yellow light at the edges;
   - it fades over a few seconds after they leave.
   - Like LanternFlash's blinding, but dark-yellow instead of white.
5. **Cost and durations.** Add RingTuning entries (run time, trail time) and a cost line in ChargeMeter.levels
   (as BULL has).

## Notes
- **Jar size.** The jar is at 29.86 MB with palette compression (see docs/findings/2026-10-13-charge-meter-melt-jar.md).
  Keep new textures small or palette them.
- **Model hook.** Leave a hook where the runner is drawn so the bbmodel can drop in. The run animation can
  be a frame set like nebula_glass_f*, or bone rotations.
