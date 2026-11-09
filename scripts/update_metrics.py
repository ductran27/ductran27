#!/usr/bin/env python3
"""Read the Google Scholar metrics of the profile (citations, h-index,
i10-index) and write them into scripts/profile.json, from which
github_cards.py draws the images of the README.

The read runs in a child process with a hard time limit, as scholarly can hang
on a slow or blocked request. Google Scholar sometimes refuses the runners of
GitHub Actions; the numbers then keep their values and the run passes, to try
again at the next schedule. A broken install (a missing module, an API change
of scholarly) fails the run instead, so that it is seen: until November 2026
bibtexparser 2 broke the import of scholarly and every run passed without an
update for two months.

The number of papers is set by hand in profile.json: Google Scholar also lists
abstracts and talks, so its count is not the number of papers.
"""
import multiprocessing
import random
import sys
import time

from profile_art import load, save

SCHOLAR_ID = "tIcTCNgAAAAJ"
ATTEMPTS = 2
TIME_LIMIT = 60          # seconds per attempt
CODE_ERRORS = ("ImportError", "ModuleNotFoundError", "AttributeError", "TypeError", "NameError")


def _fetch(scholar_id, queue):
    try:
        from scholarly import scholarly
        author = scholarly.search_author_id(scholar_id)
        if not author:
            queue.put({"error": "no author data", "kind": "empty"})
            return
        author = scholarly.fill(author, sections=["indices"])
        queue.put({"metrics": {"citations": int(author.get("citedby") or 0),
                               "h_index": int(author.get("hindex") or 0),
                               "i10_index": int(author.get("i10index") or 0)}})
    except Exception as e:
        queue.put({"error": "%s: %s" % (type(e).__name__, e), "kind": type(e).__name__})


def fetch():
    """The metrics, or None after ATTEMPTS failed reads. Exits 1 on a code error."""
    for attempt in range(1, ATTEMPTS + 1):
        time.sleep(random.uniform(1, 3))
        print("attempt %d of %d" % (attempt, ATTEMPTS), flush=True)
        queue = multiprocessing.Queue()
        proc = multiprocessing.Process(target=_fetch, args=(SCHOLAR_ID, queue))
        proc.start()
        proc.join(TIME_LIMIT)
        if proc.is_alive():
            print("no answer in %d s" % TIME_LIMIT, flush=True)
            proc.terminate()
            proc.join(5)
            if proc.is_alive():
                proc.kill()
                proc.join()
        result = queue.get_nowait() if not queue.empty() else {"error": "no result", "kind": "timeout"}
        if "metrics" in result:
            m = result["metrics"]
            if m["citations"] and m["h_index"]:
                print("metrics:", m, flush=True)
                return m
            result = {"error": "empty metrics %s" % m, "kind": "empty"}
        print("failed:", result["error"], flush=True)
        if result["kind"] in CODE_ERRORS:
            print("this is an error of the code or of its packages, not of Google Scholar", flush=True)
            sys.exit(1)
        if attempt < ATTEMPTS:
            time.sleep(random.uniform(3, 6))
    return None


def update_profile(m):
    d = load()
    if d["scholar"] == m:
        print("metrics already up to date")
        return
    d["scholar"] = m
    save(d)
    print("metrics updated")


def main():
    metrics = fetch()
    if metrics:
        update_profile(metrics)
    else:
        print("Google Scholar did not answer; the numbers keep their values")
    return 0


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    sys.exit(main())
