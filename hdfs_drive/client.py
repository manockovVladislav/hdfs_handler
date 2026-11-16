"""Минимальный безопасный адаптер командной строки HDFS."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence


class HdfsClient:
    def __init__(self, timeout: int = 300) -> None:
        self.timeout = timeout

    def run(
        self, arguments: Sequence[str], *, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["hdfs", "dfs", *map(str, arguments)],
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
        )
        if check and result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result

    def exists(self, path: str) -> bool:
        return self.run(["-test", "-e", path], check=False).returncode == 0

    def is_file(self, path: str) -> bool:
        return self.run(["-test", "-f", path], check=False).returncode == 0

    def is_directory(self, path: str) -> bool:
        return self.run(["-test", "-d", path], check=False).returncode == 0
