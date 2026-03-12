#!/usr/bin/env python3
import os
import json
import re
from datetime import datetime
import feedparser
import streamlit as st
import google.generativeai as genai

# הגדרת ה-API של גוגל
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ── IR keyword filter (נשאר ללא שינוי) ────────────────────────────────────────
IR_KW = ["china", "russia", "nato", "ukraine", "iran", "israel", "taiwan", "korea", "nuclear", "sanction", "treaty", "ceasefire", "war", "conflict", "military", "diplomacy", "geopolit", "pentagon", "kremlin", "united nations", "security council", "missile", "invasion", "coup", "election", "tariff", "trade war", "summit", "bilateral"]
RSS_FEEDS = [("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"), ("New York Times", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"), ("The Guardian", "https://www.theguardian.com/world/rss")]

def fetch_headline() -> dict | None:
    for source, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                body = f"{entry.title} {entry.get('summary', '')}".lower()
                if any(kw in body for kw in IR_KW):
                    return {"title": entry.title, "summary": entry.get("summary", ""), "link": entry.link, "source": source}
        except Exception as exc:
            print(f"Feed error ({source}): {exc}")
    return None

def generate_analysis(headline: dict) -> dict:
    """שימוש ב-Gemini במקום ב-Claude"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    today_str = datetime.now().strftime("%B %Y")
    date_id = datetime.now().strftime("%Y%m%d")

    # הפרומפט המקורי שלך (השארתי אותו כפי שהוא)
    prompt = f"""You are a Professor of International Relations. Analyze this current news event:
    Title: {headline['title']}
    Summary: {headline['summary']}
    Source: {headline['source']} — {headline['link']}
    Return ONLY a valid JSON object with the structure... (המשך הפרומפט המקורי שלך כאן)"""

    response = model.generate_content(prompt)
    
    # חילוץ ה-JSON מהתשובה
    match = re.search(r"\{[\s\S]*\}", response.text)
    if not match:
        raise ValueError("No JSON found in Gemini response")

    return json.loads(match.group())

# שאר הפונקציה main נשארת כמעט ללא שינוי...