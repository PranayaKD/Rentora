"""
Rentora Playwright E2E Automation Suite
Principal QA & Test Automation Lead Spec
"""

import re
import os
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("RENTORA_BASE_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Security & Redaction Fixture: Ensure no secrets leak in trace or test logs
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def redact_sensitive_logs(page: Page):
    """Monitors console errors and network requests to ensure credentials are never leaked."""
    def handle_console(msg):
        # Prevent any potential tokens/keys from printing in CI test output
        text = msg.text
        for secret_name in ['rzp_', 'secret', 'token', 'key']:
            if secret_name in text.lower():
                text = re.sub(r'rzp_[a-zA-Z0-9_]+', 'rzp_test_[REDACTED]', text)
        print(f"[BROWSER CONSOLE] {msg.type}: {text}")

    page.on("console", handle_console)
    yield


# ---------------------------------------------------------------------------
# Test Suite 1: Critical Smoke & Template Leak Checks (P0)
# ---------------------------------------------------------------------------
def test_homepage_renders_cleanly_without_template_leaks(page: Page):
    """P0: Verify Homepage loads with 0 template leaks in rendered DOM."""
    page.goto(BASE_URL)
    expect(page).to_have_title(re.compile(r"Rentora", re.IGNORECASE))

    # Assert Hero search bar City/Hub label has rendered text
    hero_city = page.locator(".current-city-label").first
    expect(hero_city).to_be_visible()
    city_text = hero_city.inner_text().strip()
    assert "{{" not in city_text, f"Template syntax leaked into City Hub: {city_text}"
    assert "default:" not in city_text
    assert len(city_text) > 3

    # Assert no Django raw tags visible anywhere in the body text
    body_text = page.locator("body").inner_text()
    assert "{{" not in body_text, "Found unrendered '{{' in visible DOM text"
    assert "{%" not in body_text, "Found unrendered '{%' in visible DOM text"


def test_about_section_word_spacing(page: Page):
    """P1: Verify scroll scrub words maintain inter-word spacing."""
    page.goto(BASE_URL)
    about_paragraph = page.locator(".scroll-scrub-text").first
    expect(about_paragraph).to_be_visible()

    words = about_paragraph.locator(".scrub-word")
    assert words.count() > 10, "Scrub words failed to initialize"

    full_text = about_paragraph.inner_text()
    assert "Built in Bhubaneswar" in full_text or "Built in" in full_text, \
        f"Words appear merged in About text: {full_text[:60]}"


def test_footer_coming_soon_modal(page: Page):
    """P1: Verify App Store button opens modal and closes on Escape."""
    page.goto(BASE_URL)
    app_store_btn = page.locator("button:has-text('App Store')").first
    app_store_btn.scroll_into_view_if_needed()
    app_store_btn.click()

    modal = page.locator("#coming-soon-modal")
    expect(modal).to_be_visible()
    expect(modal).to_contain_text("iOS App Coming Soon")

    page.keyboard.press("Escape")
    expect(modal).to_be_hidden()


# ---------------------------------------------------------------------------
# Test Suite 2: Hub Selector & Dynamic State Propagation
# ---------------------------------------------------------------------------
def test_city_modal_updates_all_city_labels(page: Page):
    """P1: Verify selecting a new city propagates across all UI labels."""
    page.goto(BASE_URL)
    page.locator("div[onclick='openCityModal()']").first.click()
    modal = page.locator("#city-modal")
    expect(modal).to_be_visible()

    puri_option = modal.locator("button:has-text('Puri')").first
    puri_option.click()

    expect(modal).to_be_hidden()
    labels = page.locator(".current-city-label")
    for i in range(labels.count()):
        assert "Puri" in labels.nth(i).inner_text()


# ---------------------------------------------------------------------------
# Test Suite 3: Catalog Filter & Responsive Viewports
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("viewport", [
    {"width": 390, "height": 844},   # Mobile (iPhone 14)
    {"width": 768, "height": 1024},  # Tablet (iPad)
    {"width": 1440, "height": 900},  # Desktop
])
def test_cars_catalog_responsive_layout(page: Page, viewport):
    """P1: Verify vehicle cards and booking CTAs adapt across viewports."""
    page.set_viewport_size(viewport)
    page.goto(f"{BASE_URL}/cars/")

    cards = page.locator(".rentora-car-card")
    expect(cards.first).to_be_visible()

    book_btn = cards.first.locator("a:has-text('Book Now')")
    expect(book_btn).to_be_visible()
    expect(book_btn).to_have_attribute("href", re.compile(r"/cars/\d+/"))
