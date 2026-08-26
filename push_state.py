import os
import requests

GIST_TOKEN = os.environ["GIST_TOKEN"]
GIST_ID = os.environ["GIST_ID"]
LOCAL_FILE = "timetable.json"


def main():
    if not os.path.exists(LOCAL_FILE):
        print(f"{LOCAL_FILE} not found — nothing to push (watcher likely exited early).")
        return

    with open(LOCAL_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    resp = requests.patch(
        f"https://api.github.com/gists/{GIST_ID}",
        headers={"Authorization": f"token {GIST_TOKEN}"},
        json={"files": {"state.json": {"content": content}}},
        timeout=15,
    )
    resp.raise_for_status()
    print("Pushed updated timetable state to gist.")


if __name__ == "__main__":
    main()