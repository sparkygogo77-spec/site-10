// The site's saved state (ratings, markups, render progress) as files on the `site-data` branch of the private repo
// site-10, through GitHub's contents API. Vercel never deploys that branch, so a save is a commit, not a deploy.
// J (2026-10-19) moved everything here when Vercel Blob started answering 403. Files starting with "_" in api/ are
// not routes. Needs GITHUB_TOKEN (site-10 only, Contents: read and write).
//
// Rate limit (J, 2026-10-20: "Rated it on the website but the website reverted?"): the token's user gets 5000 GitHub
// calls an hour, shared with everything else using that account. So reads are conditional (If-None-Match with the
// last ETag: a 304 doesn't count against the limit), the last good copy is kept in memory, and when GitHub says
// "rate limit exceeded" a read answers from that copy and everything else fails with status 429 + the reset time.
const REPO = process.env.SITE_DATA_REPO || "sparkygogo77-spec/site-10";
const BRANCH = process.env.SITE_DATA_BRANCH || "site-data";
const API = `https://api.github.com/repos/${REPO}/contents/`;
const url = path => API + path.split("/").map(encodeURIComponent).join("/");

let limitedUntil = 0;   // when GitHub said the limit resets (ms), so later errors can say so too
function limitError() {
  const e = new Error("GitHub rate limit: saves are paused for a while");
  e.status = 429; e.resetAt = new Date(Math.max(limitedUntil, Date.now() + 60e3)).toISOString();
  return e;
}

// One GitHub call. Throws {status: 429, resetAt} when the limit is hit (GitHub answers 403 or 429 for that).
export async function ghFetch(u, opts = {}, accept = "application/vnd.github.object") {
  if (!process.env.GITHUB_TOKEN) { const e = new Error("GITHUB_TOKEN is not set in Vercel"); e.status = 503; throw e; }
  const r = await fetch(u, { ...opts, headers: { Accept: accept, "User-Agent": "lantern-review", "X-GitHub-Api-Version": "2022-11-28",
    Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, ...(opts.body ? { "Content-Type": "application/json" } : {}), ...(opts.headers || {}) } });
  if ((r.status === 403 || r.status === 429) && (r.headers.get("x-ratelimit-remaining") === "0" || r.headers.get("retry-after"))) {
    const reset = +r.headers.get("x-ratelimit-reset") || 0, after = +r.headers.get("retry-after") || 0;
    limitedUntil = reset ? reset * 1000 : Date.now() + (after || 60) * 1000;
    throw limitError();
  }
  return r;
}
const fail = async r => { const e = new Error(`GitHub ${r.status}: ${((await r.json().catch(() => ({}))).message || "")}`); e.status = r.status; return e; };

// Error reply shared by the routes: 429 carries resetAt (and Retry-After) so the page can say when saving works again.
export function sendError(res, e) {
  const status = e.status === 429 ? 429 : e.status === 503 ? 503 : e.status === 404 ? 404 : 500;
  if (status === 429) res.setHeader("Retry-After", String(Math.max(5, Math.round((Date.parse(e.resetAt) - Date.now()) / 1000)) || 60));
  return res.status(status).json({ error: String(e && e.message || e), ...(e.resetAt ? { rateLimited: true, resetAt: e.resetAt } : {}) });
}

// Last good copy of each file this instance has read: {etag, data, sha, at}. Warm Vercel instances keep it.
const memo = new Map();

// -> {data, sha, stale?}; data = fallback and sha = null while the file doesn't exist yet
export async function readJson(path, fallback) {
  const key = `${BRANCH}:${path}`, have = memo.get(key);
  let r;
  try {
    r = await ghFetch(`${url(path)}?ref=${BRANCH}`, have?.etag ? { headers: { "If-None-Match": have.etag } } : {});
  } catch (e) {
    if (e.status === 429 && have) return { data: structuredClone(have.data), sha: have.sha, stale: true };
    throw e;
  }
  if (r.status === 304 && have) return { data: structuredClone(have.data), sha: have.sha };
  if (r.status === 404) { memo.delete(key); return { data: fallback, sha: null }; }
  if (!r.ok) throw await fail(r);
  const meta = await r.json();
  let text = Buffer.from(meta.content || "", "base64").toString("utf8");
  if (!meta.content && meta.size) text = await (await ghFetch(`${url(path)}?ref=${BRANCH}`, {}, "application/vnd.github.raw")).text();
  let data;
  try { data = JSON.parse(text) ?? fallback; } catch { data = fallback; }
  memo.set(key, { etag: r.headers.get("etag"), data, sha: meta.sha, at: Date.now() });
  return { data: structuredClone(data), sha: meta.sha };
}

async function put(path, buf, sha, message) {
  return ghFetch(url(path), { method: "PUT", body: JSON.stringify({ branch: BRANCH, message: String(message).slice(0, 120),
    content: buf.toString("base64"), ...(sha ? { sha } : {}) }) });
}

// Read, change, write back with the sha that was read; 409/422 = someone saved in between, so read again.
// mutate(data) changes data in place and returns the reply value (or throws). The read is usually a free 304.
export async function updateJson(path, fallback, mutate, message) {
  for (let attempt = 0; ; attempt++) {
    // Right after our own write we know the file and its sha: write again without reading (a 409 means someone else
    // wrote in between, and the next attempt reads).
    const mine = memo.get(`${BRANCH}:${path}`);
    const { data, sha, stale } = attempt === 0 && mine && mine.sha && !mine.etag
      ? { data: structuredClone(mine.data), sha: mine.sha } : await readJson(path, structuredClone(fallback));
    if (stale) throw limitError();
    const out = mutate(data);
    const r = await put(path, Buffer.from(JSON.stringify(data, null, 1), "utf8"), sha, message);
    if (r.ok) {
      const meta = await r.json().catch(() => null);   // keep what we wrote, so the next read is a cheap 304 or a fresh copy
      memo.set(`${BRANCH}:${path}`, { etag: null, data, sha: meta?.content?.sha || null, at: Date.now() });
      return out;
    }
    if ([409, 422].includes(r.status)) { const m = memo.get(`${BRANCH}:${path}`); if (m && !m.etag) memo.delete(`${BRANCH}:${path}`); }
    if (![409, 422].includes(r.status) || attempt >= 4) throw await fail(r);
  }
}

export async function readBinary(path) {
  const r = await ghFetch(`${url(path)}?ref=${BRANCH}`, {}, "application/vnd.github.raw");
  if (r.status === 404) return null;
  if (!r.ok) throw await fail(r);
  return Buffer.from(await r.arrayBuffer());
}

export async function writeBinary(path, buf, message) {   // new files only (each markup picture has its own id)
  const r = await put(path, buf, null, message);
  if (!r.ok) throw await fail(r);
}

export async function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  const chunks = [];
  for await (const c of req) chunks.push(c);
  try { return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"); } catch { return {}; }
}
