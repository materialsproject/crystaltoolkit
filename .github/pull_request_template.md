<!--

All previous Crystal Toolkit contributors/co-authors are encouraged to merge their own PRs once CI passes.
Crystal Toolkit is a community project, and merging your own PRs is encouraged to help
maintain the overall health of the code. If you do not have the required permissions to merge
your PR, contact @mkhorton or another repository admin.

If you have concerns about your PR, or if it has expansive changes, please request review
from @mkhorton or another active contributor.

If you are a new contributor, your PR will be fully reviewed before merging by a previous
contributor/co-author.

-->

## Checklist

Work-in-progress pull requests are encouraged but please [mark your PR as draft](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/changing-the-stage-of-a-pull-request#converting-a-pull-request-to-a-draft).

Usually, the following items should be checked before merging a PR:

- [ ] Doc strings have been added in the [Google docstring format](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- [ ] Type annotations are *highly* encouraged. Run [`mypy path/to/file.py`](https://github.com/python/mypy) to type-check your code. Type checks are run in CI.
- [ ] Tests for any new functionality as well as bug fixes, where appropriate.
- [ ] Create a new [Issue](https://github.com/materialsproject/crystaltoolkit/issues) for any TODO items that will result from merging the PR.

We recommended installing [`pre-commit`](https://pre-commit.com) to run all our linters locally. That will increase your development speed since you don't have to wait for our CI to tell about errors, your code will be checked at commit time.

```sh
pip install -U pre-commit
pre-commit install
```
