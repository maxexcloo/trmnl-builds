# TRMNL Builds

Builds firmware from [TRMNL](https://github.com/usetrmnl/trmnl-firmware) releases
using GitHub Actions, with downloads and browser USB flashing on GitHub Pages.
Targets are discovered from each release's upstream configuration.

[Open the Firmware Installer](https://maxexcloo.github.io/trmnl-builds/)

## Usage

Choose a release and your exact hardware target. Use a Web Serial browser, such as
desktop Chrome or Edge, and connect the device with a USB data cable.
Recent images can be flashed directly; older images can be downloaded and selected
in the installer, which verifies their checksum before flashing.

Actions checks hourly for new stable releases. To rebuild or backfill a release,
use **Actions → Firmware → Run Workflow** and enter its tag.
Downloads, source, checksums and build results are available in
[Releases](https://github.com/maxexcloo/trmnl-builds/releases).

Targets without a supported full-flash image offer downloads only. Installing may
erase device settings; a successful build does not guarantee hardware compatibility.

## Development

Everything runs on GitHub. The site uses ESP Web Tools without a frontend build;
uv manages build dependencies. See [AGENTS.md](AGENTS.md) for project conventions
and checks.

## Licence

The automation and website are [AGPL-3.0](LICENSE).
Firmware and its dependencies retain their upstream licences.
