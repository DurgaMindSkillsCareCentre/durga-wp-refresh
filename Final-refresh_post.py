"""
WordPress.com Weekly Content Refresh
--------------------------------------
Picks the post that hasn't been touched the longest, appends an
updated-date line, and inserts one internal link to another post
with an overlapping keyword. Runs weekly via GitHub Actions.

Uses context=edit on both fetch and update to keep content as raw
as possible and minimize WordPress.com's sanitizer reprocessing
the existing inline-styled button grid on every save.
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


def pick_oldest_updated(posts):
    return sorted(posts, key=lambda p: p["modified"])[0]


def find_related_post(target, all_posts):
    target_words = set(w.lower() for w in re.findall(r"\w{4,}", target["title"]))
    best, best_score = None, 0
    for p in all_posts:
        if p["ID"] == target["ID"]:
            continue
        words = set(w.lower() for w in re.findall(r"\w{4,}", p["title"]))
        score = len(target_words & words)
        if score > best_score:
            best, best_score = p, score
    return best if best_score > 0 else random.choice(
        [p for p in all_posts if p["ID"] != target["ID"]]
    )


def build_updated_content(original_content, related_post):
    today = datetime.date.today().strftime("%B %Y")

    if f"Updated: {today}" in original_content:
        return None

    # Self-contained inline-style block, kept isolated from the
    # existing button grid's own inline styles.
    footer = (
        f'\n\n<div style="display:block; clear:both; width:100%; margin-top:20px;">'
        f'<p><em>Updated: {today}</em> — '
        f'You may also find this related article helpful: '
        f'<a href="{related_post["URL"]}">{related_post["title"]}</a></p>'
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


def main():
    posts = get_all_posts()
    if not posts:
        print("No posts found.")
        write_summary("No posts found. Nothing was refreshed.")
        return

    target = pick_oldest_updated(posts)
    related = find_related_post(target, posts)
    new_content = build_updated_content(target["content"], related)

    if new_content is None:
        msg = f"Post '{target['title']}' already refreshed this month. Skipped."
        print(msg)
        write_summary(msg)
        return

    update_post(target["ID"], new_content)
    msg = (
        f"Refreshed post:\n  {target['title']}\n  {target['URL']}\n\n"
        f"Linked to related post:\n  {related['title']}\n  {related['URL']}"
    )
    print(f"Refreshed: {target['title']} (linked to: {related['title']})")
    write_summary(msg)


def write_summary(text):
    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
