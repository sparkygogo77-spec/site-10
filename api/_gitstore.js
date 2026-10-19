// The site's saved state (ratings, markups, render progress) as files on the `site-data` branch of the private repo
// site-10, through GitHub's contents API. Vercel never deploys that branch, so a save is a commit, not a deploy.
// J (2026-10-19) moved everything here when Vercel Blob started answering 403. Files starting with "_" in api/ are
// not routes. Needs GITHUB_TOKEN (site-10 only, Contents: read and write).
const REPO = process.env.SITE_DATA_REPO || "sparkygogo77-spec/site-10";
const BRANCH = process.env.SITE_DATA_BRANCH || "site-data";
const API = `https://api.github.com/repos/${REPO}/contents/`;
const url = path => API + path.split("/").map(encodeURIComponent).join("/");

async function gh(u, opts = {}, accept = "application/vnd.github.object") {
  if (!process.env.GITHUB_TOKEN) { const e = new Error("GITHUB_TOKEN is not set in Vercel"); e.status = 503; throw e; }
  return fetch(u, { ...opts, headers: { Accept: accept, "User-Agent": "lantern-review", "X-GitHub-Api-Version": "2022-11-28",
    Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, ...(opts.body ? { "Content-Type": "application/json" } : {}) } });
}
const fail = async r => { const e = new Error(`GitHub ${r.status}: ${((await r.json().catch(() => ({}))).message || "")}`); e.status = r.status; return e; };

// -> {data, sha}; data = fallback and sha = null while the file doesn't exist yet
export async function readJson(path, fallback) {
  const r = await gh(`${url(path)}?ref=${BRANCH}`);
  if (r.status === 404) return { data: fallback, sha: null };
  if (!r.ok) throw await fail(r);
  const meta = await r.json();
  let text = Buffer.from(meta.content || "", "base64").toString("utf8");
  if (!meta.content && meta.size) text = await (await gh(`${url(path)}?ref=${BRANCH}`, {}, "application/vnd.github.raw")).text();
  try { return { data: JSON.parse(text) ?? fallback, sha: meta.sha }; } catch { return { data: fallback, sha: meta.sha }; }
}

async function put(path, buf, sha, message) {
  return gh(url(path), { method: "PUT", body: JSON.stringify({ branch: BRANCH, message: String(message).slice(0, 120),
    content: buf.toString("base64"), ...(sha ? { sha } : {}) }) });
}

// Read, change, write back with the sha that was read; 409/422 = someone saved in between, so read again.
// mutate(data) changes data in place and returns the reply value (or throws).
export async function updateJson(path, fallback, mutate, message) {
  for (let attempt = 0; ; attempt++) {
    const { data, sha } = await readJson(path, structuredClone(fallback));
    const out = mutate(data);
    const r = await put(path, Buffer.from(JSON.stringify(data, null, 1), "utf8"), sha, message);
    if (r.ok) return out;
    if (![409, 422].includes(r.status) || attempt >= 4) throw await fail(r);
  }
}

export async function readBinary(path) {
  const r = await gh(`${url(path)}?ref=${BRANCH}`, {}, "application/vnd.github.raw");
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
