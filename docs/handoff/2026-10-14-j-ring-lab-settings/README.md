# J's Ring Lab settings: keep them, act on his ratings (2026-10-14)

**For:** the mc project chat, in the next jar.

J sent his Ring Lab report from 2.1.647 (`report-2.1.647.txt`; also GitHub issue #323):

> "some of these i havent changed but some i did leave notes on, I need the next jar to consider this and for this to
> save for me"

## 1. Stop overwriting his saved choices (the cause of "some of these I haven't changed")

`LabSettings.fillMissing()` has 10 version steps that **force** a value over J's saved pick: ringModel ×6, handPose,
lanternModel ×3, constructLook, blueLook, yellowLook.

- Replace all of that. A new pick becomes the default **only for rows J has never set.** Keep a `touched` set of option
  keys in `lanternring-lab.json`; any row J changed is touched.
- For a touched row, show a "★ new pick available" badge on the row instead of switching it.
- Never reset a touched row on load. Unknown values (an option removed in a newer jar) fall back to the default and
  are listed in the Copy report as "reset: <row> (<old value> no longer exists)".
- Seed it from this report. On the first load of the new jar, every row in `report-2.1.647.txt` counts as **touched
  with J's value**: what he has now is what he keeps.
- Add a **"Save as my profile" / "Load my profile"** pair in the Ring Lab (`config/lanternring-profile-J.json`), so a
  reset or a new install can get his setup back in one click.

## 2. His notes never arrived (bug)

J says he left notes, but issue #323 says "_(no note)_".

- Check `SendToClaudeScreen`: the typed text must go into the issue body for every action, Redo/Retry included.
- Add a **per-row note**: a small ✎ button on each row with a text box, saved in `lanternring-lab.json` next to the
  rating. Include it in the Copy report (`| note: ...`) and in Send to Claude.
- If any notes are still in his config file, read them back out.

## 3. Act on his ratings (from the report)

- **DROP**: hide them from the menus, behind "Show old takes":
  - constructs H2_NEON;
  - Yellow Y1, Y2 and Y3;
  - Blue B1.
- **KEEP**: protect; never change these without asking.
  - Constructs: W1_NEON, H1_NEON, HW_EMERALD, D1_NEON, W1_EMERALD.
  - Ring models: N01, N04.
  - Hands: RING_FORWARD, KNUCKLES_IN, FIST_DOWN.
  - Glows and effects: AURA, CONSTRUCTS (block glow), HALO, SCORCH, INTENSE.
  - Super jump landing: E2.
  - Charge styles: HAND, FLOAT, HIP.
  - Yellow W1, H1, HW; Blue BR1.
- **IMPROVE**: the next work queue. List these back to J and ask what's wrong with each (Blender chats take the
  visual ones):
  - constructs R2K1, X5_EMERALD, X5_NEON, X1_EMERALD, X3D1_EMERALD;
  - rings FORGED and P03;
  - hand KNUCKLES_FORWARD;
  - charge styles SHRINE, SUMMON, LEAN, PUSH, KNEEL;
  - Blue H1.

## 4. His current values (selected, not starred) are his choices; keep them

| Row | Value |
|---|---|
| Sprint carry | S5b |
| Standing take-off | S2b fastest spring |
| Super jump falling arm | D1B |
| Drill | D2 tiered |
| Ram hole | big crater |
| Constructs | H1 hex neon |
| Wall bricks | BR1 emerald |
| Construct opacity | 30% |
| Ring model | **N04** (not P03) |
| Hand | Knuckles in |
| Lantern | Dark |
| Charge style | Hip carry |
| Yellow | W1 |
| Blue | BR1 |
| Particles | Intense |
| Screen shake | Subtle |

His changed durations stay:

| Duration | J's value | Default |
|---|---|---|
| anvil_build | 0.6 s | 0.25 s |
| anvil_crater_time | 1.05 s | 0.5 s |
| charge_hold | 2 s | 0.5 s |
| charge_time | 1.5 s | 12 s |
| beam cooldown | 0.25 s | 0 s |
| wall cooldown | 0.5 s | 0 s |

J was on 2.1.647. The latest is 2.1.655, which already has the pass 405 landing; he updates through Ring Lab →
Updates.
