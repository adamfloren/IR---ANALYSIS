#!/usr/bin/env python3
import json
import re
import streamlit as st
import feedparser
import google.generativeai as genai

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

IR_KW = ["china", "russia", "nato", "ukraine", "iran", "israel", "taiwan", "korea", "nuclear", "war", "conflict", "election", "economy", "crisis", "global", "biden", "trump", "eu", "security", "middle east", "peace", "agreement"]
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
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""You are a Professor of International Relations. Analyze this news:
    Title: {headline['title']}
    Summary: {headline['summary']}
    Source: {headline['source']} - {headline['link']}
    Return ONLY a valid JSON object with these keys: "landscape", "analysis", "historical". 
    Do not include markdown or backticks."""

    response = model.generate_content(prompt)
    match = re.search(r"\{[\s\S]*\}", response.text)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group())

def main() -> None:
    st.title("IR Analysis Professor")
    st.write("סטטוס: סורק אתרי חדשות...")
    
    headline = fetch_headline()
    
    if headline:
        st.write(f"✅ נמצאה כותרת: **{headline['title']}**")
        try:
            analysis = generate_analysis(headline)
            st.subheader("Current Landscape")
            st.write(analysis.get("landscape"))
            st.subheader("Multidimensional Analysis")
            st.write(analysis.get("analysis"))
            st.subheader("Historical Mirroring")
            st.write(analysis.get("historical"))
        except Exception as e:
            st.error(f"שגיאה בניתוח: {e}")
    else:
        st.warning("לא נמצאו כותרות חדשות שמתאימות למילות המפתח.")

if __name__ == "__main__":
    main()