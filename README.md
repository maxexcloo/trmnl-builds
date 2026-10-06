# TRMNL builds

Build upstream [TRMNL firmware](https://github.com/usetrmnl/trmnl-firmware) release
tags for every discovered device environment. Browse tags, targets, downloads and
build failures on GitHub Pages, and flash devices over USB using ESP Web Tools.

Native GitHub Actions, one Python standard-library helper, one HTML page.
Runs entirely on GitHub. No local installation, server, frontend build, database,
PAT or additional cloud account. ESP Web Tools is loaded from its versioned CDN.

## Setup

1. Open **Actions → Firmware → Run workflow**, leaving the tag blank.
2. Visit https://maxexcloo.github.io/trmnl-builds/ after the build completes.

Pages is configured to deploy through GitHub Actions. Edit project files directly
on GitHub; validation runs on pushes and pull requests.

The first run builds the latest published stable upstream release. The hourly
schedule then builds one missing release per run, in publication order, from the
earliest release already built. It catches releases published between polls.
Enter a published stable tag to backfill or rebuild it; prereleases and bare Git
tags without a published release are intentionally excluded. Backfilling an older
tag also extends the automatic catch-up window to that release.

GitHub cannot deliver another repository's release event directly to this one.
Polling avoids a webhook service or upstream changes. Scheduled runs can be delayed;
GitHub disables schedules in public repositories after 60 days without repository
activity. Re-enable the workflow when GitHub notifies you. For guaranteed immediate
builds, upstream cooperation or an external trigger would be needed.

## Builds

M5Stack Paper S3 (`TRMNL_X_PAPERS3`) is prioritised in the build matrix and selected
by default in the installer when present in the selected release.

- Resolve each tag to a commit and use that commit for every target.
- Use PlatformIO's resolved configuration, including inherited options. Select
  environments with a board and a `BOARD_*` or `DEVICE_MODEL` build flag, excluding
  integration test environments. This currently includes development variants;
  their upstream debug settings are preserved. Review discovery if upstream changes
  its conventions.
- Run each target in a clean Ubuntu job, with at most eight concurrent builds.
- Preserve upstream build scripts and dependency pins. Publish `firmware.bin` as
  `TARGET-application.bin` and, where upstream generates it, `merged_firmware.bin`
  as `TARGET-full-flash.bin`. Never invent flash offsets or merged images.
- Publish successes alongside a manifest recording every target's result, source
  commit, checksums and workflow URL. Failed targets do not prevent other downloads.
  They remain failed jobs in Actions. Rebuild the tag manually to retry; this replaces
  its release assets. Failures before publication are retried by later polls.
- Attach the upstream source checkout, including submodules, to each release.
  Firmware and its source retain upstream GPL-3.0 licensing. Dependency licences
  remain with their respective authors; dependency sources follow upstream's pins.

The Pages workflow generates `catalogue.json` from release manifests and asset
URLs. Visitors use static files without calling the GitHub API. All binaries stay
in GitHub Releases. Recent full-flash images are also copied to Pages, with a
750 MiB budget, for one-click USB flashing without cross-origin download issues.
Older releases offer download-then-select-file flashing in the same browser UI;
the file stays in the browser and its SHA-256 must match the selected target/tag.
The generated catalogue always lists all built releases and their targets.

ESP Web Tools handles USB, chip detection and installation. Manifests are generated
in the browser from build metadata. Chip families come from the merged ESP image
header, not a manually maintained target list. Targets without a recognised merged
image remain download-only. The upstream merged images start at flash offset zero;
no offsets or merges are guessed for other targets. The user chooses the precise
board because chip detection alone cannot identify its display or wiring. Rebuilding Pages is also available
as a manual workflow. Source checkout tokens are read-only; publishing is a separate
job with write permission.

Building successfully does not establish hardware compatibility. Match the exact
target and use upstream flashing instructions. Application binaries are not
complete flash images. Some upstream targets may fail or require additional setup;
this project reports those failures without maintaining firmware patches.

## Checks

Checks run in GitHub Actions; local commands below are optional for contributors.

```sh
python3 -m unittest discover -s tests
# With actionlint installed:
actionlint .github/workflows/*.yaml
```

To inspect discovery against an upstream checkout:

```sh
export INCLUDE_GIT_HASH_IN_VERSION_NUMBER=false
pio project config --project-dir /path/to/trmnl-firmware --json-output > /tmp/trmnl-config.json
GITHUB_OUTPUT=/tmp/trmnl-targets.txt python3 scripts/firmware.py discover /tmp/trmnl-config.json
cat /tmp/trmnl-targets.txt
```

After generating `site/catalogue.json` in Actions, the site is ordinary static HTML.
The orchestration and website in this repository are AGPL-3.0; firmware is GPL-3.0.
