import tempfile
import unittest
from pathlib import Path

from app.storage.club_store import create_club
from app.storage.settings_store import load_settings
from app.ui.start import choose_club


class ChooseClubTests(unittest.TestCase):
    """The choices that need no questions (no window is opened for these)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        create_club(self.dir, "RMBC")
        create_club(self.dir, "CwMBC")

    def test_the_club_asked_for(self):
        settings = load_settings(self.dir)
        settings.default_club = "RMBC"
        self.assertEqual(choose_club(None, settings, "cwmbc").abbreviation, "CwMBC")

    def test_the_default_club(self):
        settings = load_settings(self.dir)
        settings.default_club = "RMBC"
        self.assertEqual(choose_club(None, settings, None).abbreviation, "RMBC")

    def test_the_first_club_becomes_the_default(self):
        settings = load_settings(self.dir)
        self.assertEqual(choose_club(None, settings, None).abbreviation, "CwMBC")
        self.assertEqual(load_settings(self.dir).default_club, "CwMBC")

    def test_a_default_club_that_has_gone(self):
        settings = load_settings(self.dir)
        settings.default_club = "XYZ"
        self.assertEqual(choose_club(None, settings, None).abbreviation, "CwMBC")


if __name__ == "__main__":
    unittest.main()
