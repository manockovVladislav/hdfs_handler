"""Настройки приложения из переменных окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .utils import validate_root_path


DEFAULT_ROOT = "hdfs://arnsdpsbx/user/team/my_team/u_team"


@dataclass(frozen=True, slots=True)
class AppConfig:
    root: str = DEFAULT_ROOT
    archive_name: str = ".hdfs_files.zip"
    command_timeout: int = 300
    demo_mode: bool = False

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            root=validate_root_path(os.environ.get("HDFS_DRIVE_ROOT", DEFAULT_ROOT)),
            archive_name=os.environ.get("HDFS_DRIVE_ARCHIVE", ".hdfs_files.zip"),
            command_timeout=int(os.environ.get("HDFS_DRIVE_TIMEOUT", "300")),
            demo_mode=os.environ.get("HDFS_DRIVE_DEMO", "0").lower()
            in {"1", "true", "yes"},
        )
