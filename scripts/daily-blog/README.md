# Daily blog on GitHub Actions

Migrates `/root/daily-blog/daily_blog.py` without changing the existing writing
prompts or model-routing policy. `run_actions.py` reuses its research/generation
functions, not the old non-idempotent publication entry point.

Schedule: **09:00 UTC daily** (Berlin 11:00 CEST / 10:00 CET), unchanged.
Public English article -> GitHub issue with blog/bot labels -> Bluesky;
private Chinese article -> Matrix HTML attachment. Mastodon remains paused.

The workflow installs public `RuizhangZhou/llm-gateway` at audited compatibility
commit `eeed89c95a317f279494fa27c0c44dfe5712d791` (gateway PR #1 fixes non-root
imports and optional server env loading). **Model routing still follows the
latest master/config/routing.yaml**, independently of the pinned code version.
The existing fsn refresh timer continues
updating/publishing that config; fsn is not the article execution host anymore
after cutover. No server filesystem dependency is required in the new runner.

Secrets: `DAILY_BLOG_CONFIG_JSON`, `DAILY_BLOG_CREATORS_JSON`, `KICONNECT_API_KEY`,
optional `AZURE_OPENAI_API_KEY`, `BSKY_APP_PASSWORD`, optional `SUPADATA_API_KEY`,
`MATRIX_HOMESERVER`, `MATRIX_BOT_TOKEN`, `MATRIX_RICK_ROOM`.
Variables: public `BSKY_IDENTIFIER`, optional non-secret `AZURE_OPENAI_BASE_URL`.
`GH_TOKEN` uses the temporary workflow token with issues:write for this repo;
no personal GitHub token is copied to Actions. Provider keys never go in Variables.
`MATRIX_HOMESERVER` deliberately stays in Secrets too: infrastructure addresses
need not be public configuration. This is not an API key/Variables requirement.

Private Matrix account data `com.rickandzoey.dailyblog.v1` stores existing history,
processed video IDs, playlist cache and exact pending publication content/stages.
The namespace version marker is initialized explicitly only after all three
state documents are migrated. One writer only (workflow concurrency). Missing
state fails closed. No private Chinese article, cache, profile or raw provider
error is uploaded as a public artifact or printed to public logs. Runtime files
are ignored by Git. Private content is still sent to the same configured model
providers as before, including the existing Azure fallback if configured.

Generation is checkpointed before publishing. GitHub issues reconcile an exact
date marker; an ambiguous POST with no read-back match requires manual review,
not a blind second POST. Bluesky uses a stable per-day record key. Matrix uses
stable per-day text/file transaction IDs and saves the media URI. Completed
stages resume without rerunning the model. No unlimited exactly-once guarantee.

Bluesky feed posts require a TID record key, not merely a syntactically valid
generic key. `bluesky_keys.daily_post_rkey` encodes UTC midnight and a fixed
publisher clock ID into a stable 13-character TID for each publication date.
The selected key is checkpointed before posting, and retries reuse it; completed
Bluesky stages are skipped. Schema: https://github.com/bluesky-social/atproto/blob/main/lexicons/app/bsky/feed/post.json
TID specification: https://atproto.com/specs/tid

## Deployment / cutover

1. Configure the listed Secrets/Variables using stdin, never visible shell args.
2. Migrate `history.json`, `digested_videos.json`, `playlist_cache.json` privately.
3. Merge only after explicit user authorization for this PR; fsn's gh launcher
   is transparent and the authorization policy lives in AGENTS.md/the merge skill.
4. Immediately before switching, refresh the private state from the still-running
   server job. Re-check that today's article has already shipped; don't publish
   an extra public test article just for migration.
5. Run `daily-blog.yml` with `dry_run=true`; require success. Check that source
   routing and provider authentication work from the hosted runner.
6. Disable **only** the old daily-blog cron line after validation. Keep all
   unrelated and intentionally paused entries unchanged. Next daily publication
   must confirm GitHub, Bluesky and Matrix stages.

Until cutover is explicitly recorded, the original server cron remains active.
Repository Variable `DAILY_BLOG_ENABLED` is initially false: scheduled publication
stays off even after merge, while manual dispatch remains available for validation.
Only set it true after fresh state synchronization and disabling the old cron.
If a gap exists between state migration and cutover, state MUST be re-synced.
Rollback: disable Actions first, export current private state to server files,
then restore only the original daily-blog cron line. Never restore a stale file
snapshot and run two publishers concurrently.

Actions may delay scheduled runs; public scheduled workflows can be disabled
after 60 inactive days. Check Actions if posts stop. Private-state/provider
failures fail the run visibly. Unit tests have no credentials or real posting.

## Review hardening

Public issue bodies are sanitized with pinned DOMPurify before the blog inserts
HTML; private HTML attachments use nh3 after Markdown rendering. Raw scripts,
event handlers and dangerous URL schemes are not trusted model output. KaTeX
still renders math after sanitization. Browser regression tests live in
`browser-tests` (`npm ci && npm test`, Node 24).

Bluesky hooks use grapheme-aware truncation; final text reserves space for the
actual URL and checks both the 300-grapheme and 3000-byte limits, retaining UTF-8
facet offsets. Transcript probes keep the former three-second pacing. Temporary
Supadata failures abort without publishing an essay or marking videos consumed;
confirmed unavailable native captions may still use the original fallback.

## Generation reliability

High reasoning consumes output budget as well as article text. Essay mode now
reserves 12,000 output tokens and transcript digest mode 16,000, retaining the
same prompts, high reasoning policy and shared model routing. A response ending
with `finish_reason=length` is discarded and regenerated once from the original
prompt with twice that budget (24,000 / 32,000). No partial outputs are joined.
The larger limit is a ceiling, not a requirement to use all those tokens.

Only a normal completed response with every required section exactly once, in
order and nonempty can reach the publication checkpoint. Further truncation,
refusal, malformed output or provider failures stop without consuming videos or
publishing. Existing publication checkpoints and deduplication remain unchanged.

Public failure diagnostics include only a fixed stage, exception class, safe
generation error code and HTTP status when available, never exception messages,
provider response bodies, prompts or Chinese content. Historical runs from before
this instrumentation cannot reveal their original provider HTTP error details.

The privileged workflow remains restricted to `main`, including dry-runs. A
Python `--dry-run` flag is not a security boundary for branch-controlled code with
production credentials. This incident's hosted generation test used the audited
repair branch temporarily; branch dispatch permission was then removed from the
final change. Production schedules and activation gates are unchanged.
