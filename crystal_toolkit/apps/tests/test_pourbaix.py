import threading

from playwright.sync_api import Page

from crystal_toolkit.apps.examples.pourbaix import app


def test_pourbaix(page: Page):
    thread = threading.Thread(target=app.run)
    thread.start()

    # select 1st structure
    page.locator(".react-select__input-container").click()
    page.get_by_text("Fe₃H (mp-1184287-GGA)", exact=True).click()

    # click toggle switches
    page.locator("div.mpc-switch").nth(0).click()  # click on "Filter Solids"
    page.locator("div.mpc-switch").nth(1).click()  # click on "Show Heatmap"

    # select 2nd structure
    page.locator(".react-select__input-container").click()
    page.get_by_text("CoH (mp-1206874-GGA)", exact=True).click()
