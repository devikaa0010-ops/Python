import csv
from collections import Counter
from datetime import datetime
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.bbc.com"

# Category name -> section page URL
CATEGORIES = {
    "World": BASE_URL + "/news/world",
    "Business": BASE_URL + "/business",
    "Technology": BASE_URL + "/innovation/technology",
    "Science": BASE_URL + "/innovation/science",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}

CSV_FILE = "news_headlines.csv"


def fetch_page(url):
    """Download a web page and return its HTML text (None if it fails)."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()          # raise error for 4xx / 5xx
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"  Could not fetch {url}: {e}")
        return None


def find_date(tag):
    """Look for a publication date near a headline tag."""
    # Walk up a few parent elements (the 'card' that holds the headline)
    card = tag
    for _ in range(5):
        if card.parent is None:
            break
        card = card.parent
        time_tag = card.find("time")
        if time_tag:
            return time_tag.get("datetime") or time_tag.get_text(strip=True)
        updated = card.find(attrs={"data-testid": "card-metadata-lastupdated"})
        if updated:
            return updated.get_text(strip=True)      # e.g. "2 hrs ago"
    # Fallback: date on which the headline was scraped
    return datetime.now().strftime("%Y-%m-%d")


def scrape_category(category, url):
    """Return a list of {headline, date, category, link} dictionaries."""
    html = fetch_page(url)
    if html is None:
        return []

    soup = BeautifulSoup(html, "html.parser")
    articles = []
    seen = set()

    # BBC marks headlines with data-testid="card-headline";
    # fall back to <h2>/<h3> tags if that attribute is not present.
    headline_tags = soup.find_all(attrs={"data-testid": "card-headline"})
    if not headline_tags:
        headline_tags = soup.find_all(["h2", "h3"])

    for tag in headline_tags:
        text = tag.get_text(strip=True)
        if len(text) < 15 or text in seen:    # skip short labels / duplicates
            continue
        seen.add(text)

        link_tag = tag.find_parent("a")
        link = ""
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            link = href if href.startswith("http") else BASE_URL + href

        articles.append({
            "headline": text,
            "date": find_date(tag),
            "category": category,
            "link": link,
        })
    return articles


def save_to_csv(articles, filename):
    """Write the scraped articles to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["headline", "date", "category", "link"])
        writer.writeheader()
        writer.writerows(articles)
    print(f"\nSaved {len(articles)} headlines to '{filename}'")


def analyse(articles):
    """Simple analysis: count per category and most common words."""
    print("\n===== ANALYSIS =====")
    print("Headlines per category:")
    for cat, count in Counter(a["category"] for a in articles).items():
        print(f"  {cat:<12}: {count}")

    stop_words = {"the", "a", "an", "of", "to", "in", "and", "for", "on", "is",
                  "with", "as", "at", "by", "from", "after", "over", "how",
                  "what", "why", "its", "it", "be", "are", "was", "his", "her"}
    words = []
    for a in articles:
        for w in a["headline"].lower().split():
            w = w.strip(".,:;!?'\"()‘’“”")
            if w.isalpha() and w not in stop_words:
                words.append(w)

    print("\nTop 10 keywords in headlines:")
    for word, count in Counter(words).most_common(10):
        print(f"  {word:<15} {count}")


def main():
    all_articles = []
    for category, url in CATEGORIES.items():
        print(f"Scraping {category} ...")
        items = scrape_category(category, url)
        print(f"  Found {len(items)} headlines")
        all_articles.extend(items)

    if not all_articles:
        print("No headlines extracted. Check the internet connection.")
        return

    print("\nSample headlines:")
    for a in all_articles[:5]:
        print(f"  [{a['category']}] {a['headline']} ({a['date']})")

    save_to_csv(all_articles, CSV_FILE)
    analyse(all_articles)


if __name__ == "__main__":
    main()