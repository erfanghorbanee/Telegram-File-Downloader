import unittest

from main import sanitize_filename


class TestSanitizeFilename(unittest.TestCase):
    def test_replaces_invalid_os_characters(self):
        dangerous_name = 'What: is this? / A "test" * file <1> | part 2.txt'
        cleaned = sanitize_filename(dangerous_name, fallback="101")
        for bad_char in '<>:"/\\|?*':
            self.assertNotIn(bad_char, cleaned)
        self.assertTrue(cleaned.endswith(".txt"))

    def test_strips_trailing_dots_and_spaces(self):
        self.assertEqual(
            sanitize_filename("my_document. ", fallback="102"), "my_document"
        )

    def test_neutralizes_path_traversal_inputs(self):
        cleaned = sanitize_filename("../../etc/passwd", fallback="103")
        self.assertNotIn("/", cleaned)
        self.assertNotIn("\\", cleaned)
        self.assertEqual(sanitize_filename("..", fallback="104"), "104")
        self.assertEqual(sanitize_filename(".", fallback="105"), "105")

    def test_empty_or_symbol_only_names_fall_back_to_message_id(self):
        # Empty cleaned filenames must not collide on a fixed placeholder.
        self.assertEqual(sanitize_filename("", fallback="4201"), "4201")
        self.assertEqual(sanitize_filename("???:::", fallback="4202"), "4202")
        self.assertNotEqual(
            sanitize_filename("???", fallback="4201"),
            sanitize_filename("???", fallback="4202"),
        )


if __name__ == "__main__":
    unittest.main()
