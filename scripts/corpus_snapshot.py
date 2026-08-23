#!/usr/bin/env python3
"""Summarise a GenLayer builder-projects markdown export."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from urllib.parse import urlparse


def _projects(text: str) -> list[dict]:
    rows = []
    for block in re.split(r"\n---\n", text):
        title = re.search(r"^##\s+(\d+)\.\s+(.+)$", block, re.M)
        points = re.search(r"- \*\*Points:\*\*\s+(\d+)", block)
        date = re.search(r"- \*\*Date:\*\*\s+(.+)", block)
        if not title or not points:
            continue
        rows.append(
            {
                "rank": int(title.group(1)),
                "title": title.group(2).strip(),
                "points": int(points.group(1)),
                "date": date.group(1).strip() if date else "",
                "text": block,
            }
        )
    return rows


def _keyword_stats(projects: list[dict], keyword: str) -> dict:
    hits = [p for p in projects if keyword.lower() in p["text"].lower()]
    points = [p["points"] for p in hits]
    return {
        "keyword": keyword,
        "count": len(hits),
        "mean_points": round(sum(points) / len(points), 2) if points else 0,
        "max_points": max(points) if points else 0,
    }


def _github_repositories(projects: list[dict]) -> list[str]:
    repos = set()
    for project in projects:
        for match in re.finditer(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", project["text"]):
            url = match.group(0).rstrip(").,")
            parsed = urlparse(url)
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) >= 2:
                name = parts[1]
                if name.endswith(".git"):
                    name = name[:-4]
                repos.add(f"https://github.com/{parts[0]}/{name}")
    return sorted(repos, key=str.lower)


def _contract_addresses(projects: list[dict]) -> list[str]:
    addresses = set()
    for project in projects:
        for match in re.finditer(r"0x[a-fA-F0-9]{40}", project["text"]):
            addresses.add(match.group(0))
    return sorted(addresses, key=str.lower)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("data/portal-corpus-summary.json"))
    args = parser.parse_args()

    text = args.markdown.read_text()
    projects = _projects(text)
    glbench = next(
        (p for p in projects if "glbench" in p["title"].lower() or "glbench" in p["text"].lower()),
        None,
    )
    repos = _github_repositories(projects)
    contracts = _contract_addresses(projects)
    summary = {
        "source_file": str(args.markdown),
        "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "project_count": len(projects),
        "github_repository_count": len(repos),
        "github_repository_sample": repos[:20],
        "contract_address_count": len(contracts),
        "contract_address_sample": contracts[:20],
        "keyword_stats": {
            key: _keyword_stats(projects, key)
            for key in ("research", "report", "dashboard", "benchmark", "validator", "consensus")
        },
        "high_score_count_30_plus": sum(1 for p in projects if p["points"] >= 30),
        "glbench": (
            {
                "rank": glbench["rank"],
                "title": glbench["title"],
                "points": glbench["points"],
                "date": glbench["date"],
                "positioning": "GLBench scores validators; Jastrow scores whether a specification is decidable.",
            }
            if glbench
            else None
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print("wrote " + str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
