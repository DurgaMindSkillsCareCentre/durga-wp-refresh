"""
Featured Content Page Updater
--------------------------------------
Builds a premium navy/gold styled WordPress.com page combining:
  1. Recent Telegram channel posts (image + caption + clickable link,
     parsed from the public telegram.me/s/ preview page using BeautifulSoup).
     Handles Telegram's grouped-album behavior, where only one photo in a
     multi-photo post carries the shared caption - missing captions are
     filled in from the nearest neighboring photo in the same post.
  2. A rotating selection of LinkedIn article links
Runs daily via GitHub Actions alongside the main content refresh script.
"""

import os
import random
import datetime
import requests
from bs4 import BeautifulSoup

WP_SITE = os.environ["WP_SITE"]
ACCESS_TOKEN = os.environ["WP_ACCESS_TOKEN"]
FEATURED_PAGE_ID = "1285"
API_BASE = f"https://public-api.wordpress.com/rest/v1.1/sites/{WP_SITE}"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

TELEGRAM_CHANNEL = "durgamindskillcare"
TELEGRAM_LIMIT = 4

LINKEDIN_POSTS = [
    {"title": "Future Trends in Psychology 2026-2030",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_future-trends-in-psychology-20262030-activity-7478706492523716608-qLAw"},
    {"title": "Psychology Career Professional Roadmap",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_psychology-career-professional-roadmap-activity-7479058016739147776-GoAQ"},
    {"title": "The 25 Greatest Psychology Discoveries",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_the-25-greatest-psychology-discoveries-activity-7479539046956941313-3rzI"},
    {"title": "The Psychology They Never Taught You",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_the-psychology-they-never-taught-you-activity-7481919650776178689-vSnO"},
    {"title": "12 Psychology Research Breakthroughs",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_12-psychology-research-breakthroughs-that-activity-7480975281600753664-3OFw"},
    {"title": "Evidence-Based Psychology: How Scientific",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_evidence-based-psychology-how-scientific-activity-7480849753510092800-W3kX"},
    {"title": "Artificial Intelligence in Psychology",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_artificial-intelligence-in-psychology-activity-7480273565267828737-2Hgc"},
    {"title": "100 Ways Psychology Is Changing",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_100-ways-psychology-is-changing-the-share-7482365522924306432-JNi0"},
    {"title": "Mental Health, Emotional Intelligence & Soft Skills",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_mentalhealth-emotionalintelligence-softskills-activity-7472924250652237824-gLvG"},
    {"title": "Student Success, Focus & Education",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_studentsuccess-focus-education-activity-7473039252759474177-JhzX"},
    {"title": "NRI Relationships & Marriage",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_nri-relationships-marriage-activity-7473057853126156288-xEr-"},
    {"title": "AI, Future of Work & Emotional Intelligence",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_ai-futureofwork-emotionalintelligence-activity-7473378671429361665-ygjA"},
    {"title": "Gulf Jobs, Middle East & NRI",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_gulfjobs-middleeast-nri-activity-7473688995017711616-Cfhp"},
    {"title": "Artificial Intelligence, Mental Health & Psychology",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_artificialintelligence-mentalhealth-psychology-activity-7474810942019510273-3PXR"},
    {"title": "Artificial Intelligence, Psychotherapy & Mental Health",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_artificialintelligence-psychotherapy-mentalhealth-activity-7474823153706377216-A-JQ"},
    {"title": "Can AI Predict Employee Turnover Before It Happens?",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_can-ai-predict-employee-turnover-before-activity-7475112570429915138-cvC3"},
    {"title": "Why Do Some People Fear Public Speaking?",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_why-do-some-people-fear-public-speaking-activity-7475377843334471680-1sby"},
    {"title": "Introducing the Tamil Mental Health Initiative",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_im-pleased-to-introduce-the-tamil-mental-activity-7475763847530704898-G2E_"},
    {"title": "Final Year Psychology Students",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_final-year-psychology-students-are-activity-7477770695327023104-tByK"},
    {"title": "AI & Psychology: The Future Starts Now",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_ai-psychology-the-future-starts-now-activity-7477778399193640960-4ld6"},
    {"title": "Can Just 10 Minutes in Nature Improve Your Mind?",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_can-just-10-minutes-in-nature-improve-activity-7480590050582220802-AQ-R"},
    {"title": "Psychology, Neuroscience & Mental Health",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_psychology-neuroscience-mentalhealth-activity-7482034327606710272-243s"},
    {"title": "The Psychology Behind 10 World-Changing Ideas",
     "url": "https://www.linkedin.com/posts/d-durga-116800416_the-psychology-behind-10-world-changing-activity-7482298590024060928-0gSa"},
]

LINKEDIN_DISPLAY_COUNT = 8

NAVY = "#0a1f44"
NAVY_CARD = "#132a54"
GOLD = "#d4af37"


def fetch_telegram_posts(limit=TELEGRAM_LIMIT):
    """Pull recent posts (image + caption + clickable link) from
    Telegram's public preview page. No login, no JS needed."""
    url = f"https://telegram.me/s/{TELEGRAM_CHANNEL}"

    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    messages = soup.find_all("div", class_="tgme_widget_message", attrs={"data-post": True})

    entries = []
    for msg in messages:
        photo_div = msg.find("a", class_="tgme_widget_message_photo_wrap")
        img_url = None
        if photo_div and photo_div.get("style"):
            style = photo_div["style"]
            start = style.find("url('") + 5
            end = style.find("')", start)
            if start > 4 and end > start:
                img_url = style[start:end]

        text_div = msg.find("div", class_="tgme_widget_message_text")
        text = text_div.get_text(separator=" ", strip=True) if text_div else ""

        post_id = msg.get("data-post")
        post_link = f"https://telegram.me/s/{post_id}" if post_id else f"https://telegram.me/s/{TELEGRAM_CHANNEL}"

        entries.append({"image": img_url, "text": text, "link": post_link})

    # Telegram albums (multiple photos posted together) attach the caption
    # to only one photo in the group. Borrow it for the others nearby.
    for i, e in enumerate(entries):
        if e["text"]:
            continue
        for j in list(range(i - 1, -1, -1)) + list(range(i + 1, len(entries))):
            if entries[j]["text"]:
                e["text"] = entries[j]["text"]
                break

    posts = [e for e in entries if e["image"]]
    for p in posts:
        p["text"] = p["text"][:120] if p["text"] else "Durga MindSkillsCare Centre"

    return posts[-limit:] if posts else []


def build_telegram_section():
    posts = fetch_telegram_posts()
    channel_link = f"https://telegram.me/s/{TELEGRAM_CHANNEL}"

    if not posts:
        return (
            f'<div style="background-color:{NAVY}; padding:20px 16px; text-align:center;">'
            f'<p style="color:{GOLD}; margin:0;">'
            f'<a href="{channel_link}" style="color:{GOLD};" target="_blank" rel="noopener">'
            f'Visit our Telegram channel &#8594;</a></p>'
            f'</div>'
        )

    cards = ""
    for p in posts:
        cards += (
            f'<a href="{p["link"]}" target="_blank" rel="noopener" style="text-decoration:none;">'
            f'<div style="background-color:{NAVY_CARD}; border:1px solid {GOLD}; '
            f'border-radius:10px; overflow:hidden; margin:0 0 14px 0;">'
            f'<img src="{p["image"]}" style="width:100%; height:170px; object-fit:cover; display:block;" />'
            f'<div style="padding:14px 18px;">'
            f'<p style="margin:0; color:#ffffff; font-size:15px;">{p["text"]}</p>'
            f'</div>'
            f'</div>'
            f'</a>'
        )

    return (
        f'<div style="background-color:{NAVY}; padding:24px 16px 8px 16px;">'
        f'<p style="color:{GOLD}; font-size:19px; font-weight:bold; margin:0 0 4px 0; '
        f'font-family:Georgia, serif; text-align:center;">From Our Telegram Channel</p>'
        f'<p style="text-align:center; margin:0 0 18px 0;">'
        f'<a href="{channel_link}" target="_blank" rel="noopener" '
        f'style="color:{GOLD}; font-size:13px; text-decoration:none;">'
        f'Join Durga MindSkillsCare Centre &#8594;</a></p>'
        f'{cards}'
        f'</div>'
    )


def build_linkedin_section():
    chosen = random.sample(LINKEDIN_POSTS, min(LINKEDIN_DISPLAY_COUNT, len(LINKEDIN_POSTS)))

    cards = ""
    for p in chosen:
        cards += (
            f'<div style="background-color:{NAVY_CARD}; border:1px solid {GOLD}; '
            f'border-radius:10px; padding:16px 18px; margin:0 0 14px 0;">'
            f'<p style="margin:0 0 8px 0; color:#ffffff; font-size:17px; font-weight:bold; '
            f'font-family:Georgia, serif;">{p["title"]}</p>'
            f'<p style="margin:0;"><a href="{p["url"]}" target="_blank" rel="noopener" '
            f'style="color:{GOLD}; text-decoration:none; font-weight:bold;">'
            f'VIEW ON LINKEDIN &#8594;</a></p>'
            f'</div>'
        )

    return (
        f'<div style="background-color:{NAVY}; padding:8px 16px 24px 16px;">'
        f'<p style="color:{GOLD}; font-size:19px; font-weight:bold; margin:24px 0 18px 0; '
        f'font-family:Georgia, serif; text-align:center;">Featured LinkedIn Articles</p>'
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

    return header + build_telegram_section() + build_linkedin_section()


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
