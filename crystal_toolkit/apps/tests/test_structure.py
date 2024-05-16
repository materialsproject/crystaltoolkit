import re
import threading

from playwright.sync_api import Page, expect


def test_structure(page: Page):
    from crystal_toolkit.apps.examples.structure import app

    thread = threading.Thread(target=app.run)
    thread.start()

    expect(page).to_have_title("Crystal Toolkit")
    h1_text = page.text_content("h1")
    assert h1_text == "StructureMoleculeComponent Example"

    # repeatedly drag the canvas to test rotating the structure
    canvas = page.locator("canvas")
    canvas.drag_to(target=canvas, source_position={"x": 100, "y": 20})
    canvas.drag_to(target=canvas, source_position={"x": 0, "y": 70})

    # test enter and exit "Full screen"
    full_screen_button = page.query_selector('button[data-for^="expand-"]')
    assert full_screen_button.is_visible()
    page.locator("button").filter(has_text="Full screen").click()
    page.locator("button").filter(has_text="Exit full screen").click()

    # Check if "Show settings" button exists and is visible
    settings_button = page.query_selector('button[data-for^="settings-"]')
    assert settings_button.is_visible()

    # test "export structure as image" button
    image_button = page.query_selector('div[data-for^="image-"] button')
    image_button.click()
    with page.expect_download() as download:
        page.get_by_text("Screenshot (PNG)").click()
    assert download.value.url.startswith("blob:http://")

    # test "export structure as file" button
    position_button = page.query_selector("div[data-for^='export-'] button")
    position_button.click()
    with page.expect_download() as download:
        page.get_by_text("CIF (Symmetrized)").click()

    assert re.match("<Download url='blob:http://", str(download.value))

    legend = page.get_by_text("NaK", exact=True)
    assert legend.is_visible()

    position_button.click()
    with page.expect_download() as download:
        page.get_by_text("JSON").click()
    assert re.match(
        "<Download url='blob:http://127.0.0.1:8050/[a-z0-9-]+' suggested_filename='KNa.json'>",
        str(download.value),
    )
