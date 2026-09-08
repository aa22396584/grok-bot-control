"""Exercise generated platform drift detection in isolated files."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_metadata import ROOT, generated_files, sync


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "release.json").write_bytes((ROOT / "release.json").read_bytes())
        (self.root / "CHANGELOG.md").write_bytes((ROOT / "CHANGELOG.md").read_bytes())
        self.skill = self.root / "plugins/grok-bot-control/skills/grok-bot-control/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text('---\nname: grok-bot-control\nmetadata:\n  version: "0.0.1"\n---\nUnchanged instructions\n')

    def test_check_does_not_write_and_sync_reconciles_all_platforms(self):
        original = self.skill.read_bytes()
        self.assertTrue(sync(self.root, check=True))
        self.assertEqual(self.skill.read_bytes(), original)
        sync(self.root, check=False)
        self.assertEqual(sync(self.root, check=True), [])
        self.assertTrue(self.skill.read_text().endswith("Unchanged instructions\n"))
        manifest = self.root / "plugins/grok-bot-control/.claude-plugin/plugin.json"
        data = json.loads(manifest.read_text())
        data["version"] = "9.9.9"
        manifest.write_text(json.dumps(data))
        self.assertEqual(sync(self.root, check=True), [str(manifest.relative_to(self.root))])

    def test_invalid_identity_or_version_never_generates_paths(self):
        for name, version in (("../escape", "0.2.0"), ("grok-bot-control", "0.2.0+local")):
            data = json.loads((self.root / "release.json").read_text())
            data.update(name=name, version=version)
            (self.root / "release.json").write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                generated_files(self.root)

    def test_missing_skill_version_fails_instead_of_silently_drifting(self):
        self.skill.write_text("---\nname: grok-bot-control\n---\nBody\n")
        with self.assertRaises(ValueError):
            sync(self.root, check=False)
        self.assertFalse((self.root / ".claude-plugin").exists())

    def test_plugin_changelog_is_synchronized_and_current(self):
        sync(self.root, check=False)
        packaged = self.root / "plugins/grok-bot-control/CHANGELOG.md"
        self.assertEqual(packaged.read_bytes(), (self.root / "CHANGELOG.md").read_bytes())
        packaged.write_text("## 0.1.0\nStale\n")
        self.assertIn(str(packaged.relative_to(self.root)), sync(self.root, check=True))
        (self.root / "CHANGELOG.md").write_text("## 0.1.0\nMissing current version\n")
        with self.assertRaises(ValueError):
            sync(self.root, check=False)


if __name__ == "__main__":
    unittest.main()
