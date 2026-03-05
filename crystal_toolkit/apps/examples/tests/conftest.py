from selenium.webdriver.chrome.options import Options


def pytest_setup_options():
    options = Options()

    options.add_argument("--use-angle=swiftshader")
    options.add_argument("--enable-webgl")

    return options
