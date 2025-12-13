"""Fetch Reddit JSON data without authentication."""

import requests
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def normalize_reddit_url(url):
    """Normalize Reddit URL and prepare for JSON API access."""
    parsed = urlparse(url)

    # Remove trailing slash
    path = parsed.path.rstrip("/")

    # Reconstruct as Reddit URL
    base_url = f"https://www.reddit.com{path}"

    return base_url


def fetch_posts(url, sort="hot", time_filter="all", limit=100):
    """
    Fetch posts from Reddit using the .json API.

    Args:
        url: Reddit subreddit or user URL
        sort: Sort order (hot, new, top, controversial)
        time_filter: Time filter for top/controversial (all, year, month, week, day, hour)
        limit: Maximum number of posts to fetch

    Returns:
        List of post dictionaries from Reddit's data.children[].data
    """
    base_url = normalize_reddit_url(url)

    # Build sort URL
    if sort in ["top", "controversial"]:
        fetch_url = f"{base_url}/{sort}.json"
    else:
        fetch_url = f"{base_url}/{sort}.json" if sort != "hot" else f"{base_url}.json"

    params = {"limit": min(limit, 100)}

    # Add time filter for top/controversial
    if sort in ["top", "controversial"]:
        params["t"] = time_filter

    headers = {"User-Agent": USER_AGENT}

    posts = []
    after = None

    while len(posts) < limit:
        # Add pagination cursor
        if after:
            params["after"] = after

        try:
            response = requests.get(fetch_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Reddit data: {e}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response from Reddit: {e}")

        # Navigate Reddit's JSON structure
        try:
            children = data["data"]["children"]
            after = data["data"].get("after")
        except (KeyError, TypeError) as e:
            raise Exception(f"Unexpected Reddit JSON structure: {e}")

        if not children:
            break

        # Extract post data
        for child in children:
            if child.get("kind") == "t3": # t3 = link/post
                post_data = child.get("data", {})
                posts.append(post_data)

                if len(posts) >= limit:
                    break

        # No more pages
        if not after:
            break

    return posts
