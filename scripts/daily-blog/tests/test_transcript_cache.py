from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transcript_cache import CHUNK_CHARS, INDEX_KEY, MAX_TEXT_CHARS, NEGATIVE_TTL, POSITIVE_TTL, TranscriptCache, probe_private_cache
from transcript_client import TranscriptError, TranscriptResult, collect_transcripts


class PrivateStore:
    def __init__(self):
        self.data = {}
        self.writes = []

    def get(self, key):
        return deepcopy(self.data.get(key))

    def put(self, key, value):
        self.data[key] = deepcopy(value)
        self.writes.append((key, deepcopy(value)))


class TranscriptCacheTests(unittest.TestCase):
    def setUp(self):
        self.store = PrivateStore()
        self.now = 1000

    def cache(self, **kwargs):
        return TranscriptCache(self.store, clock=lambda: self.now, **kwargs)

    def test_next_worker_reuses_captions_and_missing_results_without_provider_requests(self):
        outcomes = {'first': TranscriptResult('First caption', 'ok', 1, 200),
                    'missing': TranscriptResult(None, 'captions_unavailable', 1, 206),
                    'restricted': TranscriptError('access_denied', attempts=1, http_status=403),
                    'last': TranscriptResult('Last caption', 'ok', 1, 200)}
        def provider(video_id):
            result = outcomes[video_id]
            if isinstance(result, Exception):
                raise result
            return result
        fetch = Mock(side_effect=provider)
        candidates = [{'id': key} for key in outcomes]
        with patch('transcript_client.time.sleep'):
            for day in range(2):
                cache = self.cache()
                usable, captions = collect_transcripts(candidates,
                    lambda video_id: cache.fetch(video_id, fetch).text, 3)
                self.assertEqual(captions, {'first': 'First caption', 'last': 'Last caption'})
                self.assertEqual([video['id'] for video in usable], ['first', 'last'])
                self.now += 86400
        self.assertEqual(fetch.call_count, 4)  # First day only, including the 206/403 results.

    def test_caption_is_saved_before_generation_or_publication_can_fail(self):
        fetch = Mock(return_value=TranscriptResult('Reusable caption', 'ok', 1, 200))
        self.cache().fetch('candidate', fetch)
        # No publication took place. The next worker still reuses the unconsumed caption.
        result = self.cache().fetch('candidate', fetch)
        self.assertEqual(result.text, 'Reusable caption')
        self.assertTrue(result.cached)
        self.assertEqual(result.attempts, 0)
        fetch.assert_called_once()

    def test_negative_result_expires_and_rechecks_instead_of_permanently_discarding_video(self):
        for code in ('captions_unavailable', 'empty_transcript'):
            with self.subTest(code=code):
                self.store = PrivateStore()
                fetch = Mock(side_effect=[TranscriptResult(None, code, 1, 206),
                                          TranscriptResult('New caption', 'ok', 1, 200)])
                self.cache().fetch('candidate', fetch)
                self.now += NEGATIVE_TTL - 1
                self.assertIsNone(self.cache().fetch('candidate', fetch).text)
                self.now += 1
                self.assertEqual(self.cache().fetch('candidate', fetch).text, 'New caption')
                self.assertEqual(fetch.call_count, 2)

    def test_cache_hit_does_not_extend_positive_retention(self):
        fetch = Mock(return_value=TranscriptResult('Caption', 'ok', 1, 200))
        self.cache().fetch('candidate', fetch)
        self.now += POSITIVE_TTL - 1
        self.assertTrue(self.cache().fetch('candidate', fetch).cached)
        self.now += 1
        self.assertFalse(self.cache().fetch('candidate', fetch).cached)
        self.assertEqual(fetch.call_count, 2)

    def test_consumed_and_expired_entries_clear_payload_but_keep_unconsumed_captions(self):
        cache = self.cache()
        cache.save('used', 'ok', 'Used caption', 200)
        cache.save('unused', 'ok', 'Keep caption', 200)
        cache.save('missing', 'captions_unavailable', http_status=206)
        self.now += NEGATIVE_TTL
        self.cache().prune({'used'})
        self.assertEqual(set(self.store.data[INDEX_KEY]['entries']), {'unused'})
        self.assertEqual(self.store.get(cache.chunk_key('used', 0)), {})
        self.assertEqual(self.cache().cached_result('unused').text, 'Keep caption')

    def test_resource_cooldown_preserves_fail_closed_selection(self):
        fetch = Mock(side_effect=TranscriptError('access_denied', attempts=1, http_status=403))
        for day in range(2):
            with self.assertRaises(TranscriptError) as raised:
                collect_transcripts([{'id': 'restricted'}],
                    lambda video_id: self.cache().fetch(video_id, fetch).text, 3)
            self.assertEqual(raised.exception.code, 'access_denied')
            self.assertEqual(raised.exception.cached, day == 1)
            self.now += 86400
        fetch.assert_called_once()

    def test_quota_authentication_and_transport_errors_are_not_cached_as_missing(self):
        for code in ('quota_exhausted', 'authentication_failed', 'rate_limited', 'timeout', 'invalid_response'):
            with self.subTest(code=code):
                self.store = PrivateStore()
                fetch = Mock(side_effect=TranscriptError(code))
                for _ in range(2):
                    with self.assertRaises(TranscriptError):
                        self.cache().fetch('candidate', fetch)
                self.assertEqual(fetch.call_count, 2)
                self.assertEqual(self.store.writes, [])

    def test_dry_run_can_read_and_locally_reuse_cache_but_never_persist_or_prune_it(self):
        self.cache().save('expired', 'ok', 'Existing caption', 200)
        self.now += POSITIVE_TTL
        before, writes = deepcopy(self.store.data), len(self.store.writes)
        cache = self.cache(readonly=True)
        cache.prune()
        fetch = Mock(return_value=TranscriptResult('New caption', 'ok', 1, 200))
        cache.fetch('fresh', fetch)
        self.assertTrue(cache.fetch('fresh', fetch).cached)
        fetch.assert_called_once()
        self.assertEqual(self.store.data, before)
        self.assertEqual(len(self.store.writes), writes)

    def test_multibyte_captions_are_chunked_bounded_and_round_trip_without_loss(self):
        text = ('中文😀\n' * 20000)[:MAX_TEXT_CHARS]
        cache = self.cache()
        cache.save('large', 'ok', text + 'discarded beyond writer cap', 200)
        result = self.cache().cached_result('large')
        self.assertEqual(result.text, text)
        chunks = [value for key, value in self.store.writes if '.video.' in key]
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLess(len(json.dumps(chunk).encode('utf-8')), 49 * 1024)

    def test_entry_limit_evicts_oldest_payloads(self):
        with patch('transcript_cache.MAX_ENTRIES', 2):
            for video_id in ('first', 'second', 'third'):
                self.cache().save(video_id, 'ok', video_id, 200)
                self.now += 1
            self.assertEqual(set(self.cache().entries), {'second', 'third'})
            self.assertEqual(self.store.get(TranscriptCache.chunk_key('first', 0)), {})

    def test_interrupted_chunk_write_remains_tracked_and_is_cleaned_next_run(self):
        put = self.store.put
        def interrupted(key, value):
            if key == TranscriptCache.chunk_key('candidate', 1):
                raise RuntimeError('Simulated storage failure')
            put(key, value)
        with patch.object(self.store, 'put', side_effect=interrupted), self.assertRaises(RuntimeError):
            self.cache().save('candidate', 'ok', 'x' * (CHUNK_CHARS + 1), 200)
        self.assertEqual(self.store.get(INDEX_KEY)['entries']['candidate']['code'], 'writing')
        self.cache().prune()
        self.assertEqual(self.store.get(INDEX_KEY)['entries'], {})
        self.assertEqual(self.store.get(TranscriptCache.chunk_key('candidate', 0)), {})

    def test_missing_cached_chunk_is_repaired_without_treating_it_as_absent_captions(self):
        self.cache().save('candidate', 'ok', 'Old caption', 200)
        self.store.data[TranscriptCache.chunk_key('candidate', 0)] = {}
        fetch = Mock(return_value=TranscriptResult('New caption', 'ok', 1, 200))
        self.assertEqual(self.cache().fetch('candidate', fetch).text, 'New caption')
        fetch.assert_called_once()

    def test_malformed_index_fails_without_exposing_payload_or_making_provider_calls(self):
        for entry in ({'code': {'private': 'PRIVATE'}},
                      {'code': 'ok', 'expires_at': float('nan'), 'chunks': 1},
                      {'code': 'ok', 'expires_at': 1000, 'chunks': 0}):
            self.store.data[INDEX_KEY] = {'version': 1, 'entries': {'candidate': entry}}
            with self.assertRaisesRegex(RuntimeError, '^Invalid private transcript cache entry$'):
                self.cache()
        self.assertEqual(self.store.writes, [])

    def test_storage_probe_reuses_a_synthetic_caption_and_clears_it(self):
        probe_private_cache(self.store)
        self.assertEqual(self.store.get(INDEX_KEY)['entries'], {})
        self.assertTrue(all(value == {} for key, value in self.store.data.items() if '.video.' in key))

    def test_storage_probe_accepts_servers_that_return_not_found_after_clearing_account_data(self):
        get = self.store.get
        with patch.object(self.store, 'get', side_effect=lambda key: get(key) or None):
            probe_private_cache(self.store)


if __name__ == '__main__':
    unittest.main()
