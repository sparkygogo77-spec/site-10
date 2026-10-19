// Files the site saves to git without a Vercel deploy. They live on the `site-data` branch of the private repo
// site-10 (Vercel deploys are off for that branch), and this route is the only way in: it reads and writes that one
// branch with GITHUB_TOKEN, never any other.
//   GET  /api/files?prefix=models/      -> {sha, files:[{path, size, url}]}   (url = /api/files?path=…&b=<blob>)
//   GET  /api/files?path=models/x.glb   -> the file (newest version); a listing's url (&b=<blob>&s=<size>) is cached for good
//   POST /api/files {message, files:[{path, text} | {path, base64} | {path, delete:true}]}
//        -> one commit; {ok, sha, files:[{path, url}]}
// `live/` belongs to J's PC (renders are pushed there with plain git) and can't be written from here.
// Needs GITHUB_TOKEN: fine-grained, only site-10, Contents: read and write.

const REPO = process.env.SITE_DATA_REPO || "sparkygogo77-spec/site-10";
const BRANCH = process.env.SITE_DATA_BRANCH || "site-data";
const API = `https://api.github.com/repos/${REPO}`;
const PATH = /^(?!live\/)(?!.*\.\.)[A-Za-z0-9_][A-Za-z0-9_.\-\/ ]{0,199}$/;
const ANY = /^(?!.*\.\.)[A-Za-z0-9_][A-Za-z0-9_.\-\/ ]{0,199}$/;
const SHA = /^[0-9a-f]{40}$/;
const PROXY_MAX = 4e6;   // Vercel functions answer up to 4.5 MB; bigger files get a short-lived GitHub link
const TYPES = { mp4: "video/mp4", webm: "video/webm", jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png",
  webp: "image/webp", gif: "image/gif", json: "application/json", glb: "model/gltf-binary", gltf: "model/gltf+json",
  txt: "text/plain; charset=utf-8", md: "text/plain; charset=utf-8", csv: "text/plain; charset=utf-8" };
const typeOf = p => TYPES[(p.split(".").pop() || "").toLowerCase()] || "application/octet-stream";
const fileUrl = (path, blob, size) => `/api/files?path=${encodeURIComponent(path)}&b=${blob}&s=${size}`;

async function gh(path, opts = {}) {
  if (!process.env.GITHUB_TOKEN) { const e = new Error("GITHUB_TOKEN is not set in Vercel"); e.status = 503; throw e; }
  const headers = { "Accept": "application/vnd.github+json", "User-Agent": "lantern-review", "X-GitHub-Api-Version": "2022-11-28",
    Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, ...(opts.body ? { "Content-Type": "application/json" } : {}), ...(opts.headers || {}) };
  const r = await fetch(API + path, { ...opts, headers });
  if (opts.raw && r.ok) return r;
  const body = r.status === 204 ? null : await r.json().catch(() => null);
  if (!r.ok) { const e = new Error(`GitHub ${r.status}: ${body && body.message || ""}`); e.status = r.status; throw e; }
  return body;
}

async function head() {
  return (await gh(`/git/ref/heads/${BRANCH}`)).object.sha;
}

async function listing(prefix) {
  const sha = await head();
  const commit = await gh(`/git/commits/${sha}`);
  const tree = await gh(`/git/trees/${commit.tree.sha}?recursive=1`);
  const files = tree.tree.filter(t => t.type === "blob" && t.path.startsWith(prefix))
    .map(t => ({ path: t.path, size: t.size, blob: t.sha, url: fileUrl(t.path, t.sha, t.size) }));
  return { sha, truncated: !!tree.truncated, files };
}

// Send one file. Small ones come through here (with Range, which phones need for video); big ones redirect to a
// GitHub download link that works for a few minutes.
async function sendFile(req, res, path, blob, size) {
  if (size > PROXY_MAX) {
    const meta = await gh(`/contents/${path.split("/").map(encodeURIComponent).join("/")}?ref=${BRANCH}`,
      { headers: { Accept: "application/vnd.github.object" } });
    res.setHeader("Cache-Control", "private, max-age=60");
    res.setHeader("Location", meta.download_url);
    return res.status(302).end();
  }
  const r = await gh(`/git/blobs/${blob}`, { raw: true, headers: { Accept: "application/vnd.github.raw" } });
  const buf = Buffer.from(await r.arrayBuffer());
  res.setHeader("Content-Type", typeOf(path));
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("Content-Security-Policy", "sandbox");          // a saved .html/.svg can't run as the site
  res.setHeader("Accept-Ranges", "bytes");
  res.setHeader("Cache-Control", req.query.b ? "public, max-age=31536000, s-maxage=31536000, immutable" : "public, s-maxage=5");
  const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || "");
  if (m && (m[1] || m[2])) {
    const start = m[1] ? +m[1] : Math.max(0, buf.length - +m[2]);
    const end = m[1] && m[2] ? Math.min(+m[2], buf.length - 1) : buf.length - 1;
    if (start > end || start >= buf.length) { res.setHeader("Content-Range", `bytes */${buf.length}`); return res.status(416).end(); }
    res.setHeader("Content-Range", `bytes ${start}-${end}/${buf.length}`);
    return res.status(206).send(buf.subarray(start, end + 1));
  }
  return res.status(200).send(buf);
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
      return { sha: c.sha, blobs };
    } catch (e) {
      if (e.status !== 422 || attempt >= 3) throw e;   // 422 = not a fast-forward: the branch moved, go again
    }
  }
}

export const config = { api: { bodyParser: { sizeLimit: "4.4mb" } } };

export default async function handler(req, res) {
  try {
    if (req.method === "GET" || req.method === "HEAD") {
      const q = req.query || {};
      if (q.path) {
        const path = String(q.path);
        if (!ANY.test(path)) return res.status(400).json({ error: "path" });
        if (q.b && SHA.test(String(q.b)) && /^\d+$/.test(String(q.s)))   // exact version from a listing: no lookup
          return sendFile(req, res, path, String(q.b), +q.s);
        const f = (await listing(path)).files.find(x => x.path === path);
        if (!f) { res.setHeader("Cache-Control", "public, s-maxage=5"); return res.status(404).json({ error: "missing" }); }
        return sendFile(req, res, path, f.blob, f.size);
      }
      res.setHeader("Cache-Control", "public, s-maxage=5, stale-while-revalidate=30");   // a few GitHub calls per 5 s at most
      return res.status(200).json(await listing(String(q.prefix || "")));
    }
    res.setHeader("Cache-Control", "no-store");
    if (req.method !== "POST") return res.status(405).json({ error: "method" });
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
    const { sha, blobs } = await commit(norm, message);
    return res.status(200).json({ ok: true, sha, files: norm.map((f, i) => ({ path: f.path, deleted: !!f.delete,
      url: f.delete ? null : fileUrl(f.path, blobs[i].sha, Buffer.from(f.base64, "base64").length) })) });
  } catch (e) {
    return res.status(e.status === 404 ? 404 : e.status === 503 ? 503 : 500).json({ error: String(e && e.message || e) });
  }
}
