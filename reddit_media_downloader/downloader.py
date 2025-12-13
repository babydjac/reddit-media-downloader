"""HTTP download handler with chunked streaming."""

import requests
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
CHUNK_SIZE = 8192 # 8KB chunks


def download_media(url: str, output_path: Path):
    """
    Download media file from URL to output path.

    Args:
        url: Direct media URL
        output_path: Path object for output file

    Raises:
        Exception: On download failure (per-file, not global)
    """
    # Skip if file already exists
    if output_path.exists():
        return

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"HTTP error: {e}")

    # Write file in chunks
    try:
        with output_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
    except IOError as e:
        # Clean up partial file
        if output_path.exists():
            output_path.unlink()
        raise Exception(f"Write error: {e}")
