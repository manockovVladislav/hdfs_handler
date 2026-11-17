# HDFS Drive

Streamlit-интерфейс для работы с файлами HDFS, визуально близкий к Google Drive.

Интерфейс поддерживает полноценные светлую и тёмную темы и два представления
файлов: компактный табличный список и сетку плиток. Выбранный режим, фильтр типа
и сортировка работают одинаково для реального HDFS и изолированного демо.

## Стартовый каталог и визуальный тест

Откройте `main.ipynb`. В первой ячейке задаётся только имя конечной папки.
Базовый путь `hdfs://arnsdpsbx/user/team/my_team` зафиксирован в
`hdfs_drive/config.py` и из ноутбука не меняется:

```python
from hdfs_drive.notebook import configure_root_directory

HDFS_ROOT = "u_team"
configure_root_directory(HDFS_ROOT, create_if_missing=False)
```

Приложение открывается с этой директории, не разрешает перейти выше неё и создаёт
новые файлы и папки только внутри неё. Вторая ячейка запускает визуальный тест:

```python
from hdfs_drive.notebook import launch_preview

launch_preview()
```

Под ячейкой появится только ссылка. Сам интерфейс откроется в отдельной вкладке.
Повторный запуск ячейки использует уже запущенный процесс.

Режим задаётся флагом `TEST_MODE` в `hdfs_drive/config.py`:

- `TEST_MODE = 1` — тестовое хранилище, реальный HDFS не используется;
- `TEST_MODE = 0` — боевой HDFS.

## Запуск с HDFS

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Настройки задаются переменными окружения:

- `HDFS_DRIVE_ROOT` — собранная разрешённая корневая директория HDFS;
- `HDFS_DRIVE_TIMEOUT` — тайм-аут команды HDFS в секундах;
- `HDFS_DRIVE_TEST_MODE=0|1` — необязательно переопределяет флаг из конфига.

Загружаемые файлы записываются в HDFS по одному, без общего ZIP-архива.

## Ограничения безопасности

- любой путь проверяется на принадлежность `HDFS_DRIVE_ROOT`;
- каталоги нельзя удалять ни через интерфейс, ни через файловый сервис;
- файл удаляется только после отдельного подтверждения пользователя;
- перед `hdfs dfs -rm` объект повторно проверяется через `hdfs dfs -test -f`;
- рекурсивные флаги удаления не используются;
- команды запускаются списком аргументов без shell.

## Структура

```text
app.py                     # минимальная точка входа Streamlit
hdfs_drive/config.py       # конфигурация
hdfs_drive/models.py       # модели файлов и каталогов
hdfs_drive/client.py       # запуск команд HDFS
hdfs_drive/storage.py      # HDFS-сервис и изолированное демо-хранилище
hdfs_drive/ui.py           # сценарии и компоненты интерфейса
hdfs_drive/theme.py        # оформление
hdfs_drive/notebook.py     # запуск из одной ячейки Jupyter
tests/test_safety.py       # тесты защитных ограничений
```

## Проверка

```bash
python -m unittest discover -v
python -m compileall -q app.py hdfs_drive tests
```
