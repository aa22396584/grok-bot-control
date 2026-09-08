#!/usr/bin/env python3
"""Build allowlisted ZIPs with stable timestamps and SHA-256 manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from validate_release import ROOT, PLUGIN, SKILL, source_files, validate


def write_zip(path: Path, entries: dict[str, Path]):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, source in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 8, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(entries)
        for name, source in entries.items():
            assert archive.read(name) == source.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    result = validate()
    args.output.mkdir(parents=True, exist_ok=True)
    marketplace = {"grok-bot-control-marketplace/" + str(p.relative_to(ROOT)): p for p in source_files(PLUGIN)}
    for relative in (".agents/plugins/marketplace.json", "LICENSE"):
        marketplace["grok-bot-control-marketplace/" + relative] = ROOT / relative
    marketplace["grok-bot-control-marketplace/README.md"] = ROOT / "MARKETPLACE_README.md"
    skills = {"grok-bot-control/" + str(p.relative_to(SKILL)): p for p in source_files(SKILL)}
    skills["grok-bot-control/LICENSE"] = PLUGIN / "LICENSE"
    artifacts = []
    for suffix, entries in (("marketplace", marketplace), ("skills", skills)):
        target = args.output / f"grok-bot-control-{result['version']}-{suffix}.zip"
        write_zip(target, entries)
        artifacts.append({"file": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size, "files": len(entries)})
    (args.output / "SHA256SUMS").write_text("".join(f"{a['sha256']}  {a['file']}\n" for a in artifacts))
    report = {**result, "artifacts": artifacts, "evidence": "Offline source validation and ZIP byte readback only; no live account operations."}
    (args.output / "PACKAGE_VERIFICATION.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
