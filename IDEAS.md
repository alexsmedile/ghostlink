# Ideas

## GitHub Actions

Add a small CI workflow that runs on pull requests and pushes to `main`:

- test against supported Python versions, starting with 3.9 and the latest stable release
- run `pytest -q`
- run `python -m compileall src`
- verify `ghostlink --version` matches the package manifest

Keep CI standard-library-focused and avoid adding release automation until the packaging and publishing workflow is defined.
