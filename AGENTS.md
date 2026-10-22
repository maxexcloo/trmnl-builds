# Project Rules

## Structure

- Discover targets from each upstream release; generate the catalogue from build
  results. Do not maintain target or release lists. Keep reviewed patches in
  `patches/<upstream-target>/*.patch`, applied in filename order, with the
  reason above the diff. Bump patch-embedded platforms by hand: newer
  pioarduino platforms need PlatformIO Core 6.2.0, which upstream's older
  platforms cannot use.
- Poll only the newest stable release; do not automatically backfill older releases.
  Rebuilds of older releases must not change the Latest release.
- Always build unchanged upstream targets. Discover separate patched variants
  from patch directories; failures must not block original builds. Publish the
  exact source archive for each variant. Do not fetch patches at build time.
- Keep firmware execution in read-only jobs and publishing in a separate job.
- Keep orchestration in `.github/workflows/` and `.github/scripts/firmware.py`.
- Keep the Pages app build-free in `site/index.html`, importing the pinned ESP
  Web Tools release from unpkg.
- Preserve upstream build flags, flash layouts and licences.

## Verification

- Use uv with the committed lockfile.
- Run `mise run check` for formatting, Python, workflow, Renovate
  configuration and JavaScript syntax checks, including the firmware tests.
