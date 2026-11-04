import datetime
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.model.competition import Competition
from app.model.member_list import MemberList
from app.model.sailor import Sailor
from app.storage.club_store import create_club, find_club, list_clubs, set_logo
from app.storage.club_transfer import export_club, export_filename, import_club
from app.storage.competition_store import list_competitions, save_competition
from app.storage.errors import StorageError
from app.storage.member_store import load_members, save_members

ANN = Sailor("   12", "DF95", "Ann", "Smith")


class ClubTransferTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name)
        self.mine, self.theirs = tmp / "mine", tmp / "theirs"
        self.zip = tmp / "CwMBC.zip"
        self.club = create_club(self.mine, "CwMBC", "Chasewater Model Boat Club")
        save_members(MemberList([ANN]), self.club.sailors_file)
        save_competition(Competition("DF95 2026", 2026, ["df95"]), self.club.folder / "DF95_2026.cxml")
        logo = tmp / "logo.png"
        logo.write_bytes(b"png")
        set_logo(self.club, logo)

    def make_zip(self, files: dict[str, bytes]) -> Path:
        with zipfile.ZipFile(self.zip, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        return self.zip

    def test_export_filename(self):
        self.assertEqual(export_filename(self.club, datetime.date(2026, 11, 4)),
                         "CwMBC_club_2026-11-04.zip")

    def test_round_trip(self):
        (self.club.folder / "half.xml.tmp").write_text("x", encoding="utf-8")   # left out
        export_club(self.club, self.zip)
        with zipfile.ZipFile(self.zip) as archive:
            self.assertEqual(sorted(archive.namelist()),
                             ["CwMBC/CwMBCClasses.xml", "CwMBC/CwMBCClub.xml", "CwMBC/CwMBCLogo.png",
                              "CwMBC/CwMBCSail.xml", "CwMBC/CwMBCSail.xml.bak",     # backups too
                              "CwMBC/DF95_2026.cxml"])

        club = import_club(self.theirs, self.zip)
        self.assertEqual((club.abbreviation, club.title), ("CwMBC", "Chasewater Model Boat Club"))
        self.assertEqual(club.folder, self.theirs / "CwMBC")
        self.assertEqual(load_members(club.sailors_file).sailors, [ANN])
        self.assertEqual(club.logo.read_bytes(), b"png")
        self.assertEqual([c.name for _, c, _ in list_competitions(club.folder)], ["DF95 2026"])
        self.assertEqual([p.name for p in self.theirs.iterdir()], ["CwMBC"])   # nothing left over

    def test_beside_other_clubs(self):
        create_club(self.theirs, "RMBC")
        export_club(self.club, self.zip)
        import_club(self.theirs, self.zip)
        self.assertEqual([c.abbreviation for c in list_clubs(self.theirs)], ["CwMBC", "RMBC"])

    def test_never_overwrites_a_club(self):
        export_club(self.club, self.zip)
        theirs = create_club(self.theirs, "cwmbc", "Their own")
        with self.assertRaises(StorageError):
            import_club(self.theirs, self.zip)
        self.assertEqual(find_club(self.theirs, "CwMBC").title, "Their own")
        self.assertEqual(load_members(theirs.sailors_file).sailors, [])

    def test_refuses_what_is_not_one_club(self):
        club_xml = b"<club><title>X</title></club>"
        bad = {
            "empty": {},
            "no Club.xml": {"CwMBC/CwMBCSail.xml": b"<sails/>"},
            "two folders": {"CwMBC/CwMBCClub.xml": club_xml, "RMBC/RMBCClub.xml": club_xml},
            "leads outside": {"CwMBC/CwMBCClub.xml": club_xml, "CwMBC/../../evil.txt": b"x"},
            "absolute": {"/CwMBC/CwMBCClub.xml": club_xml},
            "sub folder": {"CwMBC/CwMBCClub.xml": club_xml, "CwMBC/sub/x.txt": b"x"},
            "loose file": {"CwMBCClub.xml": club_xml},
            "bad abbreviation": {"Chase water/Chase waterClub.xml": club_xml},
        }
        for reason, files in bad.items():
            with self.subTest(reason):
                with self.assertRaises(StorageError):
                    import_club(self.theirs, self.make_zip(files))
                self.assertEqual(list_clubs(self.theirs), [])
        self.assertFalse((Path(self._tmp.name) / "evil.txt").exists())

    def test_not_a_zip(self):
        self.zip.write_text("not a zip", encoding="utf-8")
        with self.assertRaises(StorageError):
            import_club(self.theirs, self.zip)


if __name__ == "__main__":
    unittest.main()
