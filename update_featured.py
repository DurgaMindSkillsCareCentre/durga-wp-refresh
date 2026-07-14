import random
import requests
import datetime
import os

WP_SITE = os.environ["WP_SITE"]
ACCESS_TOKEN = os.environ["WP_ACCESS_TOKEN"]
FEATURED_PAGE_ID = "1285"   # <-- replace with your actual Page ID
API_BASE = f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

LINKEDIN_POSTS = [
    {"title": "Post title 1", "url": "https://linkedin.com/posts/..."},
    {"title": "Post title 2", "url": "https://linkedin.com/posts/..."},
    # add more here over time
]

DISPLAY_COUNT = 8


def build_featured_content():
    chosen = random.sample(LINKEDIN_POSTS, min(DISPLAY_COUNT, len(LINKEDIN_POSTS)))
    today = datetime.date.today().strftime("%d %B %Y")
    items = "".join(f'<p>{p["title"]}</p>\n<p>{p["url"]}</p>\n' for p in chosen)
    return (
        f'<div style="display:block; width:100%;">'
        f'<p><em>Featured LinkedIn Articles — updated {today}</em></p>'
        f'{items}'
        f'</div>'
    )


def update_featured_page():
    content = build_featured_content()
    r = requests.post(
        f"{API_BASE}/posts/{FEATURED_PAGE_ID}/",
        headers=HEADERS,
        data={"content": content, "context": "edit"},
    )
    r.raise_for_status()
    print("Featured page updated.")


if __name__ == "__main__":
    update_featured_page()
