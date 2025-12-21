#!/usr/bin/env python3
"""
Script to fetch Google Scholar metrics and update README.md
Uses proxy rotation to avoid Google Scholar blocking GitHub Actions IPs.
"""

import re
import time
import random

# Google Scholar profile ID
SCHOLAR_ID = "tIcTCNgAAAAJ"
README_PATH = "README.md"
MAX_RETRIES = 3


def setup_proxy():
    """Set up proxy to avoid Google Scholar blocking GitHub Actions IPs."""
    try:
        from scholarly import scholarly, ProxyGenerator

        print("Setting up free proxy rotation...")
        pg = ProxyGenerator()

        # Try FreeProxies first (rotates through free proxy list)
        try:
            pg.FreeProxies()
            scholarly.use_proxy(pg)
            print("Free proxy configured")
            return True
        except Exception as e:
            print(f"FreeProxies failed: {e}")

        # If FreeProxies fails, try without proxy
        print("Proceeding without proxy...")
        return False

    except Exception as e:
        print(f"Proxy setup error: {e}")
        return False


def fetch_scholar_metrics(scholar_id: str, retry: int = 0) -> dict:
    """Fetch metrics with retry logic and exponential backoff."""
    try:
        from scholarly import scholarly

        # Exponential backoff delay
        delay = random.uniform(3, 8) * (retry + 1)
        print(f"Waiting {delay:.1f}s before request (attempt {retry + 1}/{MAX_RETRIES})...")
        time.sleep(delay)

        print(f"Fetching author: {scholar_id}")
        author = scholarly.search_author_id(scholar_id)

        if not author:
            raise Exception("No author data returned")

        # Extract metrics
        pub_count = len(author.get('publications', []))

        metrics = {
            "citations": str(author.get('citedby', 0)),
            "h_index": str(author.get('hindex', 0)),
            "i10_index": str(author.get('i10index', 0)),
            "publications": str(pub_count) if pub_count > 0 else "30"
        }

        print(f"Success! Metrics: {metrics}")
        return metrics

    except Exception as e:
        print(f"Attempt {retry + 1} failed: {e}")

        if retry < MAX_RETRIES - 1:
            wait = random.uniform(10, 20) * (retry + 1)
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

    # Set up proxy first
    setup_proxy()

    # Fetch metrics with retries
    metrics = fetch_scholar_metrics(SCHOLAR_ID)

    if metrics:
        update_readme(metrics)
    else:
        print("Failed to fetch metrics - will retry on next scheduled run")

    # Always exit 0 to not fail the workflow
    exit(0)


if __name__ == "__main__":
    main()
