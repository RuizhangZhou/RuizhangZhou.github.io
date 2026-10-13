import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests
import regex

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from text_limits import bluesky_text, truncate_text


class TextLimitTests(unittest.TestCase):
    def test_short_multibyte_text_is_not_unnecessarily_truncated(self):
        for text in ('中文' * 50, 'é' * 150, '👨‍👩‍👧‍👦' * 20):
            self.assertEqual(truncate_text(text), text)

    def test_truncation_preserves_graphemes_including_combining_and_emoji(self):
        for cluster in ('e\u0301', '👨‍👩‍👧‍👦', '中'):
            result = truncate_text(cluster * 250, max_bytes=10000)
            self.assertEqual(result, cluster * 219 + '…')
            self.assertEqual(len(regex.findall(r'\X', result)), 220)

    def test_complete_post_fits_both_limits_and_facet_selects_exact_url(self):
        url = 'https://example.org/' + 'a' * 120
        for hook in ('中文' * 500, '👨‍👩‍👧‍👦' * 500, 'a' + '\u0301' * 4000):
            text, start, end = bluesky_text(hook, url)
            self.assertLessEqual(len(regex.findall(r'\X', text)), 300)
            self.assertLessEqual(len(text.encode()), 3000)
            self.assertEqual(text.encode()[start:end].decode(), url)
            self.assertTrue(text.endswith(url))

    def test_impossible_url_budget_is_rejected(self):
        with self.assertRaises(ValueError):
            bluesky_text('Hook', 'https://example.org/' + 'a' * 300)


class WriterSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Never load server credentials merely to import the writer in a test.
        spec = importlib.util.spec_from_file_location('writer_under_test', BASE / 'daily_blog.py')
        cls.blog = importlib.util.module_from_spec(spec)
        with patch('dotenv.load_dotenv'), patch.dict(os.environ, {'BSKY_APP_PASSWORD': 'test'}):
            spec.loader.exec_module(cls.blog)

    def test_private_markdown_strips_active_html_but_keeps_tables(self):
        result = self.blog._markdown_to_html('<script>alert(1)</script>\n\n' +
            '<img src=x onerror="alert(1)"><a href="javascript:alert(1)">link</a>\n\n' +
            '| A | B |\n|---|---|\n| 1 | 2 |')
        self.assertNotIn('<script', result)
        self.assertNotIn('onerror', result)
        self.assertNotIn('javascript:', result)
        self.assertIn('<table>', result)

    def test_private_html_attachment_contains_only_sanitized_article_and_escaped_title(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(self.blog, 'OUTPUT_DIR', Path(directory)):
            path = self.blog.save_chinese_digest('<img onerror="bad">', '<script>bad()</script> **中文**')
            content = path.read_text()
        self.assertNotIn('<script', content)
        self.assertNotIn('<img onerror', content)
        self.assertIn('<strong>中文</strong>', content)

    def test_rate_limit_and_network_errors_raise_without_logging_provider_details(self):
        response = Mock(status_code=429)
        response.json.return_value = {'error': 'limit-exceeded', 'details': 'private provider data'}
        response.raise_for_status.side_effect = requests.HTTPError('private provider data')
        for outcome in (response, requests.Timeout('private provider data')):
            kwargs = {'side_effect': outcome} if isinstance(outcome, Exception) else {'return_value': outcome}
            with patch.object(self.blog, 'SUPADATA_API_KEY', 'test'), patch('requests.get', **kwargs), \
                 patch.object(self.blog, 'log') as log:
                with self.assertRaisesRegex(RuntimeError, '^Transcript service failed; playlist item retained for retry$'):
                    self.blog.fetch_transcript('video')
                log.assert_not_called()

    def test_confirmed_native_unavailable_can_still_fall_back_without_paid_transcription(self):
        response = Mock(status_code=404)
        response.json.return_value = {'error': 'transcript-unavailable'}
        with patch.object(self.blog, 'SUPADATA_API_KEY', 'test'), patch('requests.get', return_value=response) as get:
            self.assertIsNone(self.blog.fetch_transcript('video'))
        self.assertEqual(get.call_args.kwargs['params']['mode'], 'native')

    def test_native_transcript_success(self):
        response = Mock(status_code=200)
        response.json.return_value = {'content': [{'text': 'Hello'}, {'text': 'world'}]}
        with patch.object(self.blog, 'SUPADATA_API_KEY', 'test'), patch('requests.get', return_value=response):
            self.assertEqual(self.blog.fetch_transcript('video'), 'Hello world')

    def test_async_or_malformed_payload_is_not_treated_as_missing_captions(self):
        for payload in ({'jobId': 'pending'}, {'error': 'unknown'}, {'content': None}):
            response = Mock(status_code=200)
            response.json.return_value = payload
            with patch.object(self.blog, 'SUPADATA_API_KEY', 'test'), patch('requests.get', return_value=response):
                with self.assertRaises(RuntimeError):
                    self.blog.fetch_transcript('video')

    def completion(self, content, finish='stop'):
        return {'choices': [{'finish_reason': finish, 'message': {'content': content}}]}

    def sections(self):
        return ('<<<TITLE>>>', '<<<BODY>>>', '<<<TITLE_ZH>>>', '<<<BODY_ZH>>>', '<<<HOOK>>>')

    def complete_text(self):
        return '\n'.join(marker + '\nText' for marker in self.sections())

    def test_truncated_response_is_regenerated_once_with_more_budget(self):
        messages = [{'role': 'user', 'content': 'Original instructions'}]
        with patch('llm_gateway.chat', side_effect=[self.completion('Partial secret', 'length'),
                                                   self.completion(self.complete_text())]) as chat:
            parts = self.blog.complete_sections(messages, task='youtube_digest', markers=self.sections(),
                                               max_tokens=16000, timeout=240, reasoning_effort='high')
        self.assertEqual(parts, ['Text'] * 5)
        self.assertEqual([c.kwargs['max_tokens'] for c in chat.call_args_list], [16000, 32000])
        for call in chat.call_args_list:
            self.assertEqual(call.kwargs['messages'], messages)
            self.assertEqual(call.kwargs['reasoning_effort'], 'high')
            self.assertEqual(call.kwargs['task'], 'youtube_digest')

    def test_repeated_truncation_is_bounded_and_never_exposes_article(self):
        with patch('llm_gateway.chat', return_value=self.completion('PRIVATE CONTENT', 'length')) as chat:
            with self.assertRaisesRegex(self.blog.GenerationError, '^output_truncated_after_retry$'):
                self.blog.complete_sections([], task='blog', markers=self.sections(), max_tokens=12000, timeout=150)
        self.assertEqual(chat.call_count, 2)

    def test_length_is_rejected_even_if_every_marker_is_present(self):
        with patch('llm_gateway.chat', return_value=self.completion(self.complete_text(), 'length')):
            with self.assertRaises(self.blog.GenerationError):
                self.blog.complete_sections([], task='blog', markers=self.sections(), max_tokens=12000, timeout=150)

    def test_missing_unordered_duplicate_and_empty_sections_are_rejected_without_retry(self):
        invalid = ['PRIVATE CONTENT', self.complete_text().replace('<<<BODY>>>', '<<<HOOK>>>'),
                   self.complete_text() + '<<<TITLE>>>duplicate',
                   self.complete_text().replace('<<<BODY>>>\nText', '<<<BODY>>>')]
        for text in invalid:
            with self.subTest(text=text), patch('llm_gateway.chat', return_value=self.completion(text)) as chat:
                with self.assertRaises(self.blog.GenerationError) as error:
                    self.blog.complete_sections([], task='blog', markers=self.sections(), max_tokens=12000, timeout=150)
                self.assertNotIn('PRIVATE CONTENT', str(error.exception))
                self.assertEqual(chat.call_count, 1)

    def test_refusal_and_empty_content_are_safe_failures(self):
        for response in [self.completion('PRIVATE CONTENT', 'content_filter'), self.completion(None), {'choices': []}]:
            with patch('llm_gateway.chat', return_value=response):
                with self.assertRaises(self.blog.GenerationError):
                    self.blog.complete_sections([], task='blog', markers=self.sections(), max_tokens=12000, timeout=150)

    def test_essay_generation_reserves_budget_for_high_reasoning_and_two_languages(self):
        markers = ('<<<TITLE>>>', '<<<DOMAIN>>>', '<<<BODY>>>', '<<<TITLE_ZH>>>', '<<<BODY_ZH>>>', '<<<HOOK>>>')
        text = '\n'.join(marker + '\nText' for marker in markers)
        with patch('llm_gateway.chat', return_value=self.completion(text)) as chat:
            result = self.blog.generate_post([])
        self.assertEqual(chat.call_args.kwargs['max_tokens'], 12000)
        self.assertEqual(chat.call_args.kwargs['task'], 'blog')
        self.assertEqual(len(result), 6)
