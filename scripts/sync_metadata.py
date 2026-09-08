#!/usr/bin/env python3
"""Generate platform metadata from release.json; --check never writes files."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = "grok-bot-control-local"


def generated_files(root: Path) -> dict[Path, str]:
    release = json.loads((root / "release.json").read_text(encoding="utf-8"))
    name, version = release["name"], release["version"]
    if name != "grok-bot-control" or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Invalid release identity or version")
    plugin = root / "plugins" / name
    common = {key: release[key] for key in (
        "name", "version", "description", "author", "homepage", "repository",
        "license", "keywords", "skills",
    )}
    catalog = {
        "name": MARKETPLACE,
        "description": "Portable Grok Bot coordination skills and offline decision helpers.",
        "owner": {"name": release["author"]["name"]},
        "plugins": [{
            "name": name, "version": version,
            "description": release["description"],
            "source": f"./plugins/{name}",
            "category": "productivity",
        }],
    }
    native = json.loads(json.dumps(catalog))
    native["plugins"][0]["source"] = {"type": "local", "path": f"./plugins/{name}"}
    objects = {
        plugin / ".codex-plugin/plugin.json": release,
        plugin / ".claude-plugin/plugin.json": common,
        plugin / ".grok-plugin/plugin.json": common,
        root / ".claude-plugin/marketplace.json": catalog,
        root / ".grok-plugin/marketplace.json": native,
    }
    outputs = {path: json.dumps(value, indent=2) + "\n" for path, value in objects.items()}
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(rf"(?m)^## {re.escape(version)}(?:\s|$)", changelog):
        raise ValueError("Changelog is missing the current release version")
    outputs[plugin / "CHANGELOG.md"] = changelog
    skill = plugin / "skills" / name / "SKILL.md"
    content = skill.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError("Missing skill frontmatter")
    parts[1], count = re.subn(r'(?m)^  version: "[^"\n]+"$', f'  version: "{version}"', parts[1])
    if count != 1:
        raise ValueError("Expected one skill metadata version")
    outputs[skill] = "---".join(parts)
    return outputs


def sync(root: Path, *, check: bool) -> list[str]:
    outputs = generated_files(root)
    stale = [str(path.relative_to(root)) for path, text in outputs.items()
             if not path.exists() or path.read_text(encoding="utf-8") != text]
    if not check:
        for path, text in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        stale = sync(ROOT, check=args.check)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, f"Metadata validation failed: {exc}\n")
    if args.check and stale:
        parser.exit(1, "Generated metadata is stale: " + ", ".join(stale) + "\n")
    print("Metadata is current" if args.check else "Generated platform metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
