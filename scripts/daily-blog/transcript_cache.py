"""Bounded private caption cache shared by otherwise ephemeral Actions workers."""
from copy import deepcopy
import math
import re
import time

from transcript_client import TranscriptError, TranscriptResult


INDEX_KEY = 'transcript_cache.index'
POSITIVE_TTL = 30 * 24 * 60 * 60
NEGATIVE_TTL = 7 * 24 * 60 * 60
MAX_ENTRIES = 128
MAX_TEXT_CHARS = 60000
CHUNK_CHARS = 4000  # Fits below 48 KiB even with JSON-escaped supplementary Unicode.
MAX_CHUNKS = (MAX_TEXT_CHARS + CHUNK_CHARS - 1) // CHUNK_CHARS
MISSING_CODES = {'captions_unavailable', 'empty_transcript'}
RESOURCE_CODES = {'access_denied', 'video_unavailable'}


class TranscriptCache:
    def __init__(self, store, *, readonly=False, clock=time.time):
        self.store = store
        self.readonly = readonly
        self.clock = clock
        self.overlay = {}
        document = store.get(INDEX_KEY)
        if document is None or document == {}:
            document = {'version': 1, 'entries': {}}
        if (not isinstance(document, dict) or document.get('version') != 1
                or not isinstance(document.get('entries'), dict)):
            raise RuntimeError('Invalid private transcript cache index')
        self.entries = deepcopy(document['entries'])
        for video_id, entry in self.entries.items():
            self.validate_entry(video_id, entry)

    @staticmethod
    def validate_entry(video_id, entry):
        if (not isinstance(video_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', video_id)
                or not isinstance(entry, dict)
                or not isinstance(entry.get('code'), str)
                or entry['code'] not in MISSING_CODES | RESOURCE_CODES | {'ok', 'writing'}
                or type(entry.get('expires_at')) not in (int, float)
                or not math.isfinite(entry['expires_at'])
                or type(entry.get('chunks')) is not int or not 0 <= entry['chunks'] <= MAX_CHUNKS
                or (entry['code'] == 'ok' and entry['chunks'] == 0)
                or (entry['code'] in MISSING_CODES | RESOURCE_CODES and entry['chunks'] != 0)
                or (entry.get('http_status') is not None
                    and (type(entry['http_status']) is not int or not 100 <= entry['http_status'] <= 599))):
            raise RuntimeError('Invalid private transcript cache entry')

    @staticmethod
    def chunk_key(video_id, part):
        return f'transcript_cache.video.{video_id}.{part}'

    def get(self, key):
        if key in self.overlay:
            return self.overlay[key]
        return self.store.get(key)

    def put(self, key, value):
        if not self.readonly:
            self.store.put(key, value)
        self.overlay[key] = deepcopy(value)

    def save_index(self):
        self.put(INDEX_KEY, {'version': 1, 'entries': self.entries})

    def remove(self, video_id):
        entry = self.entries[video_id]
        for part in range(entry['chunks']):
            # Empty account data clears the current payload without a server-admin API.
            self.put(self.chunk_key(video_id, part), {})
        del self.entries[video_id]
        self.save_index()

    def prune(self, consumed_ids=()):
        consumed = set(consumed_ids)
        now = self.clock()
        for video_id, entry in list(self.entries.items()):
            if video_id in consumed or entry['expires_at'] <= now or entry['code'] == 'writing':
                self.remove(video_id)
        while len(self.entries) > MAX_ENTRIES:
            self.remove(min(self.entries, key=lambda key: self.entries[key]['expires_at']))

    def cached_result(self, video_id):
        entry = self.entries.get(video_id)
        if entry is None:
            return None
        if entry['expires_at'] <= self.clock() or entry['code'] == 'writing':
            self.remove(video_id)
            return None
        code, status = entry['code'], entry.get('http_status')
        if code in RESOURCE_CODES:
            raise TranscriptError(code, http_status=status, cached=True)
        if code in MISSING_CODES:
            return TranscriptResult(None, code, http_status=status, cached=True)
        parts = [self.get(self.chunk_key(video_id, part)) for part in range(entry['chunks'])]
        if not parts or any(not isinstance(part, dict) or not isinstance(part.get('text'), str)
                            or len(part['text']) > CHUNK_CHARS for part in parts):
            self.remove(video_id)
            return None
        text = ''.join(part['text'] for part in parts)
        if not text.strip() or len(text) > MAX_TEXT_CHARS:
            self.remove(video_id)
            return None
        return TranscriptResult(text, 'ok', http_status=status, cached=True)

    def save(self, video_id, code, text=None, http_status=None):
        text = text[:MAX_TEXT_CHARS] if text else ''
        parts = [text[start:start + CHUNK_CHARS] for start in range(0, len(text), CHUNK_CHARS)]
        entry = {'code': code, 'expires_at': self.clock() + (POSITIVE_TTL if code == 'ok' else NEGATIVE_TTL),
                 'chunks': len(parts), 'http_status': http_status}
        self.validate_entry(video_id, entry)
        if video_id in self.entries:
            self.remove(video_id)
        while len(self.entries) >= MAX_ENTRIES:
            self.remove(min(self.entries, key=lambda key: self.entries[key]['expires_at']))
        # Register cleanup information BEFORE writing chunks. An interrupted write
        # is discarded next run instead of leaving untracked caption payloads.
        self.entries[video_id] = {**entry, 'code': 'writing'}
        self.save_index()
        for part, content in enumerate(parts):
            self.put(self.chunk_key(video_id, part), {'text': content})
        self.entries[video_id] = entry
        self.save_index()

    def fetch(self, video_id, fetch_native):
        cached = self.cached_result(video_id)
        if cached is not None:
            return cached
        try:
            result = fetch_native(video_id)
        except TranscriptError as exc:
            if exc.code in RESOURCE_CODES:
                self.save(video_id, exc.code, http_status=exc.http_status)
            raise
        if result.code == 'ok' or result.code in MISSING_CODES:
            self.save(video_id, result.code, result.text, result.http_status)
        return result


def probe_private_cache(store):
    """Verify persistence/cleanup in a dedicated synthetic namespace, without Supadata."""
    video_id = 'synthetic_storage_probe'
    requests = 0

    def synthetic_caption(_):
        nonlocal requests
        requests += 1
        return TranscriptResult('Synthetic caption storage check.', 'ok')

    cache = TranscriptCache(store)
    cache.prune({video_id})
    try:
        first = cache.fetch(video_id, synthetic_caption)
        second = TranscriptCache(store).fetch(video_id, synthetic_caption)
        if first.text != second.text or not second.cached or requests != 1:
            raise RuntimeError('Private caption cache persistence check failed')
    finally:
        TranscriptCache(store).prune({video_id})
    if store.get(TranscriptCache.chunk_key(video_id, 0)) not in (None, {}):
        raise RuntimeError('Private caption cache cleanup check failed')
