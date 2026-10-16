# Remove the right-click flight boom (J, 2026-10-16 ~00:40 UTC)

J: "remove my right click flight boom it keeps messing with me accidentally".

What the code says (main): the sonic boom (`FlightMoves.sonicBoom`) goes off when hyper speed starts, and hyper speed is **shift held
while flying forward** (`FastFlight`), not right-click. So find which flight effect J is getting on **right-click while flying**
(candidates: a ring power fired mid-flight, e.g. Blast or the absorb/return blast R4b; the flight slam; the ram barrier; anything in
`FlightPoses`' keyUse "holding" path) and remove that right-click trigger in flight. If it turns out to be the shift sonic boom, remove
the boom from the hyper-speed start instead (keep hyper speed itself). Ask J if unsure which one; tell him what was removed.
