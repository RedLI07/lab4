"""Допустить к deploy только артефакт успешного CI из main."""
import json
import os
import urllib.request


def main():
    run_id = os.environ["SOURCE_RUN_ID"]
    if not run_id.isdigit():
        raise SystemExit("Некорректный ID запуска")
    url = f"{os.environ['GITHUB_API_URL']}/repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run_id}"
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
                                                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        run = json.load(response)
    if (run["head_branch"] != "main" or run["conclusion"] != "success"
            or run["path"] != ".github/workflows/ci.yml" or run["event"] != "push"):
        raise SystemExit("Требуется успешный push CI из ветки main")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"sha={run['head_sha']}\n")
    print(f"APPROVED_RUN={run_id}\nAPPROVED_SHA={run['head_sha']}")


if __name__ == "__main__":
    main()
