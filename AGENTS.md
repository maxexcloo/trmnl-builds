# AGENTS.md

## Structure

- Build only the owner's devices, listed in `TARGETS` in
  `.github/scripts/firmware.py`; generate the catalogue from build results. Do
  not maintain release lists. Keep reviewed patches in
  `patches/<upstream-target>/*.patch`, applied in filename order, with the
  reason above the diff.
- Poll only the newest stable release; do not automatically backfill older releases.
  Rebuilds of older releases must not change the Latest release.
- Always build listed targets unchanged. Discover separate patched variants
  from patch directories; failures must not block original builds. Publish the
  exact source archive for each variant. Do not fetch patches at build time.
- Keep firmware execution in read-only jobs and publishing in a separate job.
- Keep the Pages app build-free in `site/index.html`, importing the pinned ESP
  Web Tools release from unpkg.
- Preserve upstream build flags, flash layouts and licences.

## Verification

- Run `mise run check`.
