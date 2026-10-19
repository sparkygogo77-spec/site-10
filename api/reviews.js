// Ratings store for the Lantern review site: {"<pass>_<take>": {rating, note, updatedAt}} in reviews/reviews.json on
// site-10's site-data branch (_gitstore.js; moved off Vercel Blob 2026-10-19). Same GET/POST shape as before, so the
// page, pull_reviews.py and the PC chats' take_grid.py need no change.
import { readJson, updateJson, readBody } from "./_gitstore.js";

const PATH = "reviews/reviews.json";
const RATINGS = new Set(["", "KEEP", "IMPROVE", "DROP"]);

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  try {
    if (req.method === "GET") return res.status(200).json((await readJson(PATH, {})).data);
    if (req.method !== "POST") return res.status(405).json({ error: "method" });
    const b = await readBody(req);
    const id = String(b.id || "");
    if (!/^[A-Za-z0-9_.\- ]{1,60}$/.test(id)) return res.status(400).json({ error: "id" });
    if (b.rating !== undefined && !RATINGS.has(b.rating)) return res.status(400).json({ error: "rating" });
    const review = await updateJson(PATH, {}, all => {
      const cur = all[id] || { rating: "", note: "" };
      if (b.rating !== undefined) cur.rating = b.rating;
      if (b.note !== undefined) cur.note = String(b.note).slice(0, 2000);
      if (b.scrapped !== undefined) cur.scrapped = !!b.scrapped;   // "pass_<key>" rows: J scrapped the whole pass
      cur.updatedAt = new Date().toISOString();
      all[id] = cur;
      return cur;
    }, `Rating ${id}: ${b.rating ?? "note"}`);
    return res.status(200).json({ ok: true, review });
  } catch (e) {
    return res.status(e.status === 503 ? 503 : 500).json({ error: String(e && e.message || e) });
  }
}
