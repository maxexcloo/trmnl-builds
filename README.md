# TRMNL Builds

Builds firmware from [TRMNL](https://github.com/usetrmnl/trmnl-firmware) releases,
with optional patched variants, and offers downloads and browser USB flashing.

[Open the Firmware Installer](https://maxexcloo.github.io/trmnl-builds/)

## Usage

Choose a release and your exact hardware target. Use a browser with Web Serial,
such as desktop Chrome or Edge, and connect the device with a USB data cable. A
full-flash install overwrites saved device settings; use a compatible
application-only OTA update to keep them. Downloads and checksums are in
[Releases](https://github.com/maxexcloo/trmnl-builds/releases).

To rebuild a release, use **Actions → Firmware → Run Workflow** and enter its tag.

## Development

Install the [shared Mise configuration](https://github.com/maxexcloo/dotfiles#shared-tools--tasks)
before running local Mise tasks.

To run the same checks as CI:

```sh
mise run check
```

## Licence

The automation and website are [AGPL-3.0](LICENSE).
Firmware and its dependencies retain their upstream licences.
