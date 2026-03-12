#!/usr/bin/env python3
import os
import json
import re
from datetime import datetime
import feedparser
import streamlit as st
import google.generativeai as genai

# הגדרת ה-API של גוגל - מושך את המפתח מה-Secrets של Streamlit
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ── IR keyword filter ────────────────────────────────────────
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
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # פרומפט ממוקד ליצירת JSON תקין
        prompt = f"""You are a Professor of International Relations. Analyze this news:
        Title: {headline['title']}
        Summary: {headline['summary']}
        
        Return ONLY a JSON object with these keys: "landscape", "analysis", "historical".
        Do not add markdown formatting, no backticks, no introduction text. Just raw JSON."""

        response = model.generate_content(prompt)
        
        # חילוץ ה-JSON
        match = re.search(r"\{[\s\S]*\}", response.text)
        if not match:
            print(f"Error: No JSON found in response. Raw: {response.text}")
            return {"error": "Invalid format"}
            
        return json.loads(match.group())
        
    except Exception as e:
        print(f"Analysis error: {e}")
        return {"error": str(e)}

def main() -> None:
    st.title("IR Analysis Professor")
    headline = fetch_headline()
    
    if headline:
        st.write(f"Analyzing: {headline['title']}")
        analysis = generate_analysis(headline)
        
        if "error" in analysis:
            st.error(f"Error generating analysis: {analysis['error']}")
        else:
            st.subheader("Current Landscape")
            st.write(analysis.get("landscape"))
            st.subheader("Multidimensional Analysis")
            st.write(analysis.get("analysis"))
            st.subheader("Historical Mirroring")
            st.write(analysis.get("historical"))
    else:
        st.warning("No relevant headlines found.")

if __name__ == "__main__":
    main()