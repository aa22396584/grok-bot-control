#!/usr/bin/env python3
"""Offline structure, source, asset and relative-link checks; no account access."""
from __future__ import annotations

import argparse
import ast
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/grok-bot-control"
SKILL = PLUGIN / "skills/grok-bot-control"
SKIP = {".git", "__pycache__", "dist", ".venv", ".mypy_cache", ".ruff_cache", ".pytest_cache"}


def require(condition: object, message: str) -> None:
    """Raise a fail-closed validation error even under Python optimized mode."""
    if not condition:
        raise ValueError(message)


def source_files(root: Path):
    for path in sorted(root.rglob("*")):
        if any(part in SKIP for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink is not allowed: {path.relative_to(ROOT)}")
        if path.is_file():
            if path.name.startswith(".env") or ".session" in path.name or path.suffix in {".log", ".pyc", ".pyo"}:
                raise ValueError(f"Runtime/private file is not allowed: {path.relative_to(ROOT)}")
            yield path


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(value for key, value in attrs if key in {"href", "src"} and value)


def check_link(source: Path, url: str):
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return
    target = (source.parent / unquote(parsed.path)).resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError(f"Link escapes repository: {source.relative_to(ROOT)}: {url}")
    if not target.exists():
        raise ValueError(f"Broken local link: {source.relative_to(ROOT)}: {url}")


def validate(expected_version: str | None = None):
    release = json.loads((ROOT / "release.json").read_text(encoding="utf-8"))
    manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    require(manifest.get("name") == "grok-bot-control", "Unexpected plugin name")
    require(
        isinstance(manifest.get("version"), str)
        and re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"]),
        "Plugin version must use semantic version form",
    )
    require(release.get("name") == manifest["name"], "Release and plugin names differ")
    require(release.get("version") == manifest["version"], "Release and plugin versions differ")
    if expected_version is not None:
        require(re.fullmatch(r"\d+\.\d+\.\d+", expected_version), "Expected version must use semantic version form")
        require(manifest["version"] == expected_version, "Expected version does not match release metadata")
    require(manifest.get("license") == "MIT", "Unexpected plugin license")
    require(marketplace.get("name") == "grok-bot-control-local", "Unexpected Codex marketplace name")
    require(
        isinstance(marketplace.get("plugins"), list) and len(marketplace["plugins"]) == 1,
        "Codex marketplace must contain exactly one plugin",
    )
    entry = marketplace["plugins"][0]
    require(entry.get("name") == manifest["name"], "Marketplace plugin name differs")
    require(
        entry.get("source") == {"source": "local", "path": "./plugins/grok-bot-control"},
        "Unexpected Codex marketplace source",
    )
    require(
        entry.get("policy") == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "Unexpected Codex marketplace policy",
    )
    for key in ("logo", "composerIcon"):
        asset = PLUGIN / manifest["interface"][key]
        require(asset.resolve().is_relative_to(PLUGIN.resolve()), f"{key} escapes plugin root")
        require(asset.is_file(), f"{key} asset is missing")
        require(asset.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), f"{key} is not a PNG")
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    require(re.search(r"(?m)^name: grok-bot-control$", skill_text), "Skill name is missing or invalid")
    require(
        re.search(r'(?m)^  version: "' + re.escape(manifest["version"]) + r'"$', skill_text),
        "Skill version differs from release metadata",
    )
    files = list(source_files(ROOT))
    for path in files:
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path.relative_to(ROOT)))
        elif path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix == ".html":
            parser = Links()
            parser.feed(path.read_text(encoding="utf-8"))
            for url in parser.urls:
                check_link(path, url)
        elif path.suffix == ".md":
            for url in re.findall(r"\]\(([^\s)]+)\)", path.read_text(encoding="utf-8")):
                check_link(path, url)
    return {"status": "pass", "source_files": len(files), "version": manifest["version"], "network_used": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-version")
    arguments = parser.parse_args()
    try:
        result = validate(arguments.expected_version)
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Release validation failed: {exc}\n")
    print(json.dumps(result, indent=2))
