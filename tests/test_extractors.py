"""Unit tests for YouTube Automation Suite extractors and parsers."""

import os
import tempfile
import unittest

from src.youtube_automation_cli import (
    extract_video_id,
    extract_channel_id,
    parse_video_ids_file,
    parse_comments_file,
)


class TestExtractors(unittest.TestCase):
    def test_extract_video_id_valid_formats(self):
        # 11-char bare ID
        self.assertEqual(extract_video_id("dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        # Standard watch URL
        self.assertEqual(extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        # Short URL
        self.assertEqual(extract_video_id("https://youtu.be/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        # Embed URL
        self.assertEqual(extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        # Shorts URL
        self.assertEqual(extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_extract_video_id_invalid(self):
        self.assertIsNone(extract_video_id(""))
        self.assertIsNone(extract_video_id("invalid_id"))
        self.assertIsNone(extract_video_id("https://example.com/not-youtube"))

    def test_extract_channel_id_valid(self):
        sample_cid = "UC_x5XG1OV2P6uZZ5FSM9Ttw"
        self.assertEqual(extract_channel_id(sample_cid), sample_cid)
        self.assertEqual(extract_channel_id(f"https://www.youtube.com/channel/{sample_cid}"), sample_cid)

    def test_extract_channel_id_invalid(self):
        self.assertIsNone(extract_channel_id(""))
        self.assertIsNone(extract_channel_id("not_a_channel"))

    def test_parse_video_ids_file(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tf:
            tf.write(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ\n"
                "https://youtu.be/dQw4w9WgXcQ\n"  # Duplicate
                "https://youtu.be/9bZkp7q19f0\n"
                "\n"
                "invalid_line\n"
            )
            tf_path = tf.name

        try:
            vids = parse_video_ids_file(tf_path)
            self.assertEqual(vids, ["dQw4w9WgXcQ", "9bZkp7q19f0"])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_parse_comments_file(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tf:
            tf.write("First comment\n\nSecond comment\n")
            tf_path = tf.name

        try:
            comments = parse_comments_file(tf_path)
            self.assertEqual(comments, ["First comment", "Second comment"])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)


if __name__ == "__main__":
    unittest.main()
