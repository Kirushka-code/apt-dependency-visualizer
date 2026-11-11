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

Выполнены этапы 1 и 2:

- параметры командной строки и проверка конфигурации;
- загрузка индекса Ubuntu и получение прямых зависимостей.

## Запуск

Все команды выполняются из корневой папки проекта.

```powershell
$repo = "https://archive.ubuntu.com/ubuntu/dists/jammy/main/binary-amd64/Packages.gz"
.\run.bat --package hello --repository $repo --version 2.10-2ubuntu4
```

Репозиторий: Ubuntu 22.04 Jammy, компонент main, архитектура amd64.

Результат:

```text
package=hello
version=2.10-2ubuntu4
Direct dependencies:
  libc6 (>= 2.34)
```

Без скрипта Windows приложение можно запустить командой:

```powershell
python -m src.cli --package hello --repository $repo --version 2.10-2ubuntu4
```

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

Ошибки параметров возвращают код завершения 2.
Ошибки загрузки репозитория и поиска пакета возвращают код 1.

Приложение проверяет точное совпадение имени и версии пакета.
Если версия отсутствует, выводятся доступные версии.
При сетевых ошибках выводится сообщение без трассировки Python.

Полноценная работа с тестовым репозиторием будет добавлена на этапе 3.

## Тесты

```powershell
python -m unittest discover -s tests -v
```

## Структура

- `src/` — исходный код.
- `tests/` — автоматические тесты.
- `run.bat` — скрипт запуска для Windows.
- `.gitignore` — правила исключения служебных файлов.

## Этап 2. Получение прямых зависимостей

Приложение загружает индекс Packages по HTTP или HTTPS.
Поддерживаются обычный текст и сжатие gzip и xz.
Формат записей разбирается собственным кодом.

Используются поля Pre-Depends и Depends.
Альтернативы и ограничения версий сохраняются в исходном виде.
Рекомендации Recommends и предложения Suggests не включаются.

Для hello версии 2.10-2ubuntu4 получена зависимость:

```text
libc6 (>= 2.34)
```

Проверены следующие ошибки:

| Случай | Результат |
| --- | --- |
| Неизвестный пакет | Сообщение Package not found |
| Отсутствующая версия | Сообщение со списком доступных версий |
| Отсутствующий индекс | Сообщение HTTP Error 404 |

URL должен вести непосредственно на индекс Packages,
Packages.gz или Packages.xz, а не на главную страницу репозитория.

На этом этапе выводятся только прямые зависимости.
Транзитивный граф будет построен на этапе 3.