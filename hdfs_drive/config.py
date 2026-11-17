"""Настройки приложения из переменных окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .utils import validate_root_path


# Базовый HDFS-путь задаётся только в конфиге. В Jupyter к нему
# добавляется одно имя конечной папки.
HDFS_BASE_ROOT = "hdfs://arnsdpsbx/user/team/my_team"
DEFAULT_FOLDER = "u_team"
DEFAULT_ROOT = f"{HDFS_BASE_ROOT}/{DEFAULT_FOLDER}"

# 1 — тестовое хранилище, 0 — боевой HDFS.
TEST_MODE = 1


def _read_test_mode(value: str) -> bool:
    if value not in {"0", "1"}:
        raise ValueError("HDFS_DRIVE_TEST_MODE должен быть равен 0 или 1")
    return value == "1"


@dataclass(frozen=True, slots=True)
class AppConfig:
    root: str = DEFAULT_ROOT
    command_timeout: int = 300
    test_mode: bool = bool(TEST_MODE)

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            root=validate_root_path(os.environ.get("HDFS_DRIVE_ROOT", DEFAULT_ROOT)),
            command_timeout=int(os.environ.get("HDFS_DRIVE_TIMEOUT", "300")),
            test_mode=_read_test_mode(
                os.environ.get("HDFS_DRIVE_TEST_MODE", str(TEST_MODE))
            ),
        )
