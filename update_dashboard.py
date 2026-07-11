import os
import re
import requests
from datetime import datetime, timezone, timedelta

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

THAI_MONTHS = ["มกราคม","กุมภาพันธ์","มีนาคม","เมษายน","พฤษภาคม","มิถุนายน","กรกฎาคม","สิงหาคม","กันยายน","ตุลาคม","พฤศจิกายน","ธันวาคม"]
now_thai = datetime.now(timezone.utc) + timedelta(hours=7)
THAI_DATE = f"{now_thai.day} {THAI_MONTHS[now_thai.month - 1]} {now_thai.year + 543}"

def get_news():
    if not GEMINI_API_KEY: return "NO_NEW_NEWS"
    prompt = f"วันนี้คือ {THAI_DATE} สรุปข่าวเด่นเชิงกลยุทธ์ 1 ข่าวของ รพ.เอกชนไทย (BDMS หรือ BH) เป็น HTML: <div class=\"alert gold\"><div><strong>[ชื่อ รพ.]: [หัวข้อ]</strong> — [เนื้อหา 1 ประโยค]</div></div>"
    try:
        res = requests.post(GEMINI_URL, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30).json()
        return res['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "NO_NEW_NEWS"

def main():
    with open("index.html", "r", encoding="utf-8") as f: content = f.read()
    if "</html>" not in content: return
    
    content = re.sub(r'(<div class="date-badge" id="reportDate">)[^<]*(</div>)', rf'\g<1>{THAI_DATE}\g<2>', content)
    content = re.sub(r'(<div class="sec-title" id="referenceSection">📚 แหล่งอ้างอิง \(เข้าถึง )[^)]*(\)</div>)', rf'\g<1>{THAI_DATE}\g<2>', content)
    
    news = get_news()
    if news and "NO_NEW_NEWS" not in news and "<div" in news:
        clean_news = news.replace("```html", "").replace("```", "").strip()
        content = content.replace("", f"\n  {clean_news}")
        
    with open("index.html", "w", encoding="utf-8") as f: f.write(content)

if __name__ == "__main__": main()
