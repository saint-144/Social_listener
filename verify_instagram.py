import os
import json
import logging
from collectors.meta_collector import fetch_instagram_posts
from core.config import META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def test_instagram():
    print("--- Instagram Collector Test ---")
    
    if not META_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        print("Error: META_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ACCOUNT_ID not set in .env")
        return

    # Mock config
    config = {
        "id": 1,
        "keywords": ["#technology", "#news"]
    }
    
    print(f"Fetching posts for keywords: {config['keywords']}...")
    
    # Debugging hashtags resolution
    for kw in config['keywords']:
        from collectors.meta_collector import get_hashtag_id
        tag = kw.replace(" ", "").replace("#", "")
        hid = get_hashtag_id(tag)
        print(f"Keyword: {kw} -> Tag: {tag} -> Hashtag ID: {hid}")

    posts = fetch_instagram_posts(config)
    
    print(f"\nTotal posts returned by collector: {len(posts)}")
    for post in posts[:5]:
        print(f"\nID: {post['id']}")
        print(f"Platform: {post['platform']}")
        print(f"URL: {post['url']}")
        print(f"Text: {post['text'][:100]}...")
        print(f"Published At: {post['published_at']}")

if __name__ == "__main__":
    test_instagram()
