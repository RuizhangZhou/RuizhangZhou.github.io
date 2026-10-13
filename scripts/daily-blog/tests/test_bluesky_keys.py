from datetime import date, datetime, timezone
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from bluesky_keys import ALPHABET, CLOCK_ID, daily_post_rkey
import run_actions


class RecordKeyTests(unittest.TestCase):
    def test_key_matches_official_tid_syntax_and_is_stable(self):
        key = daily_post_rkey('2026-10-13')
        self.assertRegex(key, r'^[234567abcdefghij][234567abcdefghijklmnopqrstuvwxyz]{12}$')
        self.assertEqual(key, daily_post_rkey('2026-10-13'))
        self.assertNotEqual(key, 'daily-2026-10-13')

    def test_decoding_recovers_utc_midnight_and_publisher_clock(self):
        value = 0
        for char in daily_post_rkey('2026-10-13'):
            value = (value << 5) | ALPHABET.index(char)
        expected = (date(2026, 10, 13) - date(1970, 1, 1)).days * 86400 * 1000000
        self.assertEqual(value >> 10, expected)
        self.assertEqual(value & 1023, CLOCK_ID)

    def test_dates_have_distinct_monotonically_ordered_keys(self):
        keys = [daily_post_rkey(day) for day in ['2026-10-12', '2026-10-13', '2026-10-14']]
        self.assertEqual(keys, sorted(set(keys)))

    def test_noncanonical_invalid_and_out_of_range_dates_fail(self):
        for day in ['20261013', '2026-02-30', '1969-12-31', '9999-12-31', '2026-10-13T00:00:00Z']:
            with self.subTest(day=day), self.assertRaises(ValueError):
                daily_post_rkey(day)

    def pending_publication(self, existing_key=None):
        today = '2026-10-13'
        record = {'title': 'Example', 'body': 'English', 'title_zh': '标题', 'body_zh': '中文',
                  'hook': 'Hook', 'domain': 'finance', 'used_ids': [],
                  'created_at': '2026-10-13T20:15:50Z',
                  'issue': {'number': 252, 'url': 'https://example.invalid/issues/252'},
                  'matrix_text_done': True, 'matrix_file_done': True}
        if existing_key is not None:
            record['bluesky_rkey'] = existing_key
        expected_key = existing_key or daily_post_rkey(today)
        store = Mock()
        data = {'meta': {'version': 1}, 'history': {'posts': []}, 'digested_videos': {'ids': []},
                'playlist_cache': {'videos': []}, 'publication.' + today: record}
        store.get.side_effect = data.get
        blog = SimpleNamespace(load_history=lambda: [], load_digested_ids=lambda: set(),
            REPO='example/blog', BLOG_BASE='https://example.invalid/blog', BSKY_ID='test', BSKY_PASS='not-a-secret',
            MAX_HISTORY_KEPT=60, _bsky=Mock(side_effect=[{'did': 'did:plc:example', 'accessJwt': 'fake'},
                                                      {'uri': 'at://example', 'cid': 'example'}]))
        env = {'DAILY_BLOG_CONFIG_JSON': '{}', 'DAILY_BLOG_CREATORS_JSON': '{}',
               'MATRIX_HOMESERVER': 'https://example.invalid', 'MATRIX_BOT_TOKEN': 'test',
               'MATRIX_RICK_ROOM': 'test'}
        with tempfile.TemporaryDirectory() as directory, patch.object(run_actions, 'BASE', Path(directory)), \
             patch.object(run_actions, 'MatrixKV', return_value=store), patch.dict(os.environ, env), \
             patch.dict(sys.modules, {'daily_blog': blog}), patch.object(sys, 'argv', ['run_actions']), \
             patch.object(run_actions, 'datetime') as clock, patch.object(run_actions, 'github_request') as github:
            clock.now.return_value = datetime(2026, 10, 13, tzinfo=timezone.utc)
            run_actions.main()
            call = blog._bsky.call_args_list[1]
            self.assertEqual(call.args[0], 'com.atproto.repo.putRecord')
            self.assertEqual(call.args[1]['rkey'], expected_key)
            self.assertEqual(record['bluesky_rkey'], expected_key)
            self.assertTrue(record['bluesky_done'])
            blog._bsky.reset_mock()
            run_actions.main()
            blog._bsky.assert_not_called()
            store.send.assert_not_called()
            store.event.assert_not_called()
            github.assert_not_called()

    def test_pending_publication_uses_tid_and_completed_stages_are_not_repeated(self):
        self.pending_publication()

    def test_checkpointed_key_is_reused_even_if_generator_changes(self):
        with patch.object(run_actions, 'daily_post_rkey', side_effect=AssertionError('Must reuse saved key')):
            self.pending_publication(existing_key='3jzfcijpj2z2a')


if __name__ == '__main__':
    unittest.main()
