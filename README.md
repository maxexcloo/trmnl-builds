# TRMNL builds

[Open the USB installer](https://maxexcloo.github.io/trmnl-builds/).
M5Stack Paper S3 (`TRMNL_X_PAPERS3`) is prioritised and selected by default.

Builds [upstream TRMNL](https://github.com/usetrmnl/trmnl-firmware) release tags
entirely on GitHub. No local setup, backend, frontend build or personal access token.

## Operation

- Actions checks hourly for published stable releases. The first run starts with
  the latest; later runs catch missing releases in publication order.
- **Actions → Firmware → Run workflow** accepts a tag to rebuild or backfill.
  Backfilling extends the automatic catch-up window to that older release.
- Targets come from each tag's resolved PlatformIO configuration. Base and test
  environments are excluded; development variants retain their upstream settings.
- Each target builds in an isolated job. Failures remain visible without blocking
  successful downloads. Firmware source and flash layouts are unchanged.
- Releases contain binaries, upstream source including submodules, checksums,
  per-target results and the exact upstream commit.
- Pages lists every built release. Recent full-flash images use one-click USB
  installation; older images use download-then-select-file installation with a
  checksum check. A 750 MiB image budget keeps Pages below its 1 GB limit.

Use a Web Serial browser such as desktop Chrome or Edge. Select the precise board:
chip detection cannot distinguish boards sharing a chip. Targets without a supported
upstream merged image are download-only. Builds are not hardware certification.

Upstream release events cannot directly trigger this repository, so it polls.
GitHub may delay schedules and disables them after 60 days of repository inactivity;
re-enable the workflow when notified. Prereleases and unpublished Git tags are excluded.

## Implementation

- `astral-sh/setup-uv` manages Python, environments and dependency caching.
  `pyproject.toml` and `uv.lock` define the build tools.
- `softprops/action-gh-release` creates releases and uploads their assets.
- Official GitHub Actions handle checkout, build artefacts and Pages deployment.
- ESP Web Tools handles USB communication and flashing.
- `scripts/firmware.py` supplies the project-specific discovery, checksums and
  catalogue metadata. `site/index.html` supplies selection and file verification.
- Dependabot maintains Actions and uv dependencies with monthly grouped PRs.

## Checks

GitHub Actions runs behavioural tests, JavaScript syntax checks and actionlint.
Optional contributor commands:

```sh
uv run --locked python -m unittest discover -s tests
actionlint .github/workflows/*.yaml
```

The automation and website are AGPL-3.0. Firmware retains upstream GPL-3.0;
dependencies retain their own licences.
