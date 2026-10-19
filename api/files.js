// Files the site saves to git without a Vercel deploy: they go to the `site-data` branch of the repo (Vercel deploys
// are switched off for that branch) and the page reads them straight from GitHub at the newest commit.
//   GET  /api/files?prefix=models/  -> {sha, cdn, raw, files:[{path, size, url}]}   (url = where to load it from)
//   GET  /api/files?path=models/x.glb -> 302 to that file at the newest commit (use it as an <img>/<video> src)
//   POST /api/files {message, files:[{path, text} | {path, base64} | {path, delete:true}]}
//        -> one commit on site-data; {ok, sha, files:[{path, url}]} (the urls work at once)
// `live/` belongs to J's PC (renders are pushed there with plain git) and can't be written from here.
// Writing needs GITHUB_TOKEN (fine-grained, this repo, Contents: read and write) in the Vercel project's env vars.

const REPO = process.env.SITE_DATA_REPO || "sparkygogo77-spec/site-10";
const BRANCH = process.env.SITE_DATA_BRANCH || "site-data";
const API = `https://api.github.com/repos/${REPO}`;
const PATH = /^(?!live\/)(?!.*\.\.)[A-Za-z0-9_][A-Za-z0-9_.\-\/ ]{0,199}$/;
const CDN_MAX = 20e6;   // jsDelivr serves files up to 20 MB (with the right content type); bigger ones come from raw

const cdnBase = sha => `https://cdn.jsdelivr.net/gh/${REPO}@${sha}/`;
const rawBase = sha => `https://raw.githubusercontent.com/${REPO}/${sha}/`;
const enc = p => p.split("/").map(encodeURIComponent).join("/");
const fileUrl = (sha, path, size) => (size > CDN_MAX ? rawBase(sha) : cdnBase(sha)) + enc(path);

async function gh(path, opts = {}) {
  const headers = { "Accept": "application/vnd.github+json", "User-Agent": "lantern-review", "X-GitHub-Api-Version": "2022-11-28" };
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  const r = await fetch(API + path, { ...opts, headers: { ...headers, ...(opts.body ? { "Content-Type": "application/json" } : {}) } });
  const body = r.status === 204 ? null : await r.json().catch(() => null);
  if (!r.ok) { const e = new Error(`GitHub ${r.status}: ${body && body.message || ""}`); e.status = r.status; throw e; }
  return body;
}

async function head() {
  const ref = await gh(`/git/ref/heads/${BRANCH}`);
  return ref.object.sha;
}

async function listing(prefix) {
  const sha = await head();
  const commit = await gh(`/git/commits/${sha}`);
  const tree = await gh(`/git/trees/${commit.tree.sha}?recursive=1`);
  const files = tree.tree.filter(t => t.type === "blob" && t.path.startsWith(prefix))
    .map(t => ({ path: t.path, size: t.size, url: fileUrl(sha, t.path, t.size) }));
  return { sha, cdn: cdnBase(sha), raw: rawBase(sha), truncated: !!tree.truncated, files };
}

async function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  const chunks = [];
  for await (const c of req) chunks.push(c);
  try { return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"); } catch { return {}; }
}

// One commit with every file in it; retried if something else (J's PC, another tap) committed in between.
async function commit(files, message) {
  const blobs = await Promise.all(files.map(f => f.delete ? null :
    gh("/git/blobs", { method: "POST", body: JSON.stringify({ content: f.base64, encoding: "base64" }) })));
  for (let attempt = 0; ; attempt++) {
    const parent = await head();
    const base = await gh(`/git/commits/${parent}`);
    const tree = await gh("/git/trees", { method: "POST", body: JSON.stringify({ base_tree: base.tree.sha,
      tree: files.map((f, i) => ({ path: f.path, mode: "100644", type: "blob", sha: f.delete ? null : blobs[i].sha })) }) });
    const c = await gh("/git/commits", { method: "POST", body: JSON.stringify({ message, tree: tree.sha, parents: [parent] }) });
    try {
      await gh(`/git/refs/heads/${BRANCH}`, { method: "PATCH", body: JSON.stringify({ sha: c.sha, force: false }) });
      return c.sha;
    } catch (e) {
      if (e.status !== 422 || attempt >= 3) throw e;   // 422 = not a fast-forward: the branch moved, go again
    }
  }
}

export const config = { api: { bodyParser: { sizeLimit: "4.4mb" } } };

export default async function handler(req, res) {
  try {
    if (req.method === "GET") {
      const q = req.query || {};
      if (q.path) {
        const path = String(q.path);
        const l = await listing(path);
        const f = l.files.find(x => x.path === path);
        res.setHeader("Cache-Control", "public, s-maxage=5, stale-while-revalidate=30");
        if (!f) return res.status(404).json({ error: "missing" });
        res.setHeader("Location", f.url);
        return res.status(302).end();
      }
      res.setHeader("Cache-Control", "public, s-maxage=5, stale-while-revalidate=30");   // a few GitHub calls per 5 s at most
      return res.status(200).json(await listing(String(q.prefix || "")));
    }
    res.setHeader("Cache-Control", "no-store");
    if (req.method !== "POST") return res.status(405).json({ error: "method" });
    if (!process.env.GITHUB_TOKEN) return res.status(503).json({ error: "GITHUB_TOKEN is not set in Vercel" });
    const b = await readBody(req);
    const files = Array.isArray(b.files) ? b.files : [];
    if (!files.length || files.length > 20) return res.status(400).json({ error: "files: 1 to 20" });
    const norm = [];
    for (const f of files) {
      const path = String(f && f.path || "");
      if (!PATH.test(path) || path.endsWith("/")) return res.status(400).json({ error: `path: ${path.slice(0, 80)}` });
      if (f.delete) { norm.push({ path, delete: true }); continue; }
      const base64 = f.text !== undefined ? Buffer.from(String(f.text), "utf8").toString("base64") : String(f.base64 || "");
      if (!/^[A-Za-z0-9+/=]*$/.test(base64)) return res.status(400).json({ error: `base64: ${path}` });
      norm.push({ path, base64 });
    }
    const message = String(b.message || `Site: ${norm.map(f => f.path).join(", ")}`).slice(0, 300);
    const sha = await commit(norm, message);
    return res.status(200).json({ ok: true, sha, files: norm.map(f => ({ path: f.path, deleted: !!f.delete,
      url: f.delete ? null : fileUrl(sha, f.path, f.base64.length * 0.75) })) });
  } catch (e) {
    return res.status(e.status === 404 ? 404 : 500).json({ error: String(e && e.message || e) });
  }
}
