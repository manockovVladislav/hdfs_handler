from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from hdfs_drive.config import AppConfig
from hdfs_drive.errors import UnsafePathError
from hdfs_drive.notebook import configure_root_directory
from hdfs_drive.storage import DemoStorage
from hdfs_drive.utils import validate_root_path


class RootDirectoryTests(unittest.TestCase):
    def test_environment_selects_starting_directory(self) -> None:
        root = "hdfs://cluster/user/team/u_team"
        with patch.dict(os.environ, {"HDFS_DRIVE_ROOT": root}):
            self.assertEqual(AppConfig.from_env().root, root)

    def test_broad_filesystem_root_is_rejected(self) -> None:
        with self.assertRaises(UnsafePathError):
            validate_root_path("/")

    def test_demo_uses_configured_starting_directory(self) -> None:
        root = "hdfs://cluster/user/team/u_team"
        storage = DemoStorage(root=root)
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
        root = "hdfs://cluster/user/team/u_team"
        with patch.dict(os.environ, {}, clear=False):
            result = configure_root_directory(root)
            self.assertEqual(os.environ["HDFS_DRIVE_ROOT"], root)
            self.assertEqual(result["root"], root)


if __name__ == "__main__":
    unittest.main()
