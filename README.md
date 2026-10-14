# TRMNL Builds

Builds firmware from [TRMNL](https://github.com/usetrmnl/trmnl-firmware) releases
using GitHub Actions, with downloads and browser USB flashing on GitHub Pages.
Targets are discovered from each release's upstream configuration.

Original builds use unchanged upstream source. Targets with checked-in patches
also have a separate **Patched** variant and source archive. A patch that no
longer matches upstream fails only that variant.

[Open the Firmware Installer](https://maxexcloo.github.io/trmnl-builds/)

## Usage

Choose a release and your exact hardware target. Use a Web Serial browser, such as
desktop Chrome or Edge, and connect the device with a USB data cable.
Recent images can be flashed directly; older images can be downloaded and selected
in the installer, which verifies their checksum before flashing.

Actions checks hourly and builds only the newest stable release when it is missing.
To rebuild a release manually, use **Actions → Firmware → Run Workflow** and enter
its tag.
Downloads, source, checksums and build results are available in
[Releases](https://github.com/maxexcloo/trmnl-builds/releases).

Targets without a supported full-flash image offer downloads only. Full-flash
installation overwrites saved device settings, even without a separate erase step.
Use a compatible application-only OTA update to retain settings. A successful
build does not guarantee hardware compatibility.

## Development

Everything runs on GitHub. The site uses ESP Web Tools without a frontend build;
uv manages build dependencies. See [AGENTS.md](AGENTS.md) for project conventions
and checks.

## Licence

The automation and website are [AGPL-3.0](LICENSE).
Firmware and its dependencies retain their upstream licences.

## Dependency Updates

Mise installs the pinned Updatecli CLI. Run `mise run dependencies:check` locally
to preview updates from `.updatecli.d/`. GitHub authentication uses the existing
`gh` login; credentials stay in the command process.

Review compatibility and major upgrades separately, then apply a selected group:

```sh
mise run dependencies:update --labels group:tools
```

Use the groups declared in the policy, review the Git diff and run the project
checks before committing or deploying. Updatecli changes local files; it does
not create issues, pull requests, commits or deployments. Hosted Renovate is disabled.
