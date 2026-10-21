# TRMNL Builds

Builds firmware from [TRMNL](https://github.com/usetrmnl/trmnl-firmware) releases
with GitHub Actions, and offers downloads and browser USB flashing on GitHub
Pages. The build targets come from each release's upstream configuration.

Original builds use the upstream source as is. Targets with checked-in patches
also get a separate Patched variant and source archive. If a patch no longer
applies to upstream, only that variant fails.

[Open the Firmware Installer](https://maxexcloo.github.io/trmnl-builds/)

## Usage

Choose a release and your exact hardware target. Use a browser with Web Serial,
such as desktop Chrome or Edge, and connect the device with a USB data cable.
Recent images can be flashed directly. Older images can be downloaded and then
selected in the installer, which checks their checksum before flashing.

Actions checks every hour and only builds the newest stable release, and only if
it hasn't been built yet. To rebuild a release by hand, use **Actions → Firmware → Run
Workflow** and enter its tag. Downloads, source, checksums and build results are
in [Releases](https://github.com/maxexcloo/trmnl-builds/releases). Workflow runs on
branches other than `main` build without publishing.

Targets without a supported full-flash image only offer downloads. A full-flash
install overwrites saved device settings, even without a separate erase step. To
keep your settings, use a compatible application-only OTA update. A build that
succeeds isn't guaranteed to work on the hardware.

## Development

Install the [shared Mise configuration](https://github.com/maxexcloo/dotfiles#shared-tools--tasks)
before running local Mise tasks.

Firmware builds run on GitHub. The site uses ESP Web Tools with no frontend
build, and uv manages the build dependencies. To run the same configuration,
JavaScript and firmware planning checks as CI:

```sh
mise run check
```

See [AGENTS.md](AGENTS.md) for project conventions.

## Licence

The automation and website are [AGPL-3.0](LICENSE).
Firmware and its dependencies retain their upstream licences.
