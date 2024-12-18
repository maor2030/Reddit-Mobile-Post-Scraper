import uuid
import base64
import time
import json
from typing import Dict
import requests


class RedditMobileAuth:
    def __init__(self):
        # These appear to be constant across installations
        self.client_id = "ohXpoqrZYub1kg"
        self.vendor_id = str(uuid.uuid4())  # Generate a random vendor ID
        self.user_agent = "Reddit/Version 2024.28.1/Build 1741165/Android 9"

    def get_auth_token(self):
        """
        Get authentication token using the mobile app flow
        """
        url = "https://www.reddit.com/auth/v2/oauth/access-token/loid"

        # Create basic auth header with just client_id (no secret needed)
        auth_header = base64.b64encode(f"{self.client_id}:".encode()).decode()

        headers = {
            "Accept-Encoding": "gzip",
            "Authorization": f"Basic {auth_header}",
            "Client-Vendor-ID": self.vendor_id,
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": self.user_agent,
            "x-reddit-compression": "1",
            "X-Reddit-Media-Codecs": "available-codecs=",
            "X-Reddit-QoS": "down-rate-mbps=1.000",
            "X-Reddit-Retry": "algo=no-retries"
        }

        payload = {
            "scopes": [
                "*",
                "email",
                "pii"
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            print(f"Auth Status: {response.status_code}")
            print(f"Auth Response: {response.text[:200]}...")  # First 200 chars

            response.raise_for_status()
            return response.json()["access_token"]

        except requests.RequestException as e:
            print(f"Auth error: {e}")
            if hasattr(e, 'response'):
                print(f"Response content: {e.response.text}")
            return None


def fetch_subreddit_feed(subreddit, token, after=None):
    """
    Fetch subreddit feed using the mobile GraphQL endpoint
    """
    url = "https://gql-fed.reddit.com/"

    vendor_id = str(uuid.uuid4())

    headers = {
        "Accept": "multipart/mixed; deferSpec=20220824, application/json",
        "Authorization": f"Bearer {token}",
        "Client-Vendor-ID": vendor_id,
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Reddit/Version 2024.28.1/Build 1741165/Android 9",
        "X-APOLLO-OPERATION-ID": "c4071269a5d5e7aca80e86ed4cf2561ff29cba229760bf7cd58d67036af9a559",
        "X-APOLLO-OPERATION-NAME": "SubredditFeedSdui",
        "x-reddit-compression": "1",
        "x-reddit-device-id": vendor_id
    }

    payload = {
        "operationName": "SubredditFeedSdui",
        "variables": {
            "subredditName": subreddit,
            "sort": "HOT",
            "after": after,
            "includeViewCount": False,
            "includeCarouselRecommendations": True,
            "includeGoldInfo": False,
            "includeMediaAuth": False
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "c4071269a5d5e7aca80e86ed4cf2561ff29cba229760bf7cd58d67036af9a559"
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Feed Status: {response.status_code}")

        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        print(f"Feed error: {e}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.text}")
        return None


def extract_post_from_cells(cells):
    """Extract post data from a group of cells"""
    post_data = {
        "authorName": None,
        "title": None,
        "createdAt": None,
        "commentCount": None
    }

    for cell in cells:
        cell_type = cell.get('__typename')

        if cell_type == 'MetadataCell':
            post_data['authorName'] = cell.get('authorName')
            post_data['createdAt'] = cell.get('createdAt')

        elif cell_type == 'TitleCell':
            post_data['title'] = cell.get('title')

        elif cell_type == 'ActionCell':
            post_data['commentCount'] = cell.get('commentCount')

    return post_data


def find_posts_in_response(response_data: Dict) -> list[Dict]:
    """Find all posts following the correct JSON structure"""
    posts = []

    try:
        # Navigate to the edges array
        edges = response_data['data']['subredditV3']['elements']['edges']

        for edge in edges:
            if edge['__typename'] == 'FeedElementEdge':
                node = edge.get('node', {})
                if node['__typename'] == 'CellGroup':
                    cells = node.get('cells', [])
                    post = extract_post_from_cells(cells)
                    if all(v is not None for v in post.values()):  # Only add if all fields are present
                        posts.append(post)

        print(f"Found {len(posts)} posts in this batch")

    except KeyError as e:
        print(f"Error accessing data structure: {e}")

    return posts


def collect_posts(subreddit: str, target_count: int = 100) -> list[Dict]:
    """
    Collect posts using pagination until reaching target count
    """
    all_posts = []
    after_cursor = None
    page_count = 0
    auth = RedditMobileAuth()
    token = auth.get_auth_token()

    while len(all_posts) < target_count:
        page_count += 1
        print(f"\nFetching page {page_count} with cursor: {after_cursor}")

        response_data = fetch_subreddit_feed(subreddit, token, after_cursor)
        if not response_data:
            print("No response data received")
            break

        new_posts = find_posts_in_response(response_data)
        all_posts.extend(new_posts)
        print(f"Total posts collected: {len(all_posts)}")

        try:
            # Get cursor for next page using correct path
            page_info = response_data['data']['subredditV3']['elements']['pageInfo']
            after_cursor = page_info['endCursor']

            if not after_cursor:
                print("No more pages available (no cursor)")
                break

            # Add small delay between requests to be nice to Reddit's servers
            time.sleep(1)

        except KeyError as e:
            print(f"Error finding next cursor: {e}")
            print("Response structure:", json.dumps(response_data, indent=2)[:200] + "...")
            break

    # Trim to exactly target_count posts if we got more
    return all_posts[:target_count]


def main():
    subreddit = "Steam"
    target_count = 100

    posts = collect_posts(subreddit, target_count)

    print(f"\nFinal collection: {len(posts)} posts")
    if posts:
        print("\nFirst post:")
        print(f"Title: {posts[0]['title']}")
        print(f"Author: {posts[0]['authorName']}")
        print(f"Comments: {posts[0]['commentCount']}")
        print(f"Created: {posts[0]['createdAt']}")

        print("\nLast post:")
        print(f"Title: {posts[-1]['title']}")
        print(f"Author: {posts[-1]['authorName']}")
        print(f"Comments: {posts[-1]['commentCount']}")
        print(f"Created: {posts[-1]['createdAt']}")

    # Save to file
    with open(f'reddit_posts_{subreddit}.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(posts)} posts to reddit_posts.json")


if __name__ == "__main__":
    main()
