# intake/fetcher.py

import os
import requests
from typing import List

from .schema import RawIssue

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # set in your .env or CI secrets

def fetch_issues(repo: str) -> List[RawIssue]:
    """
    Fetch open issues from GitHub via the REST API.
    repo should be "owner/name", e.g. "YujieXuGru/SWE_agent".
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{repo}/issues"
    params = {
        "state": "open",
        "per_page": 100,
        # add "labels": "bug,enhancement" if you want to filter
    }

    issues: List[RawIssue] = []
    while url:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        for item in data:
            # skip pull-requests
            if "pull_request" in item:
                continue

            issues.append(RawIssue(
                id       = item["id"],
                number   = item["number"],
                title    = item["title"],
                body     = item.get("body") or "",
                state    = item["state"],
                labels   = [lbl["name"] for lbl in item.get("labels", [])],
                created_at = item["created_at"],
                updated_at = item["updated_at"],
            ))
        # look for the next page via Link header
        url = None
        if "Link" in resp.headers:
            links = resp.headers["Link"].split(",")
            for link in links:
                url_part, rel = link.split(";")
                if 'rel="next"' in rel:
                    url = url_part.strip()[1:-1]
        # after first page, clear params so we don’t resend them
        params = {}

    return issues
