# Практическая работа № 4 — вариант 9

Реализация на GitHub Actions. `disk_check.py` проверяет заполнение диска.
При заполнении **от 80% включительно** результат `WARNING`, код завершения 1.
Ниже порога — `OK`, код 0. Ошибка аргументов, конфигурации или диска — код 2.
Приложение использует только стандартную библиотеку Python.

```sh
python disk_check.py --help
python disk_check.py --config settings.json.example
python disk_check.py --used-percent 79 --threshold 80
python disk_check.py --used-percent 80 --threshold 80
python -m unittest discover -s tests -v
```

Аргументы CLI переопределяют JSON-конфигурацию. Допустимы конечные проценты 0..100.
`--used-percent` нужен для воспроизводимой проверки границы независимо от диска.

## CI

Файл `.github/workflows/ci.yml`. Во всех jobs точный образ `python:3.12.7-slim`.
Последовательность: validate → unit_tests → package. 20 тестов unittest.

| Событие | validate | unit_tests | package |
|---|---|---|---|
| push main | обязательно | обязательно | после успешных проверок |
| pull request в main | обязательно | обязательно | — |
| тег | — | — | автоматически |
| experiment/* | допускается ошибка | — | — |
| PR из experiment/* | допускается ошибка | обязательно | — |

Validate компилирует Python-файлы проекта и проверяет AST: в `disk_check.py`
должна быть определена функция `main` на уровне модуля.
Package собирает `disk_check.py`, `README.md`, `Dockerfile`, `settings.json.example`
и `manifest.txt` с `GITHUB_SHA`, `GITHUB_RUN_ID`, именами файлов и SHA-256.
Артефакт `disk-check-<полный SHA>` хранится 7 дней.

## Контролируемое развертывание

Workflow `.github/workflows/deploy.yml` запускается вручную через Actions →
Deploy test → Run workflow. Выбрать main и указать `run_id` успешного CI из main.
Скрипт проверяет статус, тип события, ветку и путь CI workflow через GitHub API.
Артефакт скачивается именно из утвержденного запуска; пересборка не выполняется.

Среда `test/disk` разрешает развертывание только из main. Секрет `DEPLOY_TOKEN`
хранится в этой среде, передается только deploy job и не выводится в журналы.
`APP_PORT=8109` задан в workflows. Приложение консольное, порт не открывает.

Deploy проверяет манифест и контрольные суммы, копирует файлы в `deploy/test`
в рабочей области runner и запускает дымовую проверку реального диска с порогом
100%. Ожидаемый код — 0. Отчет `deployment.txt` публикуется отдельным артефактом.
URL среды ведет на запуск ручного workflow. Это учебное развертывание в runner.

## Отрицательный эксперимент

1. Исправная версия: все 20 тестов проходят, package публикует артефакт.
2. Заменить в `check_usage` сравнение `>=` на `>`, создать и отправить коммит.
3. Должен упасть `test_warning_starts_at_threshold`; дополнительно падают проверки
   CLI и собственного порога. Job package пропускается, артефакт не выпускается.
4. Исправить сравнение новым коммитом и дождаться успешного CI.
5. Скачать артефакт из Actions, сверить манифест, вручную запустить Deploy test.

Документация: https://docs.github.com/en/actions.
