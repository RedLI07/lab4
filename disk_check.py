"""Проверка заполнения диска. Коды: 0 — OK, 1 — WARNING, 2 — ошибка."""

import argparse
import json
import math
import shutil
import sys
from pathlib import Path


def percentage(value):
    """Проверить процент без округления перед сравнением с порогом."""
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 100:
        raise ValueError("Процент должен находиться в диапазоне 0..100")
    return number


def check_usage(used_percent, threshold=80):
    used_percent = percentage(used_percent)
    threshold = percentage(threshold)
    return "WARNING" if used_percent >= threshold else "OK"


def disk_percent(path):
    usage = shutil.disk_usage(path)
    if usage.total <= 0:
        raise ValueError("Размер диска должен быть положительным")
    return usage.used / usage.total * 100


def load_settings(path):
    settings = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(settings, dict):
        raise ValueError("Конфигурация должна быть JSON-объектом")
    return {"path": str(settings.get("path", ".")),
            "threshold": percentage(settings.get("threshold", 80))}


def renamed_main(argv=None):
    parser = argparse.ArgumentParser(description="Проверка заполнения диска")
    parser.add_argument("--config", help="Путь к JSON-конфигурации")
    parser.add_argument("--path", help="Путь на проверяемом диске")
    parser.add_argument("--threshold", type=float, help="Порог предупреждения, 0..100")
    parser.add_argument("--used-percent", type=float, help="Задать заполнение для проверки границ")
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.config) if args.config else {"path": ".", "threshold": 80}
        path = args.path if args.path is not None else settings["path"]
        threshold = percentage(args.threshold if args.threshold is not None else settings["threshold"])
        used = percentage(args.used_percent) if args.used_percent is not None else disk_percent(path)
        status = check_usage(used, threshold)
        print(f"{status}: path={path}; used={used:.2f}%; threshold={threshold:g}%")
        return 0 if status == "OK" else 1
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
