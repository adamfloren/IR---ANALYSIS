#!/usr/bin/env python3
"""
Daily IR Issue Generator
Fetches today's top geopolitics headline and generates a full
Triple-Level + Historical Mirror analysis using Claude Opus 4.6.
Output: today.json  (loaded live by index.html)
"""

import os
import json
import re
from datetime import datetime

import feedparser
import anthropic

# ── IR keyword filter ────────────────────────────────────────────────────────
IR_KW = [
    "china", "russia", "nato", "ukraine", "iran", "israel", "taiwan",
    "korea", "nuclear", "sanction", "treaty", "ceasefire", "war",
    "conflict", "military", "diplomacy", "geopolit", "pentagon", "kremlin",
    "united nations", "security council", "missile", "invasion", "coup",
    "election", "tariff", "trade war", "summit", "bilateral",
]

RSS_FEEDS = [
    ("BBC World",       "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("New York Times",  "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ("The Guardian",    "https://www.theguardian.com/world/rss"),
]


def fetch_headline() -> dict | None:
    """Return the first IR-relevant headline from any feed."""
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
            print(f"  Feed error ({source}): {exc}")
    return None


def generate_analysis(headline: dict) -> dict:
    """Call Claude Opus 4.6 with adaptive thinking to produce structured JSON."""
    client = anthropic.Anthropic()
    today_str = datetime.now().strftime("%B %Y")
    date_id   = datetime.now().strftime("%Y%m%d")

    prompt = f"""You are a Professor of International Relations. Analyze this current news event and produce a structured educational analysis.

NEWS EVENT
Title:   {headline['title']}
Summary: {headline['summary']}
Source:  {headline['source']}  —  {headline['link']}

Return ONLY a valid JSON object with the structure below — no markdown fences, no preamble, no trailing text.

{{
  "id": "auto-{date_id}",
  "meta": {{
    "number": "LIVE",
    "title":    {{"en": "<concise English title>",    "he": "<Hebrew title>"}},
    "subtitle": {{"en": "<English subtitle>",          "he": "<Hebrew subtitle>"}},
    "tags":     {{"en": ["tag1","tag2","tag3"],         "he": ["תג1","תג2","תג3"]}},
    "lastUpdated": "{today_str}"
  }},
  "landscape": {{
    "summary": {{"en": "<2-3 sentence fact-based overview>", "he": "<Hebrew>"}},
    "keyFacts": [
      {{"text": {{"en": "<fact>", "he": "<Hebrew>"}}, "citations": [{{"id":"src1","label":"1","title":"{headline['source']}","href":"{headline['link']}"}}]}},
      {{"text": {{"en": "<fact>", "he": "<Hebrew>"}}, "citations": []}},
      {{"text": {{"en": "<fact>", "he": "<Hebrew>"}}, "citations": []}}
    ],
    "timeline": [
      {{"year": "<year>", "text": {{"en": "<event>", "he": "<Hebrew>"}}}},
      {{"year": "<year>", "text": {{"en": "<event>", "he": "<Hebrew>"}}}},
      {{"year": "<year>", "text": {{"en": "<event>", "he": "<Hebrew>"}}}}
    ]
  }},
  "analysis": {{
    "individual": {{
      "actor":     {{"en": "<key leaders by name>", "he": "<Hebrew>"}},
      "text":      {{"en": "<2-4 sentences — psychology, decision-making, framing>", "he": "<Hebrew>"}},
      "citations": []
    }},
    "state": {{
      "actor":     {{"en": "<states involved>", "he": "<Hebrew>"}},
      "text":      {{"en": "<2-4 sentences — domestic politics, regime type, national interest>", "he": "<Hebrew>"}},
      "citations": []
    }},
    "systemic": {{
      "actor":     {{"en": "International System", "he": "המערכת הבינלאומית"}},
      "text":      {{"en": "<2-4 sentences — anarchy, balance of power, IR theory reference>", "he": "<Hebrew>"}},
      "citations": []
    }}
  }},
  "historical": {{
    "parallel":     {{"en": "<Relevant historical precedent (year range)>", "he": "<Hebrew>"}},
    "similarities": {{"en": ["<sim1>","<sim2>","<sim3>"], "he": ["<עב1>","<עב2>","<עב3>"]}},
    "differences":  {{"en": ["<diff1>","<diff2>","<diff3>"], "he": ["<עב1>","<עב2>","<עב3>"]}},
    "keyTakeaway":  {{"en": "<one sentence verdict on the parallel's validity>", "he": "<Hebrew>"}},
    "citations": []
  }}
}}

Rules:
- Academic, rigorous, zero fluff.
- Hebrew must be proper Israeli academic Hebrew.
- Name specific leaders in the individual-level analysis.
- Reference a named IR theorist (Waltz, Mearsheimer, Keohane, Farrell, etc.) in the systemic analysis.
- Historical parallel must be genuinely analogous — flag if it is a weak analogy.
"""

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract text block (thinking blocks come first when adaptive thinking fires)
    text = next(b.text for b in response.content if b.type == "text")

    # Robustly extract the JSON object from the response
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON found in Claude response:\n{text[:400]}")

    return json.loads(match.group())


def main() -> None:
    print("── Daily IR Issue Generator ──────────────────────")
    print("Fetching latest IR headline…")
    headline = fetch_headline()

    if not headline:
        print("No IR-relevant headline found today. Exiting without writing today.json.")
        return

    print(f"  → {headline['title'][:80]}")
    print("Calling Claude Opus 4.6 (adaptive thinking)…")

    issue = generate_analysis(headline)

    out_path = os.path.join(os.path.dirname(__file__), "today.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(issue, f, ensure_ascii=False, indent=2)

    print(f"  ✓ Saved today.json")
    print(f"  Title: {issue['meta']['title']['en']}")
    print("──────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
