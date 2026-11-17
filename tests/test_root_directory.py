from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from hdfs_drive.config import HDFS_BASE_ROOT, AppConfig
from hdfs_drive.errors import UnsafePathError
from hdfs_drive.notebook import configure_root_directory
from hdfs_drive.storage import TestStorage
from hdfs_drive.utils import validate_root_path


class RootDirectoryTests(unittest.TestCase):
    def test_environment_selects_starting_directory(self) -> None:
        root = "hdfs://cluster/user/team/u_team"
        with patch.dict(os.environ, {"HDFS_DRIVE_ROOT": root}):
            self.assertEqual(AppConfig.from_env().root, root)

    def test_environment_selects_production_mode_with_zero(self) -> None:
        with patch.dict(os.environ, {"HDFS_DRIVE_TEST_MODE": "0"}):
            self.assertFalse(AppConfig.from_env().test_mode)

    def test_environment_selects_test_mode_with_one(self) -> None:
        with patch.dict(os.environ, {"HDFS_DRIVE_TEST_MODE": "1"}):
            self.assertTrue(AppConfig.from_env().test_mode)

    def test_other_mode_values_are_rejected(self) -> None:
        with patch.dict(os.environ, {"HDFS_DRIVE_TEST_MODE": "true"}):
            with self.assertRaises(ValueError):
                AppConfig.from_env()

    def test_broad_filesystem_root_is_rejected(self) -> None:
        with self.assertRaises(UnsafePathError):
            validate_root_path("/")

    def test_test_storage_uses_configured_starting_directory(self) -> None:
        root = "hdfs://cluster/user/team/u_team"
        storage = TestStorage(root=root)
        self.assertEqual(storage.root, root)
        self.assertTrue(
            all(
                entry.path.startswith(root + "/")
                for entry in storage.list_directory(root)
            )
        )

    @patch("hdfs_drive.notebook.display")
    @patch("hdfs_drive.notebook.shutil.which", return_value=None)
    def test_notebook_cell_sets_environment_without_hdfs(
        self, _which, _display
    ) -> None:
        root = f"{HDFS_BASE_ROOT}/u_team"
        with patch.dict(os.environ, {}, clear=False):
            result = configure_root_directory("u_team")
            self.assertEqual(os.environ["HDFS_DRIVE_ROOT"], root)
            self.assertEqual(result["root"], root)

    @patch("hdfs_drive.notebook.display")
    def test_notebook_rejects_full_hdfs_path(self, _display) -> None:
        with self.assertRaises(ValueError):
            configure_root_directory("hdfs://cluster/user/team/u_team")

    @patch("hdfs_drive.notebook.display")
    @patch("hdfs_drive.notebook.shutil.which")
    def test_notebook_does_not_check_hdfs_in_test_mode(
        self, which, _display
    ) -> None:
        with patch.dict(os.environ, {"HDFS_DRIVE_TEST_MODE": "1"}):
            result = configure_root_directory("u_team")

        which.assert_not_called()
        self.assertEqual(
            result["hdfs_status"], "тестовый режим; HDFS не проверялся"
        )


if __name__ == "__main__":
    unittest.main()
