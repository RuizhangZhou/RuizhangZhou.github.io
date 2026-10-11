"""Run the existing writer with private state and checkpointed publication.

No daemon or local /root/llm-gateway dependency. Private Chinese articles,
playlist state and raw model responses never go to public Actions logs/artifacts.
"""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import sys
import time

import httpx
from matrix_state import MatrixKV
from text_limits import bluesky_text

BASE = Path(__file__).resolve().parent


def github_request(method, path, **kwargs):
    response = httpx.request(method, 'https://api.github.com' + path,
                             headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                                      'Accept': 'application/vnd.github+json'}, timeout=30, **kwargs)
    if not response.is_success:
        raise RuntimeError(f'GitHub API HTTP {response.status_code}')
    return response.json()


def find_issue(repo, marker):
    matches = []
    for page in range(1, 11):
        items = github_request('GET', '/repos/' + repo + '/issues',
                               params={'labels': 'blog', 'state': 'all', 'per_page': 100, 'page': page})
        matches.extend(item for item in items if 'pull_request' not in item and marker in (item.get('body') or ''))
        if len(items) < 100:
            break
    if len(matches) > 1:
        raise RuntimeError('Duplicate blog marker requires manual review')
    return matches[0] if matches else None


def publish_issue(store, key, record, repo, date):
    if record.get('issue'):
        return record['issue']
    marker = '<!-- daily-blog-' + date + ' -->'
    existing = find_issue(repo, marker)
    if existing is None:
        if record.get('issue_sending'):
            raise RuntimeError('Uncertain prior GitHub POST; no automatic repost')
        record['issue_sending'] = True
        store.put(key, record)
        body = record['body']
        if marker not in body:
            body += '\n\n' + marker
        existing = github_request('POST', '/repos/' + repo + '/issues',
                                  json={'title': record['title'], 'body': body, 'labels': ['blog', 'bot']})
    record['issue'] = {'number': existing['number'], 'url': existing['html_url']}
    store.put(key, record)
    return record['issue']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--probe', action='store_true', help='Read-only service/auth probe; no article or post')
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    for name in ('config', 'creators'):
        value = json.loads(os.environ['DAILY_BLOG_' + name.upper() + '_JSON'])
        (BASE / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False))
    store = MatrixKV(os.environ['MATRIX_HOMESERVER'], os.environ['MATRIX_BOT_TOKEN'],
                     'com.rickandzoey.dailyblog.v1')
    if store.get('meta') != {'version': 1}:
        raise RuntimeError('Private blog state must be explicitly migrated first')
    for name in ('history', 'digested_videos', 'playlist_cache'):
        value = store.get(name)
        if value is None:
            raise RuntimeError('Missing migrated blog state: ' + name)
        (BASE / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False))
    import daily_blog as blog
    blog.log = lambda message: None
    if args.probe:
        github_request('GET', '/repos/' + blog.REPO)
        blog._bsky('com.atproto.server.createSession', {'identifier': blog.BSKY_ID, 'password': blog.BSKY_PASS})
        from llm_gateway import chat
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = chat([{'role': 'user', 'content': 'Reply only OK.'}],
                          task='blog', max_tokens=64, timeout=60)
        if not result.get('choices'):
            raise RuntimeError('Gateway probe returned no choices')
        print('GitHub access, Bluesky authentication, private Matrix state and shared gateway probe passed; no publishing.')
        return
    # Preserve the former UTC schedule/date. No change to content/model policy.
    blog.TODAY = datetime.now(timezone.utc).date().isoformat()
    today = blog.TODAY
    posts = blog.load_history()
    if any(post.get('date') == today for post in posts):
        print('Today already published according to migrated history; skipped safely.')
        return
    key = 'publication.' + today
    record = store.get(key)
    if record is None:
        # Suppress raw model/provider/transcript errors from public CI output.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            videos = blog.fetch_playlist_videos()
            digested = blog.load_digested_ids()
            candidates = blog.pick_candidate_videos(videos, digested)
            usable, transcripts = [], {}
            for attempt, video in enumerate(candidates):
                if attempt:
                    time.sleep(3)  # Preserve Supadata pacing, including unavailable captions.
                transcript = blog.fetch_transcript(video['id'])
                if transcript:
                    usable.append(video)
                    transcripts[video['id']] = transcript
                if len(usable) >= blog.MAX_DIGEST_CANDIDATES:
                    break
            if usable:
                title, body, title_zh, body_zh, hook, used_ids = blog.generate_video_digest(usable, transcripts, posts)
                domain = 'video-digest'
            else:
                title, body, title_zh, body_zh, domain, hook = blog.generate_post(posts, candidates[0] if candidates else None)
                used_ids = [candidates[0]['id']] if candidates else []
        record = {'title': title, 'body': body, 'title_zh': title_zh, 'body_zh': body_zh,
                  'domain': domain, 'hook': hook, 'used_ids': used_ids,
                  'created_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}
        if not all(isinstance(record[field], str) and record[field].strip() for field in ('title', 'body', 'title_zh', 'body_zh', 'hook')):
            raise RuntimeError('Incomplete generated article')
        if not args.dry_run:
            store.put(key, record)
            store.put('playlist_cache', json.loads(blog.PLAYLIST_CACHE_FILE.read_text()))
    if args.dry_run:
        print('Research dry-run passed; no publishing or remote-state writes. Article content withheld from public logs.')
        return
    issue = publish_issue(store, key, record, blog.REPO, today)
    blog_url = blog.BLOG_BASE + '?id=' + str(issue['number'])
    if not record.get('bluesky_done'):
        session = blog._bsky('com.atproto.server.createSession', {'identifier': blog.BSKY_ID, 'password': blog.BSKY_PASS})
        text, start, end = bluesky_text(record['hook'], blog_url)
        # Stable key: a retry updates this one record, never creates a second post.
        blog._bsky('com.atproto.repo.putRecord', {
            'repo': session['did'], 'collection': 'app.bsky.feed.post', 'rkey': 'daily-' + today,
            'record': {'$type': 'app.bsky.feed.post', 'text': text, 'createdAt': record['created_at'],
                       'facets': [{'index': {'byteStart': start, 'byteEnd': end},
                                   'features': [{'$type': 'app.bsky.richtext.facet#link', 'uri': blog_url}]}]}},
                    token=session['accessJwt'])
        record['bluesky_done'] = True
        store.put(key, record)
    room = os.environ['MATRIX_RICK_ROOM']
    if not record.get('matrix_text_done'):
        store.send(room, record['title_zh'] + '\n今日文章附有 HTML 阅读文件。\n' + blog_url, 'daily-blog-text-' + today)
        record['matrix_text_done'] = True
        store.put(key, record)
    if not record.get('matrix_file_done'):
        path = blog.save_chinese_digest(record['title_zh'], record['body_zh'])
        if not record.get('matrix_media'):
            response = store.client.post(os.environ['MATRIX_HOMESERVER'].rstrip('/') + '/_matrix/media/v3/upload',
                                         params={'filename': path.name}, content=path.read_bytes(),
                                         headers={'Content-Type': 'text/html; charset=utf-8'})
            store.check(response)
            record['matrix_media'] = response.json()['content_uri']
            store.put(key, record)
        store.event(room, {'msgtype': 'm.file', 'body': record['title_zh'] + ' · ' + today,
                          'filename': path.name, 'url': record['matrix_media'],
                          'info': {'mimetype': 'text/html', 'size': path.stat().st_size}}, 'daily-blog-file-' + today)
        record['matrix_file_done'] = True
        store.put(key, record)
    digested = blog.load_digested_ids() | set(record['used_ids'])
    store.put('digested_videos', {'ids': sorted(digested)})
    posts.insert(0, {'date': today, 'title': record['title'], 'domain': record['domain'],
                     'url': blog_url, 'used_video_ids': record['used_ids']})
    store.put('history', {'posts': posts[:blog.MAX_HISTORY_KEPT]})
    print('Publication confirmed: GitHub issue, Bluesky, Matrix text and private HTML; history checkpointed.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('Daily blog failed: ' + type(exc).__name__ + '; private state retained, no raw error/credentials printed.')
        sys.exit(1)
