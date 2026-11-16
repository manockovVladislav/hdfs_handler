"""Операции над HDFS и изолированное хранилище для визуального демо."""

from __future__ import annotations

import posixpath
import shutil
import tempfile
import zipfile
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path, PurePosixPath
from threading import RLock
from typing import Protocol

from .client import HdfsClient
from .config import AppConfig
from .errors import (
    ConfirmationRequiredError,
    DirectoryDeletionForbiddenError,
    DriveError,
)
from .models import EntryKind, FileEntry
from .utils import ensure_within_root, join_inside_root, validate_name


class UploadedFile(Protocol):
    name: str

    def seek(self, offset: int) -> int: ...

    def read(self, size: int = -1) -> bytes: ...


class DriveStorage(Protocol):
    root: str

    def is_available(self) -> bool: ...
    def list_directory(self, directory: str) -> list[FileEntry]: ...
    def create_folder(self, directory: str, name: str) -> None: ...
    def upload_files(
        self, directory: str, uploaded_files: Iterable[UploadedFile]
    ) -> tuple[list[str], list[str]]: ...
    def download_file(self, entry: FileEntry) -> bytes: ...
    def delete_file(self, entry: FileEntry, *, confirmed: bool = False) -> None: ...


class HdfsStorage:
    """Файловый сервис. Удаление каталогов отсутствует по контракту."""

    def __init__(self, config: AppConfig, client: HdfsClient | None = None) -> None:
        self.config = config
        self.root = config.root
        self.client = client or HdfsClient(config.command_timeout)

    def _safe(self, path: str) -> str:
        return ensure_within_root(path, self.root)

    def is_available(self) -> bool:
        return self.client.exists(self.root)

    def _archive_path(self, directory: str) -> str:
        return join_inside_root(self.root, directory, self.config.archive_name)

    def _archive_members(self, directory: str) -> list[FileEntry]:
        remote_archive = self._archive_path(directory)
        if not self.client.exists(remote_archive):
            return []
        with tempfile.TemporaryDirectory() as temporary:
            local_archive = Path(temporary) / self.config.archive_name
            self.client.run(["-get", remote_archive, str(local_archive)])
            with zipfile.ZipFile(local_archive, "r") as archive:
                result: list[FileEntry] = []
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    try:
                        modified = datetime(*info.date_time).strftime("%d.%m.%Y %H:%M")
                    except ValueError:
                        modified = ""
                    result.append(
                        FileEntry(
                            name=info.filename,
                            size=info.file_size,
                            modified=modified,
                            owner="Архив",
                            kind=EntryKind.ARCHIVE_MEMBER,
                            archive=remote_archive,
                            member=info.filename,
                        )
                    )
                return result

    def list_directory(self, directory: str) -> list[FileEntry]:
        directory = self._safe(directory)
        output = self.client.run(["-ls", directory]).stdout
        entries: list[FileEntry] = []
        for line in output.splitlines():
            parts = line.split(maxsplit=7)
            if len(parts) < 8:
                continue
            permissions, remote_path = parts[0], self._safe(parts[7])
            name = remote_path.rstrip("/").split("/")[-1]
            if name == self.config.archive_name:
                continue
            is_directory = permissions.startswith("d")
            entries.append(
                FileEntry(
                    name=name,
                    path=remote_path,
                    kind=(EntryKind.DIRECTORY if is_directory else EntryKind.HDFS_FILE),
                    size=0 if is_directory else int(parts[4]) if parts[4].isdigit() else 0,
                    modified=f"{parts[5]} {parts[6]}",
                    owner=parts[2],
                )
            )
        entries.extend(self._archive_members(directory))
        return sorted(entries, key=lambda entry: (not entry.is_directory, entry.name.casefold()))

    def create_folder(self, directory: str, name: str) -> None:
        clean_name = validate_name(name, object_label="папки")
        new_path = join_inside_root(self.root, directory, clean_name)
        if self.client.exists(new_path):
            raise ValueError("Такая папка или файл уже существует")
        self.client.run(["-mkdir", new_path])

    def upload_files(
        self, directory: str, uploaded_files: Iterable[UploadedFile]
    ) -> tuple[list[str], list[str]]:
        directory = self._safe(directory)
        remote_archive = self._archive_path(directory)
        added: list[str] = []
        skipped: list[str] = []
        with tempfile.TemporaryDirectory() as temporary:
            local_archive = Path(temporary) / self.config.archive_name
            if self.client.exists(remote_archive):
                self.client.run(["-get", remote_archive, str(local_archive)])
            with zipfile.ZipFile(
                local_archive, "a", zipfile.ZIP_DEFLATED, compresslevel=6
            ) as archive:
                existing = set(archive.namelist())
                for uploaded in uploaded_files:
                    name = PurePosixPath(uploaded.name.replace("\\", "/")).name
                    if (
                        not name
                        or name in {".", ".."}
                        or name in existing
                        or self.client.exists(join_inside_root(self.root, directory, name))
                    ):
                        skipped.append(name or uploaded.name)
                        continue
                    uploaded.seek(0)
                    with archive.open(name, "w") as target:
                        shutil.copyfileobj(uploaded, target)
                    existing.add(name)
                    added.append(name)
            if added:
                self.client.run(["-put", "-f", str(local_archive), remote_archive])
        return added, skipped

    def download_file(self, entry: FileEntry) -> bytes:
        if entry.is_directory:
            raise DriveError("Скачивание каталога не поддерживается")
        with tempfile.TemporaryDirectory() as temporary:
            if entry.kind == EntryKind.ARCHIVE_MEMBER:
                if not entry.archive or not entry.member:
                    raise DriveError("Некорректная ссылка на файл в архиве")
                archive_path = self._safe(entry.archive)
                local_archive = Path(temporary) / "archive.zip"
                self.client.run(["-get", archive_path, str(local_archive)])
                with zipfile.ZipFile(local_archive, "r") as archive:
                    return archive.read(entry.member)
            if not entry.path:
                raise DriveError("У файла отсутствует путь")
            remote_path = self._safe(entry.path)
            local_file = Path(temporary) / PurePosixPath(remote_path).name
            self.client.run(["-get", remote_path, str(local_file)])
            return local_file.read_bytes()

    def delete_file(self, entry: FileEntry, *, confirmed: bool = False) -> None:
        if not confirmed:
            raise ConfirmationRequiredError("Удаление требует явного подтверждения")
        if entry.is_directory:
            raise DirectoryDeletionForbiddenError("Удаление директорий запрещено")
        if entry.kind == EntryKind.ARCHIVE_MEMBER:
            self._delete_archive_member(entry)
            return
        if not entry.path:
            raise DriveError("У файла отсутствует путь")
        remote_path = self._safe(entry.path)
        if not self.client.is_file(remote_path):
            raise DirectoryDeletionForbiddenError(
                "Объект не является обычным файлом; удаление отменено"
            )
        # Никогда не добавлять сюда -r/-R/-skipTrash: удаляется ровно один файл.
        self.client.run(["-rm", remote_path])

    def _delete_archive_member(self, entry: FileEntry) -> None:
        if not entry.archive or not entry.member:
            raise DriveError("Некорректная ссылка на файл в архиве")
        remote_archive = self._safe(entry.archive)
        if not self.client.is_file(remote_archive):
            raise DriveError("Служебный архив не найден или не является файлом")
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.zip"
            target = Path(temporary) / "updated.zip"
            self.client.run(["-get", remote_archive, str(source)])
            found = False
            remaining_files = 0
            with zipfile.ZipFile(source, "r") as original, zipfile.ZipFile(
                target, "w", zipfile.ZIP_DEFLATED, compresslevel=6
            ) as updated:
                for info in original.infolist():
                    if info.filename == entry.member and not info.is_dir():
                        found = True
                        continue
                    if info.is_dir():
                        updated.writestr(info, b"")
                    else:
                        with original.open(info, "r") as source_file, updated.open(
                            info, "w"
                        ) as target_file:
                            shutil.copyfileobj(source_file, target_file)
                        remaining_files += 1
            if not found:
                raise DriveError("Файл уже отсутствует в архиве")
            if remaining_files == 0:
                self.client.run(["-rm", remote_archive])
            else:
                self.client.run(["-put", "-f", str(target), remote_archive])


class DemoStorage:
    """Изолированная память для визуальной проверки без HDFS."""

    def __init__(self, root: str = "demo://my-drive") -> None:
        self.root = root
        self._lock = RLock()
        self._directories = {root, f"{root}/Проекты", f"{root}/Команда"}
        self._files: dict[str, bytes] = {
            f"{root}/План проекта.pdf": b"Demo PDF content",
            f"{root}/Бюджет.xlsx": b"Demo spreadsheet content",
            f"{root}/Проекты/README.txt": "Демонстрационный файл".encode(),
            f"{root}/Команда/Контакты.csv": b"name,email",
        }

    def _safe(self, path: str) -> str:
        return ensure_within_root(path, self.root)

    def is_available(self) -> bool:
        return True

    def list_directory(self, directory: str) -> list[FileEntry]:
        directory = self._safe(directory)
        now = "16.11.2026 12:00"
        entries: list[FileEntry] = []
        with self._lock:
            for path in sorted(self._directories):
                if path != directory and posixpath.dirname(path) == directory:
                    entries.append(
                        FileEntry(
                            name=posixpath.basename(path),
                            path=path,
                            kind=EntryKind.DIRECTORY,
                            modified=now,
                            owner="Я",
                        )
                    )
            for path, data in sorted(self._files.items()):
                if posixpath.dirname(path) == directory:
                    entries.append(
                        FileEntry(
                            name=posixpath.basename(path),
                            path=path,
                            kind=EntryKind.HDFS_FILE,
                            size=len(data),
                            modified=now,
                            owner="Я",
                        )
                    )
        return sorted(entries, key=lambda entry: (not entry.is_directory, entry.name.casefold()))

    def create_folder(self, directory: str, name: str) -> None:
        clean_name = validate_name(name, object_label="папки")
        path = join_inside_root(self.root, directory, clean_name)
        with self._lock:
            if path in self._directories or path in self._files:
                raise ValueError("Такая папка или файл уже существует")
            self._directories.add(path)

    def upload_files(
        self, directory: str, uploaded_files: Iterable[UploadedFile]
    ) -> tuple[list[str], list[str]]:
        added: list[str] = []
        skipped: list[str] = []
        with self._lock:
            for uploaded in uploaded_files:
                name = PurePosixPath(uploaded.name.replace("\\", "/")).name
                try:
                    name = validate_name(name, object_label="файла")
                except ValueError:
                    skipped.append(uploaded.name)
                    continue
                path = join_inside_root(self.root, directory, name)
                if path in self._files or path in self._directories:
                    skipped.append(name)
                    continue
                uploaded.seek(0)
                self._files[path] = uploaded.read()
                added.append(name)
        return added, skipped

    def download_file(self, entry: FileEntry) -> bytes:
        if entry.is_directory or not entry.path:
            raise DriveError("Скачивание каталога не поддерживается")
        path = self._safe(entry.path)
        try:
            return self._files[path]
        except KeyError as error:
            raise DriveError("Файл не найден") from error

    def delete_file(self, entry: FileEntry, *, confirmed: bool = False) -> None:
        if not confirmed:
            raise ConfirmationRequiredError("Удаление требует явного подтверждения")
        if entry.is_directory:
            raise DirectoryDeletionForbiddenError("Удаление директорий запрещено")
        if not entry.path:
            raise DriveError("У файла отсутствует путь")
        path = self._safe(entry.path)
        with self._lock:
            if path not in self._files:
                raise DriveError("Файл не найден")
            del self._files[path]
