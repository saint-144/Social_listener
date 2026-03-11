from googleapiclient.discovery import build
from core.config import YOUTUBE_API_KEY
import json

youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def fetch_youtube_posts(config, published_after=None):

    keywords = config["keywords"] if isinstance(config["keywords"], list) else json.loads(config["keywords"])

    # Combine keywords into one query
    query = " OR ".join(keywords[:50])

    search_params = {
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": 50,
        "regionCode": "IN",
        "order": "date"
    }

    if published_after:
        search_params["publishedAfter"] = published_after

    request = youtube.search().list(**search_params)

    response = request.execute()

    videos = []

    for item in response.get("items", []):

        title = item["snippet"]["title"]
        description = item["snippet"]["description"]
        video_id = item["id"]["videoId"]

        video = {
            "id": video_id,
            "text": title + " " + description,
            "channel": item["snippet"]["channelTitle"],
            "url": f"https://youtube.com/watch?v={video_id}",
            "published_at": item["snippet"]["publishedAt"]
        }

        videos.append(video)

    return videos