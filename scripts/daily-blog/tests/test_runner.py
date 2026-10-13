import importlib.util
from pathlib import Path
import sys
import os
import tempfile
from types import SimpleNamespace
import unittest
import httpx
from unittest.mock import Mock, patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import run_actions


class PublicationTests(unittest.TestCase):
    def record(self):
        return {'title': 'Example', 'body': 'English article'}

    def test_existing_marker_is_reconciled_without_post(self):
        store, record = Mock(), self.record()
        existing = {'number': 12, 'html_url': 'https://github.com/example/blog/issues/12'}
        with patch.object(run_actions, 'find_issue', return_value=existing), patch.object(run_actions, 'github_request') as api:
            result = run_actions.publish_issue(store, 'key', record, 'example/blog', '2026-10-11')
        self.assertEqual(result['number'], 12)
        api.assert_not_called()

    def test_ambiguous_prior_post_never_reposted(self):
        record = {**self.record(), 'issue_sending': True}
        with patch.object(run_actions, 'find_issue', return_value=None), patch.object(run_actions, 'github_request') as api:
            with self.assertRaises(RuntimeError):
                run_actions.publish_issue(Mock(), 'key', record, 'example/blog', '2026-10-11')
        api.assert_not_called()

    def test_new_issue_is_checkpointed_before_post(self):
        record, store = self.record(), Mock()
        def api(*args, **kwargs):
            self.assertTrue(record['issue_sending'])
            store.put.assert_called()
            self.assertIn('<!-- daily-blog-2026-10-11 -->', kwargs['json']['body'])
            return {'number': 1, 'html_url': 'https://github.com/example/blog/issues/1'}
        with patch.object(run_actions, 'find_issue', return_value=None), patch.object(run_actions, 'github_request', side_effect=api):
            run_actions.publish_issue(store, 'key', record, 'example/blog', '2026-10-11')
        self.assertEqual(record['issue']['number'], 1)

    def test_known_issue_skips_network(self):
        record = {'issue': {'number': 2, 'url': 'existing'}}
        with patch.object(run_actions, 'find_issue') as find:
            self.assertEqual(run_actions.publish_issue(Mock(), 'key', record, 'repo', 'date')['number'], 2)
            find.assert_not_called()

    def test_matrix_does_not_leak_response_body_on_error(self):
        from matrix_state import MatrixKV
        response = Mock(is_success=False, status_code=403, text='secret token')
        with self.assertRaisesRegex(RuntimeError, '^Matrix API HTTP 403$'):
            MatrixKV.check(response)

    def test_duplicate_markers_fail_closed(self):
        marker = '<!-- daily-blog-2026-10-11 -->'
        with patch.object(run_actions, 'github_request', return_value=[{'body': marker}, {'body': marker}]):
            with self.assertRaises(RuntimeError):
                run_actions.find_issue('example/blog', marker)

    def test_research_dry_run_never_publishes_or_updates_remote_state(self):
        store = Mock()
        data = {'meta': {'version': 1}, 'history': {'posts': []},
                'digested_videos': {'ids': []}, 'playlist_cache': {'videos': []}}
        store.get.side_effect = data.get
        blog = SimpleNamespace(load_history=lambda: [], load_digested_ids=lambda: set(),
                               fetch_playlist_videos=lambda: [], pick_candidate_videos=lambda *a: [],
                               generate_post=lambda *a: ('Title', 'English', '标题', '中文', 'finance', 'Hook'))
        env = {'DAILY_BLOG_CONFIG_JSON': '{}', 'DAILY_BLOG_CREATORS_JSON': '{}',
               'MATRIX_HOMESERVER': 'https://example.org', 'MATRIX_BOT_TOKEN': 'test-token'}
        with tempfile.TemporaryDirectory() as directory, patch.object(run_actions, 'BASE', Path(directory)), \
             patch.object(run_actions, 'MatrixKV', return_value=store), patch.dict(os.environ, env), \
             patch.dict(sys.modules, {'daily_blog': blog}), patch.object(sys, 'argv', ['run_actions', '--dry-run']), \
             patch.object(run_actions, 'github_request') as api:
            run_actions.main()
        store.put.assert_not_called()
        store.send.assert_not_called()
        api.assert_not_called()

    def test_incomplete_private_state_stops_before_generation(self):
        store = Mock()
        store.get.return_value = None
        env = {'DAILY_BLOG_CONFIG_JSON': '{}', 'DAILY_BLOG_CREATORS_JSON': '{}',
               'MATRIX_HOMESERVER': 'https://example.org', 'MATRIX_BOT_TOKEN': 'test-token'}
        with tempfile.TemporaryDirectory() as directory, patch.object(run_actions, 'BASE', Path(directory)), \
             patch.object(run_actions, 'MatrixKV', return_value=store), patch.dict(os.environ, env), \
             patch.object(sys, 'argv', ['run_actions', '--dry-run']):
            with self.assertRaises(RuntimeError):
                run_actions.main()
        store.put.assert_not_called()

    def transcript_research(self, fetch, events=None, dry_run=True, generation_error=None):
        store = Mock()
        data = {'meta': {'version': 1}, 'history': {'posts': []},
                'digested_videos': {'ids': []}, 'playlist_cache': {'videos': []}}
        store.get.side_effect = data.get
        videos = [{'id': str(i)} for i in range(3)]
        blog = SimpleNamespace(load_history=lambda: [], load_digested_ids=lambda: set(),
            fetch_playlist_videos=lambda: videos, pick_candidate_videos=lambda *a: videos,
            fetch_transcript=fetch, MAX_DIGEST_CANDIDATES=2,
            generate_video_digest=Mock(return_value=('Title', 'English', '标题', '中文', 'Hook', ['1', '2'])),
            generate_post=Mock())
        if generation_error is not None:
            blog.generate_video_digest.side_effect = generation_error
        env = {'DAILY_BLOG_CONFIG_JSON': '{}', 'DAILY_BLOG_CREATORS_JSON': '{}',
               'MATRIX_HOMESERVER': 'https://example.org', 'MATRIX_BOT_TOKEN': 'test-token'}
        with tempfile.TemporaryDirectory() as directory, patch.object(run_actions, 'BASE', Path(directory)), \
             patch.object(run_actions, 'MatrixKV', return_value=store), patch.dict(os.environ, env), \
             patch.dict(sys.modules, {'daily_blog': blog}), \
             patch.object(sys, 'argv', ['run_actions'] + (['--dry-run'] if dry_run else [])), \
             patch.object(run_actions.time, 'sleep', side_effect=lambda seconds:
                          events.append('sleep:' + str(seconds)) if events is not None else None) as sleep, \
             patch.object(run_actions, 'github_request') as api:
            try:
                run_actions.main()
            finally:
                store.put.assert_not_called()
                store.send.assert_not_called()
                api.assert_not_called()
                blog.generate_post.assert_not_called()
        return blog, sleep

    def test_transcript_requests_keep_three_second_pacing_including_missing_captions(self):
        order = []
        def fetch(video_id):
            order.append('fetch:' + video_id)
            return None if video_id == '0' else 'Transcript'
        blog, sleep = self.transcript_research(fetch, order)
        self.assertEqual(order, ['fetch:0', 'sleep:3', 'fetch:1', 'sleep:3', 'fetch:2'])
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [3, 3])
        blog.generate_video_digest.assert_called_once()

    def test_transcript_service_failure_never_publishes_or_marks_video_consumed(self):
        with self.assertRaises(RuntimeError):
            self.transcript_research(Mock(side_effect=RuntimeError('Transcript service failed')), dry_run=False)

    def test_failure_summary_exposes_stage_and_status_not_raw_provider_data(self):
        response = httpx.Response(400, request=httpx.Request('POST', 'https://private.invalid/secret'),
                                  text='SECRET TOKEN AND ARTICLE')
        error = httpx.HTTPStatusError('SECRET TOKEN AND ARTICLE', request=response.request, response=response)
        run_actions.stage('generate_essay')
        self.assertEqual(run_actions.failure_summary(error),
                         {'stage': 'generate_essay', 'error_type': 'HTTPStatusError', 'http_status': 400})

    def test_generation_failure_never_checkpoints_or_publishes(self):
        with self.assertRaises(RuntimeError):
            self.transcript_research(Mock(return_value='Transcript'), dry_run=False,
                                     generation_error=RuntimeError('output_truncated_after_retry'))


if __name__ == '__main__':
    unittest.main()
