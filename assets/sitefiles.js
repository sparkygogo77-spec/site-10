// SiteFiles: save files to git from the site and read them back, with no Vercel deploy (see api/files.js).
//   const m = await SiteFiles.list("models/")            -> {sha, files:[{path, size, url}]}
//   SiteFiles.url(m, "models/x.glb")                      -> where to load it from, or null
//   await SiteFiles.save([{path:"models/x.glb", blob}], "3D for x")   // blob | text | base64 | delete:true
//   await SiteFiles.readJSON("notes/todo.json")           -> the parsed file, or null when it isn't there
// Saves show up for everyone within about 5 seconds; the url save() returns works at once.
(function () {
  const toBase64 = blob => new Promise((ok, bad) => {
    const r = new FileReader();
    r.onload = () => ok(String(r.result).split(",")[1] || "");
    r.onerror = () => bad(r.error);
    r.readAsDataURL(blob);
  });
  const SiteFiles = {
    async list(prefix = "") {
      const r = await fetch("/api/files?prefix=" + encodeURIComponent(prefix));
      if (!r.ok) throw new Error("list failed: " + r.status);
      return r.json();
    },
    url(listing, path) {
      const f = listing && listing.files.find(x => x.path === path);
      return f ? f.url : null;
    },
    async save(files, message) {
      const body = { message, files: await Promise.all(files.map(async f =>
        f.delete ? { path: f.path, delete: true }
        : f.blob ? { path: f.path, base64: await toBase64(f.blob) }
        : f.base64 !== undefined ? { path: f.path, base64: f.base64 }
        : { path: f.path, text: typeof f.text === "string" ? f.text : JSON.stringify(f.text ?? f.json, null, 1) })) };
      const r = await fetch("/api/files", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
      const out = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(out.error || "save failed: " + r.status);
      return out;   // {ok, sha, files:[{path, url}]}
    },
    async readText(path) {
      const u = SiteFiles.url(await SiteFiles.list(path), path);
      return u ? (await fetch(u)).text() : null;
    },
    async readJSON(path) {
      const t = await SiteFiles.readText(path);
      return t == null ? null : JSON.parse(t);
    },
  };
  window.SiteFiles = SiteFiles;
})();
