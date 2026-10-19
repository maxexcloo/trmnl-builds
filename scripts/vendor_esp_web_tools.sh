#!/bin/sh
# Replaces site/vendor/esp-web-tools with the browser build of the pinned release.
set -eu
# renovate: datasource=npm depName=esp-web-tools
version=10.4.0
directory=site/vendor/esp-web-tools
download=$(mktemp -d)
trap 'rm -rf -- "$download"' EXIT
npm pack --silent --pack-destination "$download" "esp-web-tools@$version" >/dev/null
tar -xzf "$download"/*.tgz -C "$download"
rm -rf "$directory"
mkdir -p "$directory"
cp "$download"/package/LICENSE "$download"/package/package.json "$download"/package/dist/web/*.js "$directory"
