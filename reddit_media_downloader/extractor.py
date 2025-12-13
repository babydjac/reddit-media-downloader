"""Extract media URLs from Reddit posts with schema-resilient logic."""

import re
import requests
from typing import List, Dict, Any

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Cache for Redgifs tokens
_REDGIFS_TOKEN = None


def get_redgifs_token():
    """Get temporary authentication token for Redgifs API v2."""
    global _REDGIFS_TOKEN

    if _REDGIFS_TOKEN:
        return _REDGIFS_TOKEN

    try:
        response = requests.get(
            "https://api.redgifs.com/v2/auth/temporary",
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        _REDGIFS_TOKEN = data.get("token")
        return _REDGIFS_TOKEN
    except Exception:
        # If token fetch fails, return None and let extraction fail gracefully
        return None


def extract_redgifs_id(url):
    """Extract Redgifs ID from URL."""
    # Patterns: redgifs.com/watch/{id} or redgifs.com/ifr/{id}
    match = re.search(r"redgifs\.com/(?:watch|ifr)/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    return None


def extract_redgifs_video(url):
    """
    Extract Redgifs direct video URL (NO WATERMARK).

    Returns:
        List with single dict: [{"url": "...", "filename": "...", "type": "video"}]
        Empty list on failure.
    """
    redgifs_id = extract_redgifs_id(url)
    if not redgifs_id:
        return []

    token = get_redgifs_token()
    if not token:
        return []

    try:
        response = requests.get(
            f"https://api.redgifs.com/v2/gifs/{redgifs_id}",
            headers={
                "User-Agent": USER_AGENT,
                "Authorization": f"Bearer {token}",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Navigate to video URLs
        gif_data = data.get("gif", {})
        urls = gif_data.get("urls", {})

        # Prefer HD, fallback to SD
        video_url = urls.get("hd") or urls.get("sd")

        if video_url:
            return [
                {
                    "url": video_url,
                    "filename": f"{redgifs_id}.mp4",
                    "type": "video",
                }
            ]
    except Exception:
        # Gracefully fail
        pass

    return []


def extract_vreddit_video(post):
    """
    Extract v.redd.it video URL from Reddit post.

    Checks multiple schema locations:
    1. post["secure_media"]["reddit_video"]["fallback_url"]
    2. post["media"]["reddit_video"]["fallback_url"]
    3. post["preview"]["reddit_video_preview"]["fallback_url"]
    4. post["crosspost_parent_list"][*] (recursive)

    Returns:
        List with single dict or empty list.
    """
    post_id = post.get("id", "unknown")

    # Location 1: secure_media
    try:
        fallback_url = post["secure_media"]["reddit_video"]["fallback_url"]
        if fallback_url:
            return [
                {
                    "url": fallback_url,
                    "filename": f"{post_id}.mp4",
                    "type": "video",
                }
            ]
    except (KeyError, TypeError):
        pass

    # Location 2: media
    try:
        fallback_url = post["media"]["reddit_video"]["fallback_url"]
        if fallback_url:
            return [
                {
                    "url": fallback_url,
                    "filename": f"{post_id}.mp4",
                    "type": "video",
                }
            ]
    except (KeyError, TypeError):
        pass

    # Location 3: preview.reddit_video_preview
    try:
        fallback_url = post["preview"]["reddit_video_preview"]["fallback_url"]
        if fallback_url:
            return [
                {
                    "url": fallback_url,
                    "filename": f"{post_id}.mp4",
                    "type": "video",
                }
            ]
    except (KeyError, TypeError):
        pass

    # Location 4: crosspost_parent_list (recursive)
    try:
        crosspost_parents = post.get("crosspost_parent_list", [])
        if crosspost_parents:
            # Try first crosspost parent
            return extract_vreddit_video(crosspost_parents[0])
    except (KeyError, TypeError, IndexError):
        pass

    return []


def extract_image(post):
    """
    Extract image URL from Reddit post.

    Checks:
    - url_overridden_by_dest
    - url

    Validates extension: .jpg, .jpeg, .png, .webp, .gif

    Returns:
        List with single dict or empty list.
    """
    post_id = post.get("id", "unknown")

    # Try url_overridden_by_dest first
    image_url = post.get("url_overridden_by_dest") or post.get("url")

    if not image_url:
        return []

    # Check if URL ends with image extension
    if re.search(r"\.(jpg|jpeg|png|webp|gif)($|\?)", image_url, re.IGNORECASE):
        # Determine extension
        ext_match = re.search(r"\.(jpg|jpeg|png|webp|gif)", image_url, re.IGNORECASE)
        ext = ext_match.group(1).lower() if ext_match else "jpg"

        return [
            {
                "url": image_url,
                "filename": f"{post_id}.{ext}",
                "type": "image",
            }
        ]

    return []


def extract_media(post: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract all media from a Reddit post.

    This is the SINGLE extraction function.

    CRITICAL RULES:
    - MUST ALWAYS RETURN A LIST
    - Return empty list [] if no media found
    - Never return None, dict, or string

    Args:
        post: Reddit post dictionary

    Returns:
        List of media items, each with keys:
        - url: Direct media URL
        - filename: Output filename
        - type: "video" or "image"
    """
    if not post or not isinstance(post, dict):
        return []

    url = post.get("url", "")

    # 1. Check for Redgifs
    if "redgifs.com" in url:
        result = extract_redgifs_video(url)
        if result:
            return result

    # 2. Check for v.redd.it video
    if "v.redd.it" in url or post.get("is_video"):
        result = extract_vreddit_video(post)
        if result:
            return result

    # 3. Check for image
    result = extract_image(post)
    if result:
        return result

    # No media found
    return []
