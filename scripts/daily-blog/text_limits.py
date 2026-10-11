"""Unicode-safe limits for Bluesky text and its UTF-8 link facets."""
import regex


def truncate_text(text, max_graphemes=220, max_bytes=3000):
    clusters = regex.findall(r'\X', text)
    if len(clusters) <= max_graphemes and len(text.encode('utf-8')) <= max_bytes:
        return text
    if max_graphemes < 1 or max_bytes < 3:
        raise ValueError('Insufficient text budget')
    kept, size = [], 0
    for cluster in clusters:
        cluster_size = len(cluster.encode('utf-8'))
        if len(kept) >= max_graphemes - 1 or size + cluster_size > max_bytes - 3:
            break
        kept.append(cluster)
        size += cluster_size
    return ''.join(kept) + '…'


def bluesky_text(hook, url):
    suffix = '\n\n' + url
    remaining = 300 - len(regex.findall(r'\X', suffix))
    remaining_bytes = 3000 - len(suffix.encode('utf-8'))
    if remaining < 1 or remaining_bytes < 3:
        raise ValueError('Blog URL exceeds Bluesky text budget')
    hook = truncate_text(hook, min(220, remaining), remaining_bytes)
    text = hook + suffix
    start = len(hook.encode('utf-8')) + 2
    return text, start, start + len(url.encode('utf-8'))
