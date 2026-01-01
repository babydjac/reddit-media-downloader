# Reddit Media Downloader

**Robust, modern Reddit media downloader CLI** that handles videos and images with schema-resilient extraction.

## Features

✅ Downloads videos from **v.redd.it** (Now with Sound)  
✅ Downloads videos from **Redgifs** (no watermark)  
✅ Downloads images (JPG, PNG, WebP, GIF)  
✅ **Schema-resilient** - handles Reddit's changing JSON structure  
✅ **Defensive** - never crashes on malformed posts  
✅ **Non-interactive** - perfect for automation  
✅ Clean progress bars with **Rich**  
✅ NSFW filtering support

## Installation

```bash
# Clone repository
git clone https://github.com/babydjac/reddit-media-downloader.git
cd reddit-media-downloader

# Install dependencies
pip install -r requirements.txt
# If using ffmpeg it must be installed on the system

# Install package
pip install -e .
```

## Usage

### Basic Examples

```bash
# Download all media from a subreddit
reddit https://www.reddit.com/r/funny

# Download only videos, sorted by top of all time
reddit --type video --sort top --time all https://www.reddit.com/r/videos

# Include NSFW content
reddit --include-nsfw --sort hot https://www.reddit.com/r/subreddit

# Download only images from new posts
reddit --type image --sort new https://www.reddit.com/r/pics

# Download videos with sound where avalaible
reddit --type video -ffmpeg https://www.reddit.com/r/subreddit
```

### Command-Line Options

| Flag | Options | Default | Description |
|------|---------|---------|-------------|
| `--sort` | `top`, `hot`, `new`, `controversial` | `hot`   | Sort order |
| `--time` | `all`, `year`, `month`, `week`, `day`, `hour` | `all`   | Time filter (for top/controversial) |
| `--type` | `video`, `image`, `all` | `all`   | Media type filter |
| `--include-nsfw` | — | `False` | Include NSFW (over_18) posts |
| `--limit` | integer | `100`   | Maximum posts to fetch |
| `--output` | path | subreddit name | Custom output directory |
 | `--ffmpeg` | — | `False` | Use ffmpeg to DL with sound |

### Example Output

```
Reddit Media Downloader
Target: https://www.reddit.com/r/funny
Output: /home/user/funny

Found 76 media files

Downloading ━━━━━━━━━━━━━━━━ 34/76 00:21

✓ Download complete!
Files saved to: /home/user/funny
```

## Architecture

### File Structure

```
reddit_media_downloader/
├── __init__.py       # Package initialization
├── cli.py            # CLI orchestration
├── reddit_api.py     # Reddit JSON fetching
├── extractor.py      # Media URL extraction (CRITICAL)
├── downloader.py     # HTTP downloads
```

### Data Flow

```
Reddit JSON
   ↓
fetch_posts()         # reddit_api.py
   ↓
extract_media(post)  # extractor.py → List[MediaItem]
   ↓
download_media(url)   # downloader.py
```

### Schema-Resilient Extraction

The extractor checks **multiple locations** for Reddit video URLs:

1. `post["secure_media"]["reddit_video"]["fallback_url"]`
2. `post["media"]["reddit_video"]["fallback_url"]`
3. `post["preview"]["reddit_video_preview"]["fallback_url"]`
4. `post["crosspost_parent_list"][*]` (recursive)

This ensures the tool works even when Reddit changes its JSON structure.

## Supported Media

### Reddit-Hosted Videos (v.redd.it)
- Extracts `fallback_url` from multiple schema locations
- Downloads DASH MP4 (video only, default)
- Downloads HLS MP4 (video and audio)

### Redgifs Videos
- Fetches temporary API token
- Calls Redgifs API v2: `https://api.redgifs.com/v2/gifs/{id}`
- Prefers HD quality, falls back to SD
- **No watermark**

### Images
- JPG, JPEG, PNG, WebP, GIF
- Extracted from `url_overridden_by_dest` or `url`

## Error Handling

**Philosophy:** The tool never crashes due to a single malformed post.

- **Extraction failure** → return empty list, continue
- **Download failure** → log error, continue
- **Malformed JSON** → skip post, continue
- **HTTP 403/404** → skip file, continue

The CLI **always completes execution**.

## Limitations

- **No audio merging** for DASH videos (v.redd.it video is MP4 without audio)
- **No OAuth** - uses public JSON API only
- **No rate limiting** - may hit Reddit's rate limits on large requests
- **No resumable downloads** - files are skipped if they exist

## Future Enhancements

- Audio/video muxing with ffmpeg
- User page support (`/user/{name}`)
- OAuth authentication for private subreddits
- Resumable downloads
- Parallel downloads

## License

MIT License - see repository for details.

## Author

**babydjac** - [GitHub](https://github.com/babydjac)

---

**Built with:**
- [requests](https://requests.readthedocs.io/) - HTTP library
- [rich](https://rich.readthedocs.io/) - Terminal formatting
