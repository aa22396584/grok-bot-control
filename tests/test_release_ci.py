from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIVATE_SCAN = load_module("check_private_data", SCRIPTS / "check_private_data.py")
BUILD_RELEASE = load_module("build_release", SCRIPTS / "build_release.py")
VALIDATE_RELEASE = load_module("validate_release", SCRIPTS / "validate_release.py")


class PrivateDataScanTests(unittest.TestCase):
    def test_detects_private_files_and_redacts_secret_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = "gh" + "p_" + "A" * 36
            (root / "config.txt").write_text(f"token={secret}\n", encoding="utf-8")
            (root / "work.session").write_bytes(b"SQLite format 3\x00")
            findings = PRIVATE_SCAN.scan(root)
            messages = [finding.safe_message(root) for finding in findings]
            self.assertTrue(any("GitHub access token" in message for message in messages))
            self.assertTrue(any("Telegram session file" in message for message in messages))
            self.assertNotIn(secret, "\n".join(messages))

    def test_scans_svg_and_invalid_utf8_without_disclosing_secret(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = b"github_" + b"pat_" + b"B" * 44
            (root / "image.svg").write_bytes(b"<svg>\xff" + secret + b"</svg>")
            findings = PRIVATE_SCAN.scan(root)
            messages = "\n".join(finding.safe_message(root) for finding in findings)
            self.assertIn("GitHub fine-grained token", messages)
            self.assertNotIn(secret.decode("ascii"), messages)

    def test_repository_scan_passes(self) -> None:
        self.assertEqual(PRIVATE_SCAN.scan(ROOT), [])


class ArchiveTests(unittest.TestCase):
    def test_archive_name_is_posix(self) -> None:
        root = Path("bundle")
        name = BUILD_RELEASE.archive_name("plugin", root / "nested" / "file.txt", root)
        self.assertEqual(name, "plugin/nested/file.txt")
        self.assertEqual(PurePosixPath(name).as_posix(), name)

    def test_write_zip_preserves_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_text("portable\n", encoding="utf-8")
            target = root / "artifact.zip"
            BUILD_RELEASE.write_zip(target, {"root/nested/source.txt": source})
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(archive.namelist(), ["root/nested/source.txt"])
                self.assertEqual(archive.read("root/nested/source.txt"), source.read_bytes())

    def test_write_zip_is_deterministic_for_identical_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            source.write_text("same input\n", encoding="utf-8")
            first = root / "first.zip"
            second = root / "second.zip"
            entries = {"root/source.txt": source}
            BUILD_RELEASE.write_zip(first, entries)
            BUILD_RELEASE.write_zip(second, entries)
            self.assertEqual(first.read_bytes(), second.read_bytes())


class VersionTests(unittest.TestCase):
    def test_expected_version_rejects_malformed_value(self) -> None:
        with self.assertRaises(ValueError):
            VALIDATE_RELEASE.validate("0.2")

    def test_optimized_python_rejects_expected_version_mismatch(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-O",
                str(SCRIPTS / "validate_release.py"),
                "--expected-version",
                "9.9.9",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected version does not match release metadata", result.stderr)


class WorkflowPolicyTests(unittest.TestCase):
    def test_actions_are_commit_pinned_and_privileged_triggers_are_absent(self) -> None:
        workflows = list((ROOT / ".github/workflows").glob("*.yml"))
        self.assertGreaterEqual(len(workflows), 3)
        for workflow in workflows:
            content = workflow.read_text(encoding="utf-8")
            self.assertNotIn("pull_request_target:", content)
            self.assertNotIn("workflow_run:", content)
            for line in content.splitlines():
                if "uses: actions/" in line:
                    revision = line.split("@", 1)[1].split()[0]
                    self.assertRegex(revision, r"^[0-9a-f]{40}$")

    def test_publishers_depend_on_reusable_checks(self) -> None:
        pages = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        reusable = "uses: ./.github/workflows/checks.yml"
        self.assertIn(reusable, pages)
        self.assertIn(reusable, release)
        self.assertIn("needs: checks", pages)
        self.assertIn("needs: checks", release)
        self.assertIn("git merge-base --is-ancestor", release)
        self.assertIn('gh release view "$RELEASE_TAG"', release)


if __name__ == "__main__":
    unittest.main()
