#!/usr/bin/env python3
"""CLI argument parsing and orchestration for Reddit media downloader."""

import argparse
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

from reddit_api import fetch_posts
from extractor import extract_media
from downloader import download_media

console = Console()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Reddit Media Downloader - Download videos and images from Reddit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  reddit --include-nsfw --sort top --time all --type video https://www.reddit.com/r/subreddit
  reddit --sort new --type image https://www.reddit.com/r/pics
  reddit --type all https://www.reddit.com/r/funny
        """,
    )

    parser.add_argument("url", help="Reddit subreddit or user URL")
    parser.add_argument(
        "--sort",
        choices=["top", "hot", "new", "controversial"],
        default="hot",
        help="Sort order (default: hot)",
    )
    parser.add_argument(
        "--time",
        choices=["all", "year", "month", "week", "day", "hour"],
        default="all",
        help="Time filter for top/controversial (default: all)",
    )
    parser.add_argument(
        "--type",
        choices=["video", "image", "all"],
        default="all",
        help="Media type to download (default: all)",
    )
    parser.add_argument(
        "--include-nsfw",
        action="store_true",
        help="Include NSFW (over_18) posts",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of posts to fetch (default: 100)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory (default: subreddit/user name)",
    )
    parser.add_argument(
        "--ffmpeg",
        action="store_true",
        help="Prefer using ffmpeg, supports audio"
    )

    return parser.parse_args()


def extract_target_name(url):
    """Extract subreddit or user name from Reddit URL."""
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]

    if len(path_parts) >= 2:
        if path_parts[0] == "r":
            return path_parts[1]
        elif path_parts[0] == "user" or path_parts[0] == "u":
            return f"user_{path_parts[1]}"

    # Fallback to last non-empty path component
    return path_parts[-1] if path_parts else "reddit_downloads"


def main():
    """Main CLI entry point."""
    args = parse_args()

    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        target_name = extract_target_name(args.url)
        output_dir = Path(target_name)



    output_dir.mkdir(parents=True, exist_ok=True)

    # Print header
    console.print("\n[bold cyan]Reddit Media Downloader[/bold cyan]")
    console.print(f"Target: {args.url}")
    console.print(f"Output: {output_dir.absolute()}")
    console.print()

    # check that system has ffmpeg before allowing flag use
    if args.ffmpeg:
        try:
            subprocess.Popen(["ffmpeg"],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).wait(1)
        except:
            console.print(f"[bold red]Error: Please install ffmpeg[/bold red]")
            sys.exit(1)

    # Fetch posts
    try:
        posts = fetch_posts(
            url=args.url,
            sort=args.sort,
            time_filter=args.time,
            limit=args.limit,
        )
    except Exception as e:
        console.print(f"[bold red]Error fetching posts:[/bold red] {e}")
        sys.exit(1)

    if not posts:
        console.print("[yellow]No posts found[/yellow]")
        sys.exit(0)

    # Extract media from posts
    all_media = []
    for post in posts:
        # Apply filters
        if not args.include_nsfw and post.get("over_18", False):
            continue
        # Extract media
        try:
            media_items = extract_media(post)
            # CRITICAL: extract_media MUST return a list
            if not isinstance(media_items, list):
                console.print(
                    f"[red]Warning: extract_media returned non-list for post {post.get('id', 'unknown')}[/red]")
                continue

            # Apply type filter
            for item in media_items:
                media_type = item.get("type", "unknown")
                if args.type == "all" or media_type == args.type:
                    all_media.append(item)
        except Exception as e:
            # Defensive: never crash on a single post
            console.print(
                f"[red]Warning: Failed to extract media from post {post.get('id', 'unknown')}: {e}[/red]"
            )
            continue

    if not all_media:
        console.print("[yellow]No media files found matching criteria[/yellow]")
        sys.exit(0)

    console.print(f"Found [bold green]{len(all_media)}[/bold green] media files\n")

    # Download media with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading", total=len(all_media))
        for item in all_media:
            try:
                if "hls_playlist" in item and args.ffmpeg:
                    download_media(
                    url=item["url"],
                    output_path=output_dir / item["filename"],
                    hls_url=item["hls_playlist"],
                    )
                else:
                    download_media(
                        url=item["url"],
                        output_path=output_dir / item["filename"],
                    )
            except Exception as e:
                # Defensive: log error but continue
                console.print(
                    f"\n[red]Failed to download {item['filename']}: {e}[/red]",
                )
            progress.advance(task)

    console.print(f"\n[bold green]✓[/bold green] Download complete!")
    console.print(f"Files saved to: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
