#!/usr/bin/env python3
"""Read the GitHub numbers of the profile (commits, stars, repositories,
followers, languages, stars of the featured repositories) into
scripts/profile.json and draw the images of the README from it (assets/).

Tokens (environment):
  GITHUB_TOKEN          the token of the workflow: public data only
  PROFILE_STATS_TOKEN   optional, a token that can list the private repositories
                        of the account (fine grained, Metadata read only, all
                        repositories); without it the repository count keeps
                        its value

A failed request keeps the numbers as they are and the images are drawn from
them, so a passing outage of the API does not fail the workflow. A bug in this
script fails it.
"""
import json
import os
import sys
import urllib.error
import urllib.request

from profile_art import draw, load, save

USER = "ductran27"
API = "https://api.github.com"
OTHER = "#8b949e"


class ApiError(Exception):
    pass


def request(url, token, body=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER + "-profile"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise ApiError("%s: %s" % (url, e)) from e


QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        name
        stargazerCount
        primaryLanguage { name color }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def github_numbers(d, token):
    data = request(API + "/graphql", token, {"query": QUERY, "variables": {"login": USER}})
    if data.get("errors") or not (data.get("data") or {}).get("user"):
        raise ApiError("GraphQL: %s" % data.get("errors"))
    u = data["data"]["user"]
    repos = u["repositories"]["nodes"]
    sizes = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            size, color = sizes.get(name, (0, e["node"]["color"]))
            sizes[name] = (size + e["size"], color or OTHER)
    total = sum(s for s, _ in sizes.values()) or 1
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1][0])
    langs = [[n, round(100.0 * s / total, 1), c] for n, (s, c) in ranked[:5]]
    rest = 100.0 - sum(p for _, p, _ in langs)
    if rest >= 0.05:
        langs.append(["Other", round(rest, 1), OTHER])
    cc = u["contributionsCollection"]
    d["github"] = {
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "languages": langs,
    }
    by_name = {r["name"]: r for r in repos}
    for f in d["featured"]:
        r = by_name.get(f["name"])
        if r:
            f["stars"] = r["stargazerCount"]
            if r["primaryLanguage"]:
                f["language"] = r["primaryLanguage"]["name"]
                f["color"] = r["primaryLanguage"]["color"] or OTHER


def repository_count(token):
    """All repositories owned by the account, or None without a token that can
    see the private ones."""
    if not token:
        return None
    total, page = 0, 1
    while True:
        data = request(API + "/user/repos?affiliation=owner&per_page=100&page=%d" % page, token)
        if not isinstance(data, list):
            raise ApiError("user/repos: %s" % data)
        total += len(data)
        if len(data) < 100:
            return total
        page += 1


def main():
    d = load()
    token = os.environ.get("PROFILE_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        github_numbers(d, token)
    except ApiError as e:
        print("GitHub numbers not read, kept:", e)
    try:
        count = repository_count(os.environ.get("PROFILE_STATS_TOKEN"))
    except ApiError as e:
        print("repositories not counted, kept:", e)
    else:
        if count:
            d["repositories"] = count
        else:
            print("no PROFILE_STATS_TOKEN: repository count kept")
    save(d)
    draw(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
