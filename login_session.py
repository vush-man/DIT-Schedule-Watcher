from playwright.sync_api import sync_playwright

PORTAL_URL = "https://diterp.dituniversity.edu.in/dit_inxt/default.aspx"
AUTH_FILE = "auth.json"

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)
    context = browser.new_context()    
    page = context.new_page()

    print("Opening portal...")

    page.goto(PORTAL_URL, wait_until="domcontentloaded")

    # Give the SSO redirect chain time to finish
    page.wait_for_timeout(5000)

    print("\nCurrent URL:")
    print(page.url)

    print("\nTitle:")
    print(page.title())

    print("\nPage text:")
    print(page.locator("body").inner_text()[:5000])

    input(
        "\nComplete the Outlook/Microsoft SSO login in the browser window "
        "(including MFA if prompted), then press Enter here once you can "
        "see the portal dashboard...\n"
    )

    context.storage_state(path=AUTH_FILE)
    print(f"\n✅ Session saved to {AUTH_FILE}")

    browser.close()