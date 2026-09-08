#!/usr/bin/env python3
"""Fail closed on private runtime files, common secrets, and private home paths."""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "__pycache__", "dist", ".venv", ".mypy_cache", ".ruff_cache", ".pytest_cache"}


@dataclass(frozen=True)
class Finding:
    path: Path
    rule: str
    line: int | None = None

    def safe_message(self, root: Path) -> str:
        location = self.path.relative_to(root).as_posix()
        if self.line is not None:
            location += f":{self.line}"
        return f"{location}: {self.rule}"


NAME_RULES = (
    ("private environment file", lambda path: path.name == ".env" or path.name.startswith(".env.")),
    ("Telegram session file", lambda path: ".session" in path.name.lower()),
    ("private key or certificate container", lambda path: path.suffix.lower() in {".key", ".pem", ".p12", ".pfx"}),
)

CONTENT_RULES = (
    ("private key material", re.compile(rb"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----")),
    ("GitHub access token", re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("GitHub fine-grained token", re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("AWS access key", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack access token", re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("OpenAI API key", re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b")),
    ("private macOS home path", re.compile(rb"/Users/(?!example\b|runner\b|USERNAME\b)[A-Za-z0-9._-]+/")),
    ("private Linux home path", re.compile(rb"/home/(?!example\b|runner\b|USERNAME\b)[A-Za-z0-9._-]+/")),
    ("private root home path", re.compile(rb"/root/[A-Za-z0-9._-]+")),
    ("private Windows home path", re.compile(rb"[A-Za-z]:\\Users\\(?!example\\|runner\\|USERNAME\\)[^\\\s]+\\")),
)


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        if path.is_file():
            yield path


def scan(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(root):
        for rule, matches in NAME_RULES:
            if matches(path):
                findings.append(Finding(path, rule))
        try:
            content = path.read_bytes()
        except OSError:
            findings.append(Finding(path, "file could not be scanned"))
            continue
        for line_number, line in enumerate(content.splitlines(), 1):
            for rule, pattern in CONTENT_RULES:
                if pattern.search(line):
                    findings.append(Finding(path, rule, line_number))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    findings = scan(root)
    if findings:
        print("Private-data scan failed. Values are intentionally redacted:")
        for finding in findings:
            print(f"- {finding.safe_message(root)}")
        return 1
    print("Private-data scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
