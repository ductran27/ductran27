#!/usr/bin/env python3
"""
Script to fetch Google Scholar metrics and update README.md
Uses multiprocessing with hard timeouts to prevent GitHub Actions timeouts.
"""

import re
import time
import random
import multiprocessing
import sys

# Google Scholar profile ID
SCHOLAR_ID = "tIcTCNgAAAAJ"
README_PATH = "README.md"
MAX_RETRIES = 2  # Reduced retries to stay within timeout
REQUEST_TIMEOUT = 60  # Timeout per request in seconds


def _fetch_worker(scholar_id: str, result_queue):
    """Worker function that runs in a separate process."""
    try:
        # Import scholarly inside the worker to isolate any import hangs
        from scholarly import scholarly

        print(f"Fetching author: {scholar_id}", flush=True)
        author = scholarly.search_author_id(scholar_id)

        if not author:
            result_queue.put({"error": "No author data returned"})
            return

        print("Filling indices...", flush=True)
        author = scholarly.fill(author, sections=['indices'])

        # Extract metrics
        pub_count = len(author.get('publications', []))

        metrics = {
            "citations": str(author.get('citedby', 0)),
            "h_index": str(author.get('hindex', 0)),
            "i10_index": str(author.get('i10index', 0)),
            "publications": str(pub_count) if pub_count > 0 else "35"
        }

        result_queue.put({"metrics": metrics})

    except Exception as e:
        result_queue.put({"error": str(e)})


def fetch_scholar_metrics(scholar_id: str, retry: int = 0) -> dict:
    """Fetch metrics with retry logic using multiprocessing for hard timeout."""
    print(f"Attempt {retry + 1}/{MAX_RETRIES}...", flush=True)

    # Short delay to avoid rate limiting
    delay = random.uniform(1, 3)
    print(f"Waiting {delay:.1f}s before request...", flush=True)
    time.sleep(delay)

    # Use multiprocessing to enable hard timeout (can actually kill hung processes)
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_fetch_worker,
        args=(scholar_id, result_queue)
    )

    process.start()
    process.join(timeout=REQUEST_TIMEOUT)

    if process.is_alive():
        print(f"Request timed out after {REQUEST_TIMEOUT}s, terminating...", flush=True)
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join()

    # Check for results
    if not result_queue.empty():
        result = result_queue.get_nowait()
        if "metrics" in result:
            print(f"Success! Metrics: {result['metrics']}", flush=True)
            return result["metrics"]
        elif "error" in result:
            print(f"Error: {result['error']}", flush=True)
    else:
        print("No result received (process timed out or crashed)", flush=True)

    # Retry with short delay
    if retry < MAX_RETRIES - 1:
        wait = random.uniform(3, 6)
        print(f"Waiting {wait:.1f}s before retry...", flush=True)
        time.sleep(wait)
        return fetch_scholar_metrics(scholar_id, retry + 1)

    print("All attempts failed", flush=True)
    return None


def update_readme(metrics: dict) -> bool:
    """Update the README.md with new metrics."""
    if not metrics:
        print("No metrics to update")
        return False

    try:
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Update H-Index
        if "h_index" in metrics:
            content = re.sub(
                r'(H--Index-)\d+(-blue)',
                f'\\g<1>{metrics["h_index"]}\\2',
                content
            )

        # Update Citations (exact number, no +)
        if "citations" in metrics:
            citations = metrics["citations"].replace(",", "")
            citations_formatted = f"{int(citations):,}"
            content = re.sub(
                r'(Citations-)[0-9,]+\+?(-green)',
                f'\\g<1>{citations_formatted}\\2',
                content
            )

        # Update Publications
        if "publications" in metrics:
            pubs = metrics["publications"].rstrip("+")
            content = re.sub(
                r'(Publications-)\d+\+?(-orange)',
                f'\\g<1>{pubs}+\\2',
                content
            )

        # Update i10-Index
        if "i10_index" in metrics:
            content = re.sub(
                r'(i10--Index-)\d+(-a855f7)',
                f'\\g<1>{metrics["i10_index"]}\\2',
                content
            )

        if content != original_content:
            with open(README_PATH, "w", encoding="utf-8") as f:
                f.write(content)
            print("README.md updated successfully!")
            return True
        else:
            print("No changes needed - metrics are up to date")
            return False

    except Exception as e:
        print(f"Error updating README: {e}")
        return False


def main():
    print("=" * 50, flush=True)
    print("Google Scholar Metrics Updater", flush=True)
    print("=" * 50, flush=True)

    # Fetch metrics with retries and hard timeouts
    metrics = fetch_scholar_metrics(SCHOLAR_ID)

    if metrics:
        update_readme(metrics)
    else:
        print("Failed to fetch metrics - will retry on next scheduled run")

    # Always exit 0 to not fail the workflow
    sys.exit(0)


if __name__ == "__main__":
    # Required for multiprocessing on some platforms
    multiprocessing.set_start_method('spawn', force=True)
    main()
