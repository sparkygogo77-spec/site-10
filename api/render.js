// Live status of the render running on J's PC, so he can watch it on the site instead of the command window.
//   GET  /api/render  -> {running, startedAt, updatedAt, pass, take, done, total, etaSec, uploaded, failures:[...], finishedAt}
//   POST /api/render  {...same fields}  (sent by tools/lantern_review.py after every take)
import { put, get } from "@vercel/blob";

const PATH = "render/status.json";

async function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  const chunks = [];
  for await (const c of req) chunks.push(c);
  try { return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"); } catch { return {}; }
}
const s = (v, n) => String(v ?? "").slice(0, n);
const n = v => (Number.isFinite(+v) ? +v : 0);

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  try {
    if (req.method === "GET") {
      const r = await get(PATH, { access: "private", useCache: false });
      if (!r) return res.status(200).json({ running: false });
      return res.status(200).send(await new Response(r.stream).text());
    }
    if (req.method !== "POST") return res.status(405).json({ error: "method" });
    const b = await readBody(req);
    const st = {
      running: !!b.running, startedAt: s(b.startedAt, 30), updatedAt: new Date().toISOString(), finishedAt: s(b.finishedAt, 30),
      pass: s(b.pass, 12), take: s(b.take, 24), done: n(b.done), total: n(b.total), etaSec: n(b.etaSec), uploaded: n(b.uploaded),
      note: s(b.note, 200),
      failures: Array.isArray(b.failures) ? b.failures.slice(0, 30).map(f => s(f, 160)) : [],
    };
    await put(PATH, JSON.stringify(st), { access: "private", addRandomSuffix: false, allowOverwrite: true, contentType: "application/json" });
    return res.status(200).json({ ok: true });
  } catch (e) {
    return res.status(500).json({ error: String(e && e.message || e) });
  }
}
