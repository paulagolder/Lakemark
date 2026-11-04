import tempfile
import unittest
from pathlib import Path

from app.model.limits import DEFAULT_RACES, DEFAULT_ROWS, MAX_RACES
from app.storage.settings_store import (
    DATA_DIR,
    PROPERTIES_FILE,
    SYSTEM_FOLDER,
    find_data_dir,
    load_settings,
    move_old_data_dir,
    old_title,
    save_settings,
)


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name) / ".lakemark"

    def write(self, text: str) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / PROPERTIES_FILE).write_text(text, encoding="utf-8")

    def test_creates_folder_and_default_file(self):
        settings = load_settings(self.dir)
        self.assertTrue((self.dir / PROPERTIES_FILE).exists())
        self.assertEqual((settings.default_club, settings.default_rows, settings.default_columns),
                         ("", DEFAULT_ROWS, DEFAULT_RACES))
        self.assertEqual(settings.data_dir, self.dir)

    def test_reads_values(self):
        self.write("<properties><default_club> CwMBC </default_club><default_rows>8</default_rows>"
                   "<default_columns>3</default_columns></properties>")
        settings = load_settings(self.dir)
        self.assertEqual((settings.default_club, settings.default_rows, settings.default_columns),
                         ("CwMBC", 8, 3))

    def test_saves_the_default_club(self):
        settings = load_settings(self.dir)
        settings.default_club = "RMBC"
        self.assertTrue(save_settings(settings))
        self.assertEqual(load_settings(self.dir).default_club, "RMBC")

    def test_old_title(self):
        self.write("<properties><title> RMBC Radio Sailing </title></properties>")
        self.assertEqual(old_title(self.dir), "RMBC Radio Sailing")
        for default in ("Lakemark", "RC Yacht Race Tables", ""):     # never set: no title
            self.write(f"<properties><title>{default}</title></properties>")
            self.assertEqual(old_title(self.dir), "")
        self.assertEqual(old_title(Path(self._tmp.name) / "missing"), "")

    def test_bad_values_fall_back_or_are_limited(self):
        self.write("<properties><default_club> </default_club><default_rows>lots</default_rows>"
                   "<default_columns>99</default_columns></properties>")
        settings = load_settings(self.dir)
        self.assertEqual((settings.default_club, settings.default_rows, settings.default_columns),
                         ("", DEFAULT_ROWS, MAX_RACES))

    def test_output_folder(self):
        self.assertEqual(load_settings(self.dir).output_dir,
                         Path.home() / "Documents" / "lakemark_output")
        absolute = Path(self._tmp.name) / "results"      # with its drive letter on Windows
        self.write(f"<properties><output_folder>{absolute}</output_folder></properties>")
        self.assertEqual(load_settings(self.dir).output_dir, absolute)
        self.assertEqual(load_settings(self.dir).club_output_dir("CwMBC"), absolute / "CwMBC")

    def test_relative_output_folder_is_beside_the_data_folder(self):
        self.write("<properties><output_folder>results</output_folder></properties>")
        self.assertEqual(load_settings(self.dir).output_dir, self.dir.parent / "results")

    def test_moves_the_old_data_folder(self):
        old, new = Path(self._tmp.name) / ".pyraceresults", Path(self._tmp.name) / ".lakemark"
        old.mkdir()
        (old / "DF95_2026.cxml").write_text("<competition/>", encoding="utf-8")
        self.assertEqual(move_old_data_dir(new, old), new)
        self.assertFalse(old.exists())
        self.assertTrue((new / "DF95_2026.cxml").exists())

    def test_keeps_the_new_data_folder_if_both_exist(self):
        old, new = Path(self._tmp.name) / ".pyraceresults", Path(self._tmp.name) / ".lakemark"
        old.mkdir()
        new.mkdir()
        self.assertEqual(move_old_data_dir(new, old), new)
        self.assertTrue(old.exists())                                 # left for the user to sort out

    def test_no_old_data_folder(self):
        new = Path(self._tmp.name) / ".lakemark"
        self.assertEqual(move_old_data_dir(new, Path(self._tmp.name) / ".pyraceresults"), new)
        self.assertFalse(new.exists())                                # load_settings makes it

    def test_portable_copy_uses_its_system_folder(self):
        program = Path(self._tmp.name) / "Lakemark"
        self.assertEqual(find_data_dir(program), DATA_DIR)            # no system folder
        (program / SYSTEM_FOLDER).mkdir(parents=True)
        data_dir = find_data_dir(program)
        self.assertEqual(data_dir, program / SYSTEM_FOLDER)
        settings = load_settings(data_dir)
        self.assertEqual(settings.output_folder, "output")
        self.assertEqual(settings.output_dir, program / "output")      # beside the program
        self.assertIn("<output_folder>output</output_folder>",
                      (data_dir / PROPERTIES_FILE).read_text(encoding="utf-8"))

    def test_broken_file_uses_defaults(self):
        self.write("<properties><default_rows>")
        self.assertEqual(load_settings(self.dir).default_rows, DEFAULT_ROWS)


if __name__ == "__main__":
    unittest.main()
