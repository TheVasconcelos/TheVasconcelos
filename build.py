#!/usr/bin/env python3
"""Regenerate the marked blocks in README.md from data/profile.yml."""

from pathlib import Path
import re
import sys
import yaml

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
DATA = ROOT / "profile.yml"

CELLS = 10
STYLES = {
    "bars":   ("\u25b0", "\u25b1"),
    "dots":   ("\u25cf", "\u25cb"),
    "blocks": ("\u2588", "\u2591"),
}


def bar(pct: int, style: str = "bars") -> str:
    pct = max(0, min(100, int(pct)))
    filled_ch, empty_ch = STYLES.get(style, STYLES["bars"])
    filled = round(pct / 100 * CELLS)
    return f"{filled_ch * filled}{empty_ch * (CELLS - filled)} {pct}%"


def build_stack(cfg) -> str:
    rows = ["| | |", "|---|---|"]
    for category, tools in cfg["toolstack"].items():
        rows.append(f"| **{category}** | {' · '.join(tools)} |")
    return "\n".join(rows)


def build_board(cfg) -> str:
    style = cfg.get("bar_style", "bars")
    rows = [
        "| Project | Track | Progress | Current Status |",
        "|---|---|:---:|---|",
    ]
    for p in cfg["projects"]:
        name = f"**{p['name']}**"
        if p.get("url"):
            name = f"[{name}]({p['url']})"
        rows.append(
            f"| {name} | {p['track']} | {bar(p['progress'], style)} | {p['status']} |"
        )
    return "\n".join(rows)


def build_cards(cfg) -> str:
    user, accent, muted = cfg["github_user"], cfg["accent"], cfg["muted"]
    common = (
        f"hide_border=true&bg_color=00000000"
        f"&title_color={accent}&icon_color={accent}&text_color={muted}"
    )
    stats = (
        f"https://github-readme-stats.vercel.app/api"
        f"?username={user}&hide=stars&show_icons=true&{common}"
    )
    langs = (
        f"https://github-readme-stats.vercel.app/api/top-langs/"
        f"?username={user}&layout=compact&langs_count=6&{common}"
    )
    out = [
        "<p align=\"center\">",
        f"  <img src=\"{stats}\" alt=\"GitHub stats\" height=\"165\">",
        f"  <img src=\"{langs}\" alt=\"Technology footprint\" height=\"165\">",
        "</p>",
    ]

    leet = (
        f"https://leetcard.jacoblin.cool/{cfg['leetcode_user']}"
        f"?theme=light,dark&ext=activity"
    )
    line = (
        f"<p align=\"center\">\n"
        f"  <img src=\"{leet}\" alt=\"LeetCode stats\" width=\"500\">\n"
        f"</p>"
    )
    if cfg.get("leetcode_enabled"):
        out.append("")
        out.append(line)
    else:
        out.append("")
        out.append("<!-- Flip leetcode_enabled to true in data/profile.yml")
        out.append(line)
        out.append("-->")
    return "\n".join(out)


def inject(text: str, marker: str, block: str) -> str:
    pattern = re.compile(
        rf"(<!-- {marker}:START -->)(.*?)(<!-- {marker}:END -->)", re.S
    )
    if not pattern.search(text):
        sys.exit(f"Marker {marker} not found in README.md")
    return pattern.sub(rf"\1\n{block}\n\3", text)


def main() -> None:
    cfg = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    text = README.read_text(encoding="utf-8")
    for marker, block in (
        ("CARDS", build_cards(cfg)),
        ("STACK", build_stack(cfg)),
        ("BOARD", build_board(cfg)),
    ):
        text = inject(text, marker, block)
    README.write_text(text, encoding="utf-8")
    print("README.md regenerated")


if __name__ == "__main__":
    main()
