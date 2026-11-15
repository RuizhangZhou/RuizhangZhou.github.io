"""Permanent metadata-only caption decisions, separate from expiring caption text."""
from copy import deepcopy
import hashlib
import math
import re
import time


DECISION_CODES = {'captions_unavailable', 'empty_transcript', 'access_denied', 'video_unavailable'}
BUCKETS = '0123456789abcdef'


class TranscriptDecisions:
    def __init__(self, store, *, clock=time.time):
        self.store, self.clock = store, clock
        self.buckets = {}

    @staticmethod
    def bucket_for(video_id):
        if not isinstance(video_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', video_id):
            raise RuntimeError('Invalid caption decision ID')
        return hashlib.sha256(video_id.encode()).hexdigest()[0]

    def load(self, bucket):
        if bucket not in self.buckets:
            document = self.store.get('transcript_decisions.' + bucket)
            if document is None or document == {}:
                document = {'version': 1, 'entries': {}}
            if (not isinstance(document, dict) or document.get('version') != 1
                    or not isinstance(document.get('entries'), dict)):
                raise RuntimeError('Invalid caption decision registry')
            for video_id, entry in document['entries'].items():
                if (self.bucket_for(video_id) != bucket or not isinstance(entry, dict)
                        or not isinstance(entry.get('code'), str) or entry['code'] not in DECISION_CODES
                        or type(entry.get('checked_at')) not in (int, float)
                        or not math.isfinite(entry['checked_at'])
                        or (entry.get('http_status') is not None
                            and (type(entry['http_status']) is not int or not 100 <= entry['http_status'] <= 599))):
                    raise RuntimeError('Invalid caption decision metadata')
            self.buckets[bucket] = deepcopy(document['entries'])
        return self.buckets[bucket]

    def get(self, video_id):
        return self.load(self.bucket_for(video_id)).get(video_id)

    def remember(self, video_id, code, http_status=None, *, checked_at=None):
        if code not in DECISION_CODES:
            raise ValueError('Only confirmed caption/resource decisions can be remembered')
        bucket = self.bucket_for(video_id)
        entries = self.load(bucket)
        entries[video_id] = {'code': code, 'http_status': http_status,
                             'checked_at': self.clock() if checked_at is None else checked_at}
        self.store.put('transcript_decisions.' + bucket, {'version': 1, 'entries': entries})

    def forget(self, video_id):
        """Explicit maintenance only: permit a user-requested recheck of this ID."""
        bucket = self.bucket_for(video_id)
        entries = self.load(bucket)
        if video_id in entries:
            del entries[video_id]
            self.store.put('transcript_decisions.' + bucket, {'version': 1, 'entries': entries})

    def all_entries(self):
        return {video_id: entry for bucket in BUCKETS for video_id, entry in self.load(bucket).items()}
