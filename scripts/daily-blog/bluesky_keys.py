"""Stable per-day record keys conforming to app.bsky.feed.post's TID schema."""
from datetime import date
import hashlib

ALPHABET = '234567abcdefghijklmnopqrstuvwxyz'
CLOCK_ID = int.from_bytes(hashlib.sha256(b'ruizhangzhou.daily-blog.v1').digest()[:2], 'big') & 1023


def daily_post_rkey(day):
    """UTC midnight + a fixed publisher clock: stable across processes/retries.

    TID: 53 timestamp-microsecond bits followed by 10 clock-ID bits, encoded
    as exactly 13 base32-sortable characters. These are per-account/collection
    identifiers, not globally unique IDs. https://atproto.com/specs/tid
    """
    parsed = date.fromisoformat(day)
    if parsed.isoformat() != day:
        raise ValueError('Publication date must be canonical YYYY-MM-DD')
    micros = (parsed - date(1970, 1, 1)).days * 86400 * 1000000
    if not 0 <= micros < 2 ** 53:
        raise ValueError('Publication date outside TID timestamp range')
    value = (micros << 10) | CLOCK_ID
    result = ''
    for _ in range(13):
        result = ALPHABET[value & 31] + result
        value >>= 5
    return result
