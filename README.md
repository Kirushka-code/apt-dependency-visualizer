# Визуализатор зависимостей пакетов Ubuntu

Учебный CLI-инструмент для получения и визуализации зависимостей
пакетов Ubuntu.

## Требования

- Python 3.10 или новее.
- Для загрузки реального репозитория на следующих этапах нужен интернет.

Приложение использует стандартную библиотеку Python.
Менеджеры пакетов и сторонние библиотеки для получения зависимостей
не используются.

## Состояние проекта

Выполнен этап 1: параметры командной строки и проверка конфигурации.

## Запуск

Все команды выполняются из корневой папки проекта.

```powershell
python -m src.cli --package bash --repository https://example.org/Packages.gz --version 1.0
```

Адрес example.org используется только для демонстрации конфигурации.
На первом этапе приложение не обращается к сети.

Результат:

```text
package=bash
repository=https://example.org/Packages.gz
test_mode=false
version=1.0
```

Запуск в Windows через скрипт:

```powershell
.\run.bat --package bash --repository https://example.org/Packages.gz --version 1.0
```

## Параметры

| Параметр | Назначение |
| --- | --- |
| `--package` | Имя анализируемого пакета |
| `--repository` | URL индекса или путь к тестовому файлу |
| `--test-mode` | Включение режима тестового репозитория |
| `--version` | Точная версия пакета |
| `--help` | Справка |

В обычном режиме используются имена пакетов Ubuntu.
В тестовом режиме имена состоят из больших латинских букв.
Параметр `--test-mode` является флагом и не принимает значения.

## Проверка ошибок

Неверное имя пакета:

```powershell
python -m src.cli --package "Bad Name" --repository https://example.org/Packages.gz --version 1.0
```

Неверный URL:

```powershell
python -m src.cli --package bash --repository invalid --version 1.0
```

Неверная версия:

```powershell
python -m src.cli --package bash --repository https://example.org/Packages.gz --version latest
```

Неверное использование флага тестового режима:

```powershell
python -m src.cli --package A --repository missing.json --version 1.0 --test-mode=false
```

Несуществующий тестовый файл:

```powershell
python -m src.cli --package A --repository missing.json --version 1.0 --test-mode
```

При ошибке выводится сообщение и возвращается код завершения 2.
Проверяется также наличие всех обязательных параметров.

На первом этапе проверяются формат параметров и доступность локального
файла для чтения. Содержимое репозитория, доступность URL и наличие
версии пакета будут проверяться на этапе получения данных.

## Тесты

```powershell
python -m unittest discover -s tests -v
```

## Структура

- `src/` — исходный код.
- `tests/` — автоматические тесты.
- `run.bat` — скрипт запуска для Windows.
- `.gitignore` — правила исключения служебных файлов.