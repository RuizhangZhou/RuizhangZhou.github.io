"""Use a second native-caption key only after an explicitly exhausted allowance."""
from dataclasses import replace

import requests

from transcript_client import TranscriptError, TranscriptResult, fetch_native_transcript


PREFERENCE_KEY = 'supadata_key_preference'


class NativeCaptionProvider:
    def __init__(self, primary, secondary=None, *, state=None):
        self.keys = {slot: key for slot, key in (('primary', primary), ('secondary', secondary)) if key}
        if primary and secondary == primary:
            self.keys.pop('secondary')
        self.state = state
        self.exhausted = False
        self.exhausted_slots = set()
        saved = state.get(PREFERENCE_KEY) if state is not None and len(self.keys) > 1 else None
        preferred = saved.get('slot') if isinstance(saved, dict) else None
        self.preferred = preferred if preferred in self.keys else next(iter(self.keys), None)

    def fetch(self, video_id):
        if self.exhausted:
            raise TranscriptError('quota_exhausted')
        if not self.keys:
            return TranscriptResult(None, 'not_configured')
        ordered = [self.preferred] + [slot for slot in self.keys if slot != self.preferred]
        slots = [slot for slot in ordered if slot not in self.exhausted_slots]
        attempts = 0
        for index, slot in enumerate(slots):
            try:
                result = fetch_native_transcript(video_id, self.keys[slot])
            except TranscriptError as exc:
                exc.attempts += attempts
                if exc.code != 'quota_exhausted':
                    raise
                self.exhausted_slots.add(slot)
                if index == len(slots) - 1:
                    self.exhausted = True
                    raise
                attempts = exc.attempts
                self.preferred = slots[index + 1]
                if self.state is not None:
                    self.state.put(PREFERENCE_KEY, {'slot': self.preferred})
                continue
            return replace(result, attempts=result.attempts + attempts)

    def usage_summary(self):
        """Read account counters only; never output keys, account IDs or provider bodies."""
        result, organizations = [], []
        for slot, key in self.keys.items():
            try:
                response = requests.get('https://api.supadata.ai/v1/me', headers={'x-api-key': key},
                                        timeout=25, allow_redirects=False)
                response.raise_for_status()
                data = response.json()
                maximum, used = data.get('maxCredits'), data.get('usedCredits')
                if type(maximum) is not int or type(used) is not int or maximum < 0 or used < 0:
                    raise ValueError('Invalid account counters')
                result.append({'slot': slot, 'max_credits': maximum, 'used_credits': used})
                organizations.append(data.get('organizationId'))
            except (requests.RequestException, ValueError, TypeError, AttributeError):
                result.append({'slot': slot, 'account_read_failed': True})
        shared = None
        if len(organizations) == 2 and all(isinstance(value, str) for value in organizations):
            shared = organizations[0] == organizations[1]
        return {'accounts': result, 'shared_quota_pool': shared}
