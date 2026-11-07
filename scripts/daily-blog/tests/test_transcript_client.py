from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transcript_client import API, MAX_POLLS, TranscriptError, collect_transcripts, fetch_native_transcript, retry_after_seconds


class TranscriptClientTests(unittest.TestCase):
    def response(self, status=200, payload=None, headers=None):
        response = Mock(status_code=status, headers=headers or {})
        response.json.return_value = payload if payload is not None else {'content': [{'text': 'Captions'}]}
        return response

    def fetch(self, responses):
        with patch('transcript_client.requests.get', side_effect=responses) as get, \
             patch('transcript_client.time.sleep') as sleep:
            result = fetch_native_transcript('private-video-id', 'PRIVATE API KEY')
        return result, get, sleep

    def test_native_only_accepts_segments_and_plain_text(self):
        for content in (' First second ', [{'text': 'First'}, {'text': 'second'}]):
            with self.subTest(content=content):
                result, get, _ = self.fetch([self.response(payload={'content': content})])
                self.assertEqual(result.text, 'First second')
                self.assertEqual(result.diagnostics(),
                                 {'provider': 'supadata', 'code': 'ok', 'attempts': 1, 'http_status': 200})
                self.assertEqual(get.call_args.kwargs['params']['mode'], 'native')
                self.assertFalse(get.call_args.kwargs['allow_redirects'])
                self.assertNotIn('PRIVATE', str(result.diagnostics()))

    def test_missing_key_uses_existing_fallback_without_network(self):
        with patch('transcript_client.requests.get') as get:
            result = fetch_native_transcript('video', None)
        self.assertEqual(result.code, 'not_configured')
        self.assertIsNone(result.text)
        get.assert_not_called()

    def test_confirmed_missing_captions_is_not_a_service_failure(self):
        for status in (200, 206, 404):
            with self.subTest(status=status):
                result, get, sleep = self.fetch([self.response(status, {'error': 'transcript-unavailable'})])
                self.assertIsNone(result.text)
                self.assertEqual(result.code, 'captions_unavailable')
                self.assertEqual(get.call_count, 1)
                sleep.assert_not_called()

    def test_empty_transcript_is_distinguished_from_missing_captions(self):
        for content in ('  ', [], [{'text': ' '}]):
            result, _, _ = self.fetch([self.response(payload={'content': content})])
            self.assertEqual(result.code, 'empty_transcript')
            self.assertIsNone(result.text)

    def test_credential_plan_and_video_errors_do_not_retry_or_become_missing_captions(self):
        for status, code in ((400, 'invalid_request'), (401, 'authentication_failed'),
                             (402, 'upgrade_required'), (403, 'access_denied'),
                             (404, 'video_unavailable'), (302, 'unexpected_redirect')):
            with self.subTest(status=status), patch('transcript_client.requests.get',
                    return_value=self.response(status, {'details': 'PRIVATE PROVIDER MESSAGE'})) as get, \
                 patch('transcript_client.time.sleep') as sleep:
                with self.assertRaises(TranscriptError) as raised:
                    fetch_native_transcript('video', 'PRIVATE API KEY')
                self.assertEqual(raised.exception.code, code)
                self.assertFalse(raised.exception.retryable)
                self.assertEqual(get.call_count, 1)
                self.assertNotIn('PRIVATE', str(raised.exception.diagnostics()))
                sleep.assert_not_called()

    def test_monthly_quota_and_ambiguous_429_never_retry_blindly(self):
        for details, code in (('Plan usage limit was exceeded.', 'quota_exhausted'),
                              ('unknown PRIVATE DETAILS', 'limit_exceeded')):
            with self.subTest(code=code), patch('transcript_client.requests.get', return_value=self.response(
                    429, {'error': 'limit-exceeded', 'details': details})) as get, \
                 patch('transcript_client.time.sleep') as sleep:
                with self.assertRaises(TranscriptError) as raised:
                    fetch_native_transcript('video', 'key')
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(get.call_count, 1)
                sleep.assert_not_called()

    def test_rate_limit_honors_retry_after_and_records_recovery(self):
        for details in ('Global request rate limit was exceeded.',
                        'Request rate limit on current plan was exceeded.'):
            result, get, sleep = self.fetch([
                self.response(429, {'error': 'limit-exceeded', 'details': details}, {'Retry-After': '7'}),
                self.response()])
            self.assertEqual(result.code, 'ok')
            self.assertEqual(result.attempts, 2)
            self.assertEqual(get.call_count, 2)
            sleep.assert_called_once_with(7)

    def test_long_retry_after_stops_instead_of_retrying_before_allowed_time(self):
        with patch('transcript_client.requests.get', return_value=self.response(
                429, {'error': 'limit-exceeded', 'details': 'Request rate limit on current plan was exceeded.'},
                {'Retry-After': '120'})) as get, patch('transcript_client.time.sleep') as sleep:
            with self.assertRaises(TranscriptError) as raised:
                fetch_native_transcript('video', 'key')
        self.assertEqual(raised.exception.code, 'rate_limited')
        self.assertEqual(raised.exception.diagnostics()['retry_after_seconds'], 120)
        self.assertEqual(get.call_count, 1)
        sleep.assert_not_called()

    def test_timeout_can_recover_without_losing_outcome(self):
        result, get, sleep = self.fetch([requests.Timeout('PRIVATE URL AND TOKEN'), self.response()])
        self.assertEqual(result.attempts, 2)
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(3)

    def test_persistent_transport_and_server_errors_have_bounded_recovery(self):
        for response, code in ((requests.Timeout('PRIVATE TOKEN'), 'timeout'),
                               (requests.ConnectionError('PRIVATE URL'), 'network_error'),
                               (self.response(503, {}), 'provider_unavailable')):
            with self.subTest(code=code), patch('transcript_client.requests.get', side_effect=[response] * 3) as get, \
                 patch('transcript_client.time.sleep') as sleep:
                with self.assertRaises(TranscriptError) as raised:
                    fetch_native_transcript('video', 'key')
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(raised.exception.attempts, 3)
                self.assertTrue(raised.exception.retryable)
                self.assertEqual(get.call_count, 3)
                self.assertEqual([call.args[0] for call in sleep.call_args_list], [3, 6])
                self.assertNotIn('PRIVATE', str(raised.exception))

    def test_non_json_server_failure_still_retries_but_non_json_success_fails_closed(self):
        for status, code, attempts in ((502, 'provider_unavailable', 3), (200, 'invalid_response', 1)):
            response = self.response(status)
            response.json.side_effect = ValueError('PRIVATE BODY')
            with self.subTest(status=status), patch('transcript_client.requests.get', return_value=response) as get, \
                 patch('transcript_client.time.sleep'):
                with self.assertRaises(TranscriptError) as raised:
                    fetch_native_transcript('video', 'key')
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(get.call_count, attempts)

    def test_malformed_content_is_never_used_or_reported_as_missing(self):
        for payload in ({'content': None}, {'content': [{'text': 123}]}, {'content': ['PRIVATE CONTENT']},
                        {'error': 'PRIVATE UNKNOWN ERROR'}, {'content': {'text': 'PRIVATE'}}):
            with self.subTest(payload=payload), patch('transcript_client.requests.get',
                                                     return_value=self.response(payload=payload)):
                with self.assertRaises(TranscriptError) as raised:
                    fetch_native_transcript('video', 'key')
                self.assertEqual(raised.exception.code, 'invalid_response')
                self.assertNotIn('PRIVATE', str(raised.exception.diagnostics()))

    def test_async_job_is_polled_without_resubmitting_video(self):
        result, get, sleep = self.fetch([
            self.response(202, {'jobId': 'job_123'}), self.response(payload={'status': 'queued'}),
            self.response(payload={'status': 'active'}),
            self.response(payload={'status': 'completed', 'content': 'Ready'})])
        self.assertEqual(result.text, 'Ready')
        self.assertEqual(result.attempts, 4)
        self.assertEqual([call.args[0] for call in get.call_args_list], [API] + [API + '/job_123'] * 3)
        self.assertEqual([call.kwargs['params'] for call in get.call_args_list[1:]], [None] * 3)
        self.assertEqual(sleep.call_count, 3)

    def test_async_failure_decodes_nested_quota_and_missing_captions(self):
        for error in ({'error': 'transcript-unavailable'},
                      {'error': 'limit-exceeded', 'details': 'Plan usage limit was exceeded.'}):
            responses = [self.response(202, {'jobId': 'job'}),
                         self.response(payload={'status': 'failed', 'error': error})]
            with patch('transcript_client.requests.get', side_effect=responses), patch('transcript_client.time.sleep'):
                if error['error'] == 'transcript-unavailable':
                    self.assertEqual(fetch_native_transcript('video', 'key').code, 'captions_unavailable')
                else:
                    with self.assertRaises(TranscriptError) as raised:
                        fetch_native_transcript('video', 'key')
                    self.assertEqual(raised.exception.code, 'quota_exhausted')

    def test_async_wait_is_bounded(self):
        responses = [self.response(202, {'jobId': 'job'})] + [self.response(payload={'status': 'active'})] * MAX_POLLS
        with patch('transcript_client.requests.get', side_effect=responses) as get, \
             patch('transcript_client.time.sleep'):
            with self.assertRaises(TranscriptError) as raised:
                fetch_native_transcript('video', 'key')
        self.assertEqual(raised.exception.code, 'job_timeout')
        self.assertEqual(get.call_count, 1 + MAX_POLLS)

    def test_untrusted_job_id_cannot_change_destination(self):
        with patch('transcript_client.requests.get', return_value=self.response(202, {'jobId': '../PRIVATE'})) as get:
            with self.assertRaises(TranscriptError) as raised:
                fetch_native_transcript('video', 'key')
        self.assertEqual(raised.exception.code, 'invalid_response')
        self.assertEqual(get.call_count, 1)

    def test_total_deadline_stops_without_an_extra_request(self):
        with patch('transcript_client.time.monotonic', side_effect=[0, 91]), \
             patch('transcript_client.requests.get') as get:
            with self.assertRaises(TranscriptError) as raised:
                fetch_native_transcript('video', 'key')
        self.assertEqual(raised.exception.code, 'deadline_exceeded')
        get.assert_not_called()

    def test_retry_after_rejects_unusable_values(self):
        for value in (None, '', 'PRIVATE PROVIDER MESSAGE', '-3', 'NaN'):
            self.assertIsNone(retry_after_seconds(value))


class TranscriptSelectionTests(unittest.TestCase):
    def candidates(self, count):
        return [{'id': str(index)} for index in range(count)]

    def test_inaccessible_video_does_not_discard_prior_captions_or_block_later_candidates(self):
        for code in ('access_denied', 'video_unavailable'):
            fetch = Mock(side_effect=['First', None, TranscriptError(code), 'Last', 'Unused'])
            with self.subTest(code=code), patch('transcript_client.time.sleep') as sleep:
                usable, transcripts = collect_transcripts(self.candidates(5), fetch, 2)
            self.assertEqual(usable, [{'id': '0'}, {'id': '3'}])
            self.assertEqual(transcripts, {'0': 'First', '3': 'Last'})
            self.assertEqual(fetch.call_count, 4)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [3, 3, 3])

    def test_available_subset_can_be_used_when_all_remaining_videos_are_inaccessible(self):
        fetch = Mock(side_effect=['Available', TranscriptError('access_denied')])
        with patch('transcript_client.time.sleep'):
            usable, transcripts = collect_transcripts(self.candidates(2), fetch, 3)
        self.assertEqual(usable, [{'id': '0'}])
        self.assertEqual(transcripts, {'0': 'Available'})

    def test_no_usable_caption_and_any_inaccessible_video_raises_instead_of_essay_fallback(self):
        for responses in ([TranscriptError('access_denied'), None],
                          [None, TranscriptError('video_unavailable')]):
            with self.subTest(responses=responses), patch('transcript_client.time.sleep'):
                with self.assertRaises(TranscriptError):
                    collect_transcripts(self.candidates(2), Mock(side_effect=responses), 3)

    def test_confirmed_missing_captions_preserve_existing_fallback(self):
        with patch('transcript_client.time.sleep'):
            self.assertEqual(collect_transcripts(self.candidates(2), lambda _: None, 3), ([], {}))

    def test_account_and_service_errors_still_abort_even_with_usable_captions(self):
        for code in ('authentication_failed', 'quota_exhausted', 'rate_limited', 'provider_unavailable',
                     'timeout', 'invalid_response'):
            fetch = Mock(side_effect=['Available', TranscriptError(code), 'Never fetched'])
            with self.subTest(code=code), patch('transcript_client.time.sleep'):
                with self.assertRaises(TranscriptError) as raised:
                    collect_transcripts(self.candidates(3), fetch, 3)
            self.assertEqual(raised.exception.code, code)
            self.assertEqual(fetch.call_count, 2)


if __name__ == '__main__':
    unittest.main()
