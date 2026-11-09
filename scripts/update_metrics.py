#!/usr/bin/env python3
"""Read the Google Scholar metrics of the profile (citations, h-index,
i10-index) and write them into the badges of README.md.

The read runs in a child process with a hard time limit, as scholarly can hang
on a slow or blocked request. Google Scholar sometimes refuses the runners of
GitHub Actions; the badges then keep their values and the run passes, to try
again at the next schedule. A broken install (a missing module, an API change
of scholarly) fails the run instead, so that it is seen: until November 2026
bibtexparser 2 broke the import of scholarly and every run passed without an
update for two months.

The Publications badge is set by hand: Google Scholar also lists abstracts and
talks, so its count is not the number of papers.
"""
import multiprocessing
import random
import re
import sys
import time

SCHOLAR_ID = "tIcTCNgAAAAJ"
README_PATH = "README.md"
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


def update_readme(m):
    with open(README_PATH, encoding="utf-8") as f:
        text = f.read()
    new = re.sub(r"(badge/H--Index-)\d+(-)", r"\g<1>%d\2" % m["h_index"], text)
    new = re.sub(r"(badge/Citations-)[0-9,]+\+?(-)", r"\g<1>{:,}\2".format(m["citations"]), new)
    new = re.sub(r"(badge/i10--Index-)\d+(-)", r"\g<1>%d\2" % m["i10_index"], new)
    if new == text:
        print("README metrics already up to date")
        return
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new)
    print("README metrics updated")


def main():
    metrics = fetch()
    if metrics:
        update_readme(metrics)
    else:
        print("Google Scholar did not answer; the badges keep their values")
    return 0


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    sys.exit(main())
