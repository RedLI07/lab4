"""Сборка утвержденных файлов и манифеста с контрольными суммами."""

import hashlib
import os
import shutil
from pathlib import Path


FILES = ("disk_check.py", "README.md", "Dockerfile", "settings.json.example")


def main():
    sha = os.environ["GITHUB_SHA"]
    pipeline_id = os.environ["GITHUB_RUN_ID"]
    target = Path("dist")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    lines = [f"GITHUB_SHA={sha}", f"GITHUB_RUN_ID={pipeline_id}", "FILES:"]
    for name in FILES:
        shutil.copy2(name, target / name)
        digest = hashlib.sha256((target / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (target / "manifest.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((target / "manifest.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
