// Markups from the 3D editor: J's drawings, arrows and picked parts on a take, with a prompt for the Blender chat.
// On site-10's site-data branch (_gitstore.js; moved off Vercel Blob 2026-10-19): markups/markups.json (the list) and
// markups/<id>.jpg (the picture with the drawing on it).
//   GET  /api/markups              -> [{id, pass, take, prompt, parts, orbit, time, createdAt, status}]
//   GET  /api/markups?img=<id>     -> the picture
//   POST /api/markups {pass, take, prompt, parts, orbit, time, image}  -> new markup
//   POST /api/markups {id, status} -> status: "new" | "sent" | "done" (the coordinator marks what it passed on)
import { readJson, updateJson, readBinary, writeBinary, readBody } from "./_gitstore.js";

const LIST = "markups/markups.json";
const STATUS = new Set(["new", "sent", "done"]);
const ID = /^[A-Za-z0-9_-]{6,40}$/;
const clip = (v, n) => String(v ?? "").slice(0, n);

export const config = { api: { bodyParser: { sizeLimit: "4mb" } } };

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  try {
    if (req.method === "GET") {
      const img = req.query && req.query.img;
      if (img) {
        if (!ID.test(img)) return res.status(400).json({ error: "id" });
        const buf = await readBinary(`markups/${img}.jpg`);
        if (!buf) return res.status(404).json({ error: "missing" });
        res.setHeader("Content-Type", "image/jpeg");
        res.setHeader("Cache-Control", "private, max-age=86400");
        return res.status(200).send(buf);
      }
      return res.status(200).json((await readJson(LIST, [])).data);
    }
    if (req.method !== "POST") return res.status(405).json({ error: "method" });
    const b = await readBody(req);

    if (b.id && b.status !== undefined) {                       // status update
      if (!STATUS.has(b.status)) return res.status(400).json({ error: "status" });
      const markup = await updateJson(LIST, [], all => {
        const m = all.find(x => x.id === b.id);
        if (!m) { const e = new Error("missing"); e.status = 404; throw e; }
        m.status = b.status; m.updatedAt = new Date().toISOString();
        return m;
      }, `Markup ${b.id}: ${b.status}`);
      return res.status(200).json({ ok: true, markup });
    }

    if (!/^[0-9A-Za-z]{2,12}$/.test(String(b.pass || "")) || !/^[A-Za-z0-9_.+ -]{1,24}$/.test(String(b.take || "")))
      return res.status(400).json({ error: "take" });
    const prompt = clip(b.prompt, 4000).trim();
    const m = /^data:image\/jpeg;base64,([A-Za-z0-9+/=]+)$/.exec(String(b.image || ""));
    if (!prompt && !m) return res.status(400).json({ error: "empty" });
    const id = `${b.pass}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`.replace(/[^A-Za-z0-9_-]/g, "");
    if (m) {
      const buf = Buffer.from(m[1], "base64");
      if (buf.length > 3.5e6) return res.status(413).json({ error: "image too big" });
      await writeBinary(`markups/${id}.jpg`, buf, `Markup picture ${id}`);
    }
    const parts = Array.isArray(b.parts) ? b.parts.slice(0, 20).map(p => ({
      n: Number(p.n) || 0, label: clip(p.label, 60), material: clip(p.material, 80),
      pos: Array.isArray(p.pos) ? p.pos.slice(0, 3).map(Number) : null })) : [];
    const rec = { id, pass: String(b.pass), take: String(b.take), prompt, parts, image: !!m,
      orbit: clip(b.orbit, 80), time: Number(b.time) || 0, createdAt: new Date().toISOString(), status: "new" };
    await updateJson(LIST, [], all => { all.push(rec); }, `Markup ${id} on ${rec.pass} ${rec.take}`);
    return res.status(200).json({ ok: true, markup: rec });
  } catch (e) {
    return res.status(e.status === 404 ? 404 : e.status === 503 ? 503 : 500).json({ error: String(e && e.message || e) });
  }
}
