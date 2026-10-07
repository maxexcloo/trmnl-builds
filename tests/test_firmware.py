import contextlib
import difflib
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

    def test_prepare_preserves_native_waveform_and_is_idempotent(self):
        original = (
            "    int rc = bbep.setCustomMatrix(u8_graytable, sizeof(u8_graytable));\n"
            '    Log_info("%s [%d]: setCustomMatrix returned %d\\r\\n", __FILE__, __LINE__, rc);\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            display = root / "src/display.cpp"
            display.write_text("before\n {\n" + original + "\nafter\n")
            with contextlib.redirect_stdout(io.StringIO()):
                firmware.prepare(root, "TRMNL_X_PAPERS3")
                prepared = display.read_text()
                firmware.prepare(root, "TRMNL_X_PAPERS3")
            self.assertEqual(display.read_text(), prepared)
            self.assertNotIn("setCustomMatrix", prepared)
            self.assertIn("native Paper S3 greyscale waveform", prepared)
            self.assertTrue(prepared.startswith("before\n"))
            self.assertTrue(prepared.endswith("after\n"))

    def test_prepare_rejects_changed_source_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            display = root / "src/display.cpp"
            source = "bbep.setCustomMatrix(u8_graytable, new_size);\n"
            display.write_text(source)
            with self.assertRaisesRegex(ValueError, "does not match upstream"):
                firmware.prepare(root, "TRMNL_X_PAPERS3")
            self.assertEqual(display.read_text(), source)

    def test_prepare_discovers_patch_files_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            patches = root / "patches/example"
            patches.mkdir(parents=True)
            for filename, patch_name in [
                ("a.txt", "0002-a.patch"),
                ("b.txt", "0001-b.patch"),
            ]:
                (root / filename).write_text("original\n")
                diff = difflib.unified_diff(
                    ["original\n"],
                    ["patched\n"],
                    fromfile=f"a/{filename}",
                    tofile=f"b/{filename}",
                )
                (patches / patch_name).write_text("".join(diff))
            output = io.StringIO()
            with (
                patch.object(firmware, "PATCHES", root / "patches"),
                contextlib.redirect_stdout(output),
            ):
                firmware.prepare(root, "example")
            self.assertEqual(
                output.getvalue().splitlines(),
                ["Applied: 0001-b.patch", "Applied: 0002-a.patch"],
            )
            self.assertEqual((root / "a.txt").read_text(), "patched\n")
            self.assertEqual((root / "b.txt").read_text(), "patched\n")

    def test_pack_keeps_original_and_patched_variants_separate(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.chdir(directory):
            build = Path("upstream/.pio/build/hardware")
            build.mkdir(parents=True)
            (build / "firmware.bin").write_bytes(b"original")
            firmware.pack("hardware", "success")
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

    def test_polling_builds_only_the_latest_missing_release(self):
        upstream = [
            {"tag_name": f"v{i}", "published_at": f"2026-10-0{i}", "prerelease": False}
            for i in range(1, 5)
        ]
        for owned, expected in [
            ([], "v4"),
            ([{"tag_name": "v1"}], "v4"),
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
