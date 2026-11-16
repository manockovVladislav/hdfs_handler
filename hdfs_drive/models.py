"""Модели, которыми обмениваются хранилище и интерфейс."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EntryKind(str, Enum):
    DIRECTORY = "directory"
    HDFS_FILE = "hdfs_file"
    ARCHIVE_MEMBER = "archive_member"


@dataclass(frozen=True, slots=True)
class FileEntry:
    name: str
    kind: EntryKind
    size: int = 0
    modified: str = ""
    owner: str = ""
    path: str | None = None
    archive: str | None = None
    member: str | None = None

    @property
    def is_directory(self) -> bool:
        return self.kind == EntryKind.DIRECTORY

    @property
    def identity(self) -> str:
        return self.path or f"{self.archive}!{self.member}"
