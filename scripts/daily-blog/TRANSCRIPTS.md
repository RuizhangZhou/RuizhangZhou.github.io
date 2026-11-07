# Transcript operations

The writer requests Supadata `mode=native` only. It does not switch to paid AI
transcription. It accepts both segmented captions and plain text, and handles
asynchronous `jobId` results without resubmitting the video during polling.

## Candidate selection

Both entry points use the same caption-selection helper. A restricted or
unavailable individual video (HTTP 403/404) is deferred while other candidates
are checked. Only successfully retrieved captions enter the digest, so deferred
video IDs cannot be marked processed by that digest.

The digest can use fewer videos than its configured maximum. If no usable
captions remain and any candidate had a resource access error, the run stops
instead of writing a title-only essay from an inaccessible source. Confirmed
missing/empty captions and an unconfigured provider retain the existing essay
fallback. Authentication, quota, transport, provider and response-format errors
still stop the run after any applicable bounded recovery.

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
| `captions_unavailable`, `empty_transcript` | Try the next candidate |
| `not_configured` | Preserve the existing essay fallback |
| `access_denied`, `video_unavailable` | Defer the candidate; fail if no verified captions remain |
| `authentication_failed`, `upgrade_required` | Stop and check credentials/access/plan |
| `quota_exhausted` | Stop without retrying monthly allowance exhaustion |
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

The repair adds classified recovery and defers inaccessible candidates. Tests
cover retaining earlier/later captions, keeping failed IDs out of digest input,
stopping when every source is inaccessible, and preserving publication/state
checkpoints on account/service failures. Validate with unit tests and an explicit
`run_actions.py --dry-run` before release. A dry-run generates content using the
configured providers but does not publish or update remote blog state. Do not
rerun a production workflow merely to test transcripts: it can publish today.
