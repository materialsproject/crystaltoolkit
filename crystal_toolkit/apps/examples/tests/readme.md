# End-to-end Testing

The tests for this code are constructed as small example apps. Running a test might involve simply verifying the app starts
correctly, checking console log output does not have errors, simulating user interaction, and taking screenshots of the
app state to ensure that the app looks as expected.

Ideally, each individual component should have at least one example app. The example apps are also used to demonstrate
correct usage of these components.

## Dependencies

The tests in this folder need the dependencies specified in `tests/requirements.txt`, in particular `dash[testing]` and `selenium`.

## Troubleshooting

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

macOS may complain that it cannot verify the security of these executables in which case you can manually override and give permission in 'System Preferences > Security & Privacy'.
