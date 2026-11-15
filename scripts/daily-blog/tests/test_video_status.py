from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transcript_cache import INDEX_KEY
from video_status import read_video_status


class VideoStatusTests(unittest.TestCase):
    def store(self):
        data = {'history': {'posts': [{'date': '2026-11-14', 'used_video_ids': ['published']}]},
                'digested_videos': {'ids': ['published', 'older']},
                'playlist_cache': {'videos': [{'id': 'published'}, {'id': 'cached'}, {'id': 'new'}]},
                INDEX_KEY: {'version': 1, 'entries': {
                    'cached': {'code': 'ok', 'chunks': 1, 'expires_at': 2000, 'http_status': 200},
                    'missing': {'code': 'captions_unavailable', 'chunks': 0, 'expires_at': 900, 'http_status': 206}}}}
        store = Mock()
        store.get.side_effect = lambda key: deepcopy(data.get(key))
        return store

    def test_export_distinguishes_published_fetched_and_unchecked_ids_without_writes(self):
        store = self.store()
        rows = {row['video_id']: row for row in read_video_status(store, now=1000)}
        self.assertTrue(rows['published']['used_in_article'])
        self.assertEqual(rows['published']['publication_dates'], ['2026-11-14'])
        self.assertTrue(rows['older']['used_in_article'])
        self.assertEqual(rows['older']['publication_dates'], [])
        self.assertFalse(rows['cached']['used_in_article'])
        self.assertEqual(rows['cached']['caption_cache_status'], 'ok')
        self.assertEqual(rows['new']['caption_cache_status'], 'not_cached')
        store.put.assert_not_called()

    def test_expired_caption_result_does_not_erase_its_id_or_clean_remote_state(self):
        store = self.store()
        rows = {row['video_id']: row for row in read_video_status(store, now=1000)}
        self.assertEqual(rows['missing']['caption_cache_status'], 'expired')
        self.assertFalse(rows['missing']['used_in_article'])
        store.put.assert_not_called()


if __name__ == '__main__':
    unittest.main()
