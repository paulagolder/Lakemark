import tempfile
import unittest
from pathlib import Path

from app.model.sail_entry import SailResolver
from app.services.scoring import competition_results, final_results
from app.storage.boat_class_store import load_boat_classes
from app.storage.club_store import (SAMPLE_CLUB_FOLDER, add_sample_club, create_club,
                                    is_new_data_dir, load_club)
from app.storage.competition_store import list_competitions
from app.storage.member_store import load_members
from app.storage.settings_store import load_settings
from app.ui.start import add_sample, choose_club


class SampleClubTests(unittest.TestCase):
    """The sample club in app/resources/sample, given to a new installation."""

    def test_it_is_a_whole_club(self):
        club = load_club(SAMPLE_CLUB_FOLDER)
        self.assertEqual((club.abbreviation, club.title), ("LMBC", "LakeMark Model Boat Club"))
        self.assertEqual(load_boat_classes(club.classes_file).names(), ["DF95"])
        members = load_members(club.sailors_file)
        self.assertEqual(len(members), 6)

        [(path, competition, error)] = list_competitions(club.folder)
        self.assertEqual((competition.name, error, len(competition.race_days)), ("DF95 2026", "", 2))
        resolver = SailResolver(members, load_boat_classes(club.classes_file).classes)
        results = competition_results(competition, resolver)
        self.assertTrue(all(r.name for r in results.competitors), "every sail is a club sailor's")
        self.assertEqual(len(results.competitors), 6)
        # James Cook missed the second race day, so is left out of the final results
        self.assertEqual(final_results(results).left_out, 1)


class NewInstallationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name) / "system"

    def test_a_new_data_folder(self):
        self.assertTrue(is_new_data_dir(self.dir))                  # not there yet
        self.dir.mkdir()
        (self.dir / "README.txt").write_text("a portable copy's")
        self.assertTrue(is_new_data_dir(self.dir))

    def test_an_existing_data_folder(self):
        load_settings(self.dir)                                     # settings, no clubs
        self.assertFalse(is_new_data_dir(self.dir))
        other = Path(self._tmp.name) / "other"
        create_club(other, "RMBC")                                  # a club, no settings
        self.assertFalse(is_new_data_dir(other))

    def test_starts_with_the_sample_club(self):
        settings = load_settings(self.dir)
        add_sample(settings)
        self.assertEqual(choose_club(None, load_settings(self.dir), None).abbreviation, "LMBC")
        self.assertTrue((self.dir / "LMBC" / "DF95_2026.cxml").is_file())

    def test_cannot_copy_it(self):
        self.assertIsNone(add_sample_club(self.dir, Path(self._tmp.name) / "missing"))


if __name__ == "__main__":
    unittest.main()
