import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.model.limits import DEFAULT_RACES, DEFAULT_ROWS, MAX_RACES
from app.storage.settings_store import (
    DATA_DIR,
    LAKEMARK_DIR,
    PROPERTIES_FILE,
    SYSTEM_FOLDER,
    downloads_dir,
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
        self.dir = Path(self._tmp.name) / "data"         # a data folder named with --data

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
        self.write("<properties><title> Rugeley Model Boat Club </title></properties>")
        self.assertEqual(old_title(self.dir), "Rugeley Model Boat Club")
        for default in ("LakeMark", "Lakemark", "RC Yacht Race Tables", ""):  # never set: no title
            self.write(f"<properties><title>{default}</title></properties>")
            self.assertEqual(old_title(self.dir), "")
        self.assertEqual(old_title(Path(self._tmp.name) / "missing"), "")

    def test_bad_values_fall_back_or_are_limited(self):
        self.write("<properties><default_club> </default_club><default_rows>lots</default_rows>"
                   "<default_columns>99</default_columns></properties>")
        settings = load_settings(self.dir)
        self.assertEqual((settings.default_club, settings.default_rows, settings.default_columns),
                         ("", DEFAULT_ROWS, MAX_RACES))

    def test_old_default_output_folders_get_the_new_one(self):
        for old in ("~/Documents/raceresult_output", "~/Documents/lakemark_output",
                    "~/Documents/Lakemark_output", "~/Documents/LakeMark_output"):
            self.write(f"<properties><output_folder>{old}</output_folder></properties>")
            self.assertEqual(load_settings(self.dir).output_folder, "~/Documents/LakeMark_output")

    def test_output_folder(self):
        self.assertEqual(load_settings(self.dir).output_dir,
                         Path.home() / "Documents" / "LakeMark_output")
        absolute = Path(self._tmp.name) / "results"      # with its drive letter on Windows
        self.write(f"<properties><output_folder>{absolute}</output_folder></properties>")
        self.assertEqual(load_settings(self.dir).output_dir, absolute)
        self.assertEqual(load_settings(self.dir).club_output_dir("CwMBC"), absolute / "CwMBC")

    def test_relative_output_folder_is_beside_the_data_folder(self):
        self.write("<properties><output_folder>results</output_folder></properties>")
        self.assertEqual(load_settings(self.dir).output_dir, self.dir.parent / "results")

    def old_and_new(self) -> tuple[Path, Path, Path]:
        home = Path(self._tmp.name)
        return home / ".lakemark", home / ".pyraceresults", home / "Documents/LakeMark/system"

    def test_default_data_folder_is_in_documents(self):
        self.assertEqual(DATA_DIR, LAKEMARK_DIR / SYSTEM_FOLDER)
        self.assertEqual(LAKEMARK_DIR.name, "LakeMark")
        self.assertEqual(LAKEMARK_DIR.parent.name, "Documents")

    def test_moves_the_old_data_folder(self):
        lakemark, pyraceresults, new = self.old_and_new()
        (lakemark / "RMBC").mkdir(parents=True)
        (lakemark / "RMBC" / "RMBCClub.xml").write_text("<club/>", encoding="utf-8")
        self.assertEqual(move_old_data_dir(new, (lakemark, pyraceresults)), new)
        self.assertFalse(lakemark.exists())
        self.assertTrue((new / "RMBC" / "RMBCClub.xml").exists())

    def test_moves_the_oldest_data_folder_if_it_is_the_only_one(self):
        lakemark, pyraceresults, new = self.old_and_new()
        pyraceresults.mkdir()
        (pyraceresults / "DF95_2026.cxml").write_text("<competition/>", encoding="utf-8")
        self.assertEqual(move_old_data_dir(new, (lakemark, pyraceresults)), new)
        self.assertFalse(pyraceresults.exists())
        self.assertTrue((new / "DF95_2026.cxml").exists())

    def test_keeps_the_new_data_folder_if_both_exist(self):
        lakemark, pyraceresults, new = self.old_and_new()
        lakemark.mkdir()
        new.mkdir(parents=True)
        self.assertEqual(move_old_data_dir(new, (lakemark, pyraceresults)), new)
        self.assertTrue(lakemark.exists())                            # left for the user to sort out

    def test_no_old_data_folder(self):
        lakemark, pyraceresults, new = self.old_and_new()
        self.assertEqual(move_old_data_dir(new, (lakemark, pyraceresults)), new)
        self.assertFalse(new.exists())                                # load_settings makes it

    def test_default_data_folder_exports_beside_it(self):
        new = self.old_and_new()[2]
        settings = load_settings(new)
        self.assertEqual(settings.output_folder, "output")
        self.assertEqual(settings.output_dir, new.parent / "output")  # Documents/LakeMark/output
        (new / PROPERTIES_FILE).write_text(        # a properties.xml from 1.10, in ~/.lakemark
            "<properties><output_folder>~/Documents/LakeMark_output</output_folder></properties>",
            encoding="utf-8")
        self.assertEqual(load_settings(new).output_dir, new.parent / "output")

    def test_portable_copy_uses_its_system_folder(self):
        program = Path(self._tmp.name) / "LakeMark"
        self.assertEqual(find_data_dir(program), DATA_DIR)            # no system folder
        (program / SYSTEM_FOLDER).mkdir(parents=True)
        data_dir = find_data_dir(program)
        self.assertEqual(data_dir, program / SYSTEM_FOLDER)
        settings = load_settings(data_dir)
        self.assertEqual(settings.output_folder, "output")
        self.assertEqual(settings.output_dir, program / "output")      # beside the program
        self.assertIn("<output_folder>output</output_folder>",
                      (data_dir / PROPERTIES_FILE).read_text(encoding="utf-8"))

    @unittest.skipIf(sys.platform in ("win32", "darwin"), "Linux desktops name the folders")
    def test_downloads_folder_named_by_the_desktop(self):
        config, home = Path(self._tmp.name) / "config", Path(self._tmp.name) / "home"
        (home / "Téléchargements").mkdir(parents=True)
        config.mkdir()
        (config / "user-dirs.dirs").write_text(
            '# written by xdg-user-dirs-update\nXDG_DOWNLOAD_DIR="$HOME/Téléchargements"\n',
            encoding="utf-8")
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(config)}), \
                mock.patch.object(Path, "home", return_value=home):
            self.assertEqual(downloads_dir(), home / "Téléchargements")
            (config / "user-dirs.dirs").write_text('XDG_DOWNLOAD_DIR="$HOME/"\n', encoding="utf-8")
            self.assertEqual(downloads_dir(), home)          # turned off, and no ~/Downloads
            (home / "Downloads").mkdir()
            self.assertEqual(downloads_dir(), home / "Downloads")
            (config / "user-dirs.dirs").unlink()
            self.assertEqual(downloads_dir(), home / "Downloads")

    def test_broken_file_uses_defaults(self):
        self.write("<properties><default_rows>")
        self.assertEqual(load_settings(self.dir).default_rows, DEFAULT_ROWS)


if __name__ == "__main__":
    unittest.main()
