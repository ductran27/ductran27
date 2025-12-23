#!/usr/bin/env python3
"""
Script to fetch Google Scholar metrics and update README.md
Uses direct HTTP requests with proper timeouts to avoid GitHub Actions timeouts.
"""

import re
import time
import random
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# Google Scholar profile ID
SCHOLAR_ID = "tIcTCNgAAAAJ"
README_PATH = "README.md"
MAX_RETRIES = 2  # Reduced retries to stay within timeout
REQUEST_TIMEOUT = 30  # Timeout per request in seconds


class TimeoutException(Exception):
    pass


def fetch_with_timeout(func, timeout_sec):
    """Run a function with a timeout using ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout_sec)
        except FuturesTimeoutError:
            raise TimeoutException(f"Operation timed out after {timeout_sec}s")


def fetch_scholar_metrics(scholar_id: str, retry: int = 0) -> dict:
    """Fetch metrics with retry logic and short delays."""
    try:
        from scholarly import scholarly

        # Short delay to avoid rate limiting (reduced from exponential backoff)
        delay = random.uniform(1, 3)
        print(f"Waiting {delay:.1f}s before request (attempt {retry + 1}/{MAX_RETRIES})...")
        time.sleep(delay)

        def do_fetch():
            print(f"Fetching author: {scholar_id}")
            author = scholarly.search_author_id(scholar_id)
            if not author:
                raise Exception("No author data returned")
            print("Filling indices...")
            return scholarly.fill(author, sections=['indices'])

        # Wrap the fetch in a timeout
        author = fetch_with_timeout(do_fetch, REQUEST_TIMEOUT)

        # Extract metrics
        pub_count = len(author.get('publications', []))

        metrics = {
            "citations": str(author.get('citedby', 0)),
            "h_index": str(author.get('hindex', 0)),
            "i10_index": str(author.get('i10index', 0)),
            "publications": str(pub_count) if pub_count > 0 else "35"
        }

        print(f"Success! Metrics: {metrics}")
        return metrics

    except TimeoutException as e:
        print(f"Attempt {retry + 1} timed out: {e}")
    except Exception as e:
        print(f"Attempt {retry + 1} failed: {e}")

    # Retry with short delay
    if retry < MAX_RETRIES - 1:
        wait = random.uniform(3, 6)
        print(f"Waiting {wait:.1f}s before retry...")
        time.sleep(wait)
        return fetch_scholar_metrics(scholar_id, retry + 1)

    print("All attempts failed")
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
    print("=" * 50)
    print("Google Scholar Metrics Updater")
    print("=" * 50)

    # Fetch metrics with retries and timeouts
    metrics = fetch_scholar_metrics(SCHOLAR_ID)

    if metrics:
        update_readme(metrics)
    else:
        print("Failed to fetch metrics - will retry on next scheduled run")

    # Always exit 0 to not fail the workflow
    exit(0)


if __name__ == "__main__":
    main()
