from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_transcript_cache import PrivateStore
from transcript_cache import TranscriptCache
from transcript_decisions import TranscriptDecisions
from video_status import read_video_status


class TranscriptDecisionTests(unittest.TestCase):
    def test_many_decisions_survive_positive_cache_capacity_cleanup_and_years(self):
        store = PrivateStore()
        cache = TranscriptCache(store, clock=lambda: 1000)
        for index in range(150):
            cache.save('missing_' + str(index), 'captions_unavailable', http_status=206)
        TranscriptCache(store, clock=lambda: 10**9).prune()
        self.assertEqual(len(TranscriptDecisions(store).all_entries()), 150)
        self.assertEqual(TranscriptCache(store).entries, {})

    def test_negative_registry_contains_only_ids_timestamps_and_fixed_outcomes(self):
        store = PrivateStore()
        decisions = TranscriptDecisions(store, clock=lambda: 1000)
        decisions.remember('missing', 'captions_unavailable', 206)
        entry = decisions.get('missing')
        self.assertEqual(set(entry), {'code', 'http_status', 'checked_at'})
        with self.assertRaises(ValueError):
            decisions.remember('bad', 'quota_exhausted')

    def test_export_keeps_decision_ids_even_after_they_leave_playlist_and_caption_cache(self):
        store = PrivateStore()
        store.data.update({'history': {'posts': []}, 'digested_videos': {'ids': []},
                           'playlist_cache': {'videos': []}})
        TranscriptDecisions(store, clock=lambda: 1000).remember('removed_from_playlist', 'empty_transcript', 200)
        rows = read_video_status(store, now=10**9)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['video_id'], 'removed_from_playlist')
        self.assertTrue(rows[0]['caption_decision_persistent'])
        self.assertFalse(rows[0]['in_latest_playlist'])


if __name__ == '__main__':
    unittest.main()
