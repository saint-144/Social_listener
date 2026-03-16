import logging
import json

from datetime import datetime, timedelta, timezone
from database.connection import get_db_connection
from database.repository import save_post
# from collectors.x_collector import fetch_tweets
from parsers.sentiment import analyze_sentiment
from parsers.demographics import estimate_demographics

from collectors.youtube_collector import fetch_youtube_posts
from collectors.meta_collector import fetch_instagram_posts

from notifications.email_sender import send_email
from notifications.report_builder import build_email_table
from database.repository import get_recent_posts, get_recent_posts_platform
from notifications.report_builder import build_combined_email_table
from database.repository import get_recent_posts_all_platforms

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

EMAIL_MODE = "combined"
# options: "separate" or "combined"

# ========== Platform-specific interval settings ==========
YT_INTERVAL_MINUTES = 15
IG_INTERVAL_MINUTES = 30

# In-memory last-run timestamps per platform per config_id
# These reset when the process restarts (first run always fetches immediately)
_last_run = {
    "YOUTUBE": {},
    "INSTAGRAM": {}
}
# =========================================================


def find_matching_keywords(text, keywords):

    text = text.lower()

    matched = []

    for k in keywords:

        k_clean = k.lower()

        if k_clean in text:
            matched.append(k)

        # also match without spaces
        elif k_clean.replace(" ", "") in text.replace(" ", ""):
            matched.append(k)

    return matched


def _is_due(platform, config_id, interval_minutes):
    """Returns True if the platform+config is due for a fetch."""
    last = _last_run[platform].get(config_id)
    if last is None:
        return True  # Never fetched — run immediately
    return datetime.now(timezone.utc).replace(tzinfo=None) >= last + timedelta(minutes=interval_minutes)


def _mark_run(platform, config_id):
    _last_run[platform][config_id] = datetime.now(timezone.utc).replace(tzinfo=None)


def _save_post_and_analysis(cur, db, platform, config_id, post_id_str, text, url,
                             author, published_at, now, matched):
    """Shared helper: INSERT post, sentiment, demographics. Returns True if newly inserted."""
    cur.execute("""
        INSERT IGNORE INTO posts
        (platform_post_id, platform, keyword_config_id, matched_keywords,
        post_text, post_url, author_username, author_display_name,
        like_count, retweet_count, reply_count, impression_count,
        language, posted_at, fetched_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        post_id_str, platform, config_id, json.dumps(matched),
        text, url, author, author,
        0, 0, 0, 0, "en", published_at, now
    ))
    post_id = cur.lastrowid
    if post_id:
        sentiment, score = analyze_sentiment(text)
        cur.execute("""
            INSERT IGNORE INTO post_sentiment (post_id, sentiment, sentiment_score)
            VALUES (%s,%s,%s)
        """, (post_id, sentiment, score))
        demo = estimate_demographics(author, author, "")
        cur.execute("""
            INSERT IGNORE INTO author_demographics (post_id, estimated_age_group, estimated_gender)
            VALUES (%s,%s,%s)
        """, (post_id, demo["estimated_age_group"], demo["estimated_gender"]))
        db.commit()
        return True
    return False


def _send_report(cur, config, called_from_platform):
    """
    Send a combined email report for a config.
    - called_from_platform: 'YOUTUBE' or 'INSTAGRAM'
    Always shows YT posts from last 15m + IG posts (up to 30) from last 30m.
    """
    emails = config.get("emails")
    if not emails:
        return

    emails = emails if isinstance(emails, list) else json.loads(emails)

    # Fetch platform-specific posts with correct windows
    yt_posts = get_recent_posts_platform(cur, config["id"], "YOUTUBE", YT_INTERVAL_MINUTES)
    ig_posts = get_recent_posts_platform(cur, config["id"], "INSTAGRAM", IG_INTERVAL_MINUTES, limit=30)

    # Combine: YT first (most recent activity), then IG
    posts = yt_posts + ig_posts

    log.info(f"[{called_from_platform}] Report: {len(yt_posts)} YT + {len(ig_posts)} IG posts")

    if not posts:
        log.info("No posts to report.")
        return

    if EMAIL_MODE == "combined":
        html = build_combined_email_table(posts, "Tamil Nadu Election Social Listening")
        send_email(emails, "Social Media Monitoring Report", html)
    elif EMAIL_MODE == "separate":
        if yt_posts:
            html = build_email_table(yt_posts, "Tamil Nadu Election Social Listening (YOUTUBE)")
            send_email(emails, "YouTube Monitoring Report", html)
        if ig_posts:
            html = build_email_table(ig_posts, "Tamil Nadu Election Social Listening (INSTAGRAM)")
            send_email(emails, "Instagram Monitoring Report", html)


def run_fetch_job():
    """
    Called every 30 seconds by the scheduler.
    Each platform checks its own independent interval:
      - YouTube:   every 15 minutes
      - Instagram: every 30 minutes
    Both start immediately on first run.
    X (Twitter) collection is disabled (code kept as comments).
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM keyword_configs WHERE is_active=1")
    configs = cur.fetchall()

    for config in configs:
        config_id = config["id"]
        keywords = config["keywords"] if isinstance(config["keywords"], list) else json.loads(config["keywords"])

        # ================================
        # X TWEETS COLLECTION (DISABLED)
        # ================================

        # tweets, users = fetch_tweets(config)
        # 
        # for tweet in tweets:
        # 
        #     author = users.get(tweet.author_id)
        # 
        #     if not author:
        #         continue
        # 
        #     matched = find_matching_keywords(tweet.text, keywords)
        # 
        #     try:
        # 
        #         post_id = save_post(cur, tweet, author, config["id"], matched)
        # 
        #         if post_id:
        # 
        #             sentiment, score = analyze_sentiment(tweet.text)
        # 
        #             cur.execute("""
        #                 INSERT IGNORE INTO post_sentiment
        #                 (post_id,sentiment,sentiment_score)
        #                 VALUES (%s,%s,%s)
        #             """,(post_id,sentiment,score))
        # 
        #             demo = estimate_demographics(
        #                 author.username,
        #                 author.name,
        #                 author.description
        #             )
        # 
        #             cur.execute("""
        #                 INSERT IGNORE INTO author_demographics
        #                 (post_id,estimated_age_group,estimated_gender)
        #                 VALUES (%s,%s,%s)
        #             """,(post_id,demo["estimated_age_group"],demo["estimated_gender"]))
        # 
        #             db.commit()
        #             total += 1
        # 
        #     except Exception as e:
        # 
        #         db.rollback()
        #         log.warning(e)

        # ================================
        # YOUTUBE COLLECTION (every 15m)
        # ================================
        yt_total = 0
        if _is_due("YOUTUBE", config_id, YT_INTERVAL_MINUTES):
            yt_published_after = (datetime.now(timezone.utc) - timedelta(minutes=YT_INTERVAL_MINUTES)).isoformat().replace("+00:00", "Z")
            log.info(f"[YT] Config {config_id}: fetching last {YT_INTERVAL_MINUTES}m")
            youtube_videos = fetch_youtube_posts(config, published_after=yt_published_after)
            log.info(f"[YT] Returned {len(youtube_videos)} videos")

            for video in youtube_videos:
                text = (video.get("text") or "").strip()
                if not text:
                    continue
                matched = find_matching_keywords(text, keywords)
                try:
                    if _save_post_and_analysis(cur, db, "YOUTUBE", config_id,
                                                video["id"], text, video["url"],
                                                video["channel"], video["published_at"], now, matched):
                        yt_total += 1
                except Exception as e:
                    db.rollback()
                    log.warning(f"[YT] Failed to save {video['id']}: {e}")

            _mark_run("YOUTUBE", config_id)
            log.info(f"[YT] Saved {yt_total} new posts for config {config_id}")
            _send_report(cur, config, "YOUTUBE")

        else:
            next_yt = _last_run["YOUTUBE"].get(config_id) + timedelta(minutes=YT_INTERVAL_MINUTES)
            log.info(f"[YT] Config {config_id} not due. Next at {next_yt}")

        # ================================
        # INSTAGRAM COLLECTION (every 30m)
        # ================================
        ig_total = 0
        if _is_due("INSTAGRAM", config_id, IG_INTERVAL_MINUTES):
            ig_published_after = (datetime.now(timezone.utc) - timedelta(minutes=IG_INTERVAL_MINUTES)).isoformat().replace("+00:00", "Z")
            log.info(f"[IG] Config {config_id}: fetching last {IG_INTERVAL_MINUTES}m")
            ig_posts = fetch_instagram_posts(config, published_after=ig_published_after)
            log.info(f"[IG] Returned {len(ig_posts)} posts")

            for post in ig_posts:
                text = (post.get("text") or "").strip()
                if not text:
                    continue
                matched = find_matching_keywords(text, keywords)
                try:
                    if _save_post_and_analysis(cur, db, "INSTAGRAM", config_id,
                                                post["id"], text, post["url"],
                                                post["author"], post["published_at"], now, matched):
                        ig_total += 1
                except Exception as e:
                    db.rollback()
                    log.warning(f"[IG] Failed to save {post['id']}: {e}")

            _mark_run("INSTAGRAM", config_id)
            log.info(f"[IG] Saved {ig_total} new posts for config {config_id}")
            _send_report(cur, config, "INSTAGRAM")

        else:
            next_ig = _last_run["INSTAGRAM"].get(config_id) + timedelta(minutes=IG_INTERVAL_MINUTES)
            log.info(f"[IG] Config {config_id} not due. Next at {next_ig}")

    cur.close()
    db.close()
