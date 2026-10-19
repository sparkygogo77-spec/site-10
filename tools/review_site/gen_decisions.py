"""Build decisions.json: every open decision in J's Lantern Ring work, as cards with a ★ pick (the decision manager).

    python gen_decisions.py [SITE_DIR] [--repo DIR] [--ref REF] [--out FILE]

J (2026-10-18): "I need a decision manager built into chat that gives me better descriptions and visuals and controls
this chat, and if we can then embed this in the website". The PC chat turns each card into an AskUserQuestion
("Menu: decisions" in docs/handoff/PC-CHAT-BRIEF.md); the review site's Control tab shows the same cards and saves
J's answers to decisions/<time>-<id>.json in the data repo (no deploy). tools/review_site/pull_decisions.py brings those
answers back into docs/decisions/answers.json and DECISIONS.md.

Cards come from (git REF in --repo, default origin/dev in SITE_DIR, the same as gen_control.py):
    docs/blender/review/INBOX.md            WAITING passes with takes J hasn't rated   -> kind "rate"
    docs/handoff/2026-10-18-total-handover.md  Part 1 questions                          -> kind "question"
    docs/pc_requests/*.md (not done/)       jobs threads sent to the PC                 -> kind "request"
    docs/decisions/chats.json               what each linked chat is waiting on         -> kind "chat"
minus everything already in docs/decisions/answers.json. Ratings come from the live site (/api/reviews), else from
docs/blender/review/ratings.json. Pictures: "pass" cards point at that pass on the site (the page draws its clip);
the PC chat makes stills with tools/review_site/decision_stills.py.
"""
import json, os, re, subprocess, sys, time, urllib.request

ARGS = sys.argv[1:]
def opt(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS and ARGS.index(name) + 1 < len(ARGS) else default
POS = [a for i, a in enumerate(ARGS) if not a.startswith("--") and (i == 0 or not ARGS[i - 1].startswith("--"))]
SITE = os.path.abspath(POS[0] if POS else "/home/claude/review-site")
REPO = os.path.abspath(opt("--repo", SITE))
REF = opt("--ref", "origin/dev")
OUT = opt("--out", os.path.join(SITE, "data", "decisions.json"))
SITE_URL = "https://lantern-review-j.vercel.app"
HANDOVER = "docs/handoff/2026-10-18-total-handover.md"

# Who acts on an answer. "pc" = the PC chat (Claude Code on J's PC) does it; "project" = a thread in the Site 10
# project changes the mod (the PC chat posts the answer there, after asking J); "J" = only J can do it.
SECTION_OWNER = {"Sword": "project", "Dropped ring": "project", "Lantern charging": "project", "Combat": "project",
                 "Fear Nuke": "project", "Movement": "project", "Looks": "project", "Blender": "pc", "Other": "pc"}
SECTION_WHY = {
    "Sword": "The sword still swings like vanilla until these are set; pass 852's swings are waiting on them.",
    "Dropped ring": "Sets how a dropped ring looks on the ground in the next jar.",
    "Lantern charging": "Fixes how charging feels in the next jar.",
    "Combat": "Settles how hits feel; the Hard light tools thread is stopped on the back-hand fist.",
    "Fear Nuke": "Settles how the Fear Nuke is aimed and fired.",
    "Movement": "Settles landings and sliding in the next jar.",
    "Looks": "Picks the looks the game uses; the Ultimate dome's beam-up waits on the beam.",
    "Blender": "Tells the Blender chats what to build next.",
    "Other": "Housekeeping: the website and where the project carries on.",
}
SKIP_QUESTIONS = {"28"}     # "Blender inbox": each WAITING pass is its own card now


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def show(path):
    if REF == "WORKTREE":                              # the PC chat reads its own checkout, uncommitted edits too
        try:
            return open(os.path.join(REPO, path), encoding="utf-8").read()
        except OSError:
            return ""
    return git("show", f"{REF}:{path}")


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"\*\*|`", "", s)).strip()


def short(s, n=220):
    s = clean(s)
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def ratings():
    try:
        with urllib.request.urlopen(SITE_URL + "/api/reviews", timeout=15) as r:
            return json.load(r), "site"
    except Exception:
        try:
            return json.loads(open(os.path.join(REPO, "docs/blender/review/ratings.json"), encoding="utf-8").read()), "ratings.json"
        except Exception:
            return {}, "none"


def rate_cards(site, rev):
    inbox = show("docs/blender/review/INBOX.md")
    entries = re.findall(r"^## (\d{4}-\d\d-\d\d) pass (\d+)(?: rev \d+| update)?: (.+?)\s+\[(?:status: )?([A-Z ]+?)(?:[:\]])", inbox, re.M)
    passes = {p["key"]: p for p in site.get("passes", [])}
    titles = [(n, t) for _, n, t, _ in entries] + [(p["pass"], p["title"]) for p in site.get("passes", [])]
    out, seen, unrendered = [], set(), []
    for date, num, title, status in entries:
        if status.strip() != "WAITING" or num in seen:
            continue
        seen.add(num)
        p = passes.get(num)
        if p and (rev.get(f"pass_{num}", {}).get("scrapped") or p.get("superseded_by")):
            continue
        shown = [t for t in (p or {}).get("takes", []) if t.get("clip3p") or t.get("clipfp") or t.get("still")]
        if not shown:
            unrendered.append(num)
            continue
        left = [t for t in shown if not rev.get(t["id"], {}).get("rating")]
        refs = sorted({n for n, t in titles if n != num and re.search(rf"\b{num}\b", t)})
        if not left:
            # all rated: if J asked for changes and no later pass picked them up yet, the next round is his call
            imp = [t for t in shown if rev.get(t["id"], {}).get("rating") == "IMPROVE"]
            if imp and not refs:
                notes = "; ".join(f"{t['code']}: {rev[t['id']]['note']}" for t in imp if rev[t["id"]].get("note"))
                keep = [t["code"] for t in shown if rev.get(t["id"], {}).get("rating") == "KEEP"]
                out.append({
                    "id": f"next-{num}", "kind": "improve", "group": "Next round from your IMPROVE takes", "pass": num,
                    "date": date, "title": f"Pass {num}: next round of {', '.join(t['code'] for t in imp)}",
                    "plain": short(f"{clean(p['title'])}. You rated {len(imp)} take{'s' if len(imp) > 1 else ''} IMPROVE"
                                   + (f" ({notes})" if notes else " with no note") + (f"; KEEP: {', '.join(keep)}" if keep else "") + "."),
                    "why": "Nothing builds on it yet: the Blender chat waits for how to change them.",
                    "takes": [t["code"] for t in imp], "link": f"{SITE_URL}/#{num}/{imp[0]['code']}",
                    "options": [{"label": "3 variations of each", "star": True, "note": "the PC chat builds the next pass"},
                                {"label": "1 variation of each"},
                                {"label": "Leave them", "note": "marks the pass PICKED; KEEPs go to the game"}],
                    "owner": "pc", "score": 2 * len(imp)})
            continue
        why = (f"{len(refs)} later pass{'es build' if len(refs) > 1 else ' builds'} on it ({', '.join(refs)})" if refs
               else "Your ratings tell the Blender chat what to change or hand to the game")
        out.append({
            "id": f"pass-{num}", "kind": "rate", "group": "Rate on the review site", "pass": num, "date": date,
            "title": f"Pass {num}: {clean(p['title'])}",
            "plain": short(p.get("desc") or title),
            "why": why + f". {len(left)} of {len(shown)} takes still to rate.",
            "takes": [t["code"] for t in left],
            "link": f"{SITE_URL}/#{num}/{left[0]['code']}",
            "options": [{"label": "Rate it now", "star": True, "note": "opens the pass on the review site"},
                        {"label": "Drop the whole pass", "note": "stale: the chat marks it DROPPED"},
                        {"label": "Not now", "note": "stays on the list"}],
            "owner": "pc", "score": len(left) + 5 * len(refs),
        })
    return out, unrendered


def question_cards():
    text = show(HANDOVER)
    part = text.split("## Part 1", 1)[-1].split("\n## Part 2", 1)[0]
    out, section, context, last = [], "Other", "", None
    for line in part.splitlines():
        if line.startswith("### "):
            head = line[4:].strip()
            section = next((k for k in SECTION_OWNER if head.lower().startswith(k.lower())), "Other")
            group, context = head, ""
            continue
        m = re.match(r"^(\d+)\. \*\*(.+?):?\*\*:? ?(.*)$", line)
        if m:
            num, name, rest = m.groups()
            last = None
            if num in SKIP_QUESTIONS:
                continue
            before, _, after = rest.partition("★")
            opts = [clean(o) for o in re.split(r" / ", after) if clean(o)] if after else []
            options = [{"label": o[:120], "star": i == 0} for i, o in enumerate(opts)]
            passes = sorted(set(re.findall(r"\bpass(?:es)? (\d{3})", name + " " + rest)))
            last = {"id": f"q-{num}", "kind": "question", "group": group, "num": int(num),
                    "title": f"{num}. {clean(name)}", "plain": short(before.rstrip(" :") or context or name),
                    "why": SECTION_WHY[section],
                    "options": options or [{"label": "Yes", "star": True}, {"label": "No"}],
                    "owner": SECTION_OWNER[section], "pass": passes[0] if passes else None,
                    "link": f"{SITE_URL}/#{passes[0]}" if passes else None}
            out.append(last)
        elif line.startswith("Plan:"):
            context = short(re.sub(r"^Plan: \S+\.? ?", "", line), 200)
        elif line.strip().startswith("- ") and last:
            last["plain"] += " Also: " + short(line.strip()[2:], 200)
    return out


def request_cards():
    out = []
    names = (os.listdir(os.path.join(REPO, "docs/pc_requests")) if REF == "WORKTREE"
             else git("ls-tree", "--name-only", f"{REF}:docs/pc_requests/").split())
    for path in names:
        if not path.endswith(".md") or path == "README.md":
            continue
        body = show(f"docs/pc_requests/{path}")
        head = dict(re.findall(r"^(route|pass|from|blend):\s*(.+?)\s*(?:#.*)?$", body, re.M))
        what = "\n".join(l for l in body.splitlines() if l.strip() and not re.match(r"^(route|pass|from|script|blend):", l))
        out.append({"id": f"req-{path[:-3]}", "kind": "request", "group": "Jobs threads sent to the PC",
                    "title": f"Job from a thread: {path[:-3]}", "plain": short(what),
                    "why": f"A thread ({head.get('from', 'unknown')}) is waiting on the PC for this.",
                    "pass": head.get("pass"), "options": [{"label": "Start it here", "star": True},
                    {"label": "Later"}, {"label": "Say no", "note": "moved to done/ with your reason"}],
                    "owner": "pc", "link": None})
    return out


def chat_cards():
    try:
        rows = json.loads(show("docs/decisions/chats.json") or "[]")
    except ValueError:
        rows = []
    for r in rows:
        r.setdefault("kind", "chat"); r.setdefault("group", "Chats waiting on you")
        r.setdefault("owner", "J"); r.setdefault("pass", None); r.setdefault("link", None)
    return rows


def main():
    try:
        site = json.load(open(os.path.join(SITE, "data", "site.json"), encoding="utf-8"))
    except Exception:
        site = {}
    try:
        answered = {a["id"] for a in json.loads(show("docs/decisions/answers.json") or "[]") if a.get("final", True)}
    except ValueError:
        answered = set()
    rev, source = ratings()
    rate, unrendered = rate_cards(site, rev)
    rate.sort(key=lambda c: -c["score"])
    cards = [c for c in chat_cards() + request_cards() + rate + question_cards() if c["id"] not in answered]
    first = next((c for c in cards if c["kind"] == "rate"), None)
    for c in cards:
        c["first"] = c is first or c["kind"] in ("chat", "request")
    data = {"generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ratingsFrom": source,
            "unrendered": unrendered, "answered": len(answered), "cards": cards}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    kinds = {k: sum(1 for c in cards if c["kind"] == k) for k in ("chat", "request", "rate", "improve", "question")}
    print(f"  decisions.json: {len(cards)} open ({', '.join(f'{n} {k}' for k, n in kinds.items())}), "
          f"{len(answered)} answered, ratings from {source}")


if __name__ == "__main__":
    main()
