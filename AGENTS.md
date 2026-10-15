# Project Rules

## Structure

- Discover targets from each upstream release; generate the catalogue from build
  results. Do not maintain target or release lists. Keep reviewed patches in
  `patches/<upstream-target>/*.patch`, applied in filename order.
- Poll only the newest stable release; do not automatically backfill older releases.
- Always build unchanged upstream targets. Discover separate patched variants
  from patch directories; failures must not block original builds. Publish the
  exact source archive for each variant. Do not fetch patches at build time.
- Keep firmware execution in read-only jobs and publishing in a separate job.
- Keep orchestration in `.github/workflows/` and `.github/scripts/firmware.py`.
- Keep the Pages app build-free, using ESP Web Tools, in `site/index.html`.
- Preserve upstream build flags, flash layouts and licences.

## Style

- Prefer native GitHub Actions and maintained off-the-shelf actions over scripts
  where they cover the task. Keep custom code limited to project-specific behaviour;
  add dependencies only for a concrete need.
- Format HTML, CSS and JavaScript with Prettier defaults. Keep user-facing wording
  plain and direct; omit promotional phrases.

## Verification

- Use uv with the committed lockfile.
- Run `uv run --locked python -m unittest discover -s tests`.
- Run actionlint after workflow changes. GitHub Actions also checks JavaScript syntax.
