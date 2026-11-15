# Transcript operations

The writer requests Supadata `mode=native` only. It does not switch to paid AI
transcription. It accepts both segmented captions and plain text, and handles
asynchronous `jobId` results without resubmitting the video during polling.

## Candidate selection

Both entry points use the same caption-selection helper. A restricted or
unavailable individual video (HTTP 403/404) is deferred while other candidates
are checked. Only successfully retrieved captions enter the digest, so deferred
video IDs cannot be marked processed by that digest.

The digest can use fewer videos than its configured maximum. If no verified
captions remain, missing/empty/inaccessible resources or an exhausted caption
allowance permit a playlist-inspired essay from the selected video's available
title, creator and description. The prompt prohibits claiming to have watched or
quoting the video without a transcript; both language versions receive an explicit
metadata-only source note. This is an essay, not a spoken-content summary.
Authentication, rate limits, transport, provider and response-format errors still
stop the run after any applicable bounded recovery.

## Private persistent cache (Actions)

The production Actions runner reuses the bot's existing private Matrix account
data, under `com.rickandzoey.dailyblog.v1.transcript_cache.*`. Captions are never
committed to Git, uploaded as public Actions artifacts, or sent as room messages.
The next ephemeral runner can read the same cache without depending on FSN.

| Cached result | Retention / next check |
| --- | --- |
| Usable native captions | 30 days from retrieval; reading does not extend retention |
| Confirmed missing or empty captions | Remember indefinitely; no automatic recheck |
| Inaccessible / unavailable resource (403/404) | Remember separately as a resource restriction; no automatic recheck |
| Quota, credentials, rate limits, transport or malformed responses | Never cached as absent captions |

Fresh outcomes are saved immediately, before article generation. Captions that
the model does not select remain reusable; a later generation/publication
failure also leaves them available. Only article-confirmed IDs are consumed,
as before. After publication and history checkpointing, their caption payloads
are cleared. No video becomes consumed merely because its captions were fetched.

Negative decisions are metadata, not temporary caption text. They live under
`com.rickandzoey.dailyblog.v1.transcript_decisions.*`, partitioned across 16 lazy
buckets. They are never expired, capacity-evicted or removed merely because the
video leaves the current playlist or is used for an essay. A maintainer can
explicitly call `TranscriptDecisions.forget(video_id)` to allow a user-requested
recheck. Missing captions and access restrictions remain distinct labels.
The old 7-day cache entries migrate directly, including expired ones, without
another Supadata request. Success-cache cleanup does not clear this registry.

At the start of every normal blog run, including an already-published day, the
worker removes expired, consumed and interrupted caption-text entries. It holds at
most 128 text entries and evicts the earliest expiry if full. Captions use the writer's existing
60,000-character cap and small chunks so large/multibyte payloads fit conservative
per-request size limits. A pending index entry is written before the chunks, so
an interrupted write can be cleaned up on the next run.

Cleanup replaces current Matrix chunk payloads with `{}` and removes their index
entries. It does not promise deletion from homeserver backups or physical media.
It never clears `digested_videos` or article history: the consumed-video ID ledger
is independent of the temporary caption cache and continues preventing reuse.
The existing daily workflow owns cleanup; no separate timer is installed, so a
disabled workflow cannot clean until it runs again. The legacy standalone writer
does not acquire this Actions-specific remote store automatically.

`--dry-run` reads existing entries and maintains only an in-memory overlay;
it never saves or cleans production cache entries. Uncached dry-run videos still
use real native-caption requests. Diagnostics distinguish hits using `cached:
true` and `attempts: 0`, never caption text or video IDs.

For an ID-by-ID overview, run `video_status.py --output <new-private-file.json>`
on an authorized personal machine with the existing Matrix credentials. It uses
GET requests only, separates publication dates from caption-cache outcomes, and
includes older consumed IDs even when their article dates are no longer in the
60-entry history, and remembered no-caption IDs that have left the playlist.
It exports IDs to a new private file, never to public Actions logs; expired text
cache entries are reported without performing cleanup. Before the
cache is deployed, absent cache data cannot establish whether a video was ever
checked historically.

After deploying, the workflow's `cache_probe=true` input (or the CLI's
`--cache-probe`) verifies a synthetic caption in the separate
`com.rickandzoey.dailyblog.cache_probe.v1` account-data namespace. It reads the
caption back through a fresh cache instance, verifies reuse without another
fetch, and clears the synthetic payload. This check does not call Supadata,
generate an article, read/change publication state or publish a test post.

`caption_maintenance=true` (CLI `--caption-maintenance`) migrates production
negative metadata and reads safe account counters from Supadata `/v1/me`. It
prints outcome counts and credit totals only, not video IDs or credentials. It
does not fetch captions, call a model or publish anything.

## Optional second key

`SUPADATA_SECONDARY_API_KEY` is an optional Actions Secret. Leave it unset to
continue using only `SUPADATA_API_KEY`. Different keys in the same organization
share the same allowance; maintenance reports whether two keys share a pool.
Only an explicitly classified `quota_exhausted` switches keys. The preferred
slot (never the key) is stored privately and reused next run. When that allowance
exhausts, the other slot is tried again, allowing a monthly reset to restore it.
Each configured key is tried at most once per video; after all are exhausted,
this provider instance makes no further caption requests during the run. Cached
captions remain usable and a metadata essay remains possible. No video is marked
captionless because credits ran out. Dry-runs never persist key preference.

## Recovery limits

Each HTTP operation allows at most three attempts. Retryable failures wait 3 and
6 seconds; a larger valid `Retry-After` is respected. A requested wait longer than
30 seconds stops recovery instead of retrying too early. A video's 90-second
budget is checked before requests/waits, and socket timeouts use the remaining
budget. Async jobs are polled at most 20 times. Pacing between videos remains
three seconds. Redirects are disabled so the API key is not forwarded elsewhere.

## Public diagnostics

The final `Transcript outcomes` line contains at most eight fixed-code records,
with request counts and HTTP status. The failure summary also reports
retryability and a parsed retry delay when available. Neither log includes video
IDs, titles, URLs, captions, provider messages, response bodies or credentials.

| Code | Handling |
| --- | --- |
| `ok` | Use the verified captions |
| `captions_unavailable`, `empty_transcript` | Remember permanently; try the next candidate or a metadata essay |
| `not_configured` | Preserve the existing essay fallback |
| `access_denied`, `video_unavailable` | Remember resource restriction; try another candidate or a disclosed metadata essay |
| `authentication_failed`, `upgrade_required` | Stop and check credentials/access/plan |
| `quota_exhausted` | Try the other configured key once; then use cache/metadata without further caption calls |
| `rate_limited` | Bounded backoff, honoring `Retry-After` |
| `limit_exceeded` | Stop; an ambiguous 429 cannot establish quota versus rate limit |
| `timeout`, `network_error`, `provider_unavailable` | Bounded retry, then stop |
| `invalid_request`, `invalid_response`, `unexpected_redirect` | Stop without treating the response as missing captions |
| `job_failed`, `job_timeout`, `deadline_exceeded` | Stop and retain the video |

Quota/rate classification uses the exact documented allowlisted `details`
strings. Unknown provider details are never logged or promoted into a diagnosis.
See Supadata's [error reference](https://docs.supadata.ai/errors/list),
[quota/rate distinction](https://docs.supadata.ai/errors/limit-exceeded),
[forbidden resources](https://docs.supadata.ai/errors/forbidden) and
[native/async contract](https://docs.supadata.ai/get-transcript).

## Incident and verification

The [November 6 run](https://github.com/RuizhangZhou/RuizhangZhou.github.io/actions/runs/42254686899)
failed at `transcripts` after its 40 unit tests passed. Its legacy parser flattened
all failures into a generic `RuntimeError`. A read-only November 7 reproduction
retrieved usable captions before a later candidate returned Supadata `forbidden`
(HTTP 403), aborting the entire selection. That reproduction establishes a
blocking case; the earlier sanitized logs cannot identify each historical
provider response.

The November 7 repair added classified recovery and deferred inaccessible
candidates. The November 15 policy change also permits disclosed metadata essays
when no captions can be retrieved. Tests cover retaining verified captions,
permanent negative records, migrating old cache entries without paid probes,
bounded key failover, and preserving publication/state checkpoints on failures.
Validate with unit tests and an explicit
`run_actions.py --dry-run` before release. A dry-run generates content using the
configured providers but does not publish or update remote blog state. Do not
rerun a production workflow merely to test transcripts: it can publish today.
