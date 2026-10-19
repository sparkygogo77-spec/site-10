// Live status of the render running on J's PC, so he can watch it on the site instead of the command window.
// Kept in render/status.json on site-10's site-data branch (_gitstore.js; moved off Vercel Blob 2026-10-19).
//   GET  /api/render  -> {running, startedAt, updatedAt, pass, take, done, total, etaSec, uploaded, failures:[...], finishedAt}
//   POST /api/render  {...same fields}  (sent by tools/lantern_review.py after every take)
import { readJson, updateJson, readBody } from "./_gitstore.js";

const PATH = "render/status.json";
const s = (v, n) => String(v ?? "").slice(0, n);
const n = v => (Number.isFinite(+v) ? +v : 0);

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  try {
    if (req.method === "GET") return res.status(200).json((await readJson(PATH, { running: false })).data);
    if (req.method !== "POST") return res.status(405).json({ error: "method" });
    const b = await readBody(req);
    const st = {
      running: !!b.running, startedAt: s(b.startedAt, 30), updatedAt: new Date().toISOString(), finishedAt: s(b.finishedAt, 30),
      pass: s(b.pass, 12), take: s(b.take, 24), done: n(b.done), total: n(b.total), etaSec: n(b.etaSec), uploaded: n(b.uploaded),
      note: s(b.note, 200),
      failures: Array.isArray(b.failures) ? b.failures.slice(0, 30).map(f => s(f, 160)) : [],
    };
    await updateJson(PATH, {}, cur => { for (const k of Object.keys(cur)) delete cur[k]; Object.assign(cur, st); },
      `Render ${st.running ? `${st.pass} ${st.take} ${st.done}/${st.total}` : "finished"}`);
    return res.status(200).json({ ok: true });
  } catch (e) {
    return res.status(e.status === 503 ? 503 : 500).json({ error: String(e && e.message || e) });
  }
}
