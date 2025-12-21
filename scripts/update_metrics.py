#!/usr/bin/env python3
"""
Script to fetch Google Scholar metrics and update README.md
"""

import re
import time
import random

# Google Scholar profile ID
SCHOLAR_ID = "tIcTCNgAAAAJ"
README_PATH = "README.md"


def fetch_scholar_metrics(scholar_id: str) -> dict:
    """Fetch metrics using scholarly package."""
    try:
        from scholarly import scholarly

        # Add random delay to appear more human-like
        time.sleep(random.uniform(2, 5))

        # Search for the author by ID - this returns basic metrics
        author = scholarly.search_author_id(scholar_id)

        # Only fill indices section (fast) - skip publications (very slow)
        # The basic metrics (citedby, hindex, i10index) are in the initial response
        # We use fill with indices only to ensure we have the latest values
        author = scholarly.fill(author, sections=['indices'])

        metrics = {
            "citations": str(author.get('citedby', 0)),
            "h_index": str(author.get('hindex', 0)),
            "i10_index": str(author.get('i10index', 0)),
            "publications": "30"  # Static value - fetching all pubs is too slow
        }

        return metrics

    except Exception as e:
        print(f"Error with scholarly: {e}")
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
            # Format with comma for thousands
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
            print(f"New metrics: {metrics}")
            return True
        else:
            print("No changes needed - metrics are up to date")
            return False

    except Exception as e:
        print(f"Error updating README: {e}")
        return False


def main():
    print("Fetching Google Scholar metrics...")
    metrics = fetch_scholar_metrics(SCHOLAR_ID)

    if metrics:
        print(f"Fetched metrics: {metrics}")
        update_readme(metrics)
    else:
        print("Failed to fetch metrics - will retry on next scheduled run")
        # Exit with 0 to not fail the workflow
        # Metrics will be updated on next successful fetch
        exit(0)


if __name__ == "__main__":
    main()
