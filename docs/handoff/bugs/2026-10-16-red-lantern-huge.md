# Red lantern still huge when charging (J, 2026-10-16 ~01:00 UTC)

Screenshot `2026-10-16-red-lantern-huge.png` (first person, Red ring charging at the Red lantern, "Ring charge: 100%",
"OVERCHARGE +3% 25/25", patched Complementary). J: "red lantern still huge".

- The charging Red lantern is several times the size of the Green/Dark lantern in the same pose and fills half the view. Match the
  Dark Lantern's first-person charge size and placement (LanternFirstPerson scale x look.size()); check the Red battery/lantern's
  model scale and its `look.size()`.
- Also: its stone now reads glossy pink-white, not the approved deep glossy crimson sRGB (188, 30, 47). If the new specular map went
  in, it's too strong or the base colour got washed out; keep the gem shine but the colour must stay deep crimson.
