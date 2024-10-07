from flask import Flask, render_template, jsonify, url_for
import os
import feedparser
import re
import html
from datetime import datetime
from dateutil import parser as dateparser

app = Flask(__name__)

def load_feeds_from_file(filename):
    feed_urls = []
    try:
        with open(filename, 'r') as file:
            for line in file:
                url = line.strip()
                if url and not url.startswith('#'):
                    feed_urls.append(url)
        if not feed_urls:
            print(f"No feeds found in {filename}.")
    except FileNotFoundError:
        print(f"Feed file {filename} not found.")
    return feed_urls

# Load feeds from external file
RSS_FEEDS = load_feeds_from_file('feeds.txt')

TOPICS = [
    "Artificial Intelligence", "Machine Learning", "Tech Trends", "Startup News", 
    "New Technology", "AI Innovation", "Blockchain", "Quantum Computing", "SaaS", 
    "Cloud Computing", "Cybersecurity", "Web Development", "Mobile Technology", 
    "Data Science", "Tech Gadgets", "IT Infrastructure", "IoT", 
    "Digital Transformation", "AI Research", "Software Development", "Venture Capital", 
    "Tech Investments", "Emerging Technologies", "Fintech", "Augmented Reality", 
    "Tech Startup", "AI Tools", "Robotics", "Innovation Hub", "Tech Ecosystem"
]

def clean_summary(summary):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', summary)
    cleantext = html.unescape(cleantext)
    return cleantext.strip()

def extract_image_from_content(content):
    match = re.search(r'<img[^>]+src="([^">]+)"', content)
    if match:
        return match.group(1)
    return ''

def fetch_rss_feeds(feed_urls):
    articles = []
    for url in feed_urls:
        feed = feedparser.parse(url)
        feed_source = feed.feed.get('title', 'Unknown Source')  # Get the feed's title as the source name
        for entry in feed.entries:
            summary = entry.get('summary', 'No summary')
            summary = clean_summary(summary)
            published = entry.get('published', '')
            try:
                published_parsed = dateparser.parse(published)
                if published_parsed is not None:
                    published_parsed = published_parsed.replace(tzinfo=None)
                    published_str = published_parsed.strftime('%Y-%m-%d %H:%M')
                else:
                    published_str = 'Unknown date'
            except Exception as e:
                print(f"Error parsing date '{published}': {e}")
                published_parsed = None
                published_str = 'Unknown date'

            image_url = ''
            if 'media_content' in entry:
                image_url = entry.media_content[0].get('url', '')
            elif 'media_thumbnail' in entry:
                image_url = entry.media_thumbnail[0].get('url', '')
            elif 'links' in entry:
                for link in entry.links:
                    if link.get('type', '').startswith('image'):
                        image_url = link.get('href', '')
                        break
            if not image_url:
                content = entry.get('content', [{'value': ''}])[0]['value']
                image_url = extract_image_from_content(content)
            if not image_url:
                image_url = url_for('static', filename='assets/fallback.jpeg', _external=True)

            article = {
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', 'No link'),
                'published': published_str,
                'published_parsed': published_parsed,
                'summary': summary,
                'image': image_url,
                'source': feed_source  # Add the feed source to the article data
            }
            articles.append(article)
    return articles

def filter_articles_exact_match(articles, topics):
    filtered = []
    topics_lower = [topic.lower() for topic in topics]
    for article in articles:
        article_text = f"{article['title']} {article['summary']}".lower()
        if any(topic in article_text for topic in topics_lower):
            filtered.append(article)
    return filtered

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/articles')
def get_articles():
    articles = fetch_rss_feeds(RSS_FEEDS)
    filtered_articles = filter_articles_exact_match(articles, TOPICS)
    seen_links = set()
    unique_articles = []
    for article in filtered_articles:
        if article['link'] not in seen_links:
            seen_links.add(article['link'])
            unique_articles.append(article)
    unique_articles.sort(key=lambda x: x['published_parsed'] or datetime.min, reverse=True)
    for article in unique_articles:
        if len(article['summary']) > 300:
            article['summary'] = article['summary'][:300] + '...'
        article.pop('published_parsed', None)
    return jsonify(unique_articles)

if __name__ == '__main__':
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
