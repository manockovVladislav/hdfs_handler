"""Streamlit-представление: только UI и координация действий пользователя."""

from __future__ import annotations

import html
import json
import mimetypes
import posixpath
import uuid

import streamlit as st

from .config import AppConfig
from .models import FileEntry
from .storage import DriveStorage, HdfsStorage, TestStorage
from .theme import apply_theme
from .utils import ensure_within_root, file_icon, format_size


@st.cache_resource
def _build_storage(config: AppConfig) -> DriveStorage:
    if config.test_mode:
        return TestStorage(root=config.root)
    return HdfsStorage(config)


def _initialize_state(root: str) -> None:
    defaults = {
        "drive_root": root,
        "current_path": root,
        "pending_delete": None,
        "download_data": None,
        "download_name": None,
        "download_mime": "application/octet-stream",
        "download_token": None,
        "flash": None,
        "view_mode": "Список",
        "kind_filter": "Все объекты",
        "sort_order": "Название А–Я",
    }
    if st.session_state.get("drive_root") != root:
        for key in defaults:
            st.session_state.pop(key, None)
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _flash(message: str) -> None:
    st.session_state.flash = message
    st.rerun()


def _initialize_theme_state() -> None:
    if "theme_selector" in st.session_state:
        return
    native_theme = st.context.theme.type
    st.session_state.theme_selector = (
        "Тёмная" if native_theme == "dark" else "Светлая"
    )


def _render_theme_selector() -> None:
    selected = st.radio(
        "Оформление",
        ["Светлая", "Тёмная"],
        horizontal=True,
        key="theme_selector",
    )
    requested_theme = "Dark" if selected == "Тёмная" else "Light"
    native_theme = st.context.theme.type
    if native_theme == requested_theme.lower():
        return
    # Streamlit хранит выбранную нативную тему по пути приложения. Значение
    # статично и не содержит пользовательских данных.
    st.html(
        f"""
        <script>
        (() => {{
          const key = `stActiveTheme-${{window.location.pathname}}-v2`;
          const value = {json.dumps(requested_theme)};
          if (window.localStorage.getItem(key) !== JSON.stringify(value)) {{
            window.localStorage.setItem(key, JSON.stringify(value));
            window.location.reload();
          }}
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def _render_create_folder(storage: DriveStorage, current_path: str) -> None:
    with st.popover("＋  Новая папка", use_container_width=True):
        st.markdown("#### Новая папка")
        folder_name = st.text_input(
            "Название папки", placeholder="Например, Отчёты", key="folder_input"
        )
        if st.button("Создать папку", use_container_width=True, key="create_folder"):
            try:
                storage.create_folder(current_path, folder_name)
                _flash("Папка создана")
            except Exception as error:
                st.error(str(error))


def _render_upload_files(storage: DriveStorage, current_path: str) -> None:
    with st.popover("⬆  Добавить файл", use_container_width=True):
        st.markdown("#### Добавить файлы")
        uploaded_files = st.file_uploader(
            "Выберите файлы",
            accept_multiple_files=True,
            key="drive_uploader",
            label_visibility="collapsed",
        )
        if st.button(
            "Загрузить",
            disabled=not uploaded_files,
            use_container_width=True,
            key="upload_files",
        ):
            try:
                with st.spinner("Загрузка файлов…"):
                    added, skipped = storage.upload_files(current_path, uploaded_files)
                message = f"Загружено: {len(added)}"
                if skipped:
                    message += f" · пропущено: {len(skipped)}"
                _flash(message)
            except Exception as error:
                st.error(f"Ошибка загрузки: {error}")


def _render_sidebar(storage: DriveStorage, config: AppConfig) -> None:
    with st.sidebar:
        st.markdown(
            '<div class="drive-brand"><span class="drive-mark"></span>'
            "<span>HDFS Drive</span></div>",
            unsafe_allow_html=True,
        )
        _render_create_folder(storage, st.session_state.current_path)
        _render_upload_files(storage, st.session_state.current_path)
        st.write("")
        st.button(
            "▣  Мой диск",
            use_container_width=True,
            key="go_root",
            on_click=_navigate_to,
            args=(storage.root,),
        )
        st.write("")
        st.caption("ХРАНИЛИЩЕ")
        st.caption("Доступно только в пределах корневой папки")
        st.caption(f"Стартовый каталог: {config.root}")
        st.divider()
        _render_theme_selector()
        if config.test_mode:
            st.markdown('<span class="test-pill">ТЕСТОВЫЙ РЕЖИМ</span>', unsafe_allow_html=True)
            st.caption("Реальный HDFS не используется")
        else:
            st.caption("Подключение: HDFS")
            st.caption(config.root)
        st.markdown(
            '<div class="safety-note">🛡️ Каталоги нельзя удалять. Удаление файла '
            "выполняется только после подтверждения.</div>",
            unsafe_allow_html=True,
        )


def _render_breadcrumbs(root: str, current_path: str) -> None:
    relative = current_path[len(root) :].strip("/")
    segments = relative.split("/") if relative else []
    columns = st.columns([1.4, *([1] * len(segments)), 8])
    with columns[0]:
        st.button(
            "Мой диск",
            key="crumb_root",
            type="tertiary",
            on_click=_navigate_to,
            args=(root,),
        )
    for index, segment in enumerate(segments):
        target = posixpath.join(root, *segments[: index + 1])
        with columns[index + 1]:
            st.button(
                f"›  {segment}",
                key=f"crumb_{index}",
                type="tertiary",
                on_click=_navigate_to,
                args=(target,),
            )


def _render_download() -> None:
    if st.session_state.download_data is None:
        return
    token = st.session_state.download_token
    container_key = f"automatic_download_{token}"
    st.html(f"<style>.st-key-{container_key} {{ display: none !important; }}</style>")
    with st.container(key=container_key):
        st.download_button(
            "Автоматическое скачивание",
            data=st.session_state.download_data,
            file_name=st.session_state.download_name,
            mime=st.session_state.download_mime,
            key=f"download_payload_{token}",
            on_click="ignore",
        )
    # Streamlit требует download_button для безопасной выдачи файла.
    # Кнопка скрыта и нажимается один раз после подготовки файла.
    st.html(
        f"""
        <script>
        (() => {{
          const storageKey = {json.dumps(f"hdfs-drive-download-{token}")};
          if (window.sessionStorage.getItem(storageKey)) return;
          let attempts = 0;
          const startDownload = () => {{
            const button = document.querySelector('.st-key-{container_key} button');
            if (!button && attempts++ < 50) {{
              window.setTimeout(startDownload, 100);
              return;
            }}
            if (!button) return;
            window.sessionStorage.setItem(storageKey, '1');
            button.click();
          }};
          startDownload();
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def _clear_pending_delete() -> None:
    st.session_state.pending_delete = None


@st.dialog(
    "Удаление файла",
    width="small",
    dismissible=True,
    on_dismiss=_clear_pending_delete,
)
def _render_delete_dialog(storage: DriveStorage) -> None:
    pending: FileEntry | None = st.session_state.pending_delete
    if pending is None:
        return
    if pending.is_directory:
        st.session_state.pending_delete = None
        st.error("Удаление каталогов запрещено")
        return
    st.warning(
        f"Удалить файл «{pending.name}»? Это действие нельзя будет отменить."
    )
    cancel_col, confirm_col = st.columns(2)
    if cancel_col.button("Отмена", use_container_width=True, key="cancel_delete"):
        _clear_pending_delete()
        st.rerun()
    if confirm_col.button(
        "Удалить",
        type="primary",
        use_container_width=True,
        key="confirm_delete",
    ):
        try:
            storage.delete_file(pending, confirmed=True)
            _clear_pending_delete()
            _flash("Файл удалён")
        except Exception as error:
            st.error(f"Ошибка удаления: {error}")


def _render_delete_confirmation(storage: DriveStorage) -> None:
    if st.session_state.pending_delete is not None:
        _render_delete_dialog(storage)


def _navigate_to(path: str) -> None:
    st.session_state.current_path = path
    st.session_state.pending_delete = None
    st.session_state.kind_filter = "Все объекты"


def _render_file_actions(
    storage: DriveStorage, entry: FileEntry, *, key_prefix: str
) -> None:
    with st.popover("⋮", use_container_width=True):
        if st.button("↓ Скачать", key=f"download_{key_prefix}", use_container_width=True):
            try:
                with st.spinner("Подготовка файла…"):
                    st.session_state.download_data = storage.download_file(entry)
                st.session_state.download_name = entry.name
                st.session_state.download_mime = (
                    mimetypes.guess_type(entry.name)[0] or "application/octet-stream"
                )
                st.session_state.download_token = uuid.uuid4().hex
                st.rerun()
            except Exception as error:
                st.error(str(error))
        if st.button("🗑 Удалить", key=f"delete_{key_prefix}", use_container_width=True):
            st.session_state.pending_delete = entry
            st.rerun()


def _render_list(storage: DriveStorage, entries: list[FileEntry]) -> None:
    header = st.columns([4.6, 1.4, 1.7, 1.1, 0.35])
    header[0].markdown("**Название**")
    header[1].markdown("**Владелец**")
    header[2].markdown("**Изменено**")
    header[3].markdown("**Размер**")
    st.markdown('<div class="drive-divider"></div>', unsafe_allow_html=True)
    for index, entry in enumerate(entries):
        name_col, owner_col, date_col, size_col, menu_col = st.columns(
            [4.6, 1.4, 1.7, 1.1, 0.35]
        )
        if entry.is_directory:
            name_col.button(
                f"📁  {entry.name}",
                key=f"open_list_{index}_{entry.identity}",
                use_container_width=True,
                type="tertiary",
                on_click=_navigate_to,
                args=(entry.path,),
            )
        else:
            safe_name = html.escape(entry.name)
            name_col.markdown(
                f'<div class="file-name">{file_icon(entry.name)}&nbsp;&nbsp;{safe_name}</div>',
                unsafe_allow_html=True,
            )
        owner_col.caption(entry.owner or "—")
        date_col.caption(entry.modified or "—")
        size_col.caption("—" if entry.is_directory else format_size(entry.size))
        if not entry.is_directory:
            with menu_col:
                _render_file_actions(storage, entry, key_prefix=f"list_{index}")
        st.markdown('<div class="drive-divider"></div>', unsafe_allow_html=True)


def _render_grid(storage: DriveStorage, entries: list[FileEntry]) -> None:
    for row_start in range(0, len(entries), 4):
        columns = st.columns(4)
        for offset, entry in enumerate(entries[row_start : row_start + 4]):
            index = row_start + offset
            with columns[offset]:
                with st.container(border=True):
                    safe_name = html.escape(entry.name)
                    if entry.is_directory:
                        st.button(
                            f"📁  {entry.name}",
                            key=f"open_grid_{index}_{entry.identity}",
                            use_container_width=True,
                            type="tertiary",
                            on_click=_navigate_to,
                            args=(entry.path,),
                        )
                        st.markdown('<div class="folder-preview">📁</div>', unsafe_allow_html=True)
                        st.caption(f"Папка · {entry.modified or '—'}")
                    else:
                        title_col, menu_col = st.columns([5, 1])
                        title_col.markdown(
                            f'<div class="grid-title">{file_icon(entry.name)}&nbsp; {safe_name}</div>',
                            unsafe_allow_html=True,
                        )
                        with menu_col:
                            _render_file_actions(storage, entry, key_prefix=f"grid_{index}")
                        st.markdown(
                            f'<div class="file-preview">{file_icon(entry.name)}</div>',
                            unsafe_allow_html=True,
                        )
                        st.caption(f"{format_size(entry.size)} · {entry.modified or '—'}")


def _filter_and_sort_entries(
    entries: list[FileEntry], search: str, kind_filter: str, sort_order: str
) -> list[FileEntry]:
    if search:
        entries = [entry for entry in entries if search.casefold() in entry.name.casefold()]
    if kind_filter == "Папки":
        entries = [entry for entry in entries if entry.is_directory]
    elif kind_filter == "Файлы":
        entries = [entry for entry in entries if not entry.is_directory]
    if sort_order == "Название Я–А":
        return sorted(entries, key=lambda entry: entry.name.casefold(), reverse=True)
    if sort_order == "Сначала большие":
        return sorted(entries, key=lambda entry: (entry.is_directory, entry.size), reverse=True)
    if sort_order == "Сначала маленькие":
        return sorted(entries, key=lambda entry: (not entry.is_directory, entry.size))
    return sorted(entries, key=lambda entry: (not entry.is_directory, entry.name.casefold()))


def render_app() -> None:
    st.set_page_config(
        page_title="HDFS Drive",
        page_icon="📁",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    config = AppConfig.from_env()
    storage = _build_storage(config)
    _initialize_state(storage.root)
    _initialize_theme_state()
    apply_theme(st.session_state.theme_selector == "Тёмная")

    try:
        available = storage.is_available()
    except (FileNotFoundError, OSError) as error:
        st.error(f"Команда HDFS недоступна: {error}")
        st.info("Для визуального теста запустите единственную ячейку main.ipynb.")
        st.stop()
    if not available:
        st.error(f"Нет доступа к корневой директории: {storage.root}")
        st.stop()

    try:
        current_path = ensure_within_root(st.session_state.current_path, storage.root)
    except Exception:
        current_path = storage.root
        st.session_state.current_path = current_path

    _render_sidebar(storage, config)
    search_col, status_col = st.columns([6.5, 1])
    search = search_col.text_input(
        "Поиск", placeholder="🔍  Поиск на Диске", label_visibility="collapsed"
    )
    status_col.markdown(
        '<div class="storage-status">●&nbsp; HDFS</div>', unsafe_allow_html=True
    )

    if st.session_state.flash:
        st.success(st.session_state.flash)
        st.session_state.flash = None
    _render_download()
    _render_delete_confirmation(storage)

    try:
        entries = storage.list_directory(current_path)
    except Exception as error:
        st.error(f"Ошибка чтения хранилища: {error}")
        st.stop()

    with st.container(border=True):
        breadcrumb_col, view_col = st.columns([6.5, 1.4])
        with breadcrumb_col:
            _render_breadcrumbs(storage.root, current_path)
        with view_col:
            st.segmented_control(
                "Вид",
                options=["Список", "Сетка"],
                format_func=lambda value: "☷" if value == "Список" else "▦",
                key="view_mode",
                label_visibility="collapsed",
            )

        filter_col, sort_col, info_col = st.columns([1.4, 2, 5])
        kind_filter = filter_col.selectbox(
            "Тип",
            ["Все объекты", "Папки", "Файлы"],
            key="kind_filter",
            label_visibility="collapsed",
        )
        sort_order = sort_col.selectbox(
            "Сортировка",
            [
                "Название А–Я",
                "Название Я–А",
                "Сначала большие",
                "Сначала маленькие",
            ],
            key="sort_order",
            label_visibility="collapsed",
        )
        entries = _filter_and_sort_entries(entries, search, kind_filter, sort_order)
        info_col.caption(f"Объектов: {len(entries)}")

        if not entries:
            st.info("Ничего не найдено. Измените фильтр или загрузите файлы.")
        elif st.session_state.view_mode == "Сетка":
            _render_grid(storage, entries)
        else:
            _render_list(storage, entries)
