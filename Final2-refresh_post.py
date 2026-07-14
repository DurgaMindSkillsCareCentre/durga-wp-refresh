"""
WordPress.com Daily Content Refresh
--------------------------------------
Processes a batch of the least-recently-updated posts each run,
appends an updated-date footer with up to 3 related internal links
per post, then pings Google's sitemap endpoint to encourage re-crawl.
Runs daily via GitHub Actions.
"""

import os
import re
import random
import datetime
import requests

WP_SITE = os.environ["WP_SITE"]
ACCESS_TOKEN = os.environ["WP_ACCESS_TOKEN"]
API_BASE = f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

BATCH_SIZE = 10          # posts refreshed per run
RELATED_LINKS_PER_POST = 3


def get_all_posts():
    posts = []
    page_handle = None
    while True:
        params = {
            "number": 100,
            "fields": "ID,title,content,modified,URL",
            "context": "edit",
        }
        if page_handle:
            params["page_handle"] = page_handle
        r = requests.get(f"{API_BASE}/posts/", headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        posts.extend(data.get("posts", []))
        page_handle = data.get("meta", {}).get("next_page")
        if not page_handle:
            break
    return posts


def pick_batch(posts, batch_size=BATCH_SIZE):
    return sorted(posts, key=lambda p: p["modified"])[:batch_size]


def find_related_posts(target, all_posts, n=RELATED_LINKS_PER_POST):
    target_words = set(w.lower() for w in re.findall(r"\w{4,}", target["title"]))
    scored = []
    for p in all_posts:
        if p["ID"] == target["ID"]:
            continue
        words = set(w.lower() for w in re.findall(r"\w{4,}", p["title"]))
        score = len(target_words & words)
        scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [p for score, p in scored if score > 0][:n]
    if len(top) < n:
        # fill remaining slots with random posts if not enough keyword overlap
        remaining = [p for p in all_posts if p["ID"] != target["ID"] and p not in top]
        random.shuffle(remaining)
        top.extend(remaining[: n - len(top)])
    return top


def build_updated_content(original_content, related_posts, today):
    if f"Updated: {today}" in original_content:
        return None

    links_html = "".join(
        f'<li><a href="{p["URL"]}">{p["title"]}</a></li>' for p in related_posts
    )
    footer = (
        f'\n\n<div style="display:block; clear:both; width:100%; margin-top:20px;">'
        f'<p><em>Updated: {today}</em> — You may also find these related articles helpful:</p>'
        f'<ul>{links_html}</ul>'
        f'</div>'
    )
    return original_content + footer


def update_post(post_id, new_content):
    r = requests.post(
        f"{API_BASE}/posts/{post_id}/",
        headers=HEADERS,
        data={"content": new_content, "context": "edit"},
    )
    r.raise_for_status()
    return r.json()


def ping_sitemap():
    sitemap_url = f"https://{WP_SITE}/sitemap.xml"
    try:
        r = requests.get(
            "https://www.google.com/ping",
            params={"sitemap": sitemap_url},
            timeout=15,
        )
        return f"Sitemap ping: HTTP {r.status_code}"
    except requests.RequestException as e:
        return f"Sitemap ping failed: {e}"


def main():
    posts = get_all_posts()
    if not posts:
        print("No posts found.")
        write_summary("No posts found. Nothing was refreshed.")
        return

    today = datetime.date.today().strftime("%B %Y")
    batch = pick_batch(posts)

    refreshed = []
    skipped = []

    for target in batch:
        related = find_related_posts(target, posts)
        new_content = build_updated_content(target["content"], related, today)

        if new_content is None:
            skipped.append(target["title"])
            continue

        update_post(target["ID"], new_content)
        refreshed.append((target["title"], target["URL"], [p["title"] for p in related]))

    ping_result = ping_sitemap()

    lines = [f"Daily refresh — {today}", ""]
    if refreshed:
        lines.append(f"Refreshed {len(refreshed)} posts:")
        for title, url, related_titles in refreshed:
            lines.append(f"  - {title} ({url})")
            lines.append(f"      linked to: {', '.join(related_titles)}")
    if skipped:
        lines.append(f"\nSkipped {len(skipped)} (already refreshed this month):")
        for t in skipped:
            lines.append(f"  - {t}")
    lines.append(f"\n{ping_result}")

    summary = "\n".join(lines)
    print(summary)
    write_summary(summary)


def write_summary(text):
    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
