"""Доменные ошибки файлового приложения."""


class DriveError(RuntimeError):
    """Базовая ожидаемая ошибка приложения."""


class UnsafePathError(DriveError):
    """Путь находится за пределами разрешённого корня."""


class ConfirmationRequiredError(DriveError):
    """Разрушительная операция вызвана без подтверждения."""


class DirectoryDeletionForbiddenError(DriveError):
    """Попытка удалить каталог."""
