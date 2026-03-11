# import json
# import tweepy
# from core.config import *
# from core.query_builder import build_query
# 
# def get_x_client():
# 
#     return tweepy.Client(
#         bearer_token=X_BEARER_TOKEN,
#         consumer_key=X_API_KEY,
#         consumer_secret=X_API_SECRET,
#         access_token=X_ACCESS_TOKEN,
#         access_token_secret=X_ACCESS_SECRET,
#         wait_on_rate_limit=True
#     )
# 
# 
# def fetch_tweets(config):
# 
#     client = get_x_client()
# 
#     config["keywords"] = json.loads(config["keywords"]) if isinstance(config["keywords"],str) else config["keywords"]
#     config["locations"] = json.loads(config["locations"]) if config["locations"] else []
# 
#     query = build_query(config)
# 
#     response = client.search_recent_tweets(
#         query=query,
#         max_results=MAX_RESULTS_PER_QUERY,
#         tweet_fields=["created_at","public_metrics","lang","author_id"],
#         user_fields=["username","name","public_metrics","description"],
#         expansions=["author_id"]
#     )
# 
#     if not response.data:
#         return [], {}
# 
#     users_map = {}
# 
#     if response.includes and "users" in response.includes:
#         for user in response.includes["users"]:
#             users_map[user.id] = user
# 
#     return response.data, users_map
