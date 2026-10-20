# Spider leg movement for procedural animation (giant spider, 8 legs, 36-block span)

2026-10-19

Numbers are given in body lengths (BL, front of the head part to the rear of the abdomen) so they scale to any size. "Inference" marks animator suggestions that no source measured directly.

## 1. Gait
- Default gait is the **alternating tetrapod**. Set A = L1, R2, L3, R4 and set B = R1, L2, R3, L4. Each set swings while the other stands, so on one side legs 1 and 3 move together, and so do legs 2 and 4. Typical stepping order is 4-2-3-1. https://pmc.ncbi.nlm.nih.gov/articles/PMC6935789/
- Phase offsets in *Cupiennius*: left/right legs of a pair about 0.5 cycle apart; ipsilateral leg 3 to leg 4 about 0.54 cycle. Leg 2 shows the loosest left/right coupling. https://pmc.ncbi.nlm.nih.gov/articles/PMC3689776
- Large tarantulas mostly use a "walk-trot" with no airborne phase: R1 and R3 move with L2 and L4. https://pmc.ncbi.nlm.nih.gov/articles/PMC6766366
- Leg 1 phase is erratic, because it does more sensing than walking. https://library.museum.wa.gov.au/internaldocs/49467/WardHumphreys1981SpiderLocoJexpBiol.pdf
- Duty factor (share of the cycle a foot is down):
  - Slow walk: about 0.58–0.61 (tarantula) and 0.63–0.70 (*G. rosea*). https://pmc.ncbi.nlm.nih.gov/articles/PMC6766366 , https://pmc.ncbi.nlm.nih.gov/articles/PMC6935789/
  - Fast run: below 0.5 for legs 1, 2 and 4; leg 3 rarely drops below 0.5. https://pmc.ncbi.nlm.nih.gov/articles/PMC3689776
  - Duty factor falls in a straight line as speed rises. Small funnel-web spiders become airborne above about 54 BL/s, with top speeds over 70 BL/s. https://doi.org/10.1636/b10-45.1
- Speed and size:
  - Speed goes up mainly through stride frequency; stride length stays nearly constant. https://pmc.ncbi.nlm.nih.gov/articles/PMC6766366
  - At speed, *Cupiennius* (3.2 cm body) steps at 6–8 strides/s, while a large tarantula walks at only about 0.6–0.75 strides/s. https://pmc.ncbi.nlm.nih.gov/articles/PMC3689776 , https://pmc.ncbi.nlm.nih.gov/articles/PMC6766366
  - An 18 g tarantula changes to its fast gait above about 11 cm/s. https://air.unimi.it/handle/2434/165003
  - Inference: a giant should step slowly, about 0.5–1 stride/s when walking.

## 2. Leg-tip paths and leg roles
Foot positions relative to the body centre, as fore/aft range with + meaning forward (*Cupiennius*, BL = 32 mm). https://pmc.ncbi.nlm.nih.gov/articles/PMC3689776

| Leg | Fore/aft range | Sideways distance from the body midline |
|---|---|---|
| L1 | +0.5 to +1.6 BL | 0.43 BL |
| L2 | +0.4 to +1.3 BL | 0.92 BL |
| L3 | −0.75 to +0.15 BL | 1.07 BL |
| L4 | −1.45 to −0.7 BL | 0.58 BL |

- Ground stroke (the part of the step with the foot down) is about 1 BL for legs 1–3 and 0.75 BL for leg 4. Stride is about 2.9 BL for legs 1–2 and 2 BL for legs 3–4.
- Leg roles:
  - Legs 1 and 2 drive the body forward by bending (pulling).
  - Leg 3 carries most of the body weight.
  - Leg 4 straightens during stance and holds up the abdomen. https://pmc.ncbi.nlm.nih.gov/articles/PMC3689776
  - Leg 4 is the main pusher, and leg 1 "guides, explores, buffers". https://pmc.ncbi.nlm.nih.gov/articles/PMC6935789/
- Swing height was not measured in any source found. Inference: lift the foot about 0.15–0.25 BL, with the knee rising higher. Leg 4 swings with a larger amplitude on soft ground. https://pmc.ncbi.nlm.nih.gov/articles/PMC6935789/

## 3. Body motion
All values are medians for *Cupiennius* (https://pmc.ncbi.nlm.nih.gov/articles/PMC3689776):

| Measure | Value |
|---|---|
| Body height | 0.31 BL (10 mm) |
| Vertical bob | 0.05 BL |
| Side sway | 0.065 BL |
| Yaw | 5.4° |
| Pitch | 4.6° |
| Roll | 6.6° |

- No rotation goes above 15°.
- Slow bob is about 3.6 Hz in this small spider. Inference: bob twice per stride.
- Tarantula body height is 1.3–1.7 cm. They crouch lower on slippery slopes. https://pmc.ncbi.nlm.nih.gov/articles/PMC6766366

## 4. Joints
- The femur-patella and tibia-metatarsus joints have no extensor muscles. Blood pressure straightens them, and muscles bend them. https://pmc.ncbi.nlm.nih.gov/articles/PMC6935789/ , https://pmc.ncbi.nlm.nih.gov/articles/PMC3689776
- Ranges per stride are about 20–50° at each of these joints. The femur-patella joint works between about 130° and 90°. https://pmc.ncbi.nlm.nih.gov/articles/PMC6935789/
- In a running spider, legs straighten as fast as they bend, so hydraulics do not limit speed. https://research.usc.edu.au/esploro/outputs/journalArticle/Understanding-the-limits-to-the-hydraulic/99544208602621
- Inference (no source measured these): keep the knees well above the body, and keep each leg in its own fore/aft lane so legs never cross. A dead spider curls up because pressure is lost, which works as a death pose.

## 5. Ceilings and walls
- On inclines, duty factor and stride frequency barely change. Stride length shortens on vertical surfaces, and top speed drops. https://pmc.ncbi.nlm.nih.gov/articles/PMC5587489 , https://pmc.ncbi.nlm.nih.gov/articles/PMC6766366
- Grip comes from opposing legs pulling against each other: one leg alone cannot hold a ceiling, but two opposing legs can. Pad area matters little. https://cob.silverchair.com/jeb/article/217/2/222/12593/The-whole-is-more-than-the-sum-of-all-its-parts
- Each foot's grip direction points away from the body centre, so the whole animal works as a holdfast. https://www.nature.com/articles/srep01101
- Forelegs pull with their claw tufts and hind legs push with their scopulae (hairy foot pads). https://pmc.ncbi.nlm.nih.gov/articles/PMC6766366
- No source measured upside-down walking. Inference: always keep at least one opposing pair planted, hold the body closer to the surface, and swing one leg at a time when slow.

## 6. Climbing a dragline
- The front legs tap to find the line, then the rear legs follow and grasp it. https://www.archive.org/download/journalofarach4522017lubb/journalofarach4522017lubb_bw.pdf
- A middle tarsal claw clamps the thread against serrated bristles. Without those bristles, climbing is 5 times slower. https://www.americanarachnology.org/journal-joa/joa-all-articles/article/download/arac-43-03-417.pdf/?no_cache=1
- Spiders descend head-first, feeding out silk while one hind-leg claw controls it. https://www.montananaturalist.org/?p=10027
- No climbing speed was found.

## 7. Digging
- Trapdoor spiders loosen soil with the rastellum, a rake of spines on the chelicerae (the fang-bearing jaws). They roll the soil into a ball and kick it out with their hind legs. https://kids.britannica.com/students/article/trapdoor-spider/313879
- Tarantulas dig with the chelicerae and pedipalps (the short leg-like feelers beside the jaws), then carry the soil out or fling it. https://palaeo-electronica.org/content/2017/2003-neoichnology-of-tarantulas
- *Geolycosa* (burrowing wolf spider) dig cycle (https://pmc.ncbi.nlm.nih.gov/articles/PMC3281395/):
  1. Brace the legs against the burrow walls.
  2. Dig with the convex backs of the fangs.
  3. Legs 1–2 pat the soil into a pellet.
  4. Carry it out on the face of the chelicerae, held by the pedipalps.
  5. At the top, cock the forelegs back over 108 ms, then flick the pellet off at about 0.94 m/s, landing 6–50 cm away.
  - An average burrow takes about 918 pellets.

## 8. Patrol, stalking and strikes
- Wolf spiders mostly sit and wait. https://researchers.mq.edu.au/en/publications/hunting-without-a-web-how-lycosoid-spiders-subdue-their-prey/
- Jumping spiders hunt in steps: detect, turn to face the target, identify it, stalk. https://www.peckhamia.com/peckhamia/PECKHAMIA_317.1.pdf
- Tarantula strike (https://sicb.org/?p=25858):
  - From first leg movement to prey at the mouth takes 250–300 ms; small spiders take under 100 ms.
  - Strikes are usually straight ahead. Small spiders may first turn up to 180°.
- Lycosids hold prey with the scopulae on their legs, using hydraulic extension to keep it at leg's length. The chelicerae alone can hold prey. https://www.americanarachnology.org/journal-joa/joa-all-articles/article/download/JoA_v8_p201_grey.pdf/?no_cache=1
- Inference: for a lunge, raise legs 1–2, keep legs 3–4 planted, then extend hard. Use 1.5–3× the walking duration for the strike, scaled by size.
