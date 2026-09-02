from playwright.sync_api import sync_playwright
import json

PORTAL_URL = "https://diterp.dituniversity.edu.in/dit_inxt/default.aspx"
AUTH_FILE = "auth.json"


def timetable_to_json(rows):
    timetable_data = []

    for i in range(rows.count()):

        cells = rows.nth(i).locator("td")

        # Ignore empty/header rows
        if cells.count() < 12:
            continue

        row = {
            "batch": cells.nth(0).inner_text().strip(),
            "course_code": cells.nth(1).inner_text().strip(),
            "subject": cells.nth(2).inner_text().strip(),
            "course_type": cells.nth(3).inner_text().strip(),
            "credits": cells.nth(4).inner_text().strip(),
            "class_type": cells.nth(5).inner_text().strip(),
            "day": cells.nth(6).inner_text().strip(),
            "time": cells.nth(7).inner_text().strip(),
            "room": cells.nth(8).inner_text().strip(),
            "course_instructor": cells.nth(9).inner_text().strip(),
            "course_coordinator": cells.nth(10).inner_text().strip(),
            "department": cells.nth(11).inner_text().strip()
        }

        timetable_data.append(row)

    return timetable_data

def scrape_timetable():
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_FILE)

        try:
            page = context.new_page()

            # --------------------------------------------------
            # LOGIN
            # --------------------------------------------------

            print("Opening portal...")

            page.goto(
                PORTAL_URL,
                wait_until="commit",
                timeout=60000
            )

            # Check whether we're already authenticated
            if "ditnexus.aspx" not in page.url:

                print("Login required...")

                login_button = page.locator("#Default_BtnOutlook")

                login_button.wait_for(
                    state="visible",
                    timeout=30000
                )

                print("Clicking Login...")

                login_button.click()

                print("Waiting for Microsoft SSO...")

                page.wait_for_url(
                    "**/dit_inxt/ditnexus.aspx**",
                    timeout=60000
                )

            print("✅ Dashboard reached")

            # --------------------------------------------------
            # OPEN ACADEMICS
            # --------------------------------------------------

            print("Opening Academics menu...")

            academics = page.locator(
                "span.menu-label",
                has_text="Academics"
            ).first

            academics.wait_for(
                state="visible",
                timeout=30000
            )

            academics.click()

            print("✅ Academics menu opened")

            # --------------------------------------------------
            # OPEN ACADEMIC ACTIVITIES
            # --------------------------------------------------

            print("Opening Academic Activities...")

            academic_menu = page.locator(
                'li.has-submenu'
            ).filter(
                has_text="Academic Activities"
            ).last

            academic_menu.wait_for(
                state="attached",
                timeout=30000
            )

            print("Academic Activities found")

            academic_menu.evaluate(
                "(el) => el.click()"
            )

            print("✅ Academic Activities opened")

            # --------------------------------------------------
            # OPEN TIME TABLE
            # --------------------------------------------------

            print("Opening Time Table...")

            timetable_menu = page.locator(
                'li[data-page="time table"]'
            )

            timetable_menu.wait_for(
                state="visible",
                timeout=30000
            )

            timetable_menu.click()

            print("✅ Time Table opened")

            # --------------------------------------------------
            # GET TIMETABLE IFRAME
            # --------------------------------------------------

            print("Looking for timetable iframe...")

            iframe = page.locator(
                'iframe[src*="ShowTimeTable.aspx"]'
            )

            iframe.wait_for(
                state="attached",
                timeout=30000
            )

            print("✅ Timetable iframe found")

            # Get iframe's content
            frame = iframe.content_frame

            if frame is None:
                print("❌ Could not access timetable frame")
                context.close()
                browser.close()
                exit()

            print("✅ Connected to timetable frame")

            # --------------------------------------------------
            # FIND TABLE
            # --------------------------------------------------

            table = frame.locator(
                "table.table-hover"
            )

            table.wait_for(
                state="visible",
                timeout=30000
            )

            print("✅ Timetable table found")

            rows = table.locator(
                "tbody tr"
            )

            print(
                f"\nFound {rows.count()} rows"
            )

            # --------------------------------------------------
            # CONVERT TO JSON
            # --------------------------------------------------

            timetable_data = timetable_to_json(rows)

            print(f"Scraped {len(timetable_data)} timetable entries")

            return timetable_data

        finally:
            context.close()
            browser.close()
            print("Browser closed")

if __name__ == "__main__":
    timetable = scrape_timetable()

    with open("timetable.json", "w", encoding="utf-8") as f:
        json.dump(
            timetable,
            f,
            indent=4,
            ensure_ascii=False
        )
        print("✅ Timetable saved to timetable.json")
