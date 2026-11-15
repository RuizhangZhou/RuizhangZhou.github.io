"""Export video IDs and caption/publication states to a private local JSON file."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from matrix_state import MatrixKV
from transcript_cache import TranscriptCache


def read_video_status(store, *, now=None):
    """GET-only view; clearing a caption must never erase the consumed-ID ledger."""
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    history = store.get('history')
    digested = store.get('digested_videos')
    playlist = store.get('playlist_cache')
    if not all(isinstance(value, dict) for value in (history, digested, playlist)):
        raise RuntimeError('Missing private blog state')
    consumed = set(digested['ids'])
    dates = {}
    for post in history['posts']:
        for video_id in post.get('used_video_ids', []):
            dates.setdefault(video_id, []).append(post['date'])
    cache = TranscriptCache(store, readonly=True)
    playlist_ids = {video['id'] for video in playlist['videos']}
    video_ids = consumed | dates.keys() | playlist_ids | cache.entries.keys()
    rows = []
    for video_id in sorted(video_ids):
        entry = cache.entries.get(video_id)
        status, expires_at = 'not_cached', None
        if entry is not None:
            status = entry['code']
            expires_at = datetime.fromtimestamp(entry['expires_at'], timezone.utc).isoformat()
            if entry['expires_at'] <= now:
                status = 'expired'
        rows.append({'video_id': video_id, 'youtube_url': 'https://www.youtube.com/watch?v=' + video_id,
                     'used_in_article': video_id in consumed or video_id in dates,
                     'publication_dates': sorted(dates.get(video_id, [])),
                     'in_latest_playlist': video_id in playlist_ids,
                     'caption_cache_status': status, 'cache_expires_at': expires_at})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='Private local JSON destination; video IDs are never printed')
    args = parser.parse_args()
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        raise RuntimeError('Export video state privately, outside public Actions')
    from dotenv import load_dotenv
    load_dotenv(Path.home() / '.env', override=False)
    store = MatrixKV(os.environ['MATRIX_HOMESERVER'], os.environ['MATRIX_BOT_TOKEN'],
                     'com.rickandzoey.dailyblog.v1')
    rows = read_video_status(store)
    document = {'generated_at': datetime.now(timezone.utc).isoformat(),
                'source': 'Private Matrix blog account data', 'videos': rows}
    # Create a private file; require an explicit new destination to avoid overwriting a prior export.
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as output:
        json.dump(document, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(f'Exported {len(rows)} video status rows to the requested private file.')


if __name__ == '__main__':
    main()
