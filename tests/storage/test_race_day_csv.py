import datetime
import tempfile
import unittest
from pathlib import Path

from app import __version__
from app.model.limits import MAX_PLACES, MAX_RACES
from app.model.race_day import RaceDay
from app.storage.errors import StorageError
from app.storage.race_day_csv import RaceDayFile, read_race_day_csv, write_race_day_csv

ROWS = [["12", "7", "12"], ["7", "62*", "29/PAG"], ["", "12", ""]]
SAVED = datetime.datetime(2026, 11, 20, 18, 2)
HEADING = "LakeMark race day\nClub,RMBC\nClasses,DF95\nRace day,Race Day 16-11-2026\n\n"


def race_day(name="Race Day 16-11-2026", date=datetime.date(2026, 11, 16)) -> RaceDay:
    day = RaceDay.from_table(name, ["Race A", "Race B", "Race C"], ROWS, date)
    day.version, day.saved = 4, SAVED
    return day


def race_day_file(day: RaceDay | None = None) -> RaceDayFile:
    return RaceDayFile(day or race_day(), "RMBC", club_title="Rugeley Model Boat Club",
                       competition="DF95 2026", classes=["DF95", "Victoria"])


class RaceDayCsvTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def file(self, text: str, encoding: str = "utf-8") -> Path:
        path = self.dir / "day.csv"
        path.write_text(text, encoding=encoding)
        return path

    def test_writes_a_heading_then_the_table(self):
        path = self.dir / "day.csv"
        write_race_day_csv(path, race_day_file(), exported=datetime.datetime(2026, 11, 23, 14, 5))
        self.assertEqual(path.read_text(encoding="utf-8").splitlines(), [
            "LakeMark race day",
            "Club,RMBC,Rugeley Model Boat Club",
            "Competition,DF95 2026",
            "Classes,DF95,Victoria",
            "Race day,Race Day 16-11-2026",
            "Date,16/11/2026",
            "Version,4,20/11/2026 18:02",
            f"Exported,23/11/2026 14:05,LakeMark {__version__}",
            "",
            "Row,Race A,Race B,Race C",
            "1,12,7,12",
            "2,7,62*,29/PAG",
            "3,,12,",
        ])

    def test_reads_back_what_it_writes(self):
        path = self.dir / "renamed by someone.csv"
        write_race_day_csv(path, race_day_file(), exported=datetime.datetime(2026, 11, 23, 14, 5))
        read = read_race_day_csv(path)
        self.assertEqual(read, RaceDayFile(race_day(), "RMBC", "Rugeley Model Boat Club", "DF95 2026",
                                           ["DF95", "Victoria"], "23/11/2026 14:05",
                                           f"LakeMark {__version__}"))
        self.assertEqual((read.race_day.version, read.race_day.saved), (4, SAVED))

    def test_a_race_day_with_no_date(self):
        path = self.dir / "day.csv"
        write_race_day_csv(path, race_day_file(race_day(name="Spring open", date=None)))
        day = read_race_day_csv(path).race_day
        self.assertEqual((day.name, day.date), ("Spring open", None))

    def test_saved_again_from_a_spreadsheet(self):
        # semicolons, a byte order mark, empty cells at the ends of rows, Row column gone
        text = ("﻿LakeMark race day;;\nClub;RMBC;Rugeley Model Boat Club\nClasses;DF95;\n"
                "Race day;Spring open;\nDate;16/11/2026;\nVersion;3;\n;;\nRace A;Race B;\n 12 ; 7\n7;12;\n")
        read = read_race_day_csv(self.file(text))
        day = read.race_day
        self.assertEqual((read.club, read.classes), ("RMBC", ["DF95"]))
        self.assertEqual((day.name, day.date, day.version, day.saved),
                         ("Spring open", datetime.date(2026, 11, 16), 3, None))
        self.assertEqual((day.columns, day.rows), (["Race A", "Race B"], [["12", "7"], ["7", "12"]]))

    def test_saved_by_windows_in_its_own_encoding(self):
        day = read_race_day_csv(self.file(HEADING + "Row,Course é\n1,12\n", "cp1252")).race_day
        self.assertEqual(day.columns, ["Course é"])

    def test_no_version_is_version_0(self):
        self.assertEqual(read_race_day_csv(self.file(HEADING + "Row,Race A\n1,12\n")).race_day.version, 0)

    def test_refused(self):
        too_wide = "Row," + ",".join(f"R{i}" for i in range(MAX_RACES + 1)) + "\n"
        too_long = "Row,Race A\n" + "".join(f"{i},{i}\n" for i in range(1, MAX_PLACES + 2))
        for text in ("", "\n\n",
                     "Row,Race A\n1,12\n",                                   # no heading (1.11)
                     "LakeMark race day\nRace day,Day 1\n\nRow,Race A\n1,12\n",   # no club
                     HEADING, HEADING + "Row\n1\n", HEADING + "Row,Race A,,Race C\n1,2,3,4\n",
                     HEADING + too_wide, HEADING + too_long, HEADING + "Row,Race A\n1,12,13\n",
                     HEADING.replace("Race day,Race Day 16-11-2026\n", "") + "Row,Race A\n1,12\n",
                     HEADING + "Date,31/02/2026\n\nRow,Race A\n1,12\n"):
            with self.subTest(text=text[:50]):
                with self.assertRaises(StorageError):
                    read_race_day_csv(self.file(text))

    def test_missing_file(self):
        with self.assertRaises(StorageError):
            read_race_day_csv(self.dir / "missing.csv")

    def test_cannot_write(self):
        with self.assertRaises(StorageError):
            write_race_day_csv(self.dir / "no folder" / "day.csv", race_day_file())


if __name__ == "__main__":
    unittest.main()
