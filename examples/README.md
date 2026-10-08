# Примеры TWYLT 1.1.1

Каждый пример содержит свой контракт и бизнес-логику в tool.py. Нужны только
Python, TWYLT и его зависимости; twylt-pack-essential не нужен. Ping/echo основаны
на essential 0.2.0, но не импортируют код пака. Guardrails импортируются из TWYLT.

Установка из корня репозитория:

```bash
python -m pip install -e '.[test]'
```

| Пример | Бизнес-проверки | Системные зависимости |
|---|---|---|
| list_directory | Workspace.resolve для запрошенного пути; inspect для каждого результата перед is_dir | нет |
| ping | check_network перед поиском/запуском программы; безопасные аргументы без shell | iputils-ping в Linux; ping в Windows |
| echo | нет; возвращает текст без преобразований | нет |

Проверки включаются TWYLT_GUARDRAILS=1. Когда переменная отсутствует или равна 0,
общая политика не ограничивает бизнес-операции. Валидация моделей и защита от
внедрения аргументов ping сохраняются. Это механизмы типового контроля; автор
тула отвечает за их использование, произвольные обращения ограничивает ОС.

## list_directory

Создайте workspace вне исходников, чтобы пример не показывал свои временные файлы:

```bash
mkdir -p /tmp/twylt-example-workspace/sub
printf 'hello\n' > /tmp/twylt-example-workspace/a.txt
TWYLT_GUARDRAILS=1 TWYLT_WORKSPACE_ROOT=/tmp/twylt-example-workspace \
  python examples/list_directory/run.py '{"path":"/"}'
```

`/` — виртуальный корень workspace, а `/sub` и `sub` — каталог sub внутри него.
`..`, симлинки/junctions, hardlinks, специальные файлы и переход устройства
отклоняются политикой. Проверяются и запрошенный каталог, и непосредственные дети;
пример не выполняет рекурсивный обход. Если ребёнок запрещён, отклоняется весь
запрос, вместо следования по ссылке при is_dir().

Запрос с выходом через .. завершается guardrails_error, exit code 6:

```bash
TWYLT_GUARDRAILS=1 TWYLT_WORKSPACE_ROOT=/tmp/twylt-example-workspace \
  python examples/list_directory/run.py '{"path":"../outside"}'
```

Без guardrails и без workspace используется обычный путь ФС:

```bash
TWYLT_GUARDRAILS=0 TWYLT_WORKSPACE_ROOT= \
  python examples/list_directory/run.py '{"path":"."}'
```

## ping

Linux: установите iputils-ping средствами дистрибутива. Поддерживаются Linux и
Windows; macOS не поддерживается. Нужные права на ICMP определяются ОС.

```bash
TWYLT_GUARDRAILS=1 TWYLT_DISABLE_NETWORK=0 \
  python examples/ping/run.py '{"host":"127.0.0.1","count":1,"timeout":5}'
```

Сетевой запрет проверяется до запуска subprocess, workspace для CLI не нужен:

```bash
TWYLT_GUARDRAILS=1 TWYLT_DISABLE_NETWORK=1 \
  python examples/ping/run.py '{"host":"127.0.0.1","count":1}'
```

Получится guardrails_error / network_disabled, exit code 6. Отказ содержит
incident_id; событие JSONL пишется в stderr или TWYLT_INCIDENT_LOG. Это отдельное
событие перед JSON-ошибкой. При разрешённой сети ответ показывает reachable,
returncode, timed_out, stdout/stderr и elapsed_seconds. Фактическая недоступность
хоста представляется структурированным результатом; отсутствие ping — ошибка
исполнения. count/family/timeout и host входят в контракт, команда запускается без shell.

## echo

```bash
python examples/echo/run.py '{"text":"Привет!\nВторая строка"}'
TWYLT_GUARDRAILS=1 TWYLT_DISABLE_NETWORK=1 \
  python examples/echo/run.py '{"text":"Работает при запрете сети"}'
```

Echo не импортирует guardrails и не обращается к сети или бизнес-файлам. Возвращает
поле text точно, включая пробелы и переводы строк. Строгая валидация контракта остаётся.

Общая защита файлового транспорта внутри Tool.run применяется и к echo, если
guardrails включены и используется input.json/output.json. Поэтому "без guardrails"
в этом примере означает отсутствие явных проверок в бизнес-логике. Для файлового
режима используйте cwd внутри workspace либо TWYLT_ALLOWED_CWD, включая подкаталоги;
этот допуск не расширяет бизнес-workspace. CLI/stdin выводят результат в stdout.

## Описание

Для каждого примера доступны все штатные describe-режимы, например:

```bash
python examples/list_directory/run.py '{"describe":"json_spec"}'
python examples/ping/run.py '{"describe":"json_spec"}'
python examples/echo/run.py '{"describe":"json_spec"}'
```

Описание не выполняет бизнес-логику, не запускает ping и не требует workspace.
Метаданные остаются литералами для bootstrap при отсутствующих зависимостях.
