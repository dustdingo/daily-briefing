#!/usr/bin/env python3
"""Build the daily briefing page.

Reads briefing-data.json, checks it against the schema in SPEC.md, injects it
into template.html, and writes index.html. Optionally commits and pushes.

Usage (run from the repo folder on the Mac Mini):
    python3 build.py                 # validate + build index.html
    python3 build.py --check         # validate only, write nothing
    python3 build.py --push          # build, then git add/commit/push

Standard library only. Works with the python3 that ships with macOS developer
tools (or any Python 3.8+).
"""
import argparse, html, json, subprocess, sys
from pathlib import Path

ROLES = {"Speaking", "SPS", "Teaching", "Seacoast", "Freelance", "Personal"}
LEVELS = {"Critical", "High", "Medium", "Low"}
TONES = {"ok", "warn", "neutral"}


def check(D):
    errs = []

    def need(obj, path, keys):
        for k in keys:
            if not isinstance(obj, dict) or k not in obj:
                errs.append("missing %s.%s" % (path, k) if path else "missing %s" % k)
        return isinstance(obj, dict)

    def role(v, where, optional=False):
        if v is None and optional:
            return
        if v not in ROLES:
            errs.append("%s: role must be one of %s (got %r)" % (where, sorted(ROLES), v))

    def lst(obj, key, where, minimum=1):
        v = obj.get(key) if isinstance(obj, dict) else None
        if not isinstance(v, list) or len(v) < minimum:
            errs.append("%s.%s must be a list with at least %d item(s)" % (where, key, minimum))
            return []
        return v

    if not need(D, "", ["schemaVersion", "title", "date", "dateLabel", "generatedAt",
                        "today", "brief", "reading", "fitness", "time", "week"]):
        return errs
    if D["schemaVersion"] != 1:
        errs.append("schemaVersion must be 1")

    t = D["today"]
    need(t, "today", ["weather", "gamePlan", "priorities", "sequence", "headsUp"])
    if isinstance(t, dict):
        need(t.get("weather"), "today.weather", ["hi", "lo", "feelsLike", "humidity", "summary"])
        for i, g in enumerate(lst(t, "gamePlan", "today")):
            if g.get("tone") not in TONES:
                errs.append("today.gamePlan[%d].tone must be ok|warn|neutral" % i)
        for i, p in enumerate(lst(t, "priorities", "today")):
            need(p, "today.priorities[%d]" % i, ["title", "due", "next"])
            role(p.get("role"), "today.priorities[%d]" % i)
        lst(t, "sequence", "today")
        for i, x in enumerate(lst(t, "headsUp", "today", 0)):
            role(x.get("role"), "today.headsUp[%d]" % i, optional=True)

    b = D["brief"]
    need(b, "brief", ["morningRead", "forgetting", "whatsNext", "opportunities", "projectCards"])
    if isinstance(b, dict):
        for i, x in enumerate(lst(b, "forgetting", "brief", 0)):
            role(x.get("role"), "brief.forgetting[%d]" % i, optional=True)
        for i, x in enumerate(lst(b, "opportunities", "brief", 0)):
            role(x.get("role"), "brief.opportunities[%d]" % i)
        for i, x in enumerate(lst(b, "projectCards", "brief", 0)):
            role(x.get("role"), "brief.projectCards[%d]" % i)
            if x.get("level") not in LEVELS:
                errs.append("brief.projectCards[%d].level must be Critical|High|Medium|Low" % i)
            need(x, "brief.projectCards[%d]" % i, ["why", "best", "watch"])

    r = D["reading"]
    need(r, "reading", ["devotional", "prayer", "creative"])
    if isinstance(r, dict):
        need(r.get("devotional"), "reading.devotional", ["series", "date", "title", "reference"])

    f = D["fitness"]
    need(f, "fitness", ["stats", "progress", "goals", "workout", "split", "macroTargets", "meals"])
    if isinstance(f, dict):
        for i, m in enumerate(lst(f, "meals", "fitness")):
            for k in ("cal", "protein", "carbs", "fat"):
                if not isinstance(m.get(k), (int, float)):
                    errs.append("fitness.meals[%d].%s must be a number" % (i, k))
        need(f.get("macroTargets"), "fitness.macroTargets", ["cal", "protein", "carbs", "fat"])
        for i, g in enumerate(lst(f, "goals", "fitness", 0)):
            for k in ("done", "total"):
                if not isinstance(g.get(k), (int, float)):
                    errs.append("fitness.goals[%d].%s must be a number" % (i, k))

    tm = D["time"]
    if isinstance(tm, dict):
        for i, p in enumerate(lst(tm, "periods", "time")):
            need(p, "time.periods[%d]" % i, ["id", "label", "total", "rows"])
            for j, row in enumerate(p.get("rows", [])):
                role(row.get("role"), "time.periods[%d].rows[%d]" % (i, j), optional=True)
                if not isinstance(row.get("hours"), (int, float)):
                    errs.append("time.periods[%d].rows[%d].hours must be a number" % (i, j))

    w = D["week"]
    need(w, "week", ["rangeLabel", "focus", "overdue", "projects", "calendar"])
    if isinstance(w, dict):
        for i, x in enumerate(lst(w, "focus", "week")):
            role(x.get("role"), "week.focus[%d]" % i)
        for i, x in enumerate(lst(w, "overdue", "week", 0)):
            role(x.get("role"), "week.overdue[%d]" % i)
        for i, x in enumerate(lst(w, "projects", "week")):
            role(x.get("role"), "week.projects[%d]" % i)
            for blk in x.get("blocks", []):
                if not isinstance(blk.get("lines"), list):
                    errs.append("week.projects[%d] block %r needs a lines list" % (i, blk.get("label")))
        lst(w, "calendar", "week")
    return errs


def build(here, data_path, template_path, out_path):
    D = json.loads(data_path.read_text(encoding="utf-8"))
    errs = check(D)
    if errs:
        print("briefing-data.json has %d problem(s):" % len(errs), file=sys.stderr)
        for e in errs:
            print("  - " + e, file=sys.stderr)
        sys.exit(2)
    payload = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
    # Keep the JSON safe inside a <script> element.
    payload = payload.replace("</", "<\\/").replace("<!--", "<\\!--").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    tpl = template_path.read_text(encoding="utf-8")
    for token in ("__TITLE__", "__BRIEFING_DATA__"):
        if token not in tpl:
            sys.exit("template.html is missing the %s placeholder" % token)
    page = tpl.replace("__TITLE__", html.escape(D["title"])).replace("__BRIEFING_DATA__", payload)
    out_path.write_text(page, encoding="utf-8")
    return D


def push(repo, files, message):
    def run(*cmd):
        subprocess.run(cmd, cwd=repo, check=True)
    run("git", "add", *files)
    # Nothing to commit is not an error (e.g. a re-run with identical data).
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo).returncode == 0:
        print("No changes to publish.")
        return
    run("git", "commit", "-m", message)
    run("git", "push")


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=str(here / "briefing-data.json"))
    ap.add_argument("--template", default=str(here / "template.html"))
    ap.add_argument("--out", default=str(here / "index.html"))
    ap.add_argument("--check", action="store_true", help="validate the data only")
    ap.add_argument("--push", action="store_true", help="git add, commit and push after building")
    a = ap.parse_args()

    data_path, template_path, out_path = Path(a.data), Path(a.template), Path(a.out)
    if a.check:
        errs = check(json.loads(data_path.read_text(encoding="utf-8")))
        if errs:
            print("\n".join("  - " + e for e in errs), file=sys.stderr)
            sys.exit(2)
        print("briefing-data.json is valid.")
        return
    D = build(here, data_path, template_path, out_path)
    print("Wrote %s (%d KB) for %s" % (out_path, out_path.stat().st_size // 1024, D["date"]))
    if a.push:
        repo = out_path.parent
        push(repo, [out_path.name, data_path.name] if data_path.parent == repo else [out_path.name],
             "Briefing " + D["date"])
        print("Pushed.")


if __name__ == "__main__":
    main()
