"""Generate the GitHub activity and technology footprint cards as local SVG.

No third-party services: we query the GitHub API ourselves and draw the
cards, so nothing breaks when someone else's hosting goes away.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
RAMP = ["#0F6E56", "#1D9E75", "#3FBB93", "#5DCAA5", "#8CDBC0", "#BCE9D9"]


def _get(path: str) -> dict:
    req = urllib.request.Request(
        f"{API}{path}",
        headers={
            "User-Agent": "profile-readme",
            "Accept": "application/vnd.github+json",
        },
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _count(query: str) -> int:
    q = urllib.parse.quote(query)
    return int(_get(f"/search/issues?q={q}&per_page=1")["total_count"])


def fetch_stats(user: str) -> dict:
    profile = _get(f"/users/{user}")
    stats = {
        "Repositories": profile["public_repos"],
        "Followers": profile["followers"],
    }
    try:
        stats["Pull requests"] = _count(f"author:{user} type:pr")
        stats["Issues"] = _count(f"author:{user} type:issue")
    except urllib.error.HTTPError:
        pass
    return stats


def fetch_languages(user: str, top: int = 6) -> list[tuple[str, float]]:
    repos = _get(f"/users/{user}/repos?per_page=100&type=owner")
    totals: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        for lang, size in _get(f"/repos/{repo['full_name']}/languages").items():
            totals[lang] = totals.get(lang, 0) + size
    grand = sum(totals.values())
    if not grand:
        return []
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:top]
    scale = 100 / sum(v for _, v in ranked)
    return [(name, round(size * scale, 2)) for name, size in ranked]


HEAD = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 430 {h}" width="430" height="{h}" role="img" aria-label="{label}">
  <style>
    .bg {{ fill: #fbfbfa; }}
    .fr {{ stroke: #16150f; opacity: .22; stroke-width: 1; fill: none; }}
    .ti {{ fill: #0F6E56; font-family: ui-monospace, Menlo, monospace; font-size: 12px; letter-spacing: 1.6px; }}
    .lb {{ fill: #16150f; opacity: .72; font-family: ui-monospace, Menlo, monospace; font-size: 11.5px; }}
    .vl {{ fill: #16150f; font-family: ui-monospace, Menlo, monospace; font-size: 13px; }}
    .rl {{ stroke: #16150f; opacity: .12; stroke-width: 1; }}
    @media (prefers-color-scheme: dark) {{
      .bg {{ fill: #0d1117; }}
      .fr {{ stroke: #f2f0ec; opacity: .18; }}
      .ti {{ fill: #5DCAA5; }}
      .lb {{ fill: #f2f0ec; opacity: .62; }}
      .vl {{ fill: #f2f0ec; }}
      .rl {{ stroke: #f2f0ec; opacity: .14; }}
    }}
  </style>
  <rect class="bg" width="430" height="{h}"/>
"""
FOOT = '  <rect class="fr" x=".6" y=".6" width="428.8" height="{h2}"/>\n</svg>\n'


def render_stats(stats: dict) -> str:
    order = ["Repositories", "Pull requests", "Issues", "Followers"]
    rows = [(k, stats[k]) for k in order if k in stats]
    h = 58 + len(rows) * 28 + 14
    out = [HEAD.format(h=h, label="GitHub activity")]
    out.append('  <text class="ti" x="24" y="34">GITHUB ACTIVITY</text>\n')
    out.append('  <path class="rl" d="M24 46 L406 46"/>\n')
    y = 72
    for label, value in rows:
        out.append(f'  <text class="lb" x="24" y="{y}">{label}</text>\n')
        out.append(f'  <text class="vl" x="406" y="{y}" text-anchor="end">{value}</text>\n')
        y += 28
    out.append(FOOT.format(h2=h - 1.2))
    return "".join(out)


def render_languages(langs: list[tuple[str, float]]) -> str:
    if not langs:
        h = 120
        return (
            HEAD.format(h=h, label="Technology footprint")
            + '  <text class="ti" x="24" y="34">TECHNOLOGY FOOTPRINT</text>\n'
            + '  <path class="rl" d="M24 46 L406 46"/>\n'
            + '  <text class="lb" x="24" y="78">No public repositories yet</text>\n'
            + FOOT.format(h2=h - 1.2)
        )
    rows = (len(langs) + 1) // 2
    h = 58 + 30 + rows * 24 + 14
    out = [HEAD.format(h=h, label="Technology footprint")]
    out.append('  <text class="ti" x="24" y="34">TECHNOLOGY FOOTPRINT</text>\n')
    out.append('  <path class="rl" d="M24 46 L406 46"/>\n')

    x, total = 24.0, 382.0
    for i, (_, pct) in enumerate(langs):
        w = total * pct / 100
        r = ' rx="3"' if i in (0, len(langs) - 1) else ""
        out.append(
            f'  <rect x="{x:.1f}" y="62" width="{max(w, 1.5):.1f}" height="9"{r} fill="{RAMP[i % len(RAMP)]}"/>\n'
        )
        x += w

    y = 104
    for i, (name, pct) in enumerate(langs):
        col = 24 if i % 2 == 0 else 224
        out.append(
            f'  <circle cx="{col + 4}" cy="{y - 4}" r="4" fill="{RAMP[i % len(RAMP)]}"/>\n'
        )
        out.append(f'  <text class="lb" x="{col + 16}" y="{y}">{name} {pct:g}%</text>\n')
        if i % 2 == 1:
            y += 24
    out.append(FOOT.format(h2=h - 1.2))
    return "".join(out)