import datetime
import unittest

from app.model.competition import Competition
from app.model.limits import MAX_RACE_DAYS
from app.model.race_day import RaceDay
from app.services.race_day_import import ImportRefused, plan_import, source_text
from app.storage.race_day_csv import RaceDayFile

DAY = datetime.date(2026, 11, 16)
NAME = "Race Day 16-11-2026"


def race_day(version: int, rows=(("12", "7"), ("7", "12")), name: str = NAME) -> RaceDay:
    day = RaceDay.from_table(name, ["Race A", "Race B"], [list(r) for r in rows], DAY)
    day.version, day.saved = version, datetime.datetime(2026, 11, 20, 18, version)
    return day


def file(day: RaceDay, club="RMBC", classes=("DF95",)) -> RaceDayFile:
    return RaceDayFile(day, club, club_title="Chasewater" if club == "CwMBC" else "",
                       competition="DF95 2026", classes=list(classes), exported="23/11/2026 14:05")


def competition(*days: RaceDay) -> Competition:
    return Competition("DF95 2026", 2026, ["DF95"], race_days=list(days))


def plan(f: RaceDayFile, comp: Competition, classes=("DF95", "Victoria")):
    return plan_import(f, "RMBC", list(classes), comp)


class RefusedTests(unittest.TestCase):
    def test_another_club(self):
        with self.assertRaisesRegex(ImportRefused, r"another club, CwMBC \(Chasewater\)"):
            plan(file(race_day(1), club="CwMBC"), competition())

    def test_classes_this_competition_does_not_have(self):
        with self.assertRaisesRegex(ImportRefused, "raced in DF95, Victoria"):
            plan(file(race_day(1), classes=["DF95", "Victoria"]), competition(), classes=["DF95"])
        with self.assertRaises(ImportRefused):
            plan(file(race_day(1), classes=[]), competition())

    def test_same_club_and_classes_whatever_the_case(self):
        self.assertIsNone(plan(file(race_day(1), club="rmbc", classes=["df95"]), competition()).replace)

    def test_a_full_competition(self):
        full = competition(*(race_day(1, name=f"Day {n}") for n in range(MAX_RACE_DAYS)))
        with self.assertRaisesRegex(ImportRefused, "the most it can have"):
            plan(file(race_day(1)), full)

    def test_already_up_to_date(self):
        with self.assertRaisesRegex(ImportRefused, "already up to date"):
            plan(file(race_day(3)), competition(race_day(3)))


class PlanTests(unittest.TestCase):
    def test_a_new_race_day_is_added(self):
        result = plan(file(race_day(2)), competition(race_day(1, name="Race Day 02-11-2026")))
        self.assertEqual((result.replace, result.question), (None, ""))
        self.assertEqual(result.race_day.version, 2)

    def test_a_later_version_replaces_it(self):
        comp = competition(race_day(1, name="Race Day 02-11-2026"), race_day(3))
        result = plan(file(race_day(4, rows=[["7", "12"]])), comp)
        self.assertEqual((result.replace, result.question), (1, ""))

    def test_matched_by_name_whatever_the_spacing_or_case(self):
        result = plan(file(race_day(2, name="race day  16-11-2026")), competition(race_day(1)))
        self.assertEqual(result.replace, 0)

    def test_an_earlier_version_asks_first(self):
        result = plan(file(race_day(2)), competition(race_day(3, rows=[["7", "12"]])))
        self.assertEqual(result.replace, 0)
        self.assertIn("This competition: version 3, saved 20/11/2026 18:03", result.question)
        self.assertIn("The file: version 2, saved 20/11/2026 18:02", result.question)
        self.assertIn("earlier version", result.question)

    def test_the_same_version_changed_in_both_asks_first(self):
        result = plan(file(race_day(3)), competition(race_day(3, rows=[["7", "12"]])))
        self.assertEqual(result.replace, 0)
        self.assertIn("changed in both", result.question)

    def test_race_days_from_before_versions(self):
        # version 0 on both sides, different results: ask; the same: up to date
        self.assertTrue(plan(file(race_day(0)), competition(race_day(0, rows=[["1"]]))).question)
        with self.assertRaises(ImportRefused):
            plan(file(race_day(0)), competition(race_day(0)))

    def test_source_text(self):
        self.assertEqual(source_text(file(race_day(4))),
                         "RMBC, DF95 2026, version 4, exported 23/11/2026 14:05")


if __name__ == "__main__":
    unittest.main()
