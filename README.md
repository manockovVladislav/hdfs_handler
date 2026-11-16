# HDFS Drive

Streamlit-интерфейс для работы с файлами HDFS, визуально близкий к Google Drive.

Интерфейс поддерживает полноценные светлую и тёмную темы и два представления
файлов: компактный табличный список и сетку плиток. Выбранный режим, фильтр типа
и сортировка работают одинаково для реального HDFS и изолированного демо.

## Стартовый каталог и визуальный тест

Откройте `main.ipynb`. В первой ячейке задаётся верхняя директория HDFS:

```python
from hdfs_drive.notebook import configure_root_directory

HDFS_ROOT = "hdfs://arnsdpsbx/user/team/my_team/u_team"
configure_root_directory(HDFS_ROOT, create_if_missing=False)
```

Приложение открывается с этой директории, не разрешает перейти выше неё и создаёт
новые файлы и папки только внутри неё. Вторая ячейка запускает визуальный тест:

```python
from hdfs_drive.notebook import launch_preview

launch_preview()
```

Предпросмотр запускается в изолированном демо-режиме. Он не подключается к HDFS,
не читает и не изменяет реальные данные. Интерфейс появится под ячейкой, а рядом будет
ссылка для открытия в новой вкладке. Повторный запуск ячейки использует уже запущенный
процесс.

## Запуск с HDFS

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Настройки задаются переменными окружения:

- `HDFS_DRIVE_ROOT` — разрешённая корневая директория HDFS;
- `HDFS_DRIVE_ARCHIVE` — имя внутреннего ZIP (`.hdfs_files.zip` по умолчанию);
- `HDFS_DRIVE_TIMEOUT` — тайм-аут команды HDFS в секундах;
- `HDFS_DRIVE_DEMO=1` — изолированный визуальный демо-режим.

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
