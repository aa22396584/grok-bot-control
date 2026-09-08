#!/usr/bin/env python3
"""Build allowlisted ZIPs with deterministic construction and byte readback."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from validate_release import ROOT, PLUGIN, SKILL, source_files, validate


def archive_name(prefix: str, path: Path, root: Path) -> str:
    """Return a portable ZIP member name on every host OS."""
    return f"{prefix}/{path.relative_to(root).as_posix()}"


def write_zip(path: Path, entries: dict[str, Path]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, source in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 8, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())
    with zipfile.ZipFile(path) as archive:
        damaged = archive.testzip()
        if damaged is not None:
            raise RuntimeError("ZIP integrity check failed")
        if len(archive.namelist()) != len(entries):
            raise RuntimeError("ZIP member count differs from requested entries")
        for name, source in entries.items():
            if archive.read(name) != source.read_bytes():
                raise RuntimeError(f"ZIP byte readback failed for {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    result = validate()
    args.output.mkdir(parents=True, exist_ok=True)
    marketplace = {
        archive_name("grok-bot-control-marketplace", p, ROOT): p
        for p in source_files(PLUGIN)
    }
    for relative in (".agents/plugins/marketplace.json", "LICENSE"):
        marketplace["grok-bot-control-marketplace/" + relative] = ROOT / relative
    for relative in (".claude-plugin/marketplace.json", ".grok-plugin/marketplace.json"):
        source = ROOT / relative
        if source.is_file():
            marketplace["grok-bot-control-marketplace/" + relative] = source
    marketplace["grok-bot-control-marketplace/README.md"] = ROOT / "MARKETPLACE_README.md"
    plugin = {
        archive_name("grok-bot-control", p, PLUGIN): p
        for p in source_files(PLUGIN)
    }
    skills = {
        archive_name("grok-bot-control", p, SKILL): p
        for p in source_files(SKILL)
    }
    skills["grok-bot-control/LICENSE"] = PLUGIN / "LICENSE"
    artifacts = []
    for suffix, entries in (
        ("marketplace", marketplace),
        ("plugin", plugin),
        ("skills", skills),
    ):
        target = args.output / f"grok-bot-control-{result['version']}-{suffix}.zip"
        write_zip(target, entries)
        artifacts.append({"file": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size, "files": len(entries)})
    (args.output / "SHA256SUMS").write_text(
        "".join(f"{a['sha256']}  {a['file']}\n" for a in artifacts),
        encoding="utf-8",
    )
    report = {
        **result,
        "artifacts": artifacts,
        "evidence": "Deterministic ZIP construction and byte readback; no live account operations.",
    }
    (args.output / "PACKAGE_VERIFICATION.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
