import unittest

from main import (
    FILE_CATEGORIES,
    determine_file_extension,
    resolve_entity,
    sanitize_filename,
)


class TestTelegramFileDownloader(unittest.TestCase):
    def test_sanitize_filename_replaces_invalid_characters(self):
        # Characters forbidden on Windows / POSIX
        dangerous_name = 'What: is this? / A "test" * file <1> | part 2.txt'
        cleaned = sanitize_filename(dangerous_name)
        self.assertNotIn(":", cleaned)
        self.assertNotIn("?", cleaned)
        self.assertNotIn("/", cleaned)
        self.assertNotIn('"', cleaned)
        self.assertNotIn("*", cleaned)
        self.assertNotIn("<", cleaned)
        self.assertNotIn(">", cleaned)
        self.assertNotIn("|", cleaned)
        self.assertTrue(cleaned.endswith(".txt"))

    def test_sanitize_filename_strips_trailing_dots_and_spaces(self):
        cleaned = sanitize_filename("my_document. ")
        self.assertEqual(cleaned, "my_document")

    def test_sanitize_filename_empty_fallback(self):
        self.assertEqual(sanitize_filename(""), "unnamed_file")
        self.assertEqual(sanitize_filename("???:::"), "unnamed_file")

    def test_determine_file_extension_from_name(self):
        self.assertEqual(determine_file_extension("document.PDF"), "pdf")
        self.assertEqual(determine_file_extension("archive.tar.gz"), "gz")
        self.assertEqual(determine_file_extension("music.opus"), "opus")

    def test_determine_file_extension_fallback_to_mimetype(self):
        # File name without extension falls back to mime_type
        self.assertEqual(determine_file_extension("12345", "image/png"), "png")
        self.assertEqual(determine_file_extension("audio_sample", "audio/ogg"), "ogg")

    def test_determine_file_extension_unknown(self):
        self.assertEqual(determine_file_extension("no_ext_file", None), "")

    def test_resolve_entity(self):
        self.assertEqual(resolve_entity("12345678"), 12345678)
        self.assertEqual(resolve_entity("-1001234567890"), -1001234567890)
        self.assertEqual(resolve_entity("@telegram"), "@telegram")
        self.assertEqual(resolve_entity("me"), "me")

    def test_file_categories_expansion(self):
        self.assertIn("opus", FILE_CATEGORIES["audios"])
        self.assertIn("webm", FILE_CATEGORIES["videos"])
        self.assertIn("json", FILE_CATEGORIES["documents"])
        self.assertIn("md", FILE_CATEGORIES["documents"])
        self.assertIn("xz", FILE_CATEGORIES["archives"])


if __name__ == "__main__":
    unittest.main()
