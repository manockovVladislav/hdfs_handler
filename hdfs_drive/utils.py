"""Чистые функции форматирования и проверки путей."""

from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from .errors import UnsafePathError


def ensure_within_root(path: str, root: str) -> str:
    """Возвращает нормализованный путь или запрещает выход из корня."""
    path_parts = urlsplit(path)
    root_parts = urlsplit(root)
    if path_parts.query or path_parts.fragment:
        raise UnsafePathError("HDFS-путь не должен содержать query или fragment")
    path_value = posixpath.normpath(path_parts.path or "/")
    root_value = posixpath.normpath(root_parts.path or "/")
    same_storage = (
        path_parts.scheme == root_parts.scheme and path_parts.netloc == root_parts.netloc
    )
    root_prefix = root_value if root_value == "/" else root_value + "/"
    if not same_storage or (
        path_value != root_value and not path_value.startswith(root_prefix)
    ):
        raise UnsafePathError("Путь находится вне разрешённой директории HDFS")
    return path.rstrip("/") or "/"


def validate_root_path(root: str) -> str:
    """Проверяет, что корень задан явно и не охватывает всё хранилище."""
    clean_root = root.strip().rstrip("/")
    if not clean_root:
        raise UnsafePathError("Стартовый каталог не может быть пустым или равным /")
    parts = urlsplit(clean_root)
    normalized_path = posixpath.normpath(parts.path or "/")
    if normalized_path == "/" or parts.query or parts.fragment:
        raise UnsafePathError("Укажите конкретный стартовый каталог HDFS")
    return clean_root


def join_inside_root(root: str, directory: str, name: str) -> str:
    ensure_within_root(directory, root)
    return ensure_within_root(posixpath.join(directory, name), root)


def validate_name(name: str, *, object_label: str = "объекта") -> str:
    clean = name.strip()
    if (
        not clean
        or clean in {".", ".."}
        or "/" in clean
        or "\\" in clean
        or any(ord(char) < 32 for char in clean)
    ):
        raise ValueError(f"Некорректное название {object_label}")
    return clean


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} Б"
    if size < 1024**2:
        return f"{size / 1024:.1f} КБ"
    if size < 1024**3:
        return f"{size / 1024**2:.1f} МБ"
    return f"{size / 1024**3:.2f} ГБ"


def file_icon(name: str) -> str:
    extension = PurePosixPath(name).suffix.lower()
    return {
        ".pdf": "📕",
        ".doc": "📘",
        ".docx": "📘",
        ".xls": "📗",
        ".xlsx": "📗",
        ".csv": "📊",
        ".txt": "📄",
        ".json": "📋",
        ".xml": "📋",
        ".py": "🐍",
        ".zip": "📦",
        ".jpg": "🖼️",
        ".jpeg": "🖼️",
        ".png": "🖼️",
        ".parquet": "📊",
    }.get(extension, "📄")
