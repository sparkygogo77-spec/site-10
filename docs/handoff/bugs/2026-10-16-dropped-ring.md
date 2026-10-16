# Dropped ring: make it a real, physical, glowing ring on the ground (J, 2026-10-16 ~00:45 UTC)

Screenshot `2026-10-16-dropped-ring.png`: a dropped ring item in a dark cave shows as the flat emblem icon lying on the ground, dark,
no glow. J: "change the ring model so it looks like an actual physical glowing ring when dropped".

- Ground (dropped item entity) display: draw the ring's real 3D model (the one `RingModels` / the worn ring uses, in the ring's
  current model and corps colour), at real ring size (a little bigger is fine so it's findable), lying or standing on its band,
  turning slowly like a dropped item.
- Glow: the emerald/face glows (pack-safe glow path, `ShaderGlow`), steady, saturated green, never white; a soft light on the
  ground round it (dynamic light or particles) so it's findable in the dark, like in this cave.
- Keep the flat icon for the inventory/hotbar only.
- Screenshot test: a dropped ring at night or in a dark room, with and without the patched pack.
