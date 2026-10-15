// Ratings store for the Lantern review site: one private JSON blob, {"<pass>_<take>": {rating, note, updatedAt}}.
import { put, get } from "@vercel/blob";

const PATH = "reviews/reviews.json";
const RATINGS = new Set(["", "KEEP", "IMPROVE", "DROP"]);

async function load() {
  const r = await get(PATH, { access: "private", useCache: false });
  if (!r) return {};
  const text = await new Response(r.stream).text();
  try { return JSON.parse(text) || {}; } catch { return {}; }
}

async function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  const chunks = [];
  for await (const c of req) chunks.push(c);
  try { return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"); } catch { return {}; }
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  try {
    if (req.method === "GET") return res.status(200).json(await load());
    if (req.method !== "POST") return res.status(405).json({ error: "method" });
    const b = await readBody(req);
    const id = String(b.id || "");
    if (!/^[A-Za-z0-9_.\- ]{1,60}$/.test(id)) return res.status(400).json({ error: "id" });
    const all = await load();
    const cur = all[id] || { rating: "", note: "" };
    if (b.rating !== undefined) {
      if (!RATINGS.has(b.rating)) return res.status(400).json({ error: "rating" });
      cur.rating = b.rating;
    }
    if (b.note !== undefined) cur.note = String(b.note).slice(0, 2000);
    if (b.scrapped !== undefined) cur.scrapped = !!b.scrapped;   // "pass_<key>" rows: J scrapped the whole pass
    cur.updatedAt = new Date().toISOString();
    all[id] = cur;
    await put(PATH, JSON.stringify(all), { access: "private", addRandomSuffix: false, allowOverwrite: true, contentType: "application/json" });
    return res.status(200).json({ ok: true, review: cur });
  } catch (e) {
    return res.status(500).json({ error: String(e && e.message || e) });
  }
}
