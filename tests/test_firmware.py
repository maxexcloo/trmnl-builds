import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_discovery_supports_legacy_board_selection(self):
        config = [
            ["env:local", [["board", "esp32-c3-devkitc-02"]]],
            ["env:esp32-c3-devkitc-02", [["board", "esp32-c3-devkitc-02"]]],
            ["env:native", [["platform", "native"]]],
            ["env:test", [["board", "esp32"], ["test_build_src", True]]],
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
                json.loads(output.call_args.args[1]), ["esp32-c3-devkitc-02", "local"]
            )

    def test_polling_bootstraps_latest_then_catches_every_missing_release(self):
        upstream = [
            {"tag_name": f"v{i}", "published_at": f"2026-10-0{i}", "prerelease": False}
            for i in range(1, 5)
        ]
        for owned, expected in [
            ([], "v4"),
            ([{"tag_name": "v1"}], "v2"),
            ([{"tag_name": "v4"}], ""),
        ]:
            with (
                self.subTest(owned=owned),
                patch.dict(os.environ, GITHUB_REPOSITORY="owner/builds"),
                patch.object(firmware, "releases", side_effect=[upstream, owned]),
                patch.object(firmware, "output") as output,
            ):
                firmware.plan("")
                output.assert_called_once_with("tag", expected)

    def test_full_flash_chip_comes_from_image_header(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            build = Path("upstream/.pio/build/hardware")
            build.mkdir(parents=True)
            (build / "firmware.bin").write_bytes(b"application")
            image = bytearray(24)
            image[0] = 0xE9
            image[12] = 9
            (build / "merged_firmware.bin").write_bytes(image)
            firmware.pack("hardware", "success")
            result = json.loads(Path("results/hardware/result.json").read_text())
            self.assertEqual(result["flash"]["chipFamily"], "ESP32-S3")
            self.assertEqual(result["flash"]["file"], "hardware-full-flash.bin")

    def test_failure_never_packages_leftover_binaries(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            build = Path("upstream/.pio/build/hardware")
            build.mkdir(parents=True)
            (build / "firmware.bin").write_bytes(b"stale")
            firmware.pack("hardware", "failure")
            result = json.loads(Path("results/hardware/result.json").read_text())
            self.assertEqual(result["files"], [])
            self.assertEqual(list(Path("results").rglob("*.bin")), [])


if __name__ == "__main__":
    unittest.main()
