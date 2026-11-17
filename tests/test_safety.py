from __future__ import annotations

import io
import subprocess
import unittest
from pathlib import Path

from hdfs_drive.config import AppConfig
from hdfs_drive.errors import (
    ConfirmationRequiredError,
    DirectoryDeletionForbiddenError,
    UnsafePathError,
)
from hdfs_drive.models import EntryKind, FileEntry
from hdfs_drive.storage import HdfsStorage


ROOT = "hdfs://cluster/safe/root"


class FakeHdfsClient:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.file_paths: set[str] = set()

    def run(self, arguments, *, check=True):
        command = list(arguments)
        self.commands.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    def exists(self, path: str) -> bool:
        return path in self.file_paths

    def is_file(self, path: str) -> bool:
        return path in self.file_paths


class UploadedBytes(io.BytesIO):
    def __init__(self, name: str, data: bytes) -> None:
        super().__init__(data)
        self.name = name


class DeletionSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeHdfsClient()
        self.storage = HdfsStorage(AppConfig(root=ROOT), self.client)

    def test_file_cannot_be_deleted_without_confirmation(self) -> None:
        entry = FileEntry("report.csv", EntryKind.HDFS_FILE, path=f"{ROOT}/report.csv")
        with self.assertRaises(ConfirmationRequiredError):
            self.storage.delete_file(entry)
        self.assertEqual(self.client.commands, [])

    def test_directory_cannot_be_deleted_even_when_confirmed(self) -> None:
        entry = FileEntry("folder", EntryKind.DIRECTORY, path=f"{ROOT}/folder")
        with self.assertRaises(DirectoryDeletionForbiddenError):
            self.storage.delete_file(entry, confirmed=True)
        self.assertEqual(self.client.commands, [])

    def test_confirmed_file_deletes_exactly_one_file_without_recursive_flags(self) -> None:
        path = f"{ROOT}/report.csv"
        self.client.file_paths.add(path)
        entry = FileEntry("report.csv", EntryKind.HDFS_FILE, path=path)
        self.storage.delete_file(entry, confirmed=True)
        self.assertEqual(self.client.commands, [["-rm", path]])

    def test_object_that_is_not_a_file_is_rejected(self) -> None:
        entry = FileEntry("unknown", EntryKind.HDFS_FILE, path=f"{ROOT}/unknown")
        with self.assertRaises(DirectoryDeletionForbiddenError):
            self.storage.delete_file(entry, confirmed=True)
        self.assertEqual(self.client.commands, [])

    def test_path_outside_root_is_rejected(self) -> None:
        entry = FileEntry("secret", EntryKind.HDFS_FILE, path="hdfs://cluster/secret")
        with self.assertRaises(UnsafePathError):
            self.storage.delete_file(entry, confirmed=True)
        self.assertEqual(self.client.commands, [])

    def test_parent_directory_traversal_is_rejected(self) -> None:
        entry = FileEntry(
            "secret", EntryKind.HDFS_FILE, path=f"{ROOT}/folder/../../secret"
        )
        with self.assertRaises(UnsafePathError):
            self.storage.delete_file(entry, confirmed=True)
        self.assertEqual(self.client.commands, [])


class UploadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeHdfsClient()
        self.storage = HdfsStorage(AppConfig(root=ROOT), self.client)

    def test_files_are_uploaded_individually_without_zip(self) -> None:
        files = [
            UploadedBytes("report.csv", b"a,b\n1,2"),
            UploadedBytes("notes.txt", b"hello"),
        ]

        added, skipped = self.storage.upload_files(ROOT, files)

        self.assertEqual(added, ["report.csv", "notes.txt"])
        self.assertEqual(skipped, [])
        self.assertEqual(len(self.client.commands), 2)
        for command, name in zip(self.client.commands, added, strict=True):
            self.assertEqual(command[0], "-put")
            self.assertEqual(Path(command[1]).name, name)
            self.assertEqual(command[2], f"{ROOT}/{name}")
            self.assertNotIn("-f", command)
            self.assertFalse(any(part.endswith(".zip") for part in command))

    def test_existing_file_is_skipped_instead_of_overwritten(self) -> None:
        self.client.file_paths.add(f"{ROOT}/report.csv")

        added, skipped = self.storage.upload_files(
            ROOT, [UploadedBytes("report.csv", b"replacement")]
        )

        self.assertEqual(added, [])
        self.assertEqual(skipped, ["report.csv"])
        self.assertEqual(self.client.commands, [])


if __name__ == "__main__":
    unittest.main()
