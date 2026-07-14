import random
import requests
import datetime
import os

WP_SITE = os.environ["WP_SITE"]
ACCESS_TOKEN = os.environ["WP_ACCESS_TOKEN"]
FEATURED_PAGE_ID = "1285"
API_BASE = f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

LINKEDIN_POSTS = [
    {
        "title": "Future Trends in Psychology 2026-2030",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_future-trends-in-psychology-20262030-activity-7478706492523716608-qLAw",
    },
    {
        "title": "Psychology Career Professional Roadmap",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_psychology-career-professional-roadmap-activity-7479058016739147776-GoAQ",
    },
    {
        "title": "The 25 Greatest Psychology Discoveries",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_the-25-greatest-psychology-discoveries-activity-7479539046956941313-3rzI",
    },
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
