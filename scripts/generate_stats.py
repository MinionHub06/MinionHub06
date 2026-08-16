#!/usr/bin/env python3
"""Generate deterministic GitHub profile graphics using only the stdlib."""
from __future__ import annotations

import base64
import datetime as dt
import json
import math
import os
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT
FONT = ROOT / "assets/fonts/basic.woff2"
RAMP = " .`:-=+*cs#%@"
FG = "#242424"
MUTED = "#6b6b6b"
ACCENT = "#242424"
FONT_FAMILY = "NotoMono"


def utc_window():
    today = dt.datetime.now(dt.timezone.utc).date()
    start = dt.datetime.combine(today - dt.timedelta(days=364), dt.time.min, tzinfo=dt.timezone.utc)
    end = dt.datetime.combine(today, dt.time.max.replace(microsecond=0), tzinfo=dt.timezone.utc)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z"), today


def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "MinionHub06-profile-stats",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"], indent=2))
    return payload["data"]


def font_face():
    data = base64.b64encode(FONT.read_bytes()).decode()
    return f'@font-face{{font-family:{FONT_FAMILY};src:url(data:font/woff2;base64,{data}) format("woff2");font-weight:400}}'


def svg(width, height, body, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{label}">'
        f'<style>{font_face()} text{{font-family:{FONT_FAMILY},monospace}} .fg{{fill:{FG}}} .muted{{fill:{MUTED}}} .line{{stroke:{ACCENT};fill:none;stroke-width:1.5}}</style>'
        f"{body}</svg>"
    )


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")


def week_sums(days):
    buckets = defaultdict(int)
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        monday = date - dt.timedelta(days=date.weekday())
        buckets[monday] += d["contributionCount"]
    return [buckets[k] for k in sorted(buckets)]


def streaks(days, today):
    by_date = {dt.date.fromisoformat(d["date"]): d["contributionCount"] for d in days}
    ordered = sorted(by_date)

    best_len = 0
    best_start = best_end = None
    run_len = 0
    run_start = None
    prev = None
    for d in ordered:
        if by_date[d] > 0 and (prev is None or d == prev + dt.timedelta(days=1)):
            if run_len == 0:
                run_start = d
            run_len += 1
        else:
            run_len = 0
            run_start = None
        if run_len > best_len:
            best_len, best_start, best_end = run_len, run_start, d
        prev = d

    cur_len = 0
    cur_start = None
    d = today
    while d in by_date and by_date[d] > 0:
        cur_len += 1
        cur_start = d
        d -= dt.timedelta(days=1)
    cur_end = today if cur_len else None
    return (cur_len, cur_start, cur_end), (best_len, best_start, best_end)


def generate_stats(calendar, commits):
    days = [d for w in calendar["weeks"] for d in w["contributionDays"]]
    total = calendar["totalContributions"]
    weekly = week_sums(days)
    max_week = max(weekly or [1])
    pts = []
    left, top, w, h = 260, 22, 340, 48
    for i, val in enumerate(weekly[-53:]):
        x = left + (i / max(1, len(weekly[-53:]) - 1)) * w
        y = top + h - (val / max_week) * h
        pts.append(f"{x:.1f},{y:.1f}")
    poly = " ".join(pts)
    body = [
        '<text x="0" y="20" class="muted" font-size="12">github activity</text>',
        f'<text x="0" y="62" class="fg" font-size="38" font-weight="700">{total:,}</text>',
        '<text x="2" y="82" class="muted" font-size="11">public contributions · last 365 days</text>',
        f'<polyline class="line" points="{poly}"/>',
        f'<line x1="260" y1="70" x2="600" y2="70" stroke="#d0d0d0" stroke-width="1"/>',
    ]
    write("stats.svg", svg(620, 100, "".join(body), "GitHub contribution total and weekly activity"))

    # Streak graphic
    today = dt.date.fromisoformat(days[-1]["date"])
    current, longest = streaks(days, today)
    def fmt(s):
        n, a, b = s
        if not n:
            return "0 days"
        return f"{n} days · {a.isoformat()} → {b.isoformat()}"
    body = [
        '<text x="0" y="20" class="muted" font-size="12">streaks</text>',
        f'<text x="0" y="56" class="fg" font-size="23">current</text><text x="112" y="56" class="fg" font-size="23">{current[0]} days</text>',
        f'<text x="0" y="74" class="muted" font-size="11">{esc(fmt(current)[8:] if current[0] else "no active streak")}</text>',
        f'<text x="320" y="56" class="fg" font-size="23">longest</text><text x="445" y="56" class="fg" font-size="23">{longest[0]} days</text>',
        f'<text x="320" y="74" class="muted" font-size="11">{esc(fmt(longest)[8:] if longest[0] else "none")}</text>',
    ]
    write("streak.svg", svg(620, 95, "".join(body), "Current and longest GitHub contribution streaks"))

    # Languages
    lang_bytes = defaultdict(int)
    lang_repos = defaultdict(set)
    for repo in commits["repos"]:
        for edge in repo.get("languages", {}).get("edges", []):
            name = edge["node"]["name"]
            lang_bytes[name] += edge["size"]
            lang_repos[name].add(repo["name"])
    top = sorted(lang_bytes, key=lang_bytes.get, reverse=True)[:8]
    maxb = max([lang_bytes[x] for x in top] or [1])
    body = ['<text x="0" y="20" class="muted" font-size="12">languages · bytes / repositories</text>']
    for i, name in enumerate(top):
        y = 43 + i * 18
        pct = lang_bytes[name] / maxb
        bar = int(180 * pct)
        body.append(f'<text x="0" y="{y}" class="fg" font-size="12">{esc(name)}</text>')
        body.append(f'<rect x="120" y="{y-10}" width="180" height="9" fill="#ededed"/><rect x="120" y="{y-10}" width="{bar}" height="9" fill="{FG}"/>')
        body.append(f'<text x="315" y="{y}" class="muted" font-size="11">{lang_bytes[name]/1024:.1f} KB · {len(lang_repos[name])} repo(s)</text>')
    write("langs.svg", svg(620, 45 + len(top) * 18, "".join(body), "Top programming languages by bytes and repository count"))

    # Year: one ramp character per day, arranged in 7 rows for readable width.
    by_date = {dt.date.fromisoformat(d["date"]): d["contributionCount"] for d in days}
    max_day = max(by_date.values() or [1])
    start = today - dt.timedelta(days=364)
    chars = []
    for i in range(365):
        d = start + dt.timedelta(days=i)
        count = by_date.get(d, 0)
        idx = 0 if count == 0 else max(1, round(math.log1p(count) / math.log1p(max_day) * (len(RAMP) - 1)))
        chars.append(RAMP[idx])
    rows = ["".join(chars[i:i+53]) for i in range(0, 365, 53)]
    body = ['<text x="0" y="18" class="muted" font-size="12">one character per day · contribution year</text>']
    for i, line in enumerate(rows):
        body.append(f'<text x="0" y="{42+i*15}" class="fg" font-size="12">{esc(line)}</text>')
    write("year.svg", svg(620, 55 + len(rows) * 15, "".join(body), "One character per day contribution year"))


def main():
    login = os.environ.get("GH_LOGIN")
    token = os.environ.get("GITHUB_TOKEN")
    if not login or not token:
        raise SystemExit("GH_LOGIN and GITHUB_TOKEN are required")
    start, end, _ = utc_window()
    query = r'''
    query($login:String!, $from:DateTime!, $to:DateTime!) {
      user(login:$login) {
        contributionsCollection(from:$from, to:$to) {
          totalCommitContributions
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
        repositories(first:100, privacy:PUBLIC, ownerAffiliations:OWNER) {
          nodes {
            name
            languages(first:10, orderBy:{field:SIZE, direction:DESC}) {
              edges { size node { name } }
            }
          }
        }
      }
    }
    '''
    data = gql(query, {"login": login, "from": start, "to": end})["user"]
    generate_stats(data["contributionsCollection"]["contributionCalendar"], {"repos": data["repositories"]["nodes"]})


if __name__ == "__main__":
    main()
