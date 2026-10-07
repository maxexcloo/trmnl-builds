"""Discover upstream firmware, publish build results, and generate the Pages catalogue."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

PATCHES = Path(__file__).resolve().parents[2] / "patches"
UPSTREAM = "usetrmnl/trmnl-firmware"


def catalogue():
    repo = os.environ["GITHUB_REPOSITORY"]
    entries = []
    for release in releases(repo):
        asset = next(
            (asset for asset in release["assets"] if asset["name"] == "manifest.json"),
            None,
        )
        if not asset:
            continue
        manifest = json.loads(
            run("gh", "api", asset["url"], "-H", "Accept: application/octet-stream")
        )
        urls = {
            asset["name"]: asset["browser_download_url"] for asset in release["assets"]
        }
        manifest["targets"].sort(key=lambda result: result["target"])
        for result in manifest["targets"]:
            for item in result["files"]:
                item["url"] = urls[item["name"]]
        manifest["updated_at"] = asset["updated_at"]
        manifest["url"] = release["html_url"]
        entries.append(manifest)
    entries.sort(key=lambda entry: entry["published_at"], reverse=True)
    # Keep recent images under Pages' 1 GB limit; older images remain file-flashable.
    remaining = 750 * 1024 * 1024
    for entry in entries:
        for result in entry["targets"]:
            flash = result.get("flash")
            if not flash or flash["size"] > remaining:
                continue
            directory = Path("site/firmware") / entry["tag"]
            directory.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "gh",
                    "release",
                    "download",
                    entry["tag"],
                    "--repo",
                    repo,
                    "--pattern",
                    flash["file"],
                    "--dir",
                    str(directory),
                ],
                check=True,
            )
            binary = directory / flash["file"]
            item = next(
                item for item in result["files"] if item["name"] == flash["file"]
            )
            if hashlib.sha256(binary.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError(f"Checksum mismatch: {binary}")
            remaining -= binary.stat().st_size
            flash["path"] = str(binary.relative_to("site"))
    Path("site/catalogue.json").write_text(json.dumps(entries, indent=2) + "\n")


def discover(path):
    config = json.loads(path.read_text())
    targets = []
    skipped = []
    for section, pairs in config:
        if not section.startswith("env:"):
            continue
        name = section[4:]
        options = dict(pairs)
        flags = str(options.get("build_flags", ""))
        # Base environments have no device selection; tests replace the application.
        device = re.search(r"(?:BOARD_[A-Z0-9_]+|DEVICE_MODEL)(?:=|\b)", flags)
        if options.get("board") and device and not options.get("test_build_src"):
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
                raise ValueError(f"Unsupported target name: {name!r}")
            targets.append(name)
        else:
            skipped.append(name)
    if not targets:
        raise ValueError(
            "No firmware targets found; inspect the upstream configuration"
        )
    print("Excluded test/base environments:", ", ".join(sorted(skipped)))
    builds = []
    for target in sorted(targets):
        builds.append({"name": target, "patched": False, "target": target})
        if any((PATCHES / target).glob("*.patch")):
            builds.append(
                {"name": f"{target}-patched", "patched": True, "target": target}
            )
    names = [build["name"] for build in builds]
    if len(names) != len(set(names)):
        raise ValueError("Patched variant name conflicts with an upstream target")
    output("builds", json.dumps(builds, separators=(",", ":")))
    output("targets", json.dumps(names, separators=(",", ":")))


def manifest(tag, sha, targets):
    repo = os.environ["GITHUB_REPOSITORY"]
    results = []
    for target in json.loads(targets):
        path = Path("results") / target / "result.json"
        results.append(
            json.loads(path.read_text())
            if path.exists()
            else {"target": target, "status": "failure", "files": []}
        )
    upstream = json.loads(run("gh", "api", f"repos/{UPSTREAM}/releases/tags/{tag}"))
    manifest = {
        "commit": sha,
        "tag": tag,
        "targets": results,
        "published_at": upstream["published_at"],
        "run": f"https://github.com/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    }
    Path("manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    failed = [result["target"] for result in results if result["status"] != "success"]
    notes = (
        f"Community builds of [{UPSTREAM} {tag}](https://github.com/{UPSTREAM}/tree/{sha}).\n\n"
        f"Upstream commit: `{sha}`. [Build logs]({manifest['run']}).\n\n"
        "Firmware is GPL-3.0; the exact prepared source is attached, including any "
        "local adjustments for explicitly patched variants. Each patched variant has its own "
        "source archive. Application binaries are not full-flash images.\n\n"
        + (
            "Failed targets: " + ", ".join(failed)
            if failed
            else "All discovered targets built successfully."
        )
    )
    Path("release-notes.md").write_text(notes + "\n")
    if failed:
        print(
            f"::warning::{len(failed)} targets failed; see release manifest and build logs"
        )


def output(name, value):
    with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
        stream.write(f"{name}={value}\n")


def pack(target, outcome, name=None):
    name = name or target
    destination = Path("results") / name
    destination.mkdir(parents=True, exist_ok=True)
    files = []
    flash = None
    if outcome == "success":
        build = Path("upstream/.pio/build") / target
        if not (build / "firmware.bin").is_file():
            raise ValueError(f"Missing firmware.bin for {target}")
        for filename, kind in [
            ("firmware.bin", "application"),
            ("merged_firmware.bin", "full-flash"),
        ]:
            source = build / filename
            if source.is_file():
                filename = f"{name}-{kind}.bin"
                data = source.read_bytes()
                (destination / filename).write_bytes(data)
                files.append(
                    {"name": filename, "sha256": hashlib.sha256(data).hexdigest()}
                )
                # ESP image headers identify the chip, independent of target names.
                # Upstream merged images start with the bootloader at offset zero.
                if kind == "full-flash" and len(data) >= 24 and data[0] == 0xE9:
                    from esptool.targets import CHIP_DEFS

                    chip_id = int.from_bytes(data[12:14], "little")
                    chip = next(
                        (
                            definition.CHIP_NAME
                            for definition in CHIP_DEFS.values()
                            if getattr(definition, "IMAGE_CHIP_ID", None) == chip_id
                        ),
                        None,
                    )
                    if chip:
                        flash = {
                            "chipFamily": chip,
                            "file": filename,
                            "size": len(data),
                        }
    (destination / "result.json").write_text(
        json.dumps(
            {
                "environment": target,
                "patched": name != target,
                "status": outcome,
                "target": name,
                "files": files,
                "flash": flash,
            }
        )
    )


def plan(tag):
    upstream = [release for release in releases(UPSTREAM) if not release["prerelease"]]
    upstream.sort(key=lambda release: release["published_at"])
    published = {
        release["tag_name"] for release in releases(os.environ["GITHUB_REPOSITORY"])
    }
    if tag:
        matches = [release for release in upstream if release["tag_name"] == tag]
        if not matches:
            raise ValueError("Choose a published, stable upstream release tag")
        selected = matches[0]
    else:
        selected = upstream[-1] if upstream else None
        if selected and selected["tag_name"] in published:
            selected = None
    tag = selected["tag_name"] if selected else ""
    if tag and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", tag):
        raise ValueError(f"Unsupported release tag: {tag!r}")
    output("tag", tag)


def prepare(path, target):
    """Apply the target's checked-in patches in filename order."""
    patches = sorted((PATCHES / target).glob("*.patch"))
    if not patches:
        raise ValueError(f"No patches found for {target}")
    for patch_file in patches:
        command = ["git", "-C", str(path.resolve()), "apply"]
        patch_path = str(patch_file.resolve())
        reverse = subprocess.run(
            [*command, "--reverse", "--check", patch_path], capture_output=True
        )
        if reverse.returncode == 0:
            print(f"Already applied: {patch_file.name}")
            continue
        check = subprocess.run(
            [*command, "--check", patch_path], capture_output=True, text=True
        )
        if check.returncode:
            raise ValueError(
                f"Patch {patch_file.name} does not match upstream: {check.stderr.strip()}"
            )
        subprocess.run([*command, patch_path], check=True)
        print(f"Applied: {patch_file.name}")


def releases(repo):
    pages = json.loads(
        run("gh", "api", "--paginate", "--slurp", f"repos/{repo}/releases?per_page=100")
    )
    return [release for page in pages for release in page if not release["draft"]]


def run(*args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs).strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("catalogue")
    commands.add_parser("discover").add_argument("path", type=Path)
    commands.add_parser("plan").add_argument("tag", nargs="?", default="")
    prepare_command = commands.add_parser("prepare")
    prepare_command.add_argument("path", type=Path)
    prepare_command.add_argument("target")
    package = commands.add_parser("pack")
    package.add_argument("target")
    package.add_argument("outcome")
    package.add_argument("--name")
    release = commands.add_parser("manifest")
    release.add_argument("tag")
    release.add_argument("sha")
    release.add_argument("targets")
    args = vars(parser.parse_args())
    globals()[args.pop("command")](**args)
