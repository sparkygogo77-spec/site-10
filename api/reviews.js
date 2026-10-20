// Ratings store for the Lantern review site: {"<pass>_<take>": {rating, note, updatedAt}} in reviews/reviews.json on
// site-10's site-data branch (_gitstore.js; moved off Vercel Blob 2026-10-19). Same GET/POST shape as before, so the
// page, pull_reviews.py and the PC chats' take_grid.py need no change.
//   GET  /api/reviews                         -> {id: {rating, note, updatedAt, scrapped?}}  (X-Stale: 1 = last good copy
//                                                 while GitHub's rate limit is hit)
//   POST /api/reviews {id, rating?, note?, scrapped?}            -> {ok, review}
//   POST /api/reviews {items: [{id, rating?, note?, scrapped?}]}  -> {ok, reviews: {id: review}}  (one commit for all;
//        the page sends every tap it is still holding this way)
// Errors: 429 {rateLimited, resetAt} when GitHub's limit is hit; the page keeps the taps and sends them again.
import { readJson, updateJson, readBody, sendError } from "./_gitstore.js";

const PATH = "reviews/reviews.json";
const RATINGS = new Set(["", "KEEP", "IMPROVE", "DROP"]);
const ID = /^[A-Za-z0-9_.\- ]{1,60}$/;

function check(b) {
  const id = String(b && b.id || "");
  if (!ID.test(id)) return "id";
  if (b.rating !== undefined && !RATINGS.has(b.rating)) return "rating";
  return null;
}
function apply(all, b) {
  const id = String(b.id), cur = all[id] || { rating: "", note: "" };
  if (b.rating !== undefined) cur.rating = b.rating;
  if (b.note !== undefined) cur.note = String(b.note).slice(0, 2000);
  if (b.scrapped !== undefined) cur.scrapped = !!b.scrapped;   // "pass_<key>" rows: J scrapped the whole pass
  cur.updatedAt = new Date().toISOString();
  all[id] = cur;
  return cur;
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  try {
    if (req.method === "GET") {
      const { data, stale } = await readJson(PATH, {});
      if (stale) res.setHeader("X-Stale", "1");
      return res.status(200).json(data);
    }
    if (req.method !== "POST") return res.status(405).json({ error: "method" });
    const b = await readBody(req);
    if (Array.isArray(b.items)) {
      const items = b.items.slice(0, 200);
      for (const it of items) { const bad = check(it); if (bad) return res.status(400).json({ error: `${bad}: ${String(it && it.id).slice(0, 60)}` }); }
      if (!items.length) return res.status(400).json({ error: "items" });
      const reviews = await updateJson(PATH, {}, all => Object.fromEntries(items.map(it => [String(it.id), apply(all, it)])),
        items.length === 1 ? `Rating ${items[0].id}: ${items[0].rating ?? "note"}` : `Ratings: ${items.length} taps (${items.map(i => i.id).join(", ")})`);
      return res.status(200).json({ ok: true, reviews });
    }
    const bad = check(b);
    if (bad) return res.status(400).json({ error: bad });
    const review = await updateJson(PATH, {}, all => apply(all, b), `Rating ${b.id}: ${b.rating ?? "note"}`);
    return res.status(200).json({ ok: true, review });
  } catch (e) {
    return sendError(res, e);
  }
}
