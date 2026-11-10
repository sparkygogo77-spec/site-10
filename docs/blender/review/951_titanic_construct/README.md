# Pass 951: the Titanic construct (replaces the Anvil mode's ship)

J, 2026-11-09: "a titanic construct to replace our current one, as big as it can be, it should have random generation
patterns instead of bottom up, it should start from random points and circles all over and connect that way, always
random or maybe just a few repeating random patterns, give me sizes and how accurate we can make it" / "to replace the
anvil mode we have" / "how accurate is the real titanic for size, use that scale".

**Open:** `C:\Users\Josh\Documents\LanternLive\constructs\titanic_construct.blend`, camera `Cam F1`, frames 1-110
(forms 1-80 = 4 s, holds to 110). **Script:** `docs/blender/blender_updates/951_titanic_construct.update.py`.

## Takes

| Take | How it forms | Cameras |
|---|---|---|
| F1 Seeds | 40 random points on the hull, each starting at its own moment, spread along the surface as patches until they meet | Cam F1, Cam F1 close, Cam F1 side |
| F2 Circles | 26 random centres send out expanding rings; the ring lines land first, the bands between fill after | Cam F2, Cam F2 close, Cam F2 side |
| F3 Web | 34 random points throw jagged lines to their nearest neighbours, then the plating spreads from the lines | Cam F3, Cam F3 close, Cam F3 side |
| F4 Mix | F2's rings at half the centres + F3's web between them | Cam F4, Cam F4 close, Cam F4 side |
| B0 Bottom up | how the Anvil builds now (comparison only, not a pick) | Cam B0 |
| SZ Sizes | 1:1 (269 blocks), 1:2 (135), 1:4 (67), the Anvil's current 48-block ship, a 7 x 7 house, a 2-block player | Cam SZ |

`SEED` at the top of the script picks the pattern. Every number is a different pattern ("always random"); a fixed list
of 4 numbers is "a few repeating".

## Size and accuracy (1 block = 1 metre)

| | Real ship | 1:1 | 1:2 | 1:4 | Anvil ship now |
|---|---|---|---|---|---|
| Length | 269.1 m | 269 | 135 | 67 | 48 |
| Beam | 28.2 m | 28 | 14 | 7 | 12 |
| Keel to funnel tops | 53.3 m | 53 | 26 | 13 | 21 |
| Keel to mast tops | about 63 m | 63 | 32 | 16 | - |
| Shell blocks | - | 26,813 | 6,105 | 1,443 | about 3,000 |
| Boxes to draw (up to 16 a side) | - | 3,843 | 675 | 100 | - |
| Boxes to draw (up to 64 a side) | - | 1,398 | 280 | 47 | - |

What reads at each size:
- **1:1**: four raked oval funnels (8 x 6) with dark tops, both masts and the crow's nest, forecastle / well decks /
  poop, three superstructure decks, the open promenade, 16 lifeboats (9 x 3), counter stern, rudder, three propellers,
  porthole rows. Missing: railings, rigging, anything under 1 m.
- **1:2**: funnels (4 x 3), masts, deck steps, lifeboats as bumps. The promenade and propellers go.
- **1:4**: hull shape, four funnel stubs (2 x 2), two masts. Reads as "a liner", not as this ship.

## Check (numbers)

- Every take: all 34,058 faces in by form 0.94 (frame 76); 0 faces never arrive.
- Pacing: 70% by rank, so about the same share of the ship lands every tick in every pattern.
- Emission capped at 1.45 (saturated green, not mint). Material is dithered, 96% opaque.

## For the game (not built yet)

- `AnvilShape` packs x, y, z into 10 bits each (-512..511), so 269 x 28 x 63 fits as it is.
- The Anvil draws one block display per box. 1:1 needs 1,398-3,843 displays against "a few hundred" now: draw it as
  one client mesh instead (the server sends only the seed; each client computes the same arrival pattern).
- Open: build time (4 s here against about 1.8 s for the ship now), the crater of a 269-block ship, charge cost.
