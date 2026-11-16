"""Настройка стартового каталога и запуск визуального демо из Jupyter."""

from __future__ import annotations

import html
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from IPython.display import HTML, display

from .config import AppConfig
from .storage import HdfsStorage
from .utils import validate_root_path


_PROCESS: subprocess.Popen[str] | None = None
_LOG_FILE = None
_PORT: int | None = None


def _stop_preview() -> None:
    global _PROCESS, _LOG_FILE, _PORT
    if _PROCESS is not None and _PROCESS.poll() is None:
        _PROCESS.terminate()
        try:
            _PROCESS.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _PROCESS.kill()
            _PROCESS.wait(timeout=5)
    if _LOG_FILE is not None and not _LOG_FILE.closed:
        _LOG_FILE.close()
    _PROCESS = None
    _LOG_FILE = None
    _PORT = None


def configure_root_directory(
    root_path: str, *, create_if_missing: bool = False
) -> dict[str, object]:
    """Задаёт единственный стартовый каталог приложения и проверяет HDFS."""
    root = validate_root_path(root_path)
    os.environ["HDFS_DRIVE_ROOT"] = root
    result: dict[str, object] = {
        "root": root,
        "created": False,
        "hdfs_status": "не проверялся",
    }

    if shutil.which("hdfs") is None:
        result["hdfs_status"] = "команда hdfs не найдена; путь применён к демо"
    else:
        try:
            storage = HdfsStorage(AppConfig.from_env())
            if storage.client.exists(root):
                if not storage.client.is_directory(root):
                    raise RuntimeError("Указанный путь существует, но не является папкой")
                result["hdfs_status"] = "каталог доступен"
            elif create_if_missing:
                storage.client.run(["-mkdir", root])
                result["created"] = True
                result["hdfs_status"] = "каталог создан"
            else:
                result["hdfs_status"] = "каталог не найден"
        except Exception as error:
            result["hdfs_status"] = f"ошибка подключения: {error}"

    # Следующий предпросмотр должен получить обновлённый HDFS_DRIVE_ROOT.
    _stop_preview()
    display(
        HTML(
            f"""
            <div style="font-family:system-ui;padding:12px 14px;border:1px solid #dadce0;
                        border-radius:12px;margin:6px 0 12px">
              <b>Стартовый каталог настроен</b><br>
              <code>{html.escape(root)}</code><br>
              <small>HDFS: {html.escape(str(result['hdfs_status']))}</small>
            </div>
            """
        )
    )
    return result


def _free_port(start: int = 8501, attempts: int = 50) -> int:
    for port in range(start, start + attempts):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("Не удалось найти свободный порт для Streamlit")


def _wait_until_ready(port: int, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/_stcore/health"
    while time.monotonic() < deadline:
        if _PROCESS is not None and _PROCESS.poll() is not None:
            raise RuntimeError("Streamlit завершился во время запуска")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.25)
    raise TimeoutError("Streamlit не успел запуститься за 20 секунд")


def launch_preview(*, height: int = 760) -> None:
    """Запускает безопасное демо и показывает его прямо под ячейкой."""
    global _PROCESS, _LOG_FILE, _PORT

    project_root = Path(__file__).resolve().parent.parent
    app_path = project_root / "app.py"
    if _PROCESS is None or _PROCESS.poll() is not None:
        _PORT = _free_port()
        log_path = Path("/tmp") / f"hdfs_drive_streamlit_{_PORT}.log"
        _LOG_FILE = log_path.open("w", encoding="utf-8")
        environment = os.environ.copy()
        environment["HDFS_DRIVE_DEMO"] = "1"
        _PROCESS = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_path),
                "--server.address=0.0.0.0",
                f"--server.port={_PORT}",
                "--server.headless=true",
                "--browser.gatherUsageStats=false",
                "--server.maxUploadSize=500",
            ],
            cwd=project_root,
            env=environment,
            stdout=_LOG_FILE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    assert _PORT is not None
    try:
        _wait_until_ready(_PORT)
    except Exception:
        log_path = Path("/tmp") / f"hdfs_drive_streamlit_{_PORT}.log"
        details = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        raise RuntimeError(f"Не удалось запустить предпросмотр.\n{details}") from None

    prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "").rstrip("/")
    public_url = (
        f"{prefix}/proxy/{_PORT}/"
        if prefix
        else f"http://127.0.0.1:{_PORT}/"
    )
    display(
        HTML(
            f"""
            <div style="font-family:system-ui;margin:8px 0 12px">
              <b>HDFS Drive запущен в безопасном демо-режиме.</b>
              <a href="{public_url}" target="_blank" style="margin-left:12px">
                Открыть в новой вкладке
              </a>
            </div>
            <iframe src="{public_url}" width="100%" height="{height}"
              style="border:1px solid #dadce0;border-radius:16px;background:#fff"></iframe>
            """
        )
    )
