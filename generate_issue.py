#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime

import feedparser
import google.generativeai as genai

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

IR_KW = ["china", "russia", "nato", "ukraine", "iran", "israel", "taiwan", "korea",
         "nuclear", "war", "conflict", "election", "crisis", "global", "trump", "eu",
         "security", "middle east", "peace", "agreement", "sanction", "military"]

RSS_FEEDS = [
    ("BBC World",    "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("New York Times","https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
]


def fetch_headline() -> dict | None:
    for source, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                body = f"{entry.title} {entry.get('summary', '')}".lower()
                if any(kw in body for kw in IR_KW):
                    return {
                        "title":   entry.title,
                        "summary": entry.get("summary", ""),
                        "link":    entry.link,
                        "source":  source,
                    }
        except Exception as exc:
            print(f"Feed error ({source}): {exc}")
    return None


def generate_analysis(headline: dict) -> dict:
    model  = genai.GenerativeModel("gemini-2.0-flash")
    today  = datetime.now().strftime("%B %Y")
    date_id = datetime.now().strftime("%Y%m%d")

    prompt = f"""You are a Professor of International Relations. Analyze this news event and return a structured JSON object for an educational IR web application.

NEWS:
Title: {headline['title']}
Summary: {headline['summary']}
Source: {headline['source']} — {headline['link']}

Return ONLY a valid JSON object with this exact structure (no markdown, no backticks):
{{
  "id": "auto-{date_id}",
  "meta": {{
    "number": "LIVE",
    "title":    {{"en": "<concise title>",    "he": "<Hebrew title>"}},
    "subtitle": {{"en": "<subtitle>",         "he": "<Hebrew subtitle>"}},
    "tags":     {{"en": ["tag1","tag2","tag3"],"he": ["תג1","תג2","תג3"]}},
    "lastUpdated": "{today}"
  }},
  "landscape": {{
    "summary": {{"en": "<2-3 sentence overview>", "he": "<Hebrew overview>"}},
    "keyFacts": [
      {{"text": {{"en": "<fact 1>", "he": "<Hebrew fact 1>"}}, "citations": [{{"id": "src1", "label": "1", "title": "{headline['source']}", "href": "{headline['link']}"}}]}},
      {{"text": {{"en": "<fact 2>", "he": "<Hebrew fact 2>"}}, "citations": []}},
      {{"text": {{"en": "<fact 3>", "he": "<Hebrew fact 3>"}}, "citations": []}}
    ],
    "timeline": [
      {{"year": "<year>", "text": {{"en": "<event>", "he": "<Hebrew event>"}}}},
      {{"year": "<year>", "text": {{"en": "<event>", "he": "<Hebrew event>"}}}},
      {{"year": "<year>", "text": {{"en": "<event>", "he": "<Hebrew event>"}}}}
    ]
  }},
  "analysis": {{
    "individual": {{"actor": {{"en": "<key leaders>",       "he": "<Hebrew>"}}, "text": {{"en": "<2-4 sentence individual-level analysis>", "he": "<Hebrew>"}}, "citations": []}},
    "state":      {{"actor": {{"en": "<states involved>",   "he": "<Hebrew>"}}, "text": {{"en": "<2-4 sentence state-level analysis>",      "he": "<Hebrew>"}}, "citations": []}},
    "systemic":   {{"actor": {{"en": "International System","he": "המערכת הבינלאומית"}}, "text": {{"en": "<2-4 sentence systemic/IR-theory analysis>", "he": "<Hebrew>"}}, "citations": []}}
  }},
  "historical": {{
    "parallel":     {{"en": "<Relevant historical parallel (year)>", "he": "<Hebrew>"}},
    "similarities": {{"en": ["<sim 1>","<sim 2>","<sim 3>"], "he": ["<Hebrew 1>","<Hebrew 2>","<Hebrew 3>"]}},
    "differences":  {{"en": ["<diff 1>","<diff 2>","<diff 3>"],"he": ["<Hebrew 1>","<Hebrew 2>","<Hebrew 3>"]}},
    "keyTakeaway":  {{"en": "<one sentence on what this historical parallel teaches us>", "he": "<Hebrew>"}},
    "citations": []
  }}
}}

Rules:
- Academic, rigorous tone — never jargon-heavy without context
- Hebrew must be proper Israeli academic Hebrew (RTL)
- Individual level: name specific leaders and their psychology/decisions
- State level: analyze domestic politics and national interests
- Systemic level: reference IR theory (Waltz, Mearsheimer, Keohane, etc.)
- Historical parallel: a genuinely relevant precedent, not a cliché
"""

    response = model.generate_content(prompt)
    match = re.search(r"\{[\s\S]*\}", response.text)
    if not match:
        raise ValueError(f"No JSON in response: {response.text[:300]}")
    return json.loads(match.group())


def main() -> None:
    print("Scanning RSS feeds for IR headlines...")
    headline = fetch_headline()

    if not headline:
        print("No IR-relevant headline found. Skipping.")
        return

    print(f"Headline: {headline['title']}")
    print("Generating analysis with Gemini...")

    issue = generate_analysis(headline)

    with open("today.json", "w", encoding="utf-8") as f:
        json.dump(issue, f, ensure_ascii=False, indent=2)

    print(f"Saved today.json: {issue['meta']['title']['en']}")


if __name__ == "__main__":
    main()
