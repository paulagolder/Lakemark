import tempfile
import unittest
from pathlib import Path

from app.model.boat_class import DEFAULT_BOAT_CLASSES
from app.model.club import Club, abbreviation_problem
from app.storage.boat_class_store import load_boat_classes
from app.storage.club_store import (
    convert_old_folder,
    create_club,
    find_club,
    has_old_files,
    list_clubs,
    load_club,
    remove_logo,
    save_club,
    set_logo,
)
from app.storage.competition_store import list_competitions
from app.storage.errors import StorageError
from app.storage.member_store import load_members

OLD_SAILORS = ('<sails><sail sailnumber="   12" boatclass="DF95" forename="Ann" surname="Smith" '
               'club="RMBC" /></sails>')
OLD_COMPETITION = '<competition year="2026" name="DF95 2026" classes="df95" clubs="RMBC" />'


class ClubTests(unittest.TestCase):
    def test_file_names(self):
        club = Club("CwMBC", Path("data") / "CwMBC")
        self.assertEqual(club.title, "CwMBC")                         # no title: the abbreviation
        self.assertEqual(club.details_file, Path("data", "CwMBC", "CwMBCClub.xml"))
        self.assertEqual(club.sailors_file, Path("data", "CwMBC", "CwMBCSail.xml"))
        self.assertEqual(club.classes_file, Path("data", "CwMBC", "CwMBCClasses.xml"))
        self.assertEqual(club.logo_file(".png"), Path("data", "CwMBC", "CwMBCLogo.png"))
        self.assertIsNone(club.logo)                                  # no logo file

    def test_is_called_ignores_case(self):
        self.assertTrue(Club("CwMBC", Path("x")).is_called(" cwmbc "))
        self.assertFalse(Club("CwMBC", Path("x")).is_called("RMBC"))

    def test_abbreviation(self):
        for good in ("RMBC", "CwMBC", "C1"):
            self.assertIsNone(abbreviation_problem(good))
        for bad in ("", "Chase water", "../x", "R.M.B.C", "A" * 11):
            self.assertIsNotNone(abbreviation_problem(bad), bad)


class ClubStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_create_club(self):
        club = create_club(self.dir, " CwMBC ", "Chasewater Model Boat Club")
        self.assertEqual((club.abbreviation, club.folder), ("CwMBC", self.dir / "CwMBC"))
        self.assertEqual(load_members(club.sailors_file).sailors, [])
        self.assertEqual(load_boat_classes(club.classes_file).classes, DEFAULT_BOAT_CLASSES)
        self.assertEqual(load_club(club.folder).title, "Chasewater Model Boat Club")

    def test_create_refuses_bad_or_repeated_abbreviations(self):
        create_club(self.dir, "CwMBC")
        for abbreviation in ("cwmbc", "Chase water", ""):
            with self.assertRaises(StorageError):
                create_club(self.dir, abbreviation)

    def test_list_and_find(self):
        create_club(self.dir, "RMBC")
        create_club(self.dir, "CwMBC")
        (self.dir / "not_a_club").mkdir()                 # no Club.xml: left alone
        (self.dir / "properties.xml").write_text("<properties/>", encoding="utf-8")
        self.assertEqual([c.abbreviation for c in list_clubs(self.dir)], ["CwMBC", "RMBC"])
        self.assertEqual(find_club(self.dir, "rmbc").folder, self.dir / "RMBC")
        self.assertIsNone(find_club(self.dir, "XYZ"))
        self.assertEqual(list_clubs(self.dir / "missing"), [])

    def test_title_is_saved(self):
        club = create_club(self.dir, "RMBC")
        club.title = "Rugeley Model Boat Club"
        save_club(club)
        self.assertEqual(find_club(self.dir, "RMBC").title, "Rugeley Model Boat Club")
        club.details_file.write_text("<club><title>", encoding="utf-8")   # broken: abbreviation
        self.assertEqual(find_club(self.dir, "RMBC").title, "RMBC")

    def test_logo(self):
        club = create_club(self.dir, "CwMBC")
        png, gif = self.dir / "chasewater.PNG", self.dir / "chasewater.gif"
        png.write_bytes(b"png")
        gif.write_bytes(b"gif")
        self.assertEqual(set_logo(club, png), self.dir / "CwMBC" / "CwMBCLogo.png")
        self.assertEqual(club.logo.read_bytes(), b"png")
        set_logo(club, gif)                               # replaces the PNG
        self.assertEqual(club.logo, self.dir / "CwMBC" / "CwMBCLogo.gif")
        self.assertFalse(club.logo_file(".png").exists())
        remove_logo(club)
        self.assertIsNone(club.logo)

    def test_logo_must_be_png_or_gif(self):
        club = create_club(self.dir, "CwMBC")
        jpg = self.dir / "chasewater_icon.jpg"
        jpg.write_bytes(b"jpg")
        with self.assertRaises(StorageError):
            set_logo(club, jpg)
        self.assertIsNone(club.logo)


class ConvertOldFolderTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write(self, name: str, text: str) -> None:
        (self.dir / name).write_text(text, encoding="utf-8")

    def test_moves_the_files_into_an_rmbc_folder(self):
        self.write("RMBCSail.xml", OLD_SAILORS)
        self.write("RMBCSail.xml.bak", OLD_SAILORS)
        self.write("yachtclasses.xml", '<classes><boatclass key="iom" fullname="IOM" /></classes>')
        self.write("DF95_2026.cxml", OLD_COMPETITION)
        self.write("DF95_2026.cxml.bak", OLD_COMPETITION)
        self.write("Old.cxml.deleted", OLD_COMPETITION)
        self.write("properties.xml", "<properties/>")
        self.write("notes.txt", "mine")
        logo = self.dir / "logo.png"
        logo.write_bytes(b"png")
        self.assertTrue(has_old_files(self.dir))

        club = convert_old_folder(self.dir, "Rugeley Model Boat Club", logo)
        self.assertEqual((club.abbreviation, club.title), ("RMBC", "Rugeley Model Boat Club"))
        self.assertFalse(has_old_files(self.dir))
        self.assertEqual(sorted(p.name for p in club.folder.iterdir()),
                         ["DF95_2026.cxml", "DF95_2026.cxml.bak", "Old.cxml.deleted", "RMBCClasses.xml",
                          "RMBCClub.xml", "RMBCLogo.png", "RMBCSail.xml", "RMBCSail.xml.bak"])
        self.assertEqual(sorted(p.name for p in self.dir.iterdir() if p.is_file()),
                         ["logo.png", "notes.txt", "properties.xml"])     # left where they were
        self.assertEqual(load_members(club.sailors_file).sailors[0].name, "Ann Smith")
        self.assertEqual(load_boat_classes(club.classes_file).names(), ["IOM"])
        [(_, competition, _)] = list_competitions(club.folder)
        self.assertEqual(competition.name, "DF95 2026")
        self.assertEqual(find_club(self.dir, "RMBC"), club)

    def test_nothing_to_move(self):
        self.write("properties.xml", "<properties/>")
        self.assertIsNone(convert_old_folder(self.dir))
        self.assertEqual(list_clubs(self.dir), [])

    def test_does_not_overwrite_a_club_file(self):
        club = create_club(self.dir, "RMBC")
        self.write("RMBCSail.xml", OLD_SAILORS)
        with self.assertRaises(StorageError):
            convert_old_folder(self.dir)
        self.assertTrue((self.dir / "RMBCSail.xml").exists())             # nothing lost
        self.assertEqual(load_members(club.sailors_file).sailors, [])


if __name__ == "__main__":
    unittest.main()
