import json
import os
import requests

GIST_TOKEN = os.environ["GIST_TOKEN"]
GIST_ID = os.environ["GIST_ID"]
LOCAL_FILE = "timetable.json"


def main():
    resp = requests.get(
        f"https://api.github.com/gists/{GIST_ID}",
        headers={"Authorization": f"token {GIST_TOKEN}"},
        timeout=15,
    )
    resp.raise_for_status()

    files = resp.json().get("files", {})
    content = files.get("state.json", {}).get("content", "")

    if not content or not content.strip():
        data = []
        print("Gist state.json is empty — treating this as the first run.")
    else:
        data = json.loads(content)
        print(f"Restored previous timetable state ({len(data)} entries) from gist.")

    with open(LOCAL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()