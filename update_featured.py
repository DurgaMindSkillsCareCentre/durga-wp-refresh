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
    {
        "title": "The Psychology They Never Taught You",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_the-psychology-they-never-taught-you-activity-7481919650776178689-vSnO",
    },
    {
        "title": "12 Psychology Research Breakthroughs",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_12-psychology-research-breakthroughs-that-activity-7480975281600753664-3OFw",
    },
    {
        "title": "Evidence-Based Psychology: How Scientific",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_evidence-based-psychology-how-scientific-activity-7480849753510092800-W3kX",
    },
    {
        "title": "Artificial Intelligence in Psychology",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_artificial-intelligence-in-psychology-activity-7480273565267828737-2Hgc",
    },
    {
        "title": "100 Ways Psychology Is Changing",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_100-ways-psychology-is-changing-the-share-7482365522924306432-JNi0",
    },
    {
        "title": "Mental Health, Emotional Intelligence & Soft Skills",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_mentalhealth-emotionalintelligence-softskills-activity-7472924250652237824-gLvG",
    },
    {
        "title": "Student Success, Focus & Education",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_studentsuccess-focus-education-activity-7473039252759474177-JhzX",
    },
    {
        "title": "NRI Relationships & Marriage",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_nri-relationships-marriage-activity-7473057853126156288-xEr-",
    },
    {
        "title": "AI, Future of Work & Emotional Intelligence",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_ai-futureofwork-emotionalintelligence-activity-7473378671429361665-ygjA",
    },
    {
        "title": "Gulf Jobs, Middle East & NRI",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_gulfjobs-middleeast-nri-activity-7473688995017711616-Cfhp",
    },
    {
        "title": "Artificial Intelligence, Mental Health & Psychology",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_artificialintelligence-mentalhealth-psychology-activity-7474810942019510273-3PXR",
    },
    {
        "title": "Artificial Intelligence, Psychotherapy & Mental Health",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_artificialintelligence-psychotherapy-mentalhealth-activity-7474823153706377216-A-JQ",
    },
    {
        "title": "Can AI Predict Employee Turnover Before It Happens?",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_can-ai-predict-employee-turnover-before-activity-7475112570429915138-cvC3",
    },
    {
        "title": "Why Do Some People Fear Public Speaking?",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_why-do-some-people-fear-public-speaking-activity-7475377843334471680-1sby",
    },
    {
        "title": "Introducing the Tamil Mental Health Initiative",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_im-pleased-to-introduce-the-tamil-mental-activity-7475763847530704898-G2E_",
    },
    {
        "title": "Final Year Psychology Students",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_final-year-psychology-students-are-activity-7477770695327023104-tByK",
    },
    {
        "title": "AI & Psychology: The Future Starts Now",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_ai-psychology-the-future-starts-now-activity-7477778399193640960-4ld6",
    },
    {
        "title": "Can Just 10 Minutes in Nature Improve Your Mind?",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_can-just-10-minutes-in-nature-improve-activity-7480590050582220802-AQ-R",
    },
    {
        "title": "Psychology, Neuroscience & Mental Health",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_psychology-neuroscience-mentalhealth-activity-7482034327606710272-243s",
    },
    {
        "title": "The Psychology Behind 10 World-Changing Ideas",
        "url": "https://www.linkedin.com/posts/d-durga-116800416_the-psychology-behind-10-world-changing-activity-7482298590024060928-0gSa",
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
