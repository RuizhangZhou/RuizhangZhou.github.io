#!/usr/bin/env python3
# /// script
# dependencies = ["python-dotenv", "requests", "markdown", "llm-gateway @ git+https://github.com/RuizhangZhou/llm-gateway.git@master"]
# ///
"""
daily-blog: video-digest-first, essay-fallback → GitHub Issues + Bluesky (EN) + Matrix (ZH).

Primary mode: digest the oldest undigested video(s) from Rick's curated YouTube playlist —
full transcript in, real substance out (specific claims/numbers/examples, not a vague summary).
Falls back to the old domain-rotation essay generator on days the playlist has nothing new
(or SUPADATA_API_KEY isn't configured yet).

Every post ships in two languages: English (formal, goes to the public blog + Bluesky) and
Chinese (a natural adaptation for Rick's own reading, sent privately to Matrix).

Usage:
  uv run daily_blog.py            # full run
  uv run daily_blog.py --dry-run  # generate only, no publish
"""
import json
import html
import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.home() / ".env", override=False)

# ── Config ────────────────────────────────────────────────────────────────────

REPO         = "RuizhangZhou/RuizhangZhou.github.io"
TODAY        = date.today().isoformat()
SCRIPT_DIR   = Path(__file__).parent
HISTORY_FILE = SCRIPT_DIR / "history.json"
LOG_FILE     = SCRIPT_DIR / "daily-blog.log"
CONFIG_FILE  = SCRIPT_DIR / "config.json"
OUTPUT_DIR   = SCRIPT_DIR / "output"


def load_config() -> dict:
    """Load non-secret, user-editable settings kept next to this script."""
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text())


CONFIG = load_config()

BSKY_SERVICE   = os.environ.get("BSKY_SERVICE", "https://bsky.social")
BSKY_ID        = os.environ.get("BSKY_IDENTIFIER", "rickzrz.bsky.social")
BSKY_PASS      = os.environ["BSKY_APP_PASSWORD"]

MASTO_INSTANCE = os.environ.get("MASTODON_INSTANCE", "https://mastodon.social")
MASTO_TOKEN    = os.environ.get("MASTODON_ACCESS_TOKEN")

# Mastodon posting is paused: @rickzrz@mastodon.social was suspended on 2026-06-03
# (account flagged by mastodon.social anti-spam after a burst of link posts from a
# dormant, non-bot-flagged account). Re-enable by setting this to True once the
# account is restored or a new one is set up.
MASTODON_ENABLED = False

SUPADATA_API_KEY  = os.environ.get("SUPADATA_API_KEY")
MATRIX_HOMESERVER = os.environ.get("MATRIX_HOMESERVER")
MATRIX_BOT_TOKEN  = os.environ.get("MATRIX_BOT_TOKEN")
MATRIX_RICK_ROOM  = os.environ.get("MATRIX_RICK_ROOM")

DOMAIN_COOLDOWN_DAYS = 7
HISTORY_WINDOW       = 14   # titles shown to LLM to avoid angle duplication
MAX_HISTORY_KEPT     = 60   # entries to keep in history.json

# ── Topic domains (essay-mode fallback) ─────────────────────────────────────────
# Each domain maps to the channel / mental-model cluster that feeds it.

DOMAINS = {
    "finance-independence": "financial independence, passive income, FIRE movement, systematic investing, wealth accumulation",
    "investment-risk":      "risk management, risk arbitrage, portfolio theory, quantitative analysis, asymmetric bets, position sizing",
    "poker-gametheory":     "Texas Hold'em strategy, expected value, prediction markets, game theory, decisions under uncertainty",
    "ai-technology":        "AI products, ML engineering trade-offs, technology trends, model selection, automation impact on work",
    "psychology-cognition": "behavioral science, cognitive biases, habit formation, attention economics, decision-making under pressure",
    "entrepreneurship":     "building products, small teams, bootstrapping, career ownership, navigating large organisations vs. going solo",
    "leverage-systems":     "leverage points, compounding returns, network effects, scalable systems, making assets work for you",
    "philosophy-anthropology": "stoicism, human nature, anthropology of technology, ancient wisdom applied to modern complexity",
    "economics-geopolitics": "macro trends, regulatory shifts, geopolitical technology risk, global capital flows, EU/China/US dynamics",
    "cinema-storytelling":  "narrative structures, film theory as mental models, how stories shape perception and decision-making",
    "life-health-meaning":  "marriage and long-term partnership, having children and the decision to become a parent, genetics and heredity, "
                            "what we pass on to the next generation, longevity and personal health, the meaning of family, "
                            "personal development across life stages — approached with intellectual honesty and biological/philosophical grounding",
    "money-life-diary":     "everyday money decisions as life philosophy — spending vs. saving choices, the emotional and psychological "
                            "side of money, financial peace of mind, journal-style reflection on wealth and contentment, "
                            "how small daily financial habits reflect deeper values and shape the life you're building",
}

# ── Creator inspiration library (essay-mode fallback) ────────────────────────────

CREATORS_FILE = SCRIPT_DIR / "creators.json"


def load_creators() -> list[dict]:
    if CREATORS_FILE.exists():
        return json.loads(CREATORS_FILE.read_text())["creators"]
    return []


# ── Video playlist ────────────────────────────────────────────────────────────
# Rick's personal curated YouTube playlist ("NoteLLM Playlist") — he drops in videos
# he wants absorbed but doesn't have time to watch in full. Pulled via the playlist's
# RSS feed (no API key, no consent wall, unlike scraping the playlist page directly).

PLAYLIST_URL          = os.environ.get(
    "YOUTUBE_PLAYLIST_URL",
    CONFIG.get("youtube_playlist_url", "https://www.youtube.com/playlist?list=PLLyrAkI8SEhs"),
)
PLAYLIST_ID           = urllib.parse.parse_qs(urllib.parse.urlparse(PLAYLIST_URL).query).get("list", [""])[0]
if not PLAYLIST_ID:
    raise RuntimeError(f"Invalid youtube_playlist_url in {CONFIG_FILE}: missing list= playlist ID")
PLAYLIST_CACHE_FILE   = SCRIPT_DIR / "playlist_cache.json"
DIGESTED_VIDEOS_FILE  = SCRIPT_DIR / "digested_videos.json"
MAX_DIGEST_CANDIDATES = int(CONFIG.get("max_digest_videos_per_post", 3))
# Keep looking past videos without usable captions. Previously the first three
# captionless videos permanently blocked every later playlist item.
MAX_TRANSCRIPT_ATTEMPTS = int(CONFIG.get("max_transcript_attempts_per_run", 8))
MAX_TRANSCRIPT_CHARS  = 60000  # per-video safety cap (~13k tokens), guards against outlier-length videos


def fetch_playlist_videos() -> list[dict]:
    """Returns [{id, title, author}] from the playlist RSS feed, in playlist order.
    Falls back to the last successful fetch if the network call fails."""
    import xml.etree.ElementTree as ET

    url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        log(f"Playlist fetch failed ({e}); using cache if available.")
        if PLAYLIST_CACHE_FILE.exists():
            return json.loads(PLAYLIST_CACHE_FILE.read_text())["videos"]
        return []

    ns = {
        "a": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    videos = []
    for entry in root.findall("a:entry", ns):
        title = entry.findtext("a:title", default="", namespaces=ns)
        author = entry.findtext("a:author/a:name", default="", namespaces=ns)
        video_id = entry.findtext("yt:videoId", default="", namespaces=ns)
        description = entry.findtext("media:group/media:description", default="", namespaces=ns)
        if title and video_id:
            videos.append({
                "id": video_id,
                "title": title,
                "author": author,
                "description": description[:6000],
            })

    PLAYLIST_CACHE_FILE.write_text(json.dumps({
        "playlist_url": PLAYLIST_URL,
        "feed_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "videos": videos,
    }, ensure_ascii=False, indent=2))
    return videos


def load_digested_ids() -> set[str]:
    if DIGESTED_VIDEOS_FILE.exists():
        return set(json.loads(DIGESTED_VIDEOS_FILE.read_text())["ids"])
    return set()


def save_digested_ids(ids: set[str]) -> None:
    DIGESTED_VIDEOS_FILE.write_text(json.dumps({"ids": sorted(ids)}, indent=2))


def pick_candidate_videos(videos: list[dict], digested_ids: set[str]) -> list[dict]:
    """Undigested videos to probe for captions, in the playlist feed's order."""
    undigested = [v for v in videos if v["id"] not in digested_ids]
    return undigested[:MAX_TRANSCRIPT_ATTEMPTS]


def fetch_transcript(video_id: str) -> str | None:
    """Full transcript text via Supadata, or None if unavailable/unconfigured."""
    import requests

    if not SUPADATA_API_KEY:
        return None
    try:
        r = requests.get(
            "https://api.supadata.ai/v1/transcript",
            # mode=native: only fetch existing captions, never fall back to AI-generated
            # transcription — that path bills 2 credits/video-minute and can burn the whole
            # monthly free quota on a single long video.
            params={"url": f"https://youtu.be/{video_id}", "mode": "native"},
            headers={"x-api-key": SUPADATA_API_KEY},
            timeout=30,
        )
        r.raise_for_status()
        text = " ".join(seg["text"] for seg in r.json().get("content", []))
    except Exception as e:
        log(f"Transcript fetch failed for {video_id}: {e}")
        return None

    if not text:
        log(f"No usable native transcript for {video_id}; trying the next playlist item.")
        return None
    if len(text) > MAX_TRANSCRIPT_CHARS:
        log(f"Transcript for {video_id} truncated from {len(text)} to {MAX_TRANSCRIPT_CHARS} chars.")
        text = text[:MAX_TRANSCRIPT_CHARS]
    return text


# ── History ───────────────────────────────────────────────────────────────────

def load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())["posts"]
    return []


def save_history(posts: list[dict]) -> None:
    trimmed = posts[:MAX_HISTORY_KEPT]
    HISTORY_FILE.write_text(json.dumps({"posts": trimmed}, indent=2, ensure_ascii=False))


def available_domains(posts: list[dict]) -> list[str]:
    """Domains not used in the last DOMAIN_COOLDOWN_DAYS days."""
    cutoff = date.today() - timedelta(days=DOMAIN_COOLDOWN_DAYS)
    recently_used = {
        p["domain"]
        for p in posts
        if p.get("domain") != "unknown" and date.fromisoformat(p["date"]) > cutoff
    }
    return [d for d in DOMAINS if d not in recently_used]


def recent_titles(posts: list[dict]) -> list[str]:
    return [p["title"] for p in posts[:HISTORY_WINDOW]]


def _escape_braces(s: str) -> str:
    """Defends str.format() against stray { } in untrusted transcript text."""
    return s.replace("{", "{{").replace("}", "}}")


# ── LLM generation: video-digest mode (primary) ──────────────────────────────────

DIGEST_SYSTEM_PROMPT_TEMPLATE = """\
You are writing Rick's daily video-digest post. Rick curates a personal YouTube watch-list of videos \
he wants to absorb but doesn't have time to watch in full (they run 30-90 minutes). Your job is to \
extract the real substance — specific claims, numbers, arguments, examples — not a vague "this video \
is about X" summary. Someone reading your digest should walk away knowing the actual content, as if \
they'd watched it, in a fraction of the time.

Source material — transcript(s) of today's candidate video(s), listed in priority order (first is primary):
{transcripts_block}

Instructions:
1. If there is more than one video and they share a genuine connecting theme, synthesize across all of \
   them into one digest that draws out the connection. If they are unrelated, focus entirely on the \
   FIRST (primary) video and ignore the others — they'll get their own digest another day.
2. Extract specific, concrete content: names, numbers, claims, examples, the actual argument structure — \
   never "the speaker discusses various aspects of X."
3. Structure: ## section headers, at least one table or numbered breakdown of key points.
4. Open with the single most surprising or useful claim from the source, not a throat-clearing intro.
5. Close with your own one- or two-sentence take — where you agree, disagree, or want to apply this.
6. Length: 700-900 words for the English version.
7. Write for a global reader — no assumed regional context.
8. Use math sparingly. Prefer plain language and concrete numbers over notation. If a formula truly is \
   the clearest way to say something, keep it short and explain it in words right after. Use `$$...$$` \
   for display math, `$...$` for inline — never bare `[...]`. LaTeX subscripts MUST always have an \
   explicit underscore: write `X_` before any subscript group. `\\underbrace` labels must use \
   `\\underbrace{{content}}_{{label}}` — never omit the underscore before the label.

After the English version, write a Chinese version: a natural, faithful adaptation carrying the same \
content and structure — not a mechanical word-for-word translation. This copy is for Rick's own reading, \
so prioritize clarity and natural Chinese phrasing over literal fidelity to English sentence structure.

Recent post titles — avoid repeating these angles:
{recent_titles}

Respond using EXACTLY this format, no other text before or after:

<<<TITLE>>>
English title
<<<BODY>>>
Full English Markdown body (no H1 heading at the top)
<<<TITLE_ZH>>>
中文标题
<<<BODY_ZH>>>
完整中文 Markdown 正文,自然表达同样的内容和结构,不是逐字翻译(不要顶层 H1 标题)
<<<HOOK>>>
Your Bluesky micro-post here — this one is ENGLISH regardless of the Chinese section above (it accompanies \
the public English post). 2-3 short sentences, hard 220-character limit, do NOT just restate the title — \
open a different angle (a surprising fact, a counterintuitive claim, a one-line scenario). Tone: direct, \
slightly provocative, conversational. End with a hint the full digest is linked, without saying "click \
here" or "read more."
<<<USED_VIDEO_IDS>>>
Comma-separated video IDs you actually drew on, from the reference list below (usually just the primary \
one, unless you synthesized several), e.g. abc123,def456

Video ID reference:
{video_id_list}
"""


def generate_video_digest(candidates: list[dict], transcripts: dict[str, str], posts: list[dict]):
    """Returns (title, body, title_zh, body_zh, hook, used_video_ids)."""
    from llm_gateway import chat

    transcripts_block = "\n\n".join(
        f'--- Video: "{v["title"]}" by {v["author"]} (id: {v["id"]}) ---\n'
        f'{_escape_braces(transcripts[v["id"]])}'
        for v in candidates
    )
    video_id_list = "\n".join(f'  - {v["id"]}: "{v["title"]}"' for v in candidates)
    titles_str = "\n".join(f"  - {t}" for t in recent_titles(posts)) or "  (none yet)"

    prompt = DIGEST_SYSTEM_PROMPT_TEMPLATE.format(
        transcripts_block=transcripts_block,
        recent_titles=titles_str,
        video_id_list=video_id_list,
    )

    resp = chat(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user",   "content": f"Write today's digest. Date: {TODAY}."},
        ],
        task="youtube_digest",
        max_tokens=6000,
        timeout=240.0,
        reasoning_effort="high",
    )

    raw = resp["choices"][0]["message"]["content"]
    try:
        title    = raw.split("<<<TITLE>>>")[1].split("<<<BODY>>>")[0].strip()
        body     = raw.split("<<<BODY>>>")[1].split("<<<TITLE_ZH>>>")[0].strip()
        title_zh = raw.split("<<<TITLE_ZH>>>")[1].split("<<<BODY_ZH>>>")[0].strip()
        body_zh  = raw.split("<<<BODY_ZH>>>")[1].split("<<<HOOK>>>")[0].strip()
        hook     = raw.split("<<<HOOK>>>")[1].split("<<<USED_VIDEO_IDS>>>")[0].strip()
        used_raw = raw.split("<<<USED_VIDEO_IDS>>>")[1].strip()
    except IndexError:
        raise RuntimeError(f"LLM response missing expected separators:\n{raw[:300]}")

    valid_ids = {v["id"] for v in candidates}
    used_ids = [x.strip() for x in used_raw.split(",") if x.strip() in valid_ids]
    if not used_ids:
        used_ids = [candidates[0]["id"]]  # always mark at least the primary video as covered

    if len(hook.encode()) > 220:
        hook = hook[:217] + "…"

    body += f"\n\n---\n\n_Published by bot · {TODAY}_\n\n<!-- daily-blog-{TODAY} -->"
    return title, body, title_zh, body_zh, hook, used_ids


# ── LLM generation: essay mode (fallback when the playlist has nothing new) ──────

SYSTEM_PROMPT_TEMPLATE = """\
You are the writer behind a daily essay blog with a global readership — curious people who think seriously about money, technology, psychology, and how the world works.
Your voice is intellectually rigorous but personally grounded — like a thoughtful letter to a smart friend, not a LinkedIn post or a startup pitch.

You draw on ideas from these thinkers and content creators:
- Personal finance / wealth-building: systematic investing, FIRE, passive income strategies, macro literacy
- Behavioral psychology: cognitive biases, decision science, attention and habit research
- AI and technology: engineering trade-offs, model risk, automation's effect on work and society
- Geopolitics and economics: global capital flows, regulatory shifts, EU/China/US tech dynamics
- Game theory and probability: poker strategy, expected value, prediction markets, risk under uncertainty
- Philosophy and anthropology: stoicism, human nature, how ancient frameworks apply to modern complexity
- Film theory and storytelling: narrative structures as mental models, how stories shape perception
- Career and work: building products, leverage, systems that work without you
- Life, health and meaning: marriage and partnership, the decision to have children, genetics and what we inherit and pass on,
  longevity and health optimisation, the philosophy of family, personal development across life stages

Available topic domains today (7-day cooldown enforced — pick exactly ONE):
{available_domains}

Domain descriptions:
{domain_descriptions}

Recent post titles — avoid repeating these angles or framings:
{recent_titles}

{playlist_inspiration}

Write today's essay following these rules:
1. Title: a specific, surprising thesis — not a listicle headline, not a generic question
2. Opening: a concrete scenario, counterintuitive claim, or dissonant real-world observation that pulls the reader in
3. Structure: ## section headers, at least one table or numbered breakdown
4. Section "Personal Glimpse": a brief first-person anecdote that connects theory to lived experience
5. Closing: a *bold question* that opens rather than closes the thought
6. Length: 900–1300 words for the English version
7. Cross-pollinate domains when it sharpens the argument (e.g. poker EV applied to career risk-sizing)
8. Write for a global reader — no regional assumed context, no jargon tied to one subculture
9. Use math sparingly. Most essays should have zero formulas, maybe one if it genuinely sharpens the point.
   Prefer plain language and concrete numbers over notation — "if you win $100 seven times out of ten" beats
   formal EV notation. Never reach for a formula just because the domain (poker, investing, risk) suggests one.
   If a formula truly is the clearest way to say something, keep it short and explain it in words right after.
   When you do write one, use `$$...$$` for display math, `$...$` for inline — never bare `[...]`.
   LaTeX subscripts MUST always have an explicit underscore: write `X_` before any subscript group.
   `\\underbrace` labels must use `\\underbrace{{content}}_{{label}}` — never omit the underscore before the label.

After the English version, write a Chinese version: a natural, faithful adaptation carrying the same
content and structure — not a mechanical word-for-word translation. This copy is for Rick's own reading,
so prioritize clarity and natural Chinese phrasing over literal fidelity to English sentence structure.

Respond using EXACTLY this format — six sections, no other text before or after:

<<<TITLE>>>
Your title here
<<<DOMAIN>>>
chosen-domain-slug
<<<BODY>>>
Full Markdown essay body here (no H1 heading at the top)
<<<TITLE_ZH>>>
中文标题
<<<BODY_ZH>>>
完整中文 Markdown 正文,自然表达同样的内容和结构,不是逐字翻译(不要顶层 H1 标题)
<<<HOOK>>>
Your Bluesky micro-post here

Rules for <<<HOOK>>> (read carefully):
- Write this in ENGLISH regardless of the Chinese section above — it accompanies the public English post.
- This is the ONLY thing most people will see before deciding whether to click. Make it earn the click.
- 2–3 short sentences. Hard 220-character limit (count carefully).
- Do NOT just restate the title. Open a different angle — a surprising fact, a counterintuitive claim,
  a rhetorical question, or a one-line scenario that creates an open loop in the reader's mind.
- Tone: direct, slightly provocative, conversational. No em-dashes overload. No "In this post…".
- End with a hint that the full answer is in the linked essay — but don't say "click here" or "read more".
- Good examples of hook structure:
    "Most investors obsess over picking stocks. The real alpha is in what you never sell. →"
    "Your attention isn't being stolen. You're renting it out — cheaply. Here's the invoice."
    "The research on habit formation is mostly wrong. What actually sticks looks nothing like a streak."
- Bad: "Today I explore why X matters for Y. Read my latest post!"
- Bad: restating the title as a sentence."""


def generate_post(posts: list[dict], inspiration_video: dict | None = None):
    """Returns (title, body, title_zh, body_zh, domain, hook)."""
    from llm_gateway import chat

    avail = available_domains(posts)
    if not avail:
        avail = list(DOMAINS.keys())   # all domains expired cooldown simultaneously — reset

    creator_notes: dict[str, list[str]] = {}
    for c in load_creators():
        for d in c["domains"]:
            creator_notes.setdefault(d, []).append(c["description"])

    available_str = "\n".join(f"  - {d}" for d in avail)
    descriptions_str = "\n".join(
        f"  {d}: {desc}" + "".join(f"\n    Inspiration: {note}" for note in creator_notes.get(d, []))
        for d, desc in DOMAINS.items() if d in avail
    )
    titles_str = "\n".join(f"  - {t}" for t in recent_titles(posts)) or "  (none yet)"
    if inspiration_video:
        description = inspiration_video.get("description", "").strip() or "(No description supplied.)"
        playlist_inspiration = f"""\
Fresh playlist signal (native captions were unavailable):
- Title: {inspiration_video['title']}
- Creator: {inspiration_video['author']}
- Creator-supplied description: {_escape_braces(description)}

You MUST make this fresh playlist item the central subject of today's essay. Treat the title and
description as topic/source notes, not as a full transcript: do not claim to have watched the video,
quote the speaker, or invent facts beyond these notes. The essay may add clearly framed analysis and
general knowledge."""
    else:
        playlist_inspiration = "No fresh playlist item is available today; choose from the domain rotation."

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        available_domains=available_str,
        domain_descriptions=descriptions_str,
        recent_titles=titles_str,
        playlist_inspiration=playlist_inspiration,
    )

    resp = chat(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user",   "content": f"Write today's post. Date: {TODAY}."},
        ],
        task="blog",
        max_tokens=4500,
        timeout=150.0,
    )

    raw = resp["choices"][0]["message"]["content"]
    try:
        title    = raw.split("<<<TITLE>>>")[1].split("<<<DOMAIN>>>")[0].strip()
        domain   = raw.split("<<<DOMAIN>>>")[1].split("<<<BODY>>>")[0].strip()
        body     = raw.split("<<<BODY>>>")[1].split("<<<TITLE_ZH>>>")[0].strip()
        title_zh = raw.split("<<<TITLE_ZH>>>")[1].split("<<<BODY_ZH>>>")[0].strip()
        body_zh  = raw.split("<<<BODY_ZH>>>")[1].split("<<<HOOK>>>")[0].strip()
        hook     = raw.split("<<<HOOK>>>")[1].strip()
    except IndexError:
        raise RuntimeError(f"LLM response missing expected separators:\n{raw[:300]}")

    # Enforce Bluesky 300-char limit on hook (leave ~80 chars for URL + newlines)
    if len(hook.encode()) > 220:
        hook = hook[:217] + "…"

    body += f"\n\n---\n\n_Published by bot · {TODAY}_\n\n<!-- daily-blog-{TODAY} -->"
    return title, body, title_zh, body_zh, domain, hook


# ── GitHub Issues ─────────────────────────────────────────────────────────────

BLOG_BASE = "https://ruizhangzhou.github.io/blog.html"


def create_github_issue(title: str, body: str) -> tuple[str, str]:
    """Returns (github_issue_url, personal_blog_url)."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(body)
        body_file = f.name
    try:
        env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
        r = subprocess.run(
            ["/usr/bin/gh", "issue", "create",
             "--repo", REPO,
             "--title", title,
             "--body-file", body_file,
             "--label", "blog",
             "--label", "bot"],
            capture_output=True, text=True, env=env,
        )
        if r.returncode != 0:
            raise RuntimeError(f"gh issue create failed:\nSTDOUT: {r.stdout}\nSTDERR: {r.stderr}")
    finally:
        Path(body_file).unlink(missing_ok=True)
    github_url = r.stdout.strip()
    issue_number = github_url.rstrip("/").split("/")[-1]
    blog_url = f"{BLOG_BASE}?id={issue_number}"
    return github_url, blog_url


# ── Bluesky ───────────────────────────────────────────────────────────────────

def _bsky(path: str, payload: dict, token: str | None = None) -> dict:
    req = urllib.request.Request(
        f"{BSKY_SERVICE}/xrpc/{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 **({"Authorization": f"Bearer {token}"} if token else {})},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Bluesky {path} → {e.code}: {e.read().decode()}") from e


def post_to_bluesky(hook: str, blog_url: str) -> None:
    session = _bsky("com.atproto.server.createSession",
                    {"identifier": BSKY_ID, "password": BSKY_PASS})
    token, did = session["accessJwt"], session["did"]

    text      = f"{hook}\n\n{blog_url}"
    url_start = len(hook.encode()) + 2
    url_end   = url_start + len(blog_url.encode())

    _bsky(
        "com.atproto.repo.createRecord",
        {
            "repo": did,
            "collection": "app.bsky.feed.post",
            "record": {
                "$type":     "app.bsky.feed.post",
                "text":      text,
                "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "facets": [{
                    "index":    {"byteStart": url_start, "byteEnd": url_end},
                    "features": [{"$type": "app.bsky.richtext.facet#link", "uri": blog_url}],
                }],
            },
        },
        token=token,
    )


# ── Mastodon ──────────────────────────────────────────────────────────────────

def post_to_mastodon(hook: str, blog_url: str) -> str:
    """Posts hook + blog URL to Mastodon. Returns the toot URL."""
    text = f"{hook}\n\n{blog_url}"
    req = urllib.request.Request(
        f"{MASTO_INSTANCE}/api/v1/statuses",
        data=urllib.parse.urlencode({"status": text, "visibility": "public"}).encode(),
        headers={
            "Authorization": f"Bearer {MASTO_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            data = json.load(r)
            return data.get("url", "")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Mastodon post failed {e.code}: {e.read().decode()}") from e


# ── Matrix (private, Chinese digest) ─────────────────────────────────────────────

def _markdown_to_html(text: str) -> str:
    import markdown
    return markdown.markdown(text, extensions=["tables"])


def send_matrix_message(text: str) -> None:
    import uuid
    import requests

    if not (MATRIX_HOMESERVER and MATRIX_BOT_TOKEN and MATRIX_RICK_ROOM):
        log("Matrix not configured (MATRIX_HOMESERVER/MATRIX_BOT_TOKEN/MATRIX_RICK_ROOM); skipping.")
        return

    url = (f"{MATRIX_HOMESERVER.rstrip('/')}/_matrix/client/v3/rooms/"
           f"{MATRIX_RICK_ROOM}/send/m.room.message/{uuid.uuid4()}")
    r = requests.put(
        url,
        headers={"Authorization": f"Bearer {MATRIX_BOT_TOKEN}"},
        json={
            "msgtype": "m.text",
            "body": text,
            "format": "org.matrix.custom.html",
            "formatted_body": _markdown_to_html(text),
        },
        timeout=20,
    )
    r.raise_for_status()


def save_chinese_digest(title: str, body: str) -> Path:
    """Save a standalone, readable HTML copy of the private Chinese digest."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{TODAY}-zh.html"
    article = _markdown_to_html(body)
    document = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ color: #222; font: 18px/1.75 system-ui, sans-serif; margin: 0 auto; max-width: 760px; padding: 32px 20px 64px; }}
    h1 {{ line-height: 1.3; }}
    img {{ max-width: 100%; }}
    blockquote {{ border-left: 4px solid #bbb; color: #555; margin-left: 0; padding-left: 1em; }}
    code {{ background: #f3f3f3; padding: .1em .3em; }}
  </style>
</head>
<body>
  <article><h1>{html.escape(title)}</h1>{article}</article>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")
    return path


def send_matrix_file(path: Path, display_name: str) -> None:
    """Upload a file to Matrix and send it as an attachment."""
    import uuid
    import requests

    if not (MATRIX_HOMESERVER and MATRIX_BOT_TOKEN and MATRIX_RICK_ROOM):
        log("Matrix not configured; skipping file upload.")
        return

    headers = {"Authorization": f"Bearer {MATRIX_BOT_TOKEN}"}
    upload_url = f"{MATRIX_HOMESERVER.rstrip('/')}/_matrix/media/v3/upload"
    with path.open("rb") as file_obj:
        upload = requests.post(
            upload_url,
            headers={**headers, "Content-Type": "text/html; charset=utf-8"},
            params={"filename": path.name},
            data=file_obj,
            timeout=30,
        )
    upload.raise_for_status()
    content_uri = upload.json()["content_uri"]

    send_url = (f"{MATRIX_HOMESERVER.rstrip('/')}/_matrix/client/v3/rooms/"
                f"{MATRIX_RICK_ROOM}/send/m.room.message/{uuid.uuid4()}")
    sent = requests.put(
        send_url,
        headers=headers,
        json={
            "msgtype": "m.file",
            "body": display_name,
            "filename": path.name,
            "url": content_uri,
            "info": {"mimetype": "text/html", "size": path.stat().st_size},
        },
        timeout=20,
    )
    sent.raise_for_status()


# ── Main ──────────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    with LOG_FILE.open("a") as f:
        f.write(line + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the daily video digest or essay.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="generate content without publishing or updating history",
    )
    args = parser.parse_args()
    dry_run = args.dry_run

    posts = load_history()
    digested_ids = load_digested_ids()

    videos = fetch_playlist_videos()
    candidates = pick_candidate_videos(videos, digested_ids)
    log(
        f"Playlist poll: {PLAYLIST_URL} — {len(videos)} feed item(s), "
        f"{len(candidates)} undigested candidate(s) queued for transcript checks."
    )

    transcripts: dict[str, str] = {}
    attempts = 0
    for v in candidates:
        if len(transcripts) >= MAX_DIGEST_CANDIDATES:
            break
        if attempts > 0:
            time.sleep(3)  # avoid Supadata free-tier rate limiting on back-to-back calls
        attempts += 1
        t = fetch_transcript(v["id"])
        if t:
            transcripts[v["id"]] = t
    usable = [v for v in candidates if v["id"] in transcripts]

    if usable:
        log(f"Digest mode — {len(usable)} candidate video(s): {[v['title'] for v in usable]}")
        title, body, title_zh, body_zh, hook, used_ids = generate_video_digest(usable, transcripts, posts)
        domain = "video-digest"
    else:
        avail = available_domains(posts)
        if candidates:
            primary = candidates[0]
            log(
                "Playlist-inspired essay mode (no usable native transcripts) — "
                f"using fresh topic: {primary['title']}"
            )
            title, body, title_zh, body_zh, domain, hook = generate_post(posts, primary)
            # The item has now informed a post even though it was not a transcript-level digest.
            used_ids = [primary["id"]]
        else:
            log(f"Essay mode (playlist has no undigested items) — available domains: {avail}")
            title, body, title_zh, body_zh, domain, hook = generate_post(posts)
            used_ids = []

    log(f"Title: {title}  |  Domain: {domain}")
    log(f"Hook ({len(hook)} chars): {hook}")

    if dry_run:
        print("\n--- DRY RUN ---")
        print(f"TITLE    : {title}")
        print(f"TITLE_ZH : {title_zh}")
        print(f"DOMAIN   : {domain}")
        print(f"HOOK     : {hook}")
        print(f"USED IDS : {used_ids}")
        print(f"BODY (EN):\n{body[:600]}\n…")
        print(f"BODY (ZH):\n{body_zh[:600]}\n…")
        return

    log("Creating GitHub Issue…")
    github_url, blog_url = create_github_issue(title, body)
    log(f"GitHub: {github_url}")
    log(f"Blog:   {blog_url}")

    log("Posting to Bluesky…")
    post_to_bluesky(hook, blog_url)
    log("Bluesky posted.")

    if MASTODON_ENABLED:
        log("Posting to Mastodon…")
        toot_url = post_to_mastodon(hook, blog_url)
        log(f"Mastodon posted: {toot_url}")
    else:
        log("Mastodon posting paused (account suspended) — skipping.")

    log("Saving and sending Matrix digest as a readable HTML file (Chinese)…")
    digest_file = save_chinese_digest(title_zh, body_zh)
    send_matrix_message(f"**{title_zh}**\n\n今日文章已附上 HTML 阅读文件。\n\n🔗 公开博客：{blog_url}")
    send_matrix_file(digest_file, f"{title_zh} · {TODAY}")
    log(f"Matrix sent with attachment: {digest_file}")

    if used_ids:
        digested_ids |= set(used_ids)
        save_digested_ids(digested_ids)
        log(f"Marked digested: {used_ids}")

    # Persist history
    posts.insert(0, {"date": TODAY, "title": title, "domain": domain, "url": blog_url,
                      "used_video_ids": used_ids})
    save_history(posts)
    log("Done.")


if __name__ == "__main__":
    main()

