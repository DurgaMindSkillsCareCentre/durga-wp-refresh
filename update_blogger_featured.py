"""
Blogger Featured Articles Page Updater
--------------------------------------
Fetches the latest posts from the public Blogger feed (no login/API
key needed - Blogger's Atom/JSON feed is publicly accessible), picks
a rotating batch of 15 out of the most recent 100, and builds a
navy/gold styled WordPress.com page with image + snippet cards linking
back to each Blogger post.
Runs daily via GitHub Actions alongside the other refresh scripts.
"""

import os
import re
import random
import datetime
import requests

WP_SITE = os.environ["WP_SITE"]
ACCESS_TOKEN = os.environ["WP_ACCESS_TOKEN"]
BLOGGER_FEATURED_PAGE_ID = "1384"
API_BASE = f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

BLOGGER_BLOG_URL = "durgapsychiatric.blogspot.com"
BLOGGER_FEED_MAX = 100
DISPLAY_COUNT = 15

NAVY = "#0a1f44"
NAVY_CARD = "#132a54"
GOLD = "#d4af37"


def fetch_blogger_posts(max_results=BLOGGER_FEED_MAX):
    """Pull recent posts (title + snippet + image + link) from
    Blogger's public JSON feed - no auth needed."""
    url = f"https://{BLOGGER_BLOG_URL}/feeds/posts/default"
    params = {"alt": "json", "max-results": max_results}

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError):
        return []

    entries = data.get("feed", {}).get("entry", [])
    posts = []

    for e in entries:
        title = e.get("title", {}).get("$t", "Untitled")

        link = None
        for l in e.get("link", []):
            if l.get("rel") == "alternate":
                link = l.get("href")
                break
        if not link:
            continue

        # Snippet from the post summary/content, HTML tags stripped
        raw_html = e.get("summary", {}).get("$t") or e.get("content", {}).get("$t", "")
        snippet = re.sub("<[^<]+?>", " ", raw_html)
        snippet = re.sub(r"\s+", " ", snippet).strip()
        snippet = snippet[:140] + ("…" if len(snippet) > 140 else "")

        # Thumbnail image, if Blogger provides one
        img_url = None
        thumb = e.get("media$thumbnail", {}).get("url")
        if thumb:
            # Blogger thumbnails are small by default; request a larger size
            img_url = re.sub(r"/s\d+(-c)?/", "/s600/", thumb)
        else:
            # fallback: try to pull first <img> from content
            img_match = re.search(r'<img[^>]+src="([^"]+)"', raw_html)
            if img_match:
                img_url = img_match.group(1)

        posts.append({
            "title": title,
            "url": link,
            "snippet": snippet,
            "image": img_url,
        })

    return posts


def build_blogger_section():
    posts = fetch_blogger_posts()
    blog_link = f"https://{BLOGGER_BLOG_URL}/"

    if not posts:
        return (
            f'<div style="background-color:{NAVY}; padding:20px 16px; text-align:center;">'
            f'<p style="color:{GOLD}; margin:0;">'
            f'<a href="{blog_link}" style="color:{GOLD};" target="_blank" rel="noopener">'
            f'Visit our Blogger site &#8594;</a></p>'
            f'</div>'
        )

    chosen = random.sample(posts, min(DISPLAY_COUNT, len(posts)))

    cards = ""
    for p in chosen:
        img_html = (
            f'<img src="{p["image"]}" style="width:100%; height:170px; '
            f'object-fit:cover; display:block;" />'
            if p["image"] else ""
        )
        cards += (
            f'<a href="{p["url"]}" target="_blank" rel="noopener" style="text-decoration:none;">'
            f'<div style="background-color:{NAVY_CARD}; border:1px solid {GOLD}; '
            f'border-radius:10px; overflow:hidden; margin:0 0 14px 0;">'
            f'{img_html}'
            f'<div style="padding:14px 18px;">'
            f'<p style="margin:0 0 6px 0; color:#ffffff; font-size:16px; font-weight:bold; '
            f'font-family:Georgia, serif;">{p["title"]}</p>'
            f'<p style="margin:0 0 8px 0; color:#cfcfcf; font-size:13px;">{p["snippet"]}</p>'
            f'<p style="margin:0; color:{GOLD}; font-size:12px; font-weight:bold;">'
            f'READ MORE &#8594;</p>'
            f'</div>'
            f'</div>'
            f'</a>'
        )

    return (
        f'<div style="background-color:{NAVY}; padding:24px 16px;">'
        f'<p style="color:{GOLD}; font-size:19px; font-weight:bold; margin:0 0 4px 0; '
        f'font-family:Georgia, serif; text-align:center;">Featured Blogger Articles</p>'
        f'<p style="text-align:center; margin:0 0 18px 0;">'
        f'<a href="{blog_link}" target="_blank" rel="noopener" '
        f'style="color:{GOLD}; font-size:13px; text-decoration:none;">'
        f'Visit Durga Psychiatric on Blogger &#8594;</a></p>'
        f'{cards}'
        f'</div>'
    )


def build_featured_content():
    today = datetime.date.today().strftime("%d %B %Y")
    header = (
        f'<div style="background-color:{NAVY}; padding:10px 16px 0 16px; text-align:center;">'
        f'<p style="color:#ffffff; font-size:13px; opacity:0.7; margin:0;">Updated {today}</p>'
        f'</div>'
    )
    return header + build_blogger_section()


def update_featured_page():
    content = build_featured_content()
    r = requests.post(
        f"{API_BASE}/posts/{BLOGGER_FEATURED_PAGE_ID}/",
        headers=HEADERS,
        data={"content": content, "context": "edit"},
    )
    r.raise_for_status()
    print("Blogger featured page updated.")


if __name__ == "__main__":
    update_featured_page()
