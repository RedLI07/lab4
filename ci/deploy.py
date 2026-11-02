"""Учебное развертывание артефакта в рабочей области runner."""

import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    target = Path("deploy/test")
    target.mkdir(parents=True, exist_ok=True)
    report = target / "deployment.txt"
    lines = [f"TIME={datetime.now(timezone.utc).isoformat()}",
             f"SOURCE_SHA={os.environ.get('SOURCE_SHA', '')}",
             f"SOURCE_RUN_ID={os.environ.get('SOURCE_RUN_ID', '')}",
             f"DEPLOY_RUN_ID={os.environ.get('GITHUB_RUN_ID', '')}",
             "ENVIRONMENT=test/disk", f"APP_PORT={os.environ.get('APP_PORT', '')}"]
    try:
        if not os.environ.get("DEPLOY_TOKEN"):
            raise RuntimeError("DEPLOY_TOKEN отсутствует")
        lines.append("DEPLOY_TOKEN=present (value hidden)")
        manifest = Path("dist/manifest.txt").read_text(encoding="utf-8").splitlines()
        if manifest[:2] != [f"GITHUB_SHA={os.environ['SOURCE_SHA']}",
                           f"GITHUB_RUN_ID={os.environ['SOURCE_RUN_ID']}"]:
            raise RuntimeError("Манифест не соответствует утвержденному выпуску")
        expected = {"disk_check.py", "README.md", "Dockerfile", "settings.json.example"}
        verified = set()
        for line in manifest[3:]:
            digest, name = line.split("  ", 1)
            if name not in expected or name in verified:
                raise RuntimeError("Неожиданный файл в манифесте")
            data = (Path("dist") / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise RuntimeError(f"Неверная сумма: {name}")
            verified.add(name)
        if verified != expected:
            raise RuntimeError("Неполный манифест")
        lines.append("MANIFEST=verified")
        shutil.copytree("dist", target, dirs_exist_ok=True)
        command = [sys.executable, "disk_check.py", "--path", ".", "--threshold", "100"]
        result = subprocess.run(command, cwd=target, text=True, capture_output=True, check=False)
        lines.extend(["SMOKE=python disk_check.py --path . --threshold 100",
                      result.stdout.strip(), result.stderr.strip(), f"EXIT_CODE={result.returncode}"])
        if result.returncode != 0:
            raise RuntimeError("Дымовая проверка не пройдена")
        lines.append("DEPLOYMENT=success")
    except Exception as exc:
        lines.extend([f"ERROR={exc}", "DEPLOYMENT=failed"])
        raise
    finally:
        report.write_text("\n".join(line for line in lines if line) + "\n", encoding="utf-8")
        print(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
