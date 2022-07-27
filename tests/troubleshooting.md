# Troubleshooting

## Webdriver

If you're seeing errors like

```sh
ERROR    dash.testing.browser:browser.py:433 <<<Webdriver not initialized correctly>>>
```

or

```sh
E   selenium.common.exceptions.WebDriverException: Message: unknown error: cannot find Chrome binary
```

try manually installing `chromedriver` and/or `google-chrome`. On macOS, this can be done with `brew`:

```sh
brew install --cask chromedriver
brew install --cask google-chrome
```

macOs may complain that it cannot verify the security of these executables in which case you can manually override and give permission in 'System Preferences > Security & Privacy'.
