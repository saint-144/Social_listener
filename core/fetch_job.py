import logging
import json

from datetime import datetime, timedelta, timezone

from core.config import FETCH_INTERVAL_MINUTES
from database.connection import get_db_connection
from database.repository import save_post
# from collectors.x_collector import fetch_tweets
from parsers.sentiment import analyze_sentiment
from parsers.demographics import estimate_demographics

from collectors.youtube_collector import fetch_youtube_posts

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


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


def run_fetch_job():

    log.info("Starting fetch job")

    db = get_db_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM keyword_configs WHERE is_active=1")

    configs = cur.fetchall()

    total = 0

    for config in configs:

        # ================================
        # X TWEETS COLLECTION (DISABLED)
        # ================================
        
        keywords = config["keywords"] if isinstance(config["keywords"], list) else json.loads(config["keywords"])

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
        # YOUTUBE COLLECTION
        # ================================

        # Calculate time window (last 15 minutes)
        published_after = (datetime.now(timezone.utc) - timedelta(minutes=FETCH_INTERVAL_MINUTES)).isoformat().replace("+00:00", "Z")

        youtube_videos = fetch_youtube_posts(config, published_after=published_after)

        log.info(f"YouTube returned {len(youtube_videos)} videos")

        for video in youtube_videos:

            text = video.get("text", "").strip()
            
            if not text:
                continue

            matched = find_matching_keywords(text, keywords)

            # if not matched:
            #     continue

            try:

                cur.execute("""
                INSERT IGNORE INTO posts
                (platform_post_id, platform, keyword_config_id, matched_keywords,
                post_text, post_url, author_username, author_display_name,
                like_count, retweet_count, reply_count, impression_count,
                language, posted_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,(
                    video["id"],
                    "YOUTUBE",
                    config["id"],
                    json.dumps(matched),
                    text,
                    video["url"],
                    video["channel"],
                    video["channel"],
                    0,
                    0,
                    0,
                    0,
                    "en",
                    video["published_at"]
                ))

                post_id = cur.lastrowid

                if post_id:

                    sentiment, score = analyze_sentiment(text)

                    cur.execute("""
                        INSERT IGNORE INTO post_sentiment
                        (post_id, sentiment, sentiment_score)
                        VALUES (%s,%s,%s)
                    """,(post_id,sentiment,score))

                    demo = estimate_demographics(
                        video["channel"],
                        video["channel"],
                        ""
                    )

                    cur.execute("""
                        INSERT IGNORE INTO author_demographics
                        (post_id, estimated_age_group, estimated_gender)
                        VALUES (%s,%s,%s)
                    """,(post_id,demo["estimated_age_group"],demo["estimated_gender"]))

                    db.commit()
                    total += 1

            except Exception as e:

                db.rollback()
                log.warning(e)

    cur.close()
    db.close()

    log.info(f"Fetched {total} posts")

    