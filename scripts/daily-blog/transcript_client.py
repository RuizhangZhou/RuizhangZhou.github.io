"""Native captions only, bounded recovery, and content-free public diagnostics."""
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re
import time
from urllib.parse import quote

import requests


API = 'https://api.supadata.ai/v1/transcript'
MAX_ATTEMPTS = 3
MAX_POLLS = 20
TOTAL_TIMEOUT = 90
MAX_RETRY_DELAY = 30
OUTCOME_CODES = {'ok', 'captions_unavailable', 'empty_transcript', 'not_configured'}
ERROR_CODES = {
    'authentication_failed', 'access_denied', 'upgrade_required', 'quota_exhausted',
    'rate_limited', 'limit_exceeded', 'timeout', 'network_error', 'provider_unavailable',
    'video_unavailable', 'invalid_request', 'invalid_response', 'unexpected_redirect',
    'job_failed', 'job_timeout', 'deadline_exceeded',
}


class TranscriptError(RuntimeError):
    def __init__(self, code, *, attempts=0, http_status=None, retryable=False, retry_after=None):
        super().__init__('Transcript service failed; playlist item retained for retry')
        if code not in ERROR_CODES:
            raise ValueError('Unknown transcript error code')
        self.code = code
        self.attempts = attempts
        self.http_status = http_status
        self.retryable = retryable
        self.retry_after = retry_after

    def diagnostics(self):
        result = {'provider': 'supadata', 'code': self.code, 'attempts': self.attempts,
                  'retryable': self.retryable}
        if self.http_status is not None:
            result['http_status'] = self.http_status
        if self.retry_after is not None:
            result['retry_after_seconds'] = self.retry_after
        return result


@dataclass(frozen=True)
class TranscriptResult:
    text: str | None
    code: str
    attempts: int = 0
    http_status: int | None = None

    def diagnostics(self):
        result = {'provider': 'supadata', 'code': self.code, 'attempts': self.attempts}
        if self.http_status is not None:
            result['http_status'] = self.http_status
        return result


def provider_error(payload):
    """Accept the documented flat error and the nested error on failed jobs."""
    error = payload.get('error')
    if isinstance(error, dict):
        return error.get('error', error.get('code')), error.get('details')
    return error, payload.get('details')


def retry_after_seconds(value):
    if not isinstance(value, str):
        return None
    try:
        if value.strip().isdigit():
            return int(value.strip())
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            return None
        return max(0, int((date - datetime.now(timezone.utc)).total_seconds()) + 1)
    except (ValueError, TypeError, OverflowError):
        return None


class NativeTranscriptClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.attempts = 0
        self.http_status = None
        self.deadline = time.monotonic() + TOTAL_TIMEOUT

    def error(self, code, *, retryable=False, retry_after=None):
        return TranscriptError(code, attempts=self.attempts, http_status=self.http_status,
                               retryable=retryable, retry_after=retry_after)

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise self.error('deadline_exceeded', retryable=True)
        return remaining

    def response_error(self, status, payload, retry_after):
        code, details = provider_error(payload)
        if status == 401 or code == 'unauthorized':
            return self.error('authentication_failed')
        if status == 402 or code == 'upgrade-required':
            return self.error('upgrade_required')
        if status == 403 or code == 'forbidden':
            return self.error('access_denied')
        if status == 429 or code == 'limit-exceeded':
            if details == 'Plan usage limit was exceeded.':
                return self.error('quota_exhausted')
            if details in ('Global request rate limit was exceeded.',
                           'Request rate limit on current plan was exceeded.'):
                return self.error('rate_limited', retryable=True, retry_after=retry_after)
            # A bare 429 does not distinguish exhausted credits from a rate limit.
            return self.error('limit_exceeded', retry_after=retry_after)
        if 500 <= status <= 599 or code in ('internal-error', 'upstream-error'):
            return self.error('provider_unavailable', retryable=True, retry_after=retry_after)
        if status == 404 or code == 'not-found':
            return self.error('video_unavailable')
        if status == 400 or code == 'invalid-request':
            return self.error('invalid_request')
        if 300 <= status <= 399:
            return self.error('unexpected_redirect')
        return self.error('invalid_response')

    def request(self, url, params=None):
        for attempt in range(MAX_ATTEMPTS):
            timeout = min(30, self.remaining())
            self.attempts += 1
            self.http_status = None
            try:
                response = requests.get(url, params=params, headers={'x-api-key': self.api_key},
                                        timeout=timeout, allow_redirects=False)
                self.http_status = response.status_code
                try:
                    payload = response.json()
                except ValueError:
                    payload = None
                valid_payload = isinstance(payload, dict)
                safe_payload = payload if valid_payload else {}
                code, _ = provider_error(safe_payload)
                missing = code == 'transcript-unavailable' and response.status_code in (200, 206, 404)
                if missing or (response.status_code in (200, 202) and valid_payload and not code):
                    return payload
                delay = retry_after_seconds(response.headers.get('Retry-After'))
                error = self.response_error(response.status_code, safe_payload, delay)
            except requests.Timeout:
                error = self.error('timeout', retryable=True)
            except requests.RequestException:
                error = self.error('network_error', retryable=True)
            delay = max(3 * 2 ** attempt, error.retry_after or 0)
            if (not error.retryable or attempt == MAX_ATTEMPTS - 1
                    or delay > MAX_RETRY_DELAY or delay >= self.remaining()):
                raise error from None
            time.sleep(delay)
        raise AssertionError('Unreachable retry loop')

    def result(self, payload):
        code, _ = provider_error(payload)
        if code == 'transcript-unavailable':
            return TranscriptResult(None, 'captions_unavailable', self.attempts, self.http_status)
        content = payload.get('content')
        if isinstance(content, str):
            text = content.strip()
        elif isinstance(content, list) and all(isinstance(segment, dict) and isinstance(segment.get('text'), str)
                                             for segment in content):
            text = ' '.join(segment['text'] for segment in content).strip()
        else:
            raise self.error('invalid_response')
        return TranscriptResult(text or None, 'ok' if text else 'empty_transcript',
                                self.attempts, self.http_status)

    def fetch(self, video_id):
        payload = self.request(API, {'url': f'https://youtu.be/{video_id}', 'mode': 'native'})
        job_id = payload.get('jobId')
        if job_id is None:
            return self.result(payload)
        if not isinstance(job_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}', job_id):
            raise self.error('invalid_response')
        for _ in range(MAX_POLLS):
            if self.remaining() <= 3:
                raise self.error('job_timeout', retryable=True)
            time.sleep(3)
            payload = self.request(API + '/' + quote(job_id, safe=''))
            code, _ = provider_error(payload)
            if code == 'transcript-unavailable':
                return self.result(payload)
            status = payload.get('status')
            if status == 'completed':
                return self.result(payload)
            if status not in ('queued', 'active'):
                raise self.error('job_failed' if status == 'failed' else 'invalid_response')
        raise self.error('job_timeout', retryable=True)


def fetch_native_transcript(video_id, api_key):
    if not api_key:
        return TranscriptResult(None, 'not_configured')
    return NativeTranscriptClient(api_key).fetch(video_id)


def collect_transcripts(candidates, fetch, maximum_usable):
    """Defer inaccessible videos; only verified captions can feed a digest."""
    transcripts = {}
    deferred_error = None
    for attempt, video in enumerate(candidates):
        if len(transcripts) >= maximum_usable:
            break
        if attempt:
            time.sleep(3)
        try:
            text = fetch(video['id'])
        except TranscriptError as exc:
            if exc.code not in ('access_denied', 'video_unavailable'):
                raise
            deferred_error = exc
            continue
        if text:
            transcripts[video['id']] = text
    if not transcripts and deferred_error is not None:
        # Restricted sources must not become title-only essays or consumed IDs.
        raise deferred_error
    usable = [video for video in candidates if video['id'] in transcripts]
    return usable, transcripts
