# Caps Lock = one-press "shift mode" toggle, and it opens the G ring wheel (J, 2026-10-16 ~00:45 UTC)

J: "caps button should be the new shift mode for now, just a one click switch/cycle and it should also open up the G menu".

- Today, holding **Shift** is the "primed" modifier for ring moves: primed flight slam (518 P1), primed super-jump slam, hyper speed
  in flight (FastFlight: shift while flying forward), and other shift checks (~30 `keyShift.isDown()` / `isShiftKeyDown()` uses).
  **G** is the ring wheel (`key.lanternring.ring_wheel`).
- New: a rebindable key, default **Caps Lock**, that **toggles** primed mode with one press (on/off; "cycle" if there are more than two
  states). While primed is on, every ring move that checks shift behaves as if shift is held; plain Shift keeps working too (sneak).
  Show the state on the HUD (e.g. "Primed" next to the mode name) and with a click sound.
- The same press also **opens the G ring wheel** (coordinator's reading: tapping Caps toggles primed and shows the wheel; G still opens
  the wheel on its own). Confirm with J whether the wheel should open on every Caps press or only when turning primed on.
- "for now": keep it simple and easy to change later.
