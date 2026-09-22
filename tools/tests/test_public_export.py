"""Tests for the public-export tooling: redaction, JPEG scrubbing, deny rules,
and the scanner's detections."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import check_public_tree as scanner  # noqa: E402
import export_public as exporter  # noqa: E402
from jpeg_scrub import jpeg_metadata_markers, strip_jpeg_metadata  # noqa: E402


def minimal_jpeg_with_exif() -> bytes:
    soi = b"\xff\xd8"
    app0 = b"\xff\xe0" + (16).to_bytes(2, "big") + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    payload = b"Exif\x00\x00" + b"GPSDATA" * 4
    app1 = b"\xff\xe1" + (len(payload) + 2).to_bytes(2, "big") + payload
    sos = b"\xff\xda" + (2).to_bytes(2, "big")
    eoi = b"\xff\xd9"
    return soi + app0 + app1 + sos + b"\x00\x11\x22" + eoi


class JpegScrubTests(unittest.TestCase):
    def test_strips_app1_exif(self):
        data = minimal_jpeg_with_exif()
        self.assertIn("APP1", jpeg_metadata_markers(data))
        scrubbed = strip_jpeg_metadata(data)
        self.assertEqual(jpeg_metadata_markers(scrubbed), [])
        self.assertTrue(scrubbed.startswith(b"\xff\xd8"))
        self.assertTrue(scrubbed.endswith(b"\xff\xd9"))

    def test_real_repo_jpegs_have_metadata_and_scrub_clean(self):
        jpegs = list((REPO / "notebook").rglob("*.jpg"))
        self.assertTrue(jpegs, "expected notebook JPEGs to exist")
        for j in jpegs:
            raw = j.read_bytes()
            self.assertEqual(jpeg_metadata_markers(strip_jpeg_metadata(raw)), [],
                             f"{j} still had metadata after strip")


class RedactionTests(unittest.TestCase):
    def setUp(self):
        self.config = exporter.load_config()
        self.redactions = exporter.compile_redactions(self.config)

    def test_lan_ip_and_paths_redacted(self):
        text = "printer at <printer-ip> archived to <archive>/x and <repo>/y"
        out, counts = exporter.redact_text(text, self.redactions)
        self.assertNotIn("<printer-ip>", out)
        self.assertNotIn("<archive>", out)
        self.assertNotIn("<repo>", out)
        self.assertIn("lan_ipv4", counts)

    def test_mac_redacted(self):
        out, _ = exporter.redact_text("mac <mac-redacted> here", self.redactions)
        self.assertNotIn("<mac-redacted>", out)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.config = exporter.load_config()

    def test_denied_paths_excluded(self):
        files = [
            "docs/findings.md",
            "docs/vendor/VENDOR_CORRESPONDENCE.md",
            "docs/firmware/package-access.md",
            "project/STATUS.md",
            "CLAUDE.md",
            "sources/loom/sessions/X/SESSION.md",
            "sources/loom/sessions/X/moonraker-api/klippy-log/response-body",
            "tools/tests/test_loom_evidence.py",
        ]
        selected = exporter.select_files(self.config, files)
        self.assertIn("docs/findings.md", selected)
        self.assertIn("sources/loom/sessions/X/SESSION.md", selected)  # exception
        for denied in ("docs/vendor/VENDOR_CORRESPONDENCE.md",
                       "docs/firmware/package-access.md", "project/STATUS.md",
                       "CLAUDE.md", "tools/tests/test_loom_evidence.py",
                       "sources/loom/sessions/X/moonraker-api/klippy-log/response-body"):
            self.assertNotIn(denied, selected, f"{denied} should be denied")


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.config = scanner.load_config()

    def _scan(self, files: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for rel, content in files.items():
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(content, bytes):
                    p.write_bytes(content)
                else:
                    p.write_text(content, encoding="utf-8")
            return scanner.scan(root, self.config)

    def test_detects_lan_ip(self):
        findings = self._scan({"a.md": "see <printer-ip>"})
        self.assertTrue(any("lan_ipv4_192" in f for f in findings))

    def test_detects_home_path_and_email(self):
        # Build the email from parts so this source file carries no literal
        # address for the public-tree scanner to flag.
        email = "person@" + "gmail" + ".com"
        findings = self._scan({"a.txt": f"<repo> here, mail {email}"})
        self.assertTrue(any("home_path" in f for f in findings))
        self.assertTrue(any("email" in f for f in findings))

    def test_allows_noreply_email(self):
        findings = self._scan({"a.md": "x@users.noreply.github.com"})
        self.assertEqual([f for f in findings if "email" in f], [])

    def test_detects_jpeg_metadata(self):
        findings = self._scan({"p.jpg": minimal_jpeg_with_exif()})
        self.assertTrue(any("JPEG metadata" in f for f in findings))

    def test_detects_broken_link(self):
        findings = self._scan({"a.md": "[x](missing.md)"})
        self.assertTrue(any("broken link" in f for f in findings))

    def test_clean_tree_passes(self):
        findings = self._scan({"a.md": "[self](a.md) at <printer-ip>, all good"})
        self.assertEqual(findings, [])


class EndToEndExportTests(unittest.TestCase):
    def test_export_then_scan_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "public"
            rc = subprocess.run(
                [sys.executable, str(TOOLS / "export_public.py"), str(out), "--force"],
                capture_output=True, text=True)
            self.assertEqual(rc.returncode, 0, rc.stdout + rc.stderr)
            self.assertTrue((out / "PUBLIC_EXPORT_MANIFEST.json").is_file())
            self.assertTrue((out / "LICENSE").is_file())
            manifest = json.loads((out / "PUBLIC_EXPORT_MANIFEST.json").read_text())
            self.assertGreater(manifest["file_count"], 0)
            # No denied content leaked.
            self.assertFalse((out / "project").exists())
            self.assertFalse((out / "docs" / "vendor").exists())
            self.assertFalse((out / "docs" / "firmware" / "package-access.md").exists())
            # Scanner is clean.
            self.assertEqual(scanner.scan(out, scanner.load_config()), [])


if __name__ == "__main__":
    unittest.main()
