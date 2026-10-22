import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

spec = importlib.util.spec_from_file_location(
    "firmware", Path(__file__).parents[1] / ".github/scripts/firmware.py"
)
firmware = importlib.util.module_from_spec(spec)
spec.loader.exec_module(firmware)


class FirmwareTests(unittest.TestCase):
    def test_discovery_excludes_tests_and_bases_but_keeps_devices(self):
        config = [
            ["env:base", [["board", "esp32"]]],
            ["env:native", [["platform", "native"]]],
            ["env:hardware", [["board", "esp32"], ["build_flags", ["-DBOARD_TRMNL"]]]],
            [
                "env:model",
                [["board", "esp32"], ["build_flags", ['-D DEVICE_MODEL="test"']]],
            ],
            [
                "env:test",
                [
                    ["board", "esp32"],
                    ["build_flags", ["-DBOARD_TRMNL"]],
                    ["test_build_src", True],
                ],
            ],
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(config))
            with (
                patch.object(firmware, "output") as output,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                firmware.discover(path)
            self.assertEqual(
                json.loads(output.call_args.args[1]), ["hardware", "model"]
            )

    def test_discovery_adds_only_targets_with_patches(self):
        config = [
            ["env:beta", [["board", "esp32"], ["build_flags", ["-DBOARD_BETA"]]]],
            ["env:alpha", [["board", "esp32"], ["build_flags", ["-DBOARD_ALPHA"]]]],
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "alpha").mkdir()
            (root / "alpha/0001-fix.patch").touch()
            path = root / "config.json"
            path.write_text(json.dumps(config))
            with (
                patch.object(firmware, "PATCHES", root),
                patch.object(firmware, "output") as output,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                firmware.discover(path)
            values = {
                call.args[0]: json.loads(call.args[1]) for call in output.call_args_list
            }
            self.assertEqual(values["targets"], ["alpha", "alpha-patched", "beta"])
            self.assertEqual(
                values["builds"],
                [
                    {"name": "alpha", "patched": False, "target": "alpha"},
                    {"name": "alpha-patched", "patched": True, "target": "alpha"},
                    {"name": "beta", "patched": False, "target": "beta"},
                ],
            )

    def test_pack_keeps_original_and_patched_variants_separate(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            build = Path("upstream/.pio/build/hardware")
            build.mkdir(parents=True)
            (build / "firmware.bin").write_bytes(b"original")
            firmware.pack("hardware", "success", "hardware")
            (build / "firmware.bin").write_bytes(b"patched")
            firmware.pack("hardware", "success", "hardware-patched")
            self.assertEqual(
                Path("results/hardware/hardware-application.bin").read_bytes(),
                b"original",
            )
            self.assertEqual(
                Path(
                    "results/hardware-patched/hardware-patched-application.bin"
                ).read_bytes(),
                b"patched",
            )
            result = json.loads(
                Path("results/hardware-patched/result.json").read_text()
            )
            self.assertEqual(result["environment"], "hardware")
            self.assertTrue(result["patched"])
            self.assertEqual(result["target"], "hardware-patched")

    def test_plan_selects_release_and_latest_marker(self):
        upstream = [
            {"prerelease": False, "published_at": f"2026-10-0{i}", "tag_name": f"v{i}"}
            for i in range(1, 5)
        ]
        for tag, owned, expected, latest in [
            ("", [], "v4", "true"),
            ("", [{"tag_name": "v1"}], "v4", "true"),
            ("", [{"tag_name": "v4"}], "", "false"),
            ("v2", [{"tag_name": "v4"}], "v2", "false"),
            ("v4", [{"tag_name": "v4"}], "v4", "true"),
        ]:
            with (
                self.subTest(tag=tag, owned=owned),
                patch.dict(os.environ, GITHUB_REPOSITORY="owner/builds"),
                patch.object(firmware, "releases", side_effect=[upstream, owned]),
                patch.object(firmware, "output") as output,
            ):
                firmware.plan(tag)
                self.assertEqual(
                    output.call_args_list,
                    [
                        call("latest", latest),
                        call("repository", firmware.UPSTREAM),
                        call("tag", expected),
                    ],
                )

    def test_catalogue_skips_missing_release_assets(self):
        manifest = {
            "published_at": "2026-10-01",
            "tag": "v1",
            "targets": [
                {
                    "files": [
                        {"name": "a-application.bin"},
                        {"name": "a-full-flash.bin"},
                    ],
                    "flash": {"file": "a-full-flash.bin"},
                    "target": "a",
                }
            ],
        }
        release = {
            "assets": [
                {
                    "browser_download_url": "https://example.com/" + name,
                    "name": name,
                    "updated_at": "2026-10-02",
                    "url": "api/" + name,
                }
                for name in ("a-application.bin", "manifest.json")
            ],
            "html_url": "https://example.com/v1",
            "tag_name": "v1",
        }
        with (
            tempfile.TemporaryDirectory() as directory,
            contextlib.chdir(directory),
            contextlib.redirect_stdout(io.StringIO()) as stdout,
            patch.dict(os.environ, GITHUB_REPOSITORY="owner/builds"),
            patch.object(firmware, "releases", return_value=[release]),
            patch.object(firmware, "run", return_value=json.dumps(manifest)),
        ):
            Path("site").mkdir()
            firmware.catalogue()
            result = json.loads(Path("site/catalogue.json").read_text())[0]["targets"][
                0
            ]
        self.assertEqual(
            [item["name"] for item in result["files"]], ["a-application.bin"]
        )
        self.assertIsNone(result["flash"])
        self.assertIn("v1 is missing a-full-flash.bin", stdout.getvalue())

    def test_catalogue_keeps_older_images_downloadable_when_pages_budget_is_full(self):
        binary = b"small fixture"
        budget = 750 * 1024 * 1024
        newest, newest_release = self._downloadable_release("v2", binary)
        older, older_release = self._downloadable_release("v1", binary)
        newest["published_at"] = "2026-10-02"
        newest["targets"][0]["flash"]["size"] = budget

        with (
            tempfile.TemporaryDirectory() as directory,
            contextlib.chdir(directory),
            patch.dict(os.environ, GITHUB_REPOSITORY="owner/builds"),
            patch.object(
                firmware, "releases", return_value=[older_release, newest_release]
            ),
            patch.object(
                firmware, "run", side_effect=[json.dumps(older), json.dumps(newest)]
            ),
            patch.object(firmware.subprocess, "run") as download,
        ):
            Path("site").mkdir()
            firmware.catalogue()
            entries = json.loads(Path("site/catalogue.json").read_text())
            self.assertEqual([entry["tag"] for entry in entries], ["v2", "v1"])
            self.assertIn("path", entries[0]["targets"][0]["flash"])
            fallback = entries[1]["targets"][0]
            self.assertNotIn("path", fallback["flash"])
            self.assertEqual(
                fallback["files"][0]["url"], "https://example.com/v1/firmware.bin"
            )
            self.assertEqual(
                fallback["files"][0]["sha256"], hashlib.sha256(binary).hexdigest()
            )
            self.assertFalse(Path("site/firmware/v1").exists())
            download.assert_called_once()

    def _downloadable_release(self, tag, binary):
        name = "hardware-full-flash.bin"
        manifest = {
            "published_at": "2026-10-01",
            "tag": tag,
            "targets": [
                {
                    "target": "hardware",
                    "files": [
                        {"name": name, "sha256": hashlib.sha256(binary).hexdigest()}
                    ],
                    "flash": {"file": name, "size": len(binary), "chipFamily": "ESP32"},
                }
            ],
        }
        release = {
            "tag_name": tag,
            "html_url": f"https://example.com/{tag}",
            "assets": [
                {
                    "name": name,
                    "browser_download_url": f"https://example.com/{tag}/firmware.bin",
                },
                {
                    "name": "manifest.json",
                    "browser_download_url": f"https://example.com/{tag}/manifest.json",
                    "url": "api/manifest",
                    "updated_at": "2026-10-02",
                },
            ],
        }
        return manifest, release

    def test_full_flash_chip_comes_from_image_header(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            build = Path("upstream/.pio/build/hardware")
            build.mkdir(parents=True)
            (build / "firmware.bin").write_bytes(b"application")
            image = bytearray(24)
            image[0] = 0xE9
            image[12] = 9
            (build / "merged_firmware.bin").write_bytes(image)
            firmware.pack("hardware", "success", "hardware")
            result = json.loads(Path("results/hardware/result.json").read_text())
            self.assertEqual(result["flash"]["chipFamily"], "ESP32-S3")
            self.assertEqual(result["flash"]["file"], "hardware-full-flash.bin")

    def test_failure_never_packages_leftover_binaries(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            build = Path("upstream/.pio/build/hardware")
            build.mkdir(parents=True)
            (build / "firmware.bin").write_bytes(b"stale")
            firmware.pack("hardware", "failure", "hardware")
            result = json.loads(Path("results/hardware/result.json").read_text())
            self.assertEqual(result["files"], [])
            self.assertEqual(list(Path("results").rglob("*.bin")), [])


if __name__ == "__main__":
    unittest.main()
