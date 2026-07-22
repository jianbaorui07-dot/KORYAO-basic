from __future__ import annotations

import unittest

from starbridge_mcp.core.security import (
    contains_sensitive_text,
    redact_path,
    sanitize_details,
    sanitize_path,
    sanitize_text,
)

BANNED_OUTPUT_FRAGMENTS = ("C:\\Users\\", "/Users/", "/home/", "AppData", "Desktop", "Documents")


class SecuritySanitizerTests(unittest.TestCase):
    def assert_clean(self, value: object) -> None:
        text = str(value)
        for fragment in BANNED_OUTPUT_FRAGMENTS:
            self.assertNotIn(fragment, text)
        self.assertFalse(contains_sensitive_text(value))

    def test_sanitize_path_redacts_common_private_paths(self) -> None:
        windows_home = "C:" + "\\Users\\SomeName"
        samples = [
            windows_home + "\\Desktop\\file" + ".psd",
            windows_home + "\\AppData\\Local\\Adobe",
            "/Users/somename/Documents/file" + ".ai",
            "/home/somename/models/model" + ".safetensors",
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                sanitized = sanitize_path(sample)
                self.assert_clean(sanitized)

    def test_redact_path_public_alias(self) -> None:
        sanitized = redact_path("C:" + "\\Users\\SomeName\\Desktop\\source.png")
        self.assertIn("<REDACTED_PATH>", sanitized)
        self.assert_clean(sanitized)

    def test_sanitize_path_redacts_posix_temporary_roots(self) -> None:
        samples = [
            "/tmp/job/manifest.latest.json",
            "/var/tmp/job/manifest.latest.json",
            "/var/folders/ab/random/T/manifest.latest.json",
            "/private/tmp/clean-worktree/examples/output/evidence/manifest.latest.json",
            "/private/var/tmp/job/manifest.latest.json",
            "/private/var/folders/ab/random/T/manifest.latest.json",
            "/PRIVATE/TMP/job/manifest.latest.json",
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                sanitized = sanitize_path(sample)
                self.assertEqual("<REDACTED_PATH>", sanitized)
                self.assertTrue(contains_sensitive_text(sample))
                self.assert_clean(sanitized)

    def test_sanitize_path_preserves_temporary_path_context_and_punctuation(self) -> None:
        samples = {
            "Path: /tmp: denied": "Path: <REDACTED_PATH>: denied",
            "路径：/tmp。": "路径：<REDACTED_PATH>。",
            "(/tmp)": "(<REDACTED_PATH>)",
            "“/tmp”": "“<REDACTED_PATH>”",
            "prefix /tmp/secret suffix preserved": "prefix <REDACTED_PATH> suffix preserved",
            "Path: /tmp/secret)": "Path: <REDACTED_PATH>)",
            "Path: /tmp/secret” suffix": "Path: <REDACTED_PATH>” suffix",
            "prefix /tmp/secret,suffix preserved": (
                "prefix <REDACTED_PATH>,suffix preserved"
            ),
            "prefix /tmp/secret;suffix preserved": (
                "prefix <REDACTED_PATH>;suffix preserved"
            ),
            "prefix /tmp/secret:suffix preserved": (
                "prefix <REDACTED_PATH>:suffix preserved"
            ),
            "prefix /tmp/secret!suffix preserved": (
                "prefix <REDACTED_PATH>!suffix preserved"
            ),
            "prefix /tmp/secret?suffix preserved": (
                "prefix <REDACTED_PATH>?suffix preserved"
            ),
            "prefix /tmp/secret...suffix preserved": (
                "prefix <REDACTED_PATH>...suffix preserved"
            ),
            "prefix /tmp/secret.txt...next": "prefix <REDACTED_PATH>...next",
            "prefix /var/tmp/secret.txt. suffix": "prefix <REDACTED_PATH>. suffix",
            "prefix /private/var/folders/ab/random/T/file.json; suffix": (
                "prefix <REDACTED_PATH>; suffix"
            ),
            "prefix /Users/somename/Documents/client.ai suffix": (
                "prefix <REDACTED_PATH> suffix"
            ),
        }
        for sample, expected in samples.items():
            with self.subTest(sample=sample):
                sanitized = sanitize_path(sample)
                self.assertEqual(expected, sanitized)
                self.assertTrue(contains_sensitive_text(sample))
                self.assert_clean(sanitized)

    def test_sanitize_path_distinguishes_period_boundaries_from_similar_roots(self) -> None:
        samples = {
            "Path: /tmp.": ("Path: <REDACTED_PATH>.", True),
            "Path: /tmp. next": ("Path: <REDACTED_PATH>. next", True),
            "Path: /tmp...": ("Path: <REDACTED_PATH>...", True),
            "Path: /tmp…": ("Path: <REDACTED_PATH>…", True),
            "Path: /tmp—next": ("Path: <REDACTED_PATH>—next", True),
            "/tmp.foo": ("/tmp.foo", False),
            "/tmp.1": ("/tmp.1", False),
            "/tmp..foo": ("/tmp..foo", False),
            "/var/tmp.log": ("/var/tmp.log", False),
            "/var/folders.json": ("/var/folders.json", False),
        }
        for sample, (expected, is_sensitive) in samples.items():
            with self.subTest(sample=sample):
                self.assertEqual(expected, sanitize_path(sample))
                self.assertEqual(is_sensitive, contains_sensitive_text(sample))

    def test_sanitize_path_preserves_urls_and_similar_non_temporary_roots(self) -> None:
        samples = [
            "https://tmp/path",
            "https://var/tmp/path",
            "https://example.test/tmp/path",
            "file://tmp/path",
            "file:///tmp.foo",
            "file:///var/tmp.log",
            "file:///tmp%2Efoo",
            "file://localhost/tmp.foo",
            "file://localhost/tmp.1",
            "/tmpfile/public.txt",
            "/private/tmpfile/public.txt",
            "/var/folders-public/readme",
            "prefix /tmpish text",
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertEqual(sample, sanitize_path(sample))
                self.assertFalse(contains_sensitive_text(sample))

    def test_sanitize_path_redacts_local_file_uri_paths(self) -> None:
        samples = {
            "file:///tmp/private.txt": "file://<REDACTED_PATH>",
            "file:///private/tmp/private.txt": "file://<REDACTED_PATH>",
            "file://localhost/tmp/private.txt": "file://localhost<REDACTED_PATH>",
            "file://LOCALHOST/private/var/tmp/private.txt": (
                "file://LOCALHOST<REDACTED_PATH>"
            ),
            "FILE:///PRIVATE/TMP/private.txt": "FILE://<REDACTED_PATH>",
            "file:///tmp/private.txt.": "file://<REDACTED_PATH>.",
            "file:///tmp/private.txt,suffix": "file://<REDACTED_PATH>,suffix",
            "file:///tmp/private.txt...suffix": "file://<REDACTED_PATH>...suffix",
            "file:///%74mp/private.txt": "file://<REDACTED_PATH>",
            "file:///tmp%2Fprivate.txt": "file://<REDACTED_PATH>",
            "file://localhost/%74mp/private.txt": "file://localhost<REDACTED_PATH>",
            "file:///Users/somename/Documents/file.ai": "file://<REDACTED_PATH>",
        }
        for sample, expected in samples.items():
            with self.subTest(sample=sample):
                sanitized = sanitize_path(sample)
                self.assertEqual(expected, sanitized)
                self.assertTrue(contains_sensitive_text(sample))
                self.assert_clean(sanitized)

    def test_sanitize_path_redacts_temp_paths_in_uri_query_and_fragment(self) -> None:
        samples = {
            "file:///tmp/private.txt?next=/tmp/not-a-second-token#frag": (
                "file://<REDACTED_PATH>?next=<REDACTED_PATH>#frag"
            ),
            "https://example.test/?local=/private/tmp/secret": (
                "https://example.test/?local=<REDACTED_PATH>"
            ),
            "https://example.test/?local=/tmp/secret&mode=public": (
                "https://example.test/?local=<REDACTED_PATH>&mode=public"
            ),
            "https://example.test/?local=%2Fprivate%2Ftmp%2Fsecret": (
                "https://example.test/?local=<REDACTED_PATH>"
            ),
            "https://example.test/?local=/tmp%2Fsecret&mode=public": (
                "https://example.test/?local=<REDACTED_PATH>&mode=public"
            ),
            "https://tmp/path#local=/var/folders/ab/random/T/file.json": (
                "https://tmp/path#local=<REDACTED_PATH>"
            ),
            "https://tmp/path#local=%2Fvar%2Ftmp%2Fsecret": (
                "https://tmp/path#local=<REDACTED_PATH>"
            ),
            "file://remote.example/public?local=/var/tmp/secret": (
                "file://remote.example/public?local=<REDACTED_PATH>"
            ),
            "file:///tmp/private.txt?next=%2Ftmp%2Fsecond#frag": (
                "file://<REDACTED_PATH>?next=<REDACTED_PATH>#frag"
            ),
        }
        for sample, expected in samples.items():
            with self.subTest(sample=sample):
                sanitized = sanitize_path(sample)
                self.assertEqual(expected, sanitized)
                self.assertTrue(contains_sensitive_text(sample))
                self.assert_clean(sanitized)

        unchanged = "https://example.test/?local=%2Ftmp%2Efoo&mode=public"
        self.assertEqual(unchanged, sanitize_path(unchanged))
        self.assertFalse(contains_sensitive_text(unchanged))

    def test_sanitize_text_preserves_normal_bridge_text(self) -> None:
        text = "Photoshop 修图桥 当前未完全就绪，详见 details.notes。"
        self.assertEqual(sanitize_text(text), text)
        self.assert_clean(sanitize_text(text))

    def test_sanitize_details_recurses_dicts_and_lists(self) -> None:
        payload = {
            "bridge": "illustrator",
            "details": [
                {"path": "C:" + "\\Users\\SomeName\\Documents\\client" + ".ai"},
                {"model": "/home/somename/models/model" + ".safetensors"},
            ],
        }
        sanitized = sanitize_details(payload)
        self.assertEqual(sanitized["bridge"], "illustrator")
        self.assert_clean(sanitized)


if __name__ == "__main__":
    unittest.main()
