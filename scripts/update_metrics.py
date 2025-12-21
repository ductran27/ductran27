#!/usr/bin/env python3
"""
Script to fetch Google Scholar metrics and update README.md
Runs via GitHub Actions at scheduled times.
"""

import re
import requests
from bs4 import BeautifulSoup
import os

# Google Scholar profile ID
SCHOLAR_ID = "tIcTCNgAAAAJ"
README_PATH = "README.md"


def fetch_scholar_metrics(scholar_id: str) -> dict:
    """Fetch metrics from Google Scholar profile page."""
    url = f"https://scholar.google.com/citations?user={scholar_id}&hl=en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the stats table
        stats_table = soup.find("table", {"id": "gsc_rsb_st"})
        if not stats_table:
            print("Could not find stats table on Google Scholar page")
            return None

        rows = stats_table.find_all("tr")
        metrics = {}

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                label = cells[0].text.strip().lower()
                value = cells[1].text.strip()

                if "citations" in label:
                    metrics["citations"] = value
                elif "h-index" in label:
                    metrics["h_index"] = value
                elif "i10-index" in label:
                    metrics["i10_index"] = value

        # Get publication count from the profile
        pub_count = soup.find("span", {"id": "gsc_a_nn"})
        if pub_count:
            metrics["publications"] = pub_count.text.strip()
        else:
            # Count rows in publications table as fallback
            pub_table = soup.find("table", {"id": "gsc_a_t"})
            if pub_table:
                pub_rows = pub_table.find_all("tr", {"class": "gsc_a_tr"})
                metrics["publications"] = str(len(pub_rows)) + "+"

        return metrics

    except Exception as e:
        print(f"Error fetching Google Scholar data: {e}")
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

        # Update Citations
        if "citations" in metrics:
            citations = metrics["citations"].replace(",", ",")
            content = re.sub(
                r'(Citations-)[0-9,]+\+?(-green)',
                f'\\g<1>{citations}+\\2',
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
        print("Failed to fetch metrics")
        exit(1)


if __name__ == "__main__":
    main()
