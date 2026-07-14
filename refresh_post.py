"""
WordPress.com Daily Content Refresh
--------------------------------------
Processes a batch of the least-recently-updated posts each run,
appends an updated-date footer with up to 3 related internal posts
shown as clickable navy/gold image cards, then pings Google's
sitemap endpoint to encourage re-crawl.
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
SNIPPET_LENGTH = 110

NAVY = "#0a1f44"
NAVY_CARD = "#132a54"
GOLD = "#d4af37"


def get_all_posts():
    posts = []
    page_handle = None
    while True:
        params = {
            "number": 100,
            "fields": "ID,title,content,modified,URL,featured_image",
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
        remaining = [p for p in all_posts if p["ID"] != target["ID"] and p not in top]
        random.shuffle(remaining)
        top.extend(remaining[: n - len(top)])
    return top


def extract_first_image(content):
    """WordPress.com's featured_image field is unreliable, so pull the
    first <img> actually embedded in the post body instead."""
    if not content:
        return ""
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
    return match.group(1) if match else ""


def extract_snippet(content, length=SNIPPET_LENGTH):
    """Strip HTML tags/entities and return a clean plain-text snippet."""
    if not content:
        return ""
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'&nbsp;|&#8217;|&#8220;|&#8221;', ' ', text)
    text = re.sub(r'&[a-zA-Z#0-9]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '…'


def build_related_cards(related_posts):
    cards = ""
    for i, p in enumerate(related_posts):
        img = extract_first_image(p.get("content", ""))
        snippet = extract_snippet(p.get("content", ""))
        is_last = (i == len(related_posts) - 1)
        border_style = "" if is_last else f"border-bottom:1px solid rgba(212,175,55,0.35);"

        img_html = (
            f'<img src="{img}" style="width:100px; height:100px; object-fit:cover; '
            f'display:block; border-radius:8px; flex-shrink:0;" />'
            if img else
            f'<div style="width:100px; height:100px; background-color:{NAVY}; '
            f'border-radius:8px; flex-shrink:0; border:1px solid {GOLD};"></div>'
        )

        cards += (
            f'<a href="{p["URL"]}" style="text-decoration:none; display:block; '
            f'margin:0; padding:0; background-color:{NAVY_CARD};">'
            f'<div style="display:flex; align-items:center; gap:14px; '
            f'background-color:{NAVY_CARD}; padding:16px; margin:0; {border_style}">'
            f'{img_html}'
            f'<div style="flex:1; min-width:0;">'
            f'<p style="margin:0 0 6px 0; color:#ffffff; font-size:15px; font-weight:bold; '
            f'font-family:Georgia, serif; line-height:1.3;">{p["title"]}</p>'
            f'<p style="margin:0; color:#d8d8e8; font-size:12.5px; line-height:1.5;">{snippet}</p>'
            f'<p style="margin:6px 0 0 0; color:{GOLD}; font-size:11.5px; font-weight:bold; '
            f'letter-spacing:0.03em;">READ FULL ARTICLE &#8594;</p>'
            f'</div>'
            f'</div>'
            f'</a>'
        )
    return cards


def build_updated_content(original_content, related_posts, today):
    if f"Updated: {today}" in original_content:
        return None

    cards_html = build_related_cards(related_posts)
    footer = (
        '</div></div></div>'  # defensively break out of any unclosed grid/flex container
        f'\n\n<div style="all:initial; display:block; clear:both; width:100%; '
        f'background-color:{NAVY}; margin-top:24px; box-sizing:border-box; '
        f'font-family:inherit; border-radius:10px; overflow:hidden;">'
        f'<p style="color:#ffffff; margin:0; padding:16px 16px 12px 16px; '
        f'background-color:{NAVY}; font-size:13px;"><em>Updated: {today}</em> — '
        f'You may also find these related articles helpful:</p>'
        f'<div style="background-color:{NAVY_CARD};">'
        f'{cards_html}'
        f'</div>'
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
