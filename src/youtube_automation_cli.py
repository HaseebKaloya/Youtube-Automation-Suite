#!/usr/bin/env python3
"""
YouTube Automation Suite - Command Line Interface
Automated batch interactions (Like, Comment, Subscribe) using the YouTube Data API v3.

Developer: Haseeb Kaloya
Email: contact.haseebkaloya@gmail.com
License: MIT
"""

import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import List, Optional, Set

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    class _StyleFallback:
        def __getattr__(self, _):
            return ""

    Fore = _StyleFallback()
    Style = _StyleFallback()

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    Request = Credentials = InstalledAppFlow = build = HttpError = None

# ----------------- Configuration Defaults -----------------
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
DEFAULT_CREDENTIALS = "credentials.json"
DEFAULT_TOKEN = "token.json"
DEFAULT_LOG_CSV = "Logs.csv"
DEFAULT_LOG_FILE = "youtube_automation.log"
DEFAULT_PROCESSED_DIR = "processed_state"

DEFAULT_DELAY_SECONDS = 4.0
DEFAULT_JITTER = 2.0
MAX_RETRIES = 5
BASE_BACKOFF = 1.0


def setup_logging(log_file: str = DEFAULT_LOG_FILE) -> logging.Logger:
    """Configures application-level file and console logging."""
    logger = logging.getLogger("youtube_automation")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    return logger


logger = setup_logging()


# ----------------- Utility Functions -----------------
def clear_screen() -> None:
    """Clear terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    """Display clean, professional application header."""
    print(Fore.CYAN + Style.BRIGHT + "============================================================")
    print(Fore.CYAN + Style.BRIGHT + "               YouTube Automation Suite v1.0.0              ")
    print(Fore.CYAN + Style.BRIGHT + "============================================================")
    print(Fore.WHITE + "Developer: Haseeb Kaloya | contact.haseebkaloya@gmail.com")
    print(Fore.YELLOW + "Note: Operate only on accounts and targets you control.\n")


def prompt_user(msg: str, default: Optional[str] = None) -> str:
    """Read user prompt with optional default fallback."""
    try:
        if default:
            val = input(f"{msg} [{default}]: ").strip()
            return val if val != "" else default
        return input(f"{msg}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


def ensure_directory(path: str) -> None:
    """Ensure directory exists on disk."""
    os.makedirs(path, exist_ok=True)


def current_timestamp() -> str:
    """Format current ISO timestamp."""
    return time.strftime("%Y-%m-%d %H:%M:%S")


def write_csv_log(log_path: str, action: str, target_id: str, status: str, note: str = "") -> None:
    """Write structured execution records to CSV."""
    header_needed = not os.path.exists(log_path) or os.path.getsize(log_path) == 0
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header_needed:
            writer.writerow(["timestamp", "action", "target_id", "status", "note"])
        writer.writerow([current_timestamp(), action, target_id, status, note])


def load_processed_state(action: str, state_dir: str = DEFAULT_PROCESSED_DIR) -> Set[str]:
    """Load previously processed item identifiers to avoid duplicate work."""
    ensure_directory(state_dir)
    file_path = os.path.join(state_dir, f"processed_{action}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            logger.warning("Could not read state file %s: %s", file_path, e)
            return set()
    return set()


def save_processed_state(action: str, processed_set: Set[str], state_dir: str = DEFAULT_PROCESSED_DIR) -> None:
    """Save processed item identifiers to disk."""
    ensure_directory(state_dir)
    file_path = os.path.join(state_dir, f"processed_{action}.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sorted(list(processed_set)), f, indent=2)
    except Exception as e:
        logger.error("Failed to save state file %s: %s", file_path, e)


# ----------------- Identifier Extractors -----------------
def extract_video_id(input_str: str) -> Optional[str]:
    """
    Extracts an 11-character YouTube video ID from direct IDs, watch URLs,
    shortened youtu.be URLs, shorts, or embed URLs.
    """
    if not input_str:
        return None
    s = input_str.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = re.search(r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})", s)
    if m:
        return m.group(1)
    return None


def extract_channel_id(input_str: str) -> Optional[str]:
    """Extract direct UC channel ID from URL or bare string."""
    if not input_str:
        return None
    s = input_str.strip()
    m = re.search(r"youtube\.com/(?:channel/)(UC[0-9A-Za-z_-]{20,})", s)
    if m:
        return m.group(1)
    if s.startswith("UC") and len(s) >= 22:
        return s
    return None


def resolve_channel_id(youtube, input_str: str) -> Optional[str]:
    """
    Resolves a channel URL, @handle, or search term into a canonical UC channel ID.
    """
    if not input_str:
        return None
    s = input_str.strip()

    direct_id = extract_channel_id(s)
    if direct_id:
        return direct_id

    # Handle @username
    m = re.search(r"@([A-Za-z0-9_\.]+)", s)
    if m:
        handle = m.group(1)
        try:
            resp = youtube.channels().list(part="id", forHandle=handle).execute()
            items = resp.get("items", [])
            if items:
                return items[0].get("id")
        except HttpError:
            pass
        except Exception as e:
            logger.debug("forHandle failed for %s: %s", handle, e)

        # Fallback to search by handle
        try:
            resp = youtube.search().list(part="snippet", q=handle, type="channel", maxResults=1).execute()
            items = resp.get("items", [])
            if items:
                return items[0]["snippet"].get("channelId")
        except Exception as e:
            logger.debug("search fallback failed for %s: %s", handle, e)
        return None

    # Generic search for query string
    try:
        resp = youtube.search().list(part="snippet", q=s, type="channel", maxResults=1).execute()
        items = resp.get("items", [])
        if items:
            return items[0]["snippet"].get("channelId")
    except Exception as e:
        logger.debug("Generic channel search failed for %s: %s", s, e)

    return None


# ----------------- Authentication & API -----------------
def get_authenticated_service(credentials_path: str = DEFAULT_CREDENTIALS, token_path: str = DEFAULT_TOKEN):
    """
    Handles OAuth 2.0 flow, loads cached tokens, refreshes if expired,
    or triggers browser consent if needed.
    """
    if not GOOGLE_API_AVAILABLE:
        raise ImportError(
            "Missing required Google client libraries. Please install them with:\n"
            "pip install google-auth google-auth-oauthlib google-api-python-client"
        )
    creds = None
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            logger.warning("Could not read token file (%s): %s", token_path, e)
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        except Exception as e:
            logger.warning("Token refresh failed: %s", e)
            creds = None

    if not creds or not creds.valid:
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Missing OAuth client secret file at '{credentials_path}'. "
                f"Download credentials.json from Google Cloud Console and place it in the project root."
            )
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent", authorization_prompt_message="")
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        logger.info("Saved authentication token to %s", token_path)

    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def call_with_backoff(fn, *args, max_retries: int = MAX_RETRIES, **kwargs):
    """Executes a callable with exponential backoff on retryable HTTP errors."""
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except HttpError as e:
            status = getattr(e.resp, "status", None)
            if status:
                try:
                    status = int(status)
                except ValueError:
                    pass
            # Retry on rate limit (429), quota lock (403), or server errors (5xx)
            if status in (429, 403) or (isinstance(status, int) and 500 <= status < 600):
                attempt += 1
                if attempt > max_retries:
                    raise
                wait_time = BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0.5, 1.5)
                logger.warning("HTTP %s encountered. Backing off for %.2fs (attempt %d/%d)", status, wait_time, attempt, max_retries)
                time.sleep(wait_time)
                continue
            raise
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                raise
            wait_time = BASE_BACKOFF * (2 ** (attempt - 1)) + random.uniform(0.5, 1.5)
            logger.warning("Request error: %s. Retrying in %.2fs (attempt %d/%d)", e, wait_time, attempt, max_retries)
            time.sleep(wait_time)


# ----------------- Input Parsers -----------------
def parse_video_ids_file(file_path: str) -> List[str]:
    """Parse and deduplicate video IDs from input file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    vids, seen = [], set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            vid = extract_video_id(raw)
            if vid and vid not in seen:
                seen.add(vid)
                vids.append(vid)
            elif not vid:
                logger.warning("Skipping invalid video entry: %s", raw)
    return vids


def parse_comments_file(file_path: str) -> List[str]:
    """Parse comments from input file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    comments = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if raw:
                comments.append(raw)
    return comments


def parse_channel_ids_file(file_path: str, youtube) -> List[str]:
    """Parse and resolve channel identifiers from input file."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    channels, seen = [], set()
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            cid = resolve_channel_id(youtube, raw)
            if cid and cid not in seen:
                seen.add(cid)
                channels.append(cid)
                logger.info("Resolved '%s' -> %s", raw, cid)
            elif not cid:
                logger.warning("Could not resolve channel entry: %s", raw)
    return channels


# ----------------- Action Runners -----------------
def run_likes(youtube, input_file: str, delay: float, jitter: float, log_csv: str = DEFAULT_LOG_CSV) -> int:
    """Executes automated video likes."""
    video_ids = parse_video_ids_file(input_file)
    processed = load_processed_state("like")
    logger.info("Found %d video(s) to process. (%d already processed)", len(video_ids), len(processed))

    success_count = 0
    try:
        for idx, vid in enumerate(video_ids, start=1):
            if vid in processed:
                logger.info("[%d/%d] Skipping already liked video: %s", idx, len(video_ids), vid)
                continue

            logger.info("[%d/%d] Liking video: %s", idx, len(video_ids), vid)
            try:
                call_with_backoff(lambda: youtube.videos().rate(id=vid, rating="like").execute())
                write_csv_log(log_csv, "like", vid, "success", "")
                processed.add(vid)
                save_processed_state("like", processed)
                success_count += 1
                logger.info("Successfully liked video: %s", vid)
            except HttpError as e:
                code = getattr(e.resp, "status", "Error")
                logger.error("HTTP error liking %s: %s", vid, code)
                write_csv_log(log_csv, "like", vid, "failed", f"HTTP {code}")
            except Exception as e:
                logger.error("Error liking %s: %s", vid, e)
                write_csv_log(log_csv, "like", vid, "failed", str(e))

            sleep_duration = max(0.5, delay + random.uniform(-jitter, jitter))
            time.sleep(sleep_duration)
    finally:
        save_processed_state("like", processed)

    return success_count


def run_subscribes(youtube, input_file: str, delay: float, jitter: float, log_csv: str = DEFAULT_LOG_CSV) -> int:
    """Executes automated channel subscriptions."""
    channel_ids = parse_channel_ids_file(input_file, youtube)
    processed = load_processed_state("subscribe")
    logger.info("Found %d channel(s) to process. (%d already processed)", len(channel_ids), len(processed))

    success_count = 0
    try:
        for idx, cid in enumerate(channel_ids, start=1):
            if cid in processed:
                logger.info("[%d/%d] Skipping already subscribed channel: %s", idx, len(channel_ids), cid)
                continue

            logger.info("[%d/%d] Subscribing to channel: %s", idx, len(channel_ids), cid)
            try:
                body = {"snippet": {"resourceId": {"kind": "youtube#channel", "channelId": cid}}}
                resp = call_with_backoff(lambda: youtube.subscriptions().insert(part="snippet", body=body).execute())
                sub_id = resp.get("id", "") if isinstance(resp, dict) else ""
                write_csv_log(log_csv, "subscribe", cid, "success", str(sub_id))
                processed.add(cid)
                save_processed_state("subscribe", processed)
                success_count += 1
                logger.info("Successfully subscribed to channel: %s", cid)
            except HttpError as e:
                code = getattr(e.resp, "status", "Error")
                logger.error("HTTP error subscribing to %s: %s", cid, code)
                write_csv_log(log_csv, "subscribe", cid, "failed", f"HTTP {code}")
            except Exception as e:
                logger.error("Error subscribing to %s: %s", cid, e)
                write_csv_log(log_csv, "subscribe", cid, "failed", str(e))

            sleep_duration = max(0.5, delay + random.uniform(-jitter, jitter))
            time.sleep(sleep_duration)
    finally:
        save_processed_state("subscribe", processed)

    return success_count


def run_comments(youtube, input_file: str, target_video: str, delay: float, jitter: float, log_csv: str = DEFAULT_LOG_CSV) -> int:
    """Executes automated comment posting."""
    vid = extract_video_id(target_video)
    if not vid:
        raise ValueError(f"Invalid target video identifier: {target_video}")

    comments = parse_comments_file(input_file)
    processed = load_processed_state("comment")
    logger.info("Posting %d comment(s) to video %s", len(comments), vid)

    success_count = 0
    try:
        for idx, text in enumerate(comments, start=1):
            item_key = f"{vid}::{hash(text)}"
            if item_key in processed:
                logger.info("[%d/%d] Skipping duplicate comment: %.50s...", idx, len(comments), text)
                continue

            logger.info("[%d/%d] Posting comment: %.60s...", idx, len(comments), text)
            try:
                body = {
                    "snippet": {
                        "videoId": vid,
                        "topLevelComment": {"snippet": {"textOriginal": text}},
                    }
                }
                resp = call_with_backoff(lambda: youtube.commentThreads().insert(part="snippet", body=body).execute())
                comment_id = resp.get("id", "") if isinstance(resp, dict) else ""
                write_csv_log(log_csv, "comment", vid, "success", comment_id)
                processed.add(item_key)
                save_processed_state("comment", processed)
                success_count += 1
                logger.info("Comment posted successfully (id: %s)", comment_id)
            except HttpError as e:
                code = getattr(e.resp, "status", "Error")
                logger.error("HTTP error posting comment on %s: %s", vid, code)
                write_csv_log(log_csv, "comment", vid, "failed", f"HTTP {code}")
            except Exception as e:
                logger.error("Error posting comment on %s: %s", vid, e)
                write_csv_log(log_csv, "comment", vid, "failed", str(e))

            sleep_duration = max(0.5, delay + random.uniform(-jitter, jitter))
            time.sleep(sleep_duration)
    finally:
        save_processed_state("comment", processed)

    return success_count


# ----------------- CLI Dispatcher -----------------
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="YouTube Automation Suite - CLI bulk like, comment, and subscribe tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m src.youtube_automation_cli --action like --file examples/likes.txt\n"
            "  python -m src.youtube_automation_cli --action subscribe --file examples/channels.txt\n"
            "  python -m src.youtube_automation_cli --action comment --file examples/comments.txt --video <VIDEO_ID>\n"
            "  python -m src.youtube_automation_cli  # Launches interactive wizard\n"
        ),
    )
    parser.add_argument("--action", choices=["like", "comment", "subscribe", "all"], help="Automation action to run")
    parser.add_argument("--file", help="Path to input text file")
    parser.add_argument("--video", help="Target video ID or URL (required when action is 'comment')")
    parser.add_argument("--credentials", default=DEFAULT_CREDENTIALS, help="Path to OAuth credentials.json")
    parser.add_argument("--token", default=DEFAULT_TOKEN, help="Path to token.json")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS, help="Base delay between actions (seconds)")
    parser.add_argument("--jitter", type=float, default=DEFAULT_JITTER, help="Random jitter (+/- seconds)")
    parser.add_argument("--log-csv", default=DEFAULT_LOG_CSV, help="Path to CSV execution log")
    return parser.parse_args()


def interactive_wizard() -> None:
    """Interactive wizard for user-guided automation setup."""
    clear_screen()
    print_banner()

    print("Choose action:")
    print("  [1] like       - Bulk like videos")
    print("  [2] comment    - Post comments to a video")
    print("  [3] subscribe  - Bulk subscribe to channels")
    print("  [4] all        - Run all three actions in sequence")
    choice = prompt_user("Select option [1-4 or name]", "1").lower()

    action_map = {"1": "like", "2": "comment", "3": "subscribe", "4": "all"}
    chosen_action = action_map.get(choice, choice)

    creds_path = prompt_user("Path to credentials.json", DEFAULT_CREDENTIALS)
    token_path = prompt_user("Path to token.json", DEFAULT_TOKEN)

    try:
        delay = float(prompt_user("Base delay in seconds", str(DEFAULT_DELAY_SECONDS)))
        jitter = float(prompt_user("Jitter in seconds", str(DEFAULT_JITTER)))
    except ValueError:
        delay, jitter = DEFAULT_DELAY_SECONDS, DEFAULT_JITTER

    try:
        youtube = get_authenticated_service(creds_path, token_path)
    except Exception as e:
        print(Fore.RED + f"\nAuthentication failed: {e}")
        sys.exit(1)

    print(Fore.GREEN + "\nAuthentication successful. Starting selected tasks...\n")

    if chosen_action in ("like", "all"):
        fpath = prompt_user("Path to likes.txt", "examples/likes.txt")
        run_likes(youtube, fpath, delay, jitter)

    if chosen_action in ("subscribe", "all"):
        fpath = prompt_user("Path to channels.txt", "examples/channels.txt")
        run_subscribes(youtube, fpath, delay, jitter)

    if chosen_action in ("comment", "all"):
        fpath = prompt_user("Path to comments.txt", "examples/comments.txt")
        target_vid = prompt_user("Target video ID or URL")
        run_comments(youtube, fpath, target_vid, delay, jitter)

    print(Fore.GREEN + f"\nAll operations completed. Records saved to {DEFAULT_LOG_CSV}.")


def main() -> None:
    """Main CLI entrypoint."""
    args = parse_arguments()

    # If no flags passed, launch interactive wizard
    if not args.action:
        interactive_wizard()
        return

    # Headless / flag-driven execution
    print_banner()
    try:
        youtube = get_authenticated_service(args.credentials, args.token)
    except Exception as e:
        logger.error("Authentication failed: %s", e)
        sys.exit(1)

    if args.action == "like":
        if not args.file:
            logger.error("--file is required when running the 'like' action.")
            sys.exit(1)
        run_likes(youtube, args.file, args.delay, args.jitter, args.log_csv)

    elif args.action == "subscribe":
        if not args.file:
            logger.error("--file is required when running the 'subscribe' action.")
            sys.exit(1)
        run_subscribes(youtube, args.file, args.delay, args.jitter, args.log_csv)

    elif args.action == "comment":
        if not args.file or not args.video:
            logger.error("Both --file and --video are required when running the 'comment' action.")
            sys.exit(1)
        run_comments(youtube, args.file, args.video, args.delay, args.jitter, args.log_csv)

    elif args.action == "all":
        logger.error("When using flags, please specify a single action ('like', 'comment', or 'subscribe').")
        sys.exit(1)

    logger.info("Task completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nExecution interrupted by user.")
        sys.exit(0)
