# Project Rules

## Structure

- Discover targets from each upstream release; generate the catalogue from build
  results. Do not maintain target or release lists or patch upstream firmware.
- Keep firmware execution in read-only jobs and publishing in a separate job.
- Keep orchestration in `.github/workflows/` and `scripts/firmware.py`.
- Keep the Pages app build-free, using ESP Web Tools, in `site/index.html`.
- Keep the README focused on purpose and general usage. Keep only `AGENTS.md` and
  `README.md` as root Markdown files.
- Preserve upstream build flags, flash layouts and licences.

## Style

- Prefer direct code and standard tools; add dependencies only for a concrete need.
- Sort unordered entries alphabetically, with simple values before structured
  values. Preserve procedural, interface and priority order.
- Use Australian English and `.yaml` for project-owned YAML files.
- Use Title Case for headings and labels, with `&` instead of `And`. Keep prose in
  sentence case and preserve upstream names.

## Verification

- Use uv with the committed lockfile.
- Run `uv run --locked python -m unittest discover -s tests`.
- Run actionlint after workflow changes. GitHub Actions also checks JavaScript syntax.
