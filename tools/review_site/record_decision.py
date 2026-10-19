"""Record J's answers from the decision manager (PC chat or the site's Decisions view).

    python record_decision.py add <card id> "<pick>" ["<note>"] [--from chat|site] [--cards decisions.json]
    python record_decision.py pull [--cards decisions.json]     # answers saved on the site since the last pull

Each answer goes to three places in this repo (run from site-10 or pass --repo):
    docs/decisions/answers.json     every answer, so gen_decisions.py stops showing the card
    docs/blender/review/DECISIONS.md  one line under "Decision manager", newest first, J's pick in his words
    docs/decisions/OUTBOX.md        answers a project thread acts on ("project" cards): the PC chat posts them to the
                                    Site 10 project (after asking J) and ticks them
"pc" cards are acted on by the PC chat straight away; "J" cards are J's own to-dos. Prints one line per answer
with who acts on it, so the chat can route it. The site saves answers to decisions/<time>-<id>.json in the data repo
(lantern-review-data) through /api/files; `pull` reads them back through the same API.
"""
import json, os, re, sys, time, urllib.parse, urllib.request

ARGS = sys.argv[1:]
def opt(name, default=None):
    if name in ARGS:
        i = ARGS.index(name); v = ARGS[i + 1]; del ARGS[i:i + 2]; return v
    return default
REPO = os.path.abspath(opt("--repo", "."))
LIVE = os.path.dirname(REPO)
CARDS = opt("--cards") or next((p for p in (os.path.join(LIVE, "_previews", "decisions", "decisions.json"),
                                            os.path.join(LIVE, "review-site", "data", "decisions.json")) if os.path.exists(p)), None)
SOURCE = opt("--from", "chat")
SITE_URL = "https://lantern-review-j.vercel.app"
ANSWERS = os.path.join(REPO, "docs", "decisions", "answers.json")
OUTBOX = os.path.join(REPO, "docs", "decisions", "OUTBOX.md")
LOG = os.path.join(REPO, "docs", "blender", "review", "DECISIONS.md")
HEAD = "## Decision manager (PC chat menu and the site's Decisions view)"
OWNER = {"pc": "the PC chat acts on it", "project": "for a project thread (OUTBOX.md)", "J": "your to-do"}


def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return default


def card(cid):
    cards = load(CARDS, {}).get("cards", []) if CARDS else []
    return next((c for c in cards if c["id"] == cid), {"id": cid, "title": cid, "owner": "pc", "options": []})


def record(cid, pick, note="", source="chat", at=None, ref=None):
    answers = load(ANSWERS, [])
    if ref and any(a.get("ref") == ref for a in answers):
        return None                                           # already pulled
    c = card(cid)
    star = any(o.get("star") and o["label"].lower() == pick.lower() for o in c.get("options", []))
    at = at or time.strftime("%Y-%m-%d %H:%M")
    # "Not now" / "Later" keep the card open, and "Rate it now" closes itself once the takes are rated: logged, not final
    final = not re.match(r"(not now|later|haven.t tried|rate it now)", pick, re.I)
    a = {"id": cid, "title": c["title"], "pick": pick, "star": star, "note": note, "from": source, "at": at,
         "owner": c.get("owner", "pc"), "final": final}
    if ref:
        a["ref"] = ref
    answers.insert(0, a)
    os.makedirs(os.path.dirname(ANSWERS), exist_ok=True)
    json.dump(answers, open(ANSWERS, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    line = (f"- **{at[:10]} {cid}** {c['title']}: J picked \"{pick}\"{' (★)' if star else ''}"
            f"{f', note: \"{note}\"' if note else ''} [{source}]. {OWNER.get(a['owner'], '')}\n")
    text = open(LOG, encoding="utf-8").read()
    if HEAD not in text:                                      # the section goes above the first dated section
        i = text.index("\n## ") + 1 if "\n## " in text else len(text)
        text = text[:i] + HEAD + "\n\n\n" + text[i:]
    i = text.index(HEAD) + len(HEAD) + 2
    open(LOG, "w", encoding="utf-8").write(text[:i] + line + text[i:])

    if a["owner"] == "project" and final:
        new = not os.path.exists(OUTBOX)
        with open(OUTBOX, "a", encoding="utf-8") as f:
            if new:
                f.write("# Answers for the project threads\n\nJ's answers that a Site 10 project thread acts on. The PC chat "
                        "posts each one to the project (after asking J), then ticks it: `- [x]`.\n\n")
            f.write(f"- [ ] {at[:10]} {cid} {c['title']}: \"{pick}\"{f' ({note})' if note else ''}\n")
    print(f"{cid}: \"{pick}\" -> {OWNER.get(a['owner'], a['owner'])}")
    return a


def pull():
    try:
        with urllib.request.urlopen(SITE_URL + "/api/files?prefix=decisions/", timeout=20) as r:
            files = json.load(r).get("files", [])
    except Exception as e:
        print(f"site answers not reachable ({e}); is GITHUB_TOKEN set in Vercel?")
        return
    got = 0
    for f in sorted(files, key=lambda f: f["path"]):
        if not f["path"].endswith(".json"):
            continue
        try:
            with urllib.request.urlopen(f["url"], timeout=20) as r:
                d = json.load(r)
        except Exception:
            continue
        if record(d["id"], d["pick"], d.get("note", ""), "site", d.get("at"), ref=f["path"]):
            got += 1
    print(f"{got} new answer{'s' if got != 1 else ''} from the site")


if __name__ == "__main__":
    if ARGS[:1] == ["pull"]:
        pull()
    elif ARGS[:1] == ["add"] and len(ARGS) >= 3:
        record(ARGS[1], ARGS[2], ARGS[3] if len(ARGS) > 3 else "", SOURCE)
    else:
        print(__doc__)
