#!/usr/bin/env python3
"""Draw the GitHub stats and top languages cards of the profile README as
SVG files in assets/, from the GitHub GraphQL API, and update the repository
count badges of the README.

The cards used to come from a github-readme-stats deployment on Vercel, which
stopped working (it needs a token of its own). Drawing them here keeps the
README independent of any outside service.

Tokens (environment):
  GITHUB_TOKEN          the token of the workflow: public data only
  PROFILE_STATS_TOKEN   optional, a token that can list the private repositories
                        of the account (fine grained, Metadata read only, all
                        repositories); without it the repository badges keep
                        their values

A failed request leaves the files as they are and exits 0, so a passing
outage of the API does not fail the workflow. A bug in this script fails it.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from html import escape

USER = "ductran27"
README = "README.md"
ASSETS = "assets"
API = "https://api.github.com"

BG, BORDER, TITLE, TEXT, ICON, MUTED = "#1a1b27", "#1a1b27", "#a855f7", "#c9d1d9", "#a855f7", "#8b949e"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"


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
            return json.load(r), r.headers
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise ApiError("%s: %s" % (url, e)) from e


QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    issues { totalCount }
    pullRequests { totalCount }
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""


def stats(token):
    data, _ = request(API + "/graphql", token, {"query": QUERY, "variables": {"login": USER}})
    if data.get("errors") or not (data.get("data") or {}).get("user"):
        raise ApiError("GraphQL: %s" % data.get("errors"))
    u = data["data"]["user"]
    repos = u["repositories"]["nodes"]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            size, color = langs.get(n, (0, e["node"]["color"]))
            langs[n] = (size + e["size"], color or "#8b949e")
    cc = u["contributionsCollection"]
    return {
        "stars": sum(r["stargazerCount"] for r in repos),
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "langs": sorted(langs.items(), key=lambda kv: -kv[1][0]),
    }


def repo_counts(token):
    """(all, private) repositories owned by the account, or None without a
    token that can see the private ones."""
    if not token:
        return None
    total = private = 0
    page = 1
    while True:
        data, _ = request(API + "/user/repos?affiliation=owner&per_page=100&page=%d" % page, token)
        if not isinstance(data, list):
            raise ApiError("user/repos: %s" % data)
        total += len(data)
        private += sum(1 for r in data if r.get("private"))
        if len(data) < 100:
            return total, private
        page += 1


# Drawing ----------------------------------------------------------------------

ICONS = {   # 16 x 16, filled
    "star": '<path d="M8 1.2l2.1 4.3 4.7.7-3.4 3.3.8 4.7L8 12l-4.2 2.2.8-4.7L1.2 6.2l4.7-.7z"/>',
    "commit": '<path d="M8 4.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7zm0 1.6a1.9 1.9 0 1 0 0 3.8 1.9 1.9 0 0 0 0-3.8z"/>'
              '<rect x="0" y="7.2" width="4.6" height="1.6" rx=".8"/><rect x="11.4" y="7.2" width="4.6" height="1.6" rx=".8"/>',
    "pr": '<circle cx="4" cy="3.5" r="2"/><circle cx="4" cy="12.5" r="2"/><circle cx="12" cy="12.5" r="2"/>'
          '<rect x="3.2" y="5" width="1.6" height="6" rx=".8"/><path d="M7 2.5h3.2A2.3 2.3 0 0 1 12.5 4.8V10.6h-1.6V4.8a.7.7 0 0 0-.7-.7H7z"/>',
    "issue": '<path d="M8 1a7 7 0 1 1 0 14A7 7 0 0 1 8 1zm0 1.6a5.4 5.4 0 1 0 0 10.8A5.4 5.4 0 0 0 8 2.6z"/><circle cx="8" cy="8" r="1.6"/>',
    "repo": '<path d="M3 1.5h9.5a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H11v-1.6h.9V3.1H4.6v7.3h5.1V12H4.4a.8.8 0 0 0 0 1.6H6v1.6H4.4A2.4 2.4 0 0 1 2 12.8V2.5a1 1 0 0 1 1-1z"/>',
    "people": '<circle cx="5.5" cy="5" r="2.6"/><path d="M.8 13.6a4.7 4.7 0 0 1 9.4 0z"/><circle cx="11.6" cy="5.6" r="2.1"/>'
              '<path d="M11.2 9.1a4 4 0 0 1 4 4.5h-3.8a6 6 0 0 0-1.6-4.2 4 4 0 0 1 1.4-.3z"/>',
}


def card(width, height, title, body):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">\n'
        '<title>%s</title>\n'
        '<style>.t{font:600 18px %s;fill:%s}.l{font:400 14px %s;fill:%s}.v{font:700 14px %s;fill:%s}'
        '.s{font:400 12px %s;fill:%s}</style>\n'
        '<rect x="0.5" y="0.5" width="%d" height="%d" rx="4.5" fill="%s" stroke="%s"/>\n'
        '<text x="25" y="35" class="t">%s</text>\n%s</svg>\n'
        % (width, height, width, height, escape(title), escape(title), FONT, TITLE, FONT, TEXT, FONT, TEXT,
           FONT, MUTED, width - 1, height - 1, BG, BORDER, escape(title), body))


def stats_card(s):
    rows = [("star", "Total stars earned", s["stars"]),
            ("commit", "Commits (last year)", s["commits"]),
            ("pr", "Pull requests", s["prs"]),
            ("issue", "Issues", s["issues"]),
            ("repo", "Public repositories", s["repos"]),
            ("people", "Followers", s["followers"])]
    body = []
    for i, (icon, label, value) in enumerate(rows):
        y = 58 + i * 22
        body.append('<g transform="translate(25,%d)" fill="%s">%s</g>' % (y, ICON, ICONS[icon]))
        body.append('<text x="50" y="%d" class="l">%s</text>' % (y + 13, escape(label)))
        body.append('<text x="300" y="%d" class="v" text-anchor="end">%s</text>' % (y + 13, "{:,}".format(value)))
    return card(330, 195, "Duc Tran's GitHub Stats", "\n".join(body) + "\n")


def langs_card(langs, count=8):
    top = langs[:count]
    total = sum(size for _, (size, _) in top) or 1
    width, bar_w = 350, 300
    body = ['<clipPath id="r"><rect x="25" y="52" width="%d" height="8" rx="4"/></clipPath><g clip-path="url(#r)">' % bar_w]
    x = 25.0
    for name, (size, color) in top:
        w = bar_w * size / total
        body.append('<rect x="%.2f" y="52" width="%.2f" height="8" fill="%s"/>' % (x, w + 0.5, escape(color)))
        x += w
    body.append("</g>")
    for i, (name, (size, color)) in enumerate(top):
        col, row = i % 2, i // 2
        cx, cy = 25 + col * 160, 84 + row * 25
        body.append('<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (cx + 5, cy - 4, escape(color)))
        body.append('<text x="%d" y="%d" class="l">%s <tspan class="s">%.2f%%</tspan></text>'
                    % (cx + 16, cy, escape(name), 100.0 * size / total))
    return card(width, 195, "Most Used Languages", "\n".join(body) + "\n")


def write_if_changed(path, text):
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == text:
                return False
    except FileNotFoundError:
        pass
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", path)
    return True


def update_badges(counts):
    total, private = counts
    with open(README, encoding="utf-8") as f:
        text = f.read()
    new = re.sub(r"(badge/REPOSITORIES-)\d+(-)", r"\g<1>%d\2" % total, text)
    new = re.sub(r"(badge/PRIVATE_REPOS-)\d+(-)", r"\g<1>%d\2" % private, new)
    if new != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("repository badges: %d, %d private" % (total, private))


def main():
    token = os.environ.get("PROFILE_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    os.makedirs(ASSETS, exist_ok=True)
    try:
        s = stats(token)
    except ApiError as e:
        print("GitHub stats not read, cards kept:", e)
    else:
        write_if_changed(os.path.join(ASSETS, "github-stats.svg"), stats_card(s))
        write_if_changed(os.path.join(ASSETS, "top-langs.svg"), langs_card(s["langs"]))
    try:
        counts = repo_counts(os.environ.get("PROFILE_STATS_TOKEN"))
    except ApiError as e:
        print("repositories not counted, badges kept:", e)
    else:
        if counts:
            update_badges(counts)
        else:
            print("no PROFILE_STATS_TOKEN: repository badges kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
