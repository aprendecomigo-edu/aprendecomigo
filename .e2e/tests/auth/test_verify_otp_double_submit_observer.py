import re
import time

from playwright.sync_api import Page, expect


def test_observe_verify_otp_requests(page: Page, base_url: str):
    """Navigate signin → request OTP → observe /verify-otp/ POST headers and responses.

    This test doesn't assert OTP verification success. It records any POST to
    /verify-otp/ and prints the request headers (including X-CSRFToken) and
    response status to help reproduce transient 403s observed in logs.
    """
    email = "anamartinsdecarvalho@protonmail.com"

    recorded = []

    def handle_request(request):
        if request.url.endswith("/verify-otp/") and request.method == "POST":
            headers = dict(request.headers)
            post = {"url": request.url, "headers": headers}
            recorded.append(("request", post))

    def handle_response(response):
        try:
            req = response.request
            if req.url.endswith("/verify-otp/") and req.method == "POST":
                recorded.append(
                    ("response", {"url": req.url, "status": response.status, "headers": dict(response.headers)})
                )
        except Exception:
            pass

    page.on("request", handle_request)
    page.on("response", handle_response)

    # Go to signin page
    page.goto(f"{base_url}/signin/")

    # Fill email
    email_input = page.locator('[placeholder="your_email@example.com"]')
    email_input.fill(email)
    page.wait_for_timeout(300)

    # Click send code via email (try data-test, fallback to button text)
    try:
        page.locator('[data-test="send-code-email"]').click()
    except Exception:
        page.get_by_role("button", name=re.compile("Send", re.I)).click()

    # Wait for the OTP form to show
    expect(page.locator('text="Code Sent!"')).to_be_visible(timeout=10000)

    # Small wait to ensure HTMX swap settled
    page.wait_for_timeout(500)

    # Fill OTP inputs quickly to trigger auto-submit
    otp_inputs = page.locator(".otp-input")
    expect(otp_inputs).to_have_count(6)

    # Enter a bogus code quickly to simulate user input
    for i in range(6):
        otp_inputs.nth(i).fill("1")

    # Wait a moment to allow the HTMX submit to fire
    page.wait_for_timeout(1000)

    # Print recorded requests/responses
    print("--- Recorded /verify-otp/ activity ---")
    for kind, info in recorded:
        print(kind, info)

    # Basic assertion: there should be at least one request recorded
    assert any(k == "request" for k, _ in recorded), "No /verify-otp/ POST observed"
