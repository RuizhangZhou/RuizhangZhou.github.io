from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from caption_provider import NativeCaptionProvider, PREFERENCE_KEY
from transcript_client import TranscriptError, TranscriptResult


class CaptionProviderTests(unittest.TestCase):
    def state(self):
        data = {}
        store = Mock()
        store.get.side_effect = lambda key: deepcopy(data.get(key))
        store.put.side_effect = lambda key, value: data.__setitem__(key, deepcopy(value))
        return store, data

    def test_exhausted_primary_switches_to_secondary_and_persists_only_its_slot(self):
        state, data = self.state()
        with patch('caption_provider.fetch_native_transcript', side_effect=[
                TranscriptError('quota_exhausted', attempts=1, http_status=429),
                TranscriptResult('Caption', 'ok', 1, 200), TranscriptResult('Next caption', 'ok', 1, 200)]) as fetch:
            self.assertEqual(NativeCaptionProvider('PRIVATE1', 'PRIVATE2', state=state).fetch('video').attempts, 2)
            self.assertEqual(NativeCaptionProvider('PRIVATE1', 'PRIVATE2', state=state).fetch('next').text, 'Next caption')
        self.assertEqual([call.args[1] for call in fetch.call_args_list], ['PRIVATE1', 'PRIVATE2', 'PRIVATE2'])
        self.assertEqual(data, {PREFERENCE_KEY: {'slot': 'secondary'}})

    def test_exhausted_secondary_can_return_to_refilled_primary_without_a_calendar_rule(self):
        state, data = self.state()
        data[PREFERENCE_KEY] = {'slot': 'secondary'}
        with patch('caption_provider.fetch_native_transcript', side_effect=[
                TranscriptError('quota_exhausted', attempts=1), TranscriptResult('Reset primary', 'ok', 1)]) as fetch:
            result = NativeCaptionProvider('key1', 'key2', state=state).fetch('video')
        self.assertEqual(result.text, 'Reset primary')
        self.assertEqual([call.args[1] for call in fetch.call_args_list], ['key2', 'key1'])
        self.assertEqual(data[PREFERENCE_KEY], {'slot': 'primary'})

    def test_both_exhausted_are_tried_once_each_and_stop_without_looping(self):
        provider = NativeCaptionProvider('key1', 'key2')
        with patch('caption_provider.fetch_native_transcript', side_effect=[
                TranscriptError('quota_exhausted', attempts=1), TranscriptError('quota_exhausted', attempts=1)]) as fetch:
            with self.assertRaises(TranscriptError) as raised:
                provider.fetch('video')
            with self.assertRaises(TranscriptError) as second:
                provider.fetch('another_video')
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(raised.exception.code, 'quota_exhausted')
        self.assertEqual(raised.exception.attempts, 2)
        self.assertEqual(second.exception.attempts, 0)

    def test_exhausted_pool_still_allows_cached_captions_and_metadata_fallback(self):
        from transcript_cache import TranscriptCache
        from transcript_client import collect_transcripts
        from test_transcript_cache import PrivateStore
        cache = TranscriptCache(PrivateStore())
        cache.save('cached', 'ok', 'Existing caption', 200)
        provider = NativeCaptionProvider('key1', 'key2')
        with patch('caption_provider.fetch_native_transcript', side_effect=[
                TranscriptError('quota_exhausted', attempts=1), TranscriptError('quota_exhausted', attempts=1)]) as fetch, \
             patch('transcript_client.time.sleep'):
            usable, captions = collect_transcripts([{'id': 'new'}, {'id': 'cached'}, {'id': 'another'}],
                lambda video_id: cache.fetch(video_id, provider.fetch).text, 3)
        self.assertEqual(captions, {'cached': 'Existing caption'})
        self.assertEqual(usable, [{'id': 'cached'}])
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(cache.decisions.all_entries(), {})

    def test_dry_run_key_switch_is_not_persisted(self):
        from transcript_cache import TranscriptCache
        from test_transcript_cache import PrivateStore
        store = PrivateStore()
        with patch('caption_provider.fetch_native_transcript', side_effect=[
                TranscriptError('quota_exhausted'), TranscriptResult('Caption', 'ok')]):
            NativeCaptionProvider('key1', 'key2', state=TranscriptCache(store, readonly=True)).fetch('video')
        self.assertEqual(store.writes, [])

    def test_access_credentials_rate_limits_and_timeouts_do_not_rotate_keys(self):
        for code in ('access_denied', 'authentication_failed', 'limit_exceeded', 'rate_limited', 'timeout'):
            with self.subTest(code=code), patch('caption_provider.fetch_native_transcript',
                                               side_effect=TranscriptError(code)) as fetch:
                with self.assertRaises(TranscriptError):
                    NativeCaptionProvider('key1', 'key2').fetch('video')
                fetch.assert_called_once_with('video', 'key1')

    def test_single_duplicate_or_absent_keys_do_not_create_extra_requests(self):
        with patch('caption_provider.fetch_native_transcript', return_value=TranscriptResult('Caption', 'ok')) as fetch:
            NativeCaptionProvider('same', 'same').fetch('video')
            fetch.assert_called_once()
        with patch('caption_provider.fetch_native_transcript') as fetch:
            self.assertEqual(NativeCaptionProvider(None).fetch('video').code, 'not_configured')
            fetch.assert_not_called()

    def test_account_summary_detects_shared_pool_without_exposing_organization_or_keys(self):
        response = Mock()
        response.json.return_value = {'organizationId': 'PRIVATEORG', 'maxCredits': 100, 'usedCredits': 95}
        with patch('caption_provider.requests.get', return_value=response) as get:
            summary = NativeCaptionProvider('PRIVATE1', 'PRIVATE2').usage_summary()
        self.assertTrue(summary['shared_quota_pool'])
        self.assertNotIn('PRIVATE', str(summary))
        self.assertEqual(summary['accounts'][0]['used_credits'], 95)
        self.assertTrue(all(call.args[0].endswith('/v1/me') for call in get.call_args_list))


if __name__ == '__main__':
    unittest.main()
