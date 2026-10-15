# Hand-off: the "What's New" checklist book, and pass names on everything (J, 2026-10-15)

J: "I need the name passes of these updated, and for my in-game I should start on the newest features and sorted a checklist of
what's new and untested as a book that checks them once I've done them and how to get to them."

## 1. Pass names on everything in game
Every feature and Ring Lab option that came from a Blender pass shows its pass number and the take's name **as written on the review
site** (for example "Pass 807 · L3 Core swirl", "Pass 502 · P1b Step-in jab"), so J can match what he rated on the site to what he
is testing. Ring Lab rows already have picks and badges; add the pass label wherever one is missing, and use it in the book.

## 2. The What's New book
- **Item:** a written book ("What's New", Lantern Ring cover) given once when a new jar first loads, and craftable/obtainable from
  the Ring Lab (a "Get the What's New book" button) so it can be replaced. Opening it shows the current jar's version on page 1.
- **Order:** newest first, by the date the feature entered the jar. Each jar adds its new entries at the top.
- **Each entry:**
  - the name, with its pass label from section 1;
  - **How to get to it:** the exact steps (which item/slot, which ring mode, which key, which Ring Lab tab and row,
    e.g. "Ring in hand → Mode: Bridge → hold right-click to pick a level, hold left-click to build");
  - a box: ☐ untested / ☑ done.
- **Ticks itself:** each entry has a trigger that fires when J actually does the thing (power fired in that mode, landing type
  happened, Ring Lab option selected, lantern charged to overcharge…). The server records it per player, so it survives restarts and
  updates. Things without a clean trigger get a "Mark done" click in the book.
- **Untested first:** done entries move to a "Done" section at the back (still listed), so the front of the book is always what's
  left to try, newest first.
- **Data:** the entries live in one data file in the jar (id, date, pass label, title, how-to steps, trigger id), so each new feature
  adds one line. Keep this file up to date with every jar.
- Add a client game test that opens the book and screenshots page 1, and one that fires a trigger and checks the tick.

## 3. Seed entries (newest first; check the steps against the code, and add anything player-facing I missed)
From `main` commits up to jar 2.1.667 (the three in-game bugs J reported tonight are in `docs/handoff/bugs/` and should be fixed
before these are marked as ready to test):

| Date | Pass | Feature |
|---|---|---|
| 10-15 | 836 | Eight test lasers as Ring Lab Beam look options |
| 10-15 | (bubble) | Lasso bubble: steady physics and working controls |
| 10-15 | 807 · L3 Core swirl | Lantern charge light (see bug: currently lights the whole glass) |
| 10-15 | 815 · F1, F3 | Hit effects: construct shatter, outline flash on hurt mobs |
| 10-14 | 335 picks | Landing L4 with 0.3 carry; arm lead D1/D3; dart free arm A2/A1 |
| 10-14 | — | Ring slot: a worn ring stays on the right hand |
| 10-14 | — | Tools mode: construct tools as hotbar items, drawn on the worn ring too |
| 10-14 | 518 | Primed slams (shift) and shift hyper speed; slams/slides follow the ground, lined trench |
| 10-14 | 519 | Set-down lantern one block tall, Ring Lab switch to in-hand size; hip carry; first-person kneel |
| 10-14 | — | Ring Lab: keeps J's settings, new-pick badge, row notes, profiles |
| 10-14 | 519 · R2a, R2b | Construct hammer: Hammer mode tap, overhead and side swings on walls |
| 10-14 | 405 | Landing: brake and drop in, descend while flying forward |
| 10-14 | 506 · Z1-Z3 | Omega beams (hold Z): zigzag Z2 default, E2 routing, K1 snap strike, barrage, on X, under water |
| 10-14 | 801 | Rings R19d, R12b, R12c (plain), R16a in the Ring Lab ring row |
| 10-14 | 596 | Square emblem rings P03 (default), N01, N04 |
| 10-14 | — | Double-jump take-off, L2 soft landing, ring arm lead; sprint double-tap in a super jump starts ground flight |
| 10-14 | S3 M3, F2, R4b | Combat: big flight slam, flying flurry, absorb and return blast (see bug: no first-person flurry) |
| 10-14 | 400 | Power landing: stop dead, dissolve slide, plough |
| 10-14 | — | Ring Lab overhaul: tabs, search, keyboard nav, starred picks, grouped report |
| 10-14 | L1c, K3c | Charge: lantern on the block ahead, kneel and lift, glass glows from the start |
| 10-14 | F2, T4 | Sprint run, F2 take-off, ground flight, T4 trail, sonic boom |
| 10-14 | — | Saw mode: drag out a hard-light saw, hold left-click to cut a trench |
| 10-14 | L1, L4 | Nebula light in the construct look (Column, Core & cage) |
| 10-14 | T3, U3 | Green/Blue rings form construct tools as you mine or fight |
| 10-14 | — | Black hole: spreading eat, longer reach, final bang |
| 10-14 | D1-D3, T1-T9 | Blast drills in construct brick; barrier surfaces as Ring Lab options |
| 10-14 | A6 | Hope sanctuary battery + cone |
| 10-13/14 | — | Super jump/sprint: crouch-charged leap, lower forward arc, camera tilt, R1 ribbon trail, crater + dome landing |
| 10-13 | — | Hammer mode (solid hammer, aimed leap and smash) |
| 10-13 | — | Ram barrier on fast flight (1.75 s build, clashes, 2 s cooldown) |
| 10-13 | — | Bridge (pick a level, build toward the crosshair, step up/down) and Wall (pin and drag 3x3 to 17x17) |
| 10-13 | — | Blue Lantern rescue squad, Red rage, Orange horde, Red self-destruct, Fear Nuke, Dread Runner |

## 4. For J (coordinator)
Tell J the book's name, how to get it, and which jar it ships in.
