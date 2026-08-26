import json
import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from timetable_scraper import scrape_timetable


PREVIOUS_FILE = "timetable.json"
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"

load_dotenv()


def load_timetable(filename):
    """
    Load timetable data from a JSON file.
    """

    if not os.path.exists(filename):
        return []

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_timetable(filename, timetable):
    """
    Save timetable data to a JSON file.
    """

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            timetable,
            f,
            indent=4,
            ensure_ascii=False
        )


def class_id(entry):
    """
    Generate a stable identifier for a class.

    The ID remains stable even if
    the time, room, or faculty changes.
    """

    return (
        f"{entry['batch']}_"
        f"{entry['course_code']}_"
        f"{entry['class_type']}_"
        f"{entry['day']}"
    )


def index_timetable(timetable):
    """
    Convert timetable list into a dictionary
    indexed by stable class ID.
    """

    return {
        class_id(entry): entry
        for entry in timetable
    }


def compare_timetables(previous, current):

    previous_map = index_timetable(previous)
    current_map = index_timetable(current)

    changes = {
        "added": [],
        "removed": [],
        "modified": []
    }

    # --------------------------------------------------
    # ADDED / MODIFIED
    # --------------------------------------------------

    for cid, current_class in current_map.items():

        # New class
        if cid not in previous_map:

            changes["added"].append(
                current_class
            )

            continue

        previous_class = previous_map[cid]

        modifications = {}

        fields = [
            "subject",
            "time",
            "room",
            "faculty",
            "secondary_faculty"
        ]

        for field in fields:

            old_value = previous_class.get(field)
            new_value = current_class.get(field)

            if old_value != new_value:

                modifications[field] = {
                    "old": old_value,
                    "new": new_value
                }

        if modifications:

            changes["modified"].append({
                "class": current_class,
                "changes": modifications
            })

    # --------------------------------------------------
    # REMOVED
    # --------------------------------------------------

    for cid, previous_class in previous_map.items():

        if cid not in current_map:

            changes["removed"].append(
                previous_class
            )

    return changes


def print_changes(changes):

    total_changes = (
        len(changes["added"]) +
        len(changes["removed"]) +
        len(changes["modified"])
    )

    # --------------------------------------------------
    # NO CHANGES
    # --------------------------------------------------

    if total_changes == 0:

        print(
            "\n✅ No timetable changes detected."
        )

        return

    print(
        "\n🚨 TIMETABLE CHANGES DETECTED"
    )

    print("=" * 80)

    # --------------------------------------------------
    # ADDED
    # --------------------------------------------------

    if changes["added"]:

        print("\n🆕 ADDED CLASSES")
        print("-" * 80)

        for entry in changes["added"]:

            print(
                f"{entry['day']} | "
                f"{entry['time']} | "
                f"{entry['course_code']} | "
                f"{entry['subject']}"
            )

    # --------------------------------------------------
    # REMOVED
    # --------------------------------------------------

    if changes["removed"]:

        print("\n❌ REMOVED CLASSES")
        print("-" * 80)

        for entry in changes["removed"]:

            print(
                f"{entry['day']} | "
                f"{entry['time']} | "
                f"{entry['course_code']} | "
                f"{entry['subject']}"
            )

    # --------------------------------------------------
    # MODIFIED
    # --------------------------------------------------

    if changes["modified"]:

        print("\n✏️ MODIFIED CLASSES")
        print("-" * 80)

        for modification in changes["modified"]:

            entry = modification["class"]

            print(
                f"\n{entry['day']} | "
                f"{entry['course_code']} | "
                f"{entry['subject']}"
            )

            for field, change in modification["changes"].items():

                print(
                    f"  {field}: "
                    f"{change['old']} → "
                    f"{change['new']}"
                )


def _class_summary(entry):
    """Return a readable, complete description of a timetable entry."""
    faculty = entry.get("faculty") or "Not assigned"
    secondary = entry.get("secondary_faculty") or "None"
    return (
        f"{entry.get('day', 'Unknown day')} | {entry.get('time', 'Unknown time')}\n"
        f"{entry.get('course_code', 'Unknown course')} — {entry.get('subject', 'Unknown subject')}\n"
        f"Type: {entry.get('class_type', 'Unknown')} | Batch: {entry.get('batch', 'Unknown')}\n"
        f"Room: {entry.get('room', 'Not assigned')}\n"
        f"Faculty: {faculty} | Secondary faculty: {secondary}"
    )

def format_telegram_notification(changes):
    """Create a clean, readable Telegram message for timetable changes."""

    total_changes = sum(
        len(changes[kind])
        for kind in ("added", "removed", "modified")
    )

    timestamp = datetime.now().astimezone().strftime(
        "%d %b %Y • %I:%M %p %Z"
    )

    sections = [
        "📚 <b>Timetable Updated</b>",
        f"🕒 {timestamp}\n"
        f"Detected <b>{total_changes}</b> change(s)."
    ]

    # ==================================================
    # NEW CLASSES
    # ==================================================

    if changes["added"]:

        added = []

        for entry in changes["added"]:

            added.append(
                f"🆕 <b>{entry['subject']}</b>\n"
                f"📚 {entry['course_code']}\n"
                f"📅 {entry['day']}\n"
                f"⏰ {entry['time']}\n"
                f"📍 {entry['room']}\n"
                f"👨‍🏫 {entry['faculty']}"
            )

        sections.append(
            "🟢 <b>New Classes</b>\n\n"
            + "\n\n".join(added)
        )

    # ==================================================
    # REMOVED CLASSES
    # ==================================================

    if changes["removed"]:

        removed = []

        for entry in changes["removed"]:

            removed.append(
                f"❌ <b>{entry['subject']}</b>\n"
                f"📚 {entry['course_code']}\n"
                f"📅 {entry['day']}\n"
                f"⏰ {entry['time']}\n"
                f"📍 {entry['room']}"
            )

        sections.append(
            "🔴 <b>Removed Classes</b>\n\n"
            + "\n\n".join(removed)
        )

    # ==================================================
    # MODIFIED CLASSES
    # ==================================================

    if changes["modified"]:

        modified = []

        for modification in changes["modified"]:

            entry = modification["class"]

            field_changes = []

            for field, values in modification["changes"].items():

                old_value = values["old"] or "Not assigned"
                new_value = values["new"] or "Not assigned"

                field_name = field.replace(
                    "_", " "
                ).title()

                field_changes.append(
                    f"🔹 <b>{field_name} changed</b>\n\n"
                    f"<b>Before</b>\n"
                    f"{old_value}\n\n"
                    f"<b>After</b>\n"
                    f"{new_value}"
                )

            modified.append(
                f"✏️ <b>{entry['subject']}</b>\n"
                f"📚 {entry['course_code']}\n"
                f"📅 {entry['day']}\n\n"
                + "\n\n".join(field_changes)
            )

        sections.append(
            "🟡 <b>Changed Classes</b>\n\n"
            + "\n\n".join(modified)
        )

    return "\n\n".join(sections)


def _telegram_message_parts(message, limit=4000):
    """Split long notifications without cutting a line in half."""
    if len(message) <= limit:
        return [message]

    parts, current = [], ""
    for line in message.splitlines(keepends=True):
        if current and len(current) + len(line) > limit:
            parts.append(current.rstrip())
            current = ""
        while len(line) > limit:
            if current:
                parts.append(current.rstrip())
                current = ""
            parts.append(line[:limit].rstrip())
            line = line[limit:]
        current += line
    if current:
        parts.append(current.rstrip())
    return parts


def _validate_telegram_chat_id(chat_id):
    """Reject common chat-ID mistakes before calling the Telegram API."""
    if chat_id.startswith(("http://", "https://", "t.me/", "telegram.me/")):
        raise RuntimeError(
            "TELEGRAM_CHAT_ID must be a numeric chat ID (for example 123456789 "
            "or -1001234567890), not a Telegram link."
        )
    if not (chat_id.lstrip("-").isdigit() or chat_id.startswith("@")):
        raise RuntimeError(
            "TELEGRAM_CHAT_ID must be a numeric chat ID or a public channel "
            "username beginning with @."
        )


def send_telegram_notification(changes):
    """Send change details to the configured Telegram chat."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError(
            "Telegram is not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env."
        )
    _validate_telegram_chat_id(chat_id)

    message_parts = _telegram_message_parts(format_telegram_notification(changes))
    for number, text in enumerate(message_parts, start=1):
        if len(message_parts) > 1:
            text = f"Part {number}/{len(message_parts)}\n{text}"
        response = requests.post(
            TELEGRAM_API_URL.format(token=token),
            json={"chat_id": chat_id, 
                  "text": text,
                  "parse_mode": "HTML"},
            timeout=30,
        )
        try:
            payload = response.json()
        except requests.JSONDecodeError:
            payload = None
        if not response.ok:
            description = payload.get("description") if isinstance(payload, dict) else response.text
            raise RuntimeError(f"Telegram rejected the notification ({response.status_code}): {description}")
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram rejected the notification: {payload.get('description', payload)}")


def main():

    # --------------------------------------------------
    # SCRAPE CURRENT TIMETABLE
    # --------------------------------------------------

    print("\n🔍 Checking college timetable...")
    print("=" * 80)

    current = scrape_timetable()

    if not current:

        print(
            "❌ Scraper returned no timetable."
        )

        return

    print(
        f"✅ Retrieved {len(current)} classes"
    )

    # --------------------------------------------------
    # LOAD PREVIOUS SNAPSHOT
    # --------------------------------------------------

    previous = load_timetable(
        PREVIOUS_FILE
    )

    # --------------------------------------------------
    # FIRST RUN
    # --------------------------------------------------

    if not previous:

        print(
            "\nℹ️ No previous timetable found."
        )

        print(
            "Saving current timetable as baseline..."
        )

        save_timetable(
            PREVIOUS_FILE,
            current
        )

        print(
            "✅ Baseline created."
        )

        return

    # --------------------------------------------------
    # COMPARE
    # --------------------------------------------------

    print(
        "\n🔎 Comparing with previous timetable..."
    )

    changes = compare_timetables(
        previous,
        current
    )

    print_changes(changes)

    total_changes = sum(len(changes[kind]) for kind in ("added", "removed", "modified"))
    if total_changes:
        try:
            send_telegram_notification(changes)
        except (requests.RequestException, RuntimeError, ValueError) as error:
            print(f"\n❌ Telegram notification failed: {error}")
            print("Snapshot was not updated, so this change can be notified on the next run.")
            return

        print("\n✅ Telegram notification sent.")

    # --------------------------------------------------
    # UPDATE SNAPSHOT
    # --------------------------------------------------

    save_timetable(
        PREVIOUS_FILE,
        current
    )

    print(
        "\n✅ Snapshot updated."
    )


if __name__ == "__main__":
    main()
