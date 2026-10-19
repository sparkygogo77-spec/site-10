// Ratings store for the Lantern review site: {"<pass>_<take>": {rating, note, updatedAt}} in reviews/reviews.json on the
// `site-data` branch of the private repo site-10 (no Vercel deploy on that branch). J (2026-10-19) moved it off Vercel
// Blob, which started answering 403: "Move ratings to git". Same GET/POST shape as before, so the page,
// pull_reviews.py and the PC chats' take_grid.py need no change. Needs GITHUB_TOKEN (site-10, Contents read/write).
const REPO = process.env.SITE_DATA_REPO || "sparkygogo77-spec/site-10";
const BRANCH = process.env.SITE_DATA_BRANCH || "site-data";
const FILE = `https://api.github.com/repos/${REPO}/contents/reviews/reviews.json`;
const RATINGS = new Set(["", "KEEP", "IMPROVE", "DROP"]);

async function gh(url, opts = {}) {
  if (!process.env.GITHUB_TOKEN) { const e = new Error("GITHUB_TOKEN is not set in Vercel"); e.status = 503; throw e; }
  return fetch(url, { ...opts, headers: { "Accept": "application/vnd.github.object", "User-Agent": "lantern-review",
    "X-GitHub-Api-Version": "2022-11-28", Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
    ...(opts.body ? { "Content-Type": "application/json" } : {}) } });
}

// -> {all, sha}; sha is null until the first rating creates the file
async function load() {
  const r = await gh(`${FILE}?ref=${BRANCH}`);
  if (r.status === 404) return { all: {}, sha: null };
  if (!r.ok) { const e = new Error(`GitHub ${r.status}`); e.status = r.status; throw e; }
  const meta = await r.json();
  let text = Buffer.from(meta.content || "", "base64").toString("utf8");
  if (!meta.content && meta.download_url) text = await (await gh(meta.download_url)).text();   // over 1 MB
  try { return { all: JSON.parse(text) || {}, sha: meta.sha }; } catch { return { all: {}, sha: meta.sha }; }
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
    if (req.method === "GET") return res.status(200).json((await load()).all);
    if (req.method !== "POST") return res.status(405).json({ error: "method" });
    const b = await readBody(req);
    const id = String(b.id || "");
    if (!/^[A-Za-z0-9_.\- ]{1,60}$/.test(id)) return res.status(400).json({ error: "id" });
    if (b.rating !== undefined && !RATINGS.has(b.rating)) return res.status(400).json({ error: "rating" });
    // read, change one row, write back with the sha we read; 409/422 = someone saved in between, so read again
    for (let attempt = 0; ; attempt++) {
      const { all, sha } = await load();
      const cur = all[id] || { rating: "", note: "" };
      if (b.rating !== undefined) cur.rating = b.rating;
      if (b.note !== undefined) cur.note = String(b.note).slice(0, 2000);
      if (b.scrapped !== undefined) cur.scrapped = !!b.scrapped;   // "pass_<key>" rows: J scrapped the whole pass
      cur.updatedAt = new Date().toISOString();
      all[id] = cur;
      const put = await gh(FILE, { method: "PUT", body: JSON.stringify({ branch: BRANCH, ...(sha ? { sha } : {}),
        message: `Rating ${id}: ${cur.rating || "-"}`.slice(0, 120),
        content: Buffer.from(JSON.stringify(all, null, 1), "utf8").toString("base64") }) });
      if (put.ok) return res.status(200).json({ ok: true, review: cur });
      if (![409, 422].includes(put.status) || attempt >= 4) {
        const e = new Error(`GitHub ${put.status}: ${((await put.json().catch(() => ({}))).message || "")}`); e.status = put.status; throw e;
      }
    }
  } catch (e) {
    return res.status(e.status === 503 ? 503 : 500).json({ error: String(e && e.message || e) });
  }
}
