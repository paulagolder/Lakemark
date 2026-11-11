import tempfile
import unittest
from pathlib import Path

from app import __version__
from app.model.club import Club
from app.services.about import about_facts, help_text, version_text
from app.storage.settings_store import Settings


class AboutTests(unittest.TestCase):
    def test_version_text(self):
        self.assertRegex(version_text(), rf"^Lakemark {__version__} \(\d{{1,2}} \w+ \d{{4}}\)$")

    def test_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "data"
            folder = data / "CwMBC"
            folder.mkdir(parents=True)
            (folder / "a.cxml").write_text('<competition year="2026" name="A" classes="df65" />')
            (folder / "b.cxml").write_text("not a competition")      # listed all the same
            settings = Settings(data, output_folder=str(Path(tmp) / "out"))
            facts = dict(about_facts(settings, Club("CwMBC", folder, "Chasewater MBC")))
        self.assertEqual(facts["Version"], __version__)
        self.assertEqual(facts["Club"], "CwMBC: Chasewater MBC")
        self.assertEqual(facts["Competitions"], "2")
        self.assertEqual(facts["Club folder"], str(folder))
        self.assertEqual(facts["Data folder"], str(data))
        self.assertEqual(facts["Output folder"], str(Path(tmp) / "out" / "CwMBC"))

    def test_club_without_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            facts = dict(about_facts(Settings(Path(tmp)), Club("RMBC", Path(tmp) / "RMBC")))
        self.assertEqual(facts["Club"], "RMBC")
        self.assertEqual(facts["Competitions"], "0")

    def test_help(self):
        text = help_text()
        self.assertTrue(text.startswith("# Lakemark help"))
        for heading in ("Competitions", "Race days", "Results", "Clubs", "Handing a club over"):
            self.assertIn(f"\n# {heading}\n", text)


if __name__ == "__main__":
    unittest.main()
