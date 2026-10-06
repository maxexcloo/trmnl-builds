# Project rules

- Keep orchestration in `.github/workflows/` and `scripts/firmware.py`.
- Keep the Pages app build-free, using ESP Web Tools, in `site/index.html`; generate its catalogue.
- Discover targets from each upstream tag. Do not maintain a hardware list or patch
  upstream firmware here. Preserve upstream build flags and flash layouts.
- Keep firmware execution in read-only jobs and publishing in a separate job.
- Use Australian English and `.yaml` for project-owned YAML files.
- Run `python3 -m unittest discover -s tests` and actionlint after workflow changes.
- Preserve licences. Keep only README.md and AGENTS.md as root Markdown files.
