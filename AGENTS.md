# Project Rules

## Structure

- Discover targets from each upstream release; generate the catalogue from build
  results. Do not maintain target or release lists. The guarded Paper S3
  waveform adjustment is the only permitted upstream firmware patch; fail when
  its expected source changes and build from the published prepared source.
- Keep firmware execution in read-only jobs and publishing in a separate job.
- Keep orchestration in `.github/workflows/` and `.github/scripts/firmware.py`.
- Keep the Pages app build-free, using ESP Web Tools, in `site/index.html`.
- Keep the README focused on purpose and general usage. Keep only `AGENTS.md` and
  `README.md` as root Markdown files.
- Preserve upstream build flags, flash layouts and licences.

## Style

- Prefer native GitHub Actions and maintained off-the-shelf actions over scripts
  where they cover the task. Keep custom code limited to project-specific behaviour;
  add dependencies only for a concrete need.
- Sort unordered entries alphabetically, with simple values before structured
  values. Preserve procedural, interface and priority order.
- Format HTML, CSS and JavaScript with Prettier defaults. Keep user-facing wording
  plain and direct; omit promotional phrases.
- Use Australian English and `.yaml` for project-owned YAML files.
- Use Title Case for headings, labels and Actions workflow, job and step names,
  with `&` instead of `And`. Keep prose in sentence case and preserve upstream names.

## Verification

- Use uv with the committed lockfile.
- Run `uv run --locked python -m unittest discover -s tests`.
- Run actionlint after workflow changes. GitHub Actions also checks JavaScript syntax.
